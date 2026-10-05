import asyncio
import json
import threading
import time

import httpx
import pytest

from harness.config import Limits, Settings
from harness.errors import Cancelled, ModelError
from harness.models import OllamaModelClient


def test_ollama_native_protocol_preserved(monkeypatch):
    captured = []
    def handler(request):
        captured.append(json.loads(request.content))
        return httpx.Response(200, json={"message": {"role": "assistant", "tool_calls": [
            {"function": {"index": 0, "name": "read_file", "arguments": {"path": "app.py"}}}]}})
    real_client = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: real_client(
        **kwargs, transport=httpx.MockTransport(handler)))
    model = OllamaModelClient(Settings(ollama_protocol="native"))
    messages = [{"role": "assistant", "tool_calls": [{"function": {"index": 0, "name": "read_file", "arguments": {}}}]},
                {"role": "tool", "tool_name": "read_file", "content": "result"}]
    response = model.chat(messages, [], threading.Event())
    assert response["tool_calls"][0]["function"]["index"] == 0
    assert captured[0]["messages"] == messages
    assert captured[0]["stream"] is False


@pytest.mark.parametrize("content", [b"not-json", b'{"wrong":"schema"}', b"x" * 300000],
                         ids=["invalid-json", "missing-message", "oversized"])
def test_malformed_and_oversized_responses(monkeypatch, content):
    real_client = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: real_client(
        **kwargs, transport=httpx.MockTransport(lambda request: httpx.Response(200, content=content))))
    with pytest.raises(ModelError):
        OllamaModelClient(Settings(ollama_protocol="native")).chat([], [], threading.Event())


def test_cancellation_interrupts_pending_http_request(monkeypatch):
    closed = threading.Event()
    async def handler(request):
        try:
            await asyncio.sleep(30)
        finally:
            closed.set()
        return httpx.Response(200, json={})
    real_client = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: real_client(
        **kwargs, transport=httpx.MockTransport(handler)))
    cancel = threading.Event()
    timer = threading.Timer(0.15, cancel.set)
    timer.start()
    start = time.monotonic()
    with pytest.raises(Cancelled):
        OllamaModelClient(Settings(ollama_protocol="native")).chat([], [], cancel)
    timer.join()
    assert closed.is_set() and time.monotonic() - start < 2


def test_total_http_deadline(monkeypatch):
    async def handler(request):
        await asyncio.sleep(30)
        return httpx.Response(200, json={})
    real_client = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: real_client(
        **kwargs, transport=httpx.MockTransport(handler)))
    with pytest.raises(ModelError):
        OllamaModelClient(Settings(ollama_protocol="native", limits=Limits(model_seconds=1))).chat([], [], threading.Event())


def test_schema_protocol_is_explicit_and_preserves_raw_history(monkeypatch):
    from harness.repository import tool_schemas
    captured = []
    raw = json.dumps({"name": "list_files", "arguments": {}})
    def handler(request):
        captured.append(json.loads(request.content))
        return httpx.Response(200, json={"message": {"role": "assistant", "content": raw}})
    real_client = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: real_client(
        **kwargs, transport=httpx.MockTransport(handler)))
    reply = OllamaModelClient(Settings()).chat([{"role": "system", "content": "task"}], tool_schemas(), threading.Event())
    assert captured[0]["format"]["oneOf"] and "tools" not in captured[0]
    assert reply["content"] == raw
    assert reply["tool_calls"][0]["function"]["name"] == "list_files"
