"""Ein kleines Modellprotokoll: chat() liefert {name, arguments}.

Ollama liefert JSON nach dem Werkzeug-Schema. Das erleichtert die Verarbeitung,
ersetzt aber niemals die Validierung in repository.py. Der Scripted-Client
wird ausschließlich in Offline-Tests benutzt; er repariert kein echtes Repo.
"""

from __future__ import annotations

import asyncio
import copy
import json

import httpx

from harness.config import Settings
from harness.errors import Cancelled, ModelError


class ScriptedModelClient:
    """Testdouble: vorgegebene Antworten, Fehler und Wiederholungen ohne Netzwerk."""

    provider, name, simulated = "scripted", "deterministic-script", True

    def __init__(self, replies: list[dict | Exception], *, repeat=False):
        self.replies, self.repeat = replies, repeat
        self.requests: list[list[dict]] = []
        self.index = 0

    def chat(self, messages, tools, cancel):
        if cancel.is_set():
            raise Cancelled("Abbruch angefordert")
        self.requests.append(copy.deepcopy(messages))
        if not self.replies or self.index >= len(self.replies) and not self.repeat:
            raise ModelError("Simulierte Antworten aufgebraucht")
        reply = self.replies[self.index % len(self.replies)]
        self.index += 1
        if isinstance(reply, Exception):
            raise reply
        return copy.deepcopy(reply)


def tool_reply(name: str, **arguments) -> dict:
    return {"name": name, "arguments": arguments}


class OllamaModelClient:
    """HTTP-Verbindung zum konfigurierten lokalen Modell; besitzt keine Dateiwerkzeuge."""

    provider, simulated = "ollama", False

    def __init__(self, settings: Settings):
        self.settings, self.name = settings, settings.model

    async def _request(self, messages, tools, cancel):
        # Die Kopie verhindert, dass Werkzeugbeschreibungen bei jedem Aufruf
        # erneut an den gespeicherten Systemprompt angehängt werden.
        payload = {
            "model": self.name,
            "messages": copy.deepcopy(messages),
            "stream": False,
            "options": {"temperature": 0, "num_ctx": 16384, "num_predict": 4096},
        }
        alternatives = []
        for tool in tools:
            function = tool["function"]
            alternatives.append(
                {
                    "type": "object",
                    "properties": {
                        "name": {"const": function["name"]},
                        "arguments": function["parameters"],
                    },
                    "required": ["name", "arguments"],
                    "additionalProperties": False,
                }
            )
        payload["format"] = {"oneOf": alternatives}
        payload["messages"][0]["content"] += (
            "\nReturn one JSON object with name and arguments for the next tool. No Markdown. "
            "Use finish when done. Tool definitions: " + json.dumps(tools)
        )

        async def request():
            async with httpx.AsyncClient(
                base_url=self.settings.ollama_base_url,
                timeout=self.settings.limits.model_seconds,
                trust_env=False,
            ) as client:
                async with client.stream("POST", "/api/chat", json=payload) as response:
                    response.raise_for_status()
                    data = bytearray()
                    async for chunk in response.aiter_bytes(4096):
                        if len(data) + len(chunk) > 262144:
                            raise ModelError("Modellantwort überschreitet 256 KiB")
                        data.extend(chunk)
                    decoded = json.loads(data)
                    message = decoded.get("message") if isinstance(decoded, dict) else None
                    if not isinstance(message, dict):
                        raise ModelError("Ollama-Antwort enthält keine Nachricht")
                    return json.loads(message.get("content", ""))

        # HTTP läuft als abbrechbare Coroutine. Ein bloßer Thread-Timeout würde
        # die wartende Verbindung weiterlaufen lassen. finally räumt sie auf.
        task = asyncio.create_task(request())
        try:
            async with asyncio.timeout(self.settings.limits.model_seconds):
                while not task.done():
                    if cancel.is_set():
                        raise Cancelled("Modellanfrage abgebrochen")
                    await asyncio.sleep(0.05)
                return await task
        finally:
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    def chat(self, messages, tools, cancel):
        try:
            return asyncio.run(self._request(messages, tools, cancel))
        except (httpx.HTTPError, TimeoutError, ValueError) as exc:
            raise ModelError(f"Ollama-Anfrage fehlgeschlagen: {exc}") from exc

    def diagnose(self) -> dict:
        try:
            with httpx.Client(
                base_url=self.settings.ollama_base_url, timeout=5, trust_env=False
            ) as client:
                tags = client.get("/api/tags")
                tags.raise_for_status()
                models = [m["name"] for m in tags.json().get("models", [])]
                if self.name not in models:
                    return {
                        "ready": False,
                        "reason": "Konfiguriertes Modell nicht installiert",
                        "models": models,
                    }
                shown = client.post("/api/show", json={"model": self.name})
                shown.raise_for_status()
                capabilities = shown.json().get("capabilities", [])
                # Wir verwenden strukturierte JSON-Ausgaben, keine nativen Toolcalls.
                # Daher ist 'tools' keine Voraussetzung. Schemaqualität wird erst
                # beim echten Aufruf sichtbar und dort strikt geprüft.
                return {
                    "ready": "completion" in capabilities,
                    "models": models,
                    "capabilities": capabilities,
                    "reason": "" if "completion" in capabilities else "Textgenerierung fehlt",
                }
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            return {
                "ready": False,
                "reason": f"Ollama nicht erreichbar oder ungültige Antwort: {exc}",
            }
