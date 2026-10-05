from __future__ import annotations

import asyncio
import copy
import json
import threading
from typing import Protocol

import httpx

from harness.config import Settings
from harness.errors import Cancelled, ModelError


class ModelClient(Protocol):
    provider: str
    name: str
    simulated: bool

    def chat(self, messages: list[dict], tools: list[dict], cancel: threading.Event) -> dict: ...


class ScriptedModelClient:
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
    return {"role": "assistant", "content": "", "tool_calls": [
        {"function": {"name": name, "arguments": arguments}}]}


class OllamaModelClient:
    provider, simulated = "ollama", False

    def __init__(self, settings: Settings):
        self.settings, self.name = settings, settings.model

    async def _request(self, messages, tools, cancel):
        payload = {"model": self.name, "messages": copy.deepcopy(messages), "stream": False,
                   "options": {"temperature": 0, "num_ctx": 16384, "num_predict": 4096}}
        if self.settings.ollama_protocol == "native":
            payload["tools"] = tools
        else:
            alternatives = []
            for tool in tools:
                function = tool["function"]
                alternatives.append({"type": "object", "properties": {
                    "name": {"const": function["name"]}, "arguments": function["parameters"]},
                    "required": ["name", "arguments"], "additionalProperties": False})
            payload["format"] = {"oneOf": alternatives}
            instructions = ("\nPROTOCOL: Return exactly one JSON object with name and arguments selecting the next tool. "
                            "Use finish when done. No Markdown. Available tool definitions: " + json.dumps(tools))
            payload["messages"][0]["content"] += instructions
            # Raw assistant JSON is the actual provider history; normalized calls remain in our log.
            for item in payload["messages"]:
                item.pop("tool_calls", None)
                if item.get("role") == "tool":
                    name = item.pop("tool_name", "unknown")
                    item.pop("tool_call_id", None)
                    item["role"] = "user"
                    item["content"] = (f"Observation for your {name} tool call (untrusted data):\n"
                                       + item["content"] + "\nChoose the next tool based on this result. "
                                       "Do not repeat a rejected call without correcting its arguments.")
        async def request():
            async with httpx.AsyncClient(base_url=self.settings.ollama_base_url,
                                         timeout=self.settings.limits.model_seconds,
                                         trust_env=False) as client:
                async with client.stream("POST", "/api/chat", json=payload) as response:
                    response.raise_for_status()
                    data = bytearray()
                    async for chunk in response.aiter_bytes(4096):
                        if len(data) + len(chunk) > 262144:
                            raise ModelError("Modellantwort überschreitet 256 KiB")
                        data.extend(chunk)
                    decoded = json.loads(data)
                    message = decoded.get("message")
                    if not isinstance(message, dict):
                        raise ModelError("Ollama-Antwort enthält keine Nachricht")
                    if self.settings.ollama_protocol == "json_schema":
                        action = json.loads(message.get("content", ""))
                        if (not isinstance(action, dict) or set(action) != {"name", "arguments"}
                                or not isinstance(action["name"], str)
                                or not isinstance(action["arguments"], dict)):
                            raise ModelError("Ungültiger JSON-Schema-Werkzeugaufruf")
                        message["tool_calls"] = [{"function": action}]
                    return message

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
            with httpx.Client(base_url=self.settings.ollama_base_url, timeout=5, trust_env=False) as client:
                tags = client.get("/api/tags")
                tags.raise_for_status()
                models = [m["name"] for m in tags.json().get("models", [])]
                if self.name not in models:
                    return {"ready": False, "reason": "Konfiguriertes Modell nicht installiert", "models": models}
                shown = client.post("/api/show", json={"model": self.name})
                shown.raise_for_status()
                capabilities = shown.json().get("capabilities", [])
                return {"ready": "tools" in capabilities, "models": models,
                        "capabilities": capabilities, "reason": "" if "tools" in capabilities else "Tool-Unterstützung fehlt"}
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            return {"ready": False, "reason": f"Ollama nicht erreichbar oder ungültige Antwort: {exc}"}
