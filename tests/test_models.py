import asyncio
import json
import threading
import time

import httpx
import pytest

from harness.config import Limits, Settings
from harness.errors import Cancelled, ModelError
from harness.models import OllamaModelClient


@pytest.mark.parametrize(
    "content",
    [b"not-json", b'{"wrong":"schema"}', b"x" * 300000],
    ids=["invalid-json", "missing-message", "oversized"],
)
def test_malformed_and_oversized_responses(monkeypatch, content):
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: real_client(
            **kwargs,
            transport=httpx.MockTransport(lambda request: httpx.Response(200, content=content)),
        ),
    )
    with pytest.raises(ModelError):
        OllamaModelClient(Settings()).chat(
            [{"role": "system", "content": "task"}], [], threading.Event()
        )


def test_cancellation_interrupts_pending_http_request(monkeypatch):
    closed = threading.Event()

    async def handler(request):
        try:
            await asyncio.sleep(30)
        finally:
            closed.set()
        return httpx.Response(200, json={})

    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: real_client(**kwargs, transport=httpx.MockTransport(handler)),
    )
    cancel = threading.Event()
    timer = threading.Timer(0.15, cancel.set)
    timer.start()
    start = time.monotonic()
    with pytest.raises(Cancelled):
        OllamaModelClient(Settings()).chat([{"role": "system", "content": "task"}], [], cancel)
    timer.join()
    assert closed.is_set() and time.monotonic() - start < 2


def test_total_http_deadline(monkeypatch):
    async def handler(request):
        await asyncio.sleep(30)
        return httpx.Response(200, json={})

    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: real_client(**kwargs, transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ModelError):
        OllamaModelClient(Settings(limits=Limits(model_seconds=1))).chat(
            [{"role": "system", "content": "task"}], [], threading.Event()
        )


def test_schema_protocol_is_explicit_and_preserves_raw_history(monkeypatch):
    from harness.repository import tool_schemas

    captured = []
    raw = json.dumps({"name": "list_files", "arguments": {}})

    def handler(request):
        captured.append(json.loads(request.content))
        return httpx.Response(200, json={"message": {"role": "assistant", "content": raw}})

    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: real_client(**kwargs, transport=httpx.MockTransport(handler)),
    )
    reply = OllamaModelClient(Settings()).chat(
        [{"role": "system", "content": "task"}], tool_schemas(), threading.Event()
    )
    assert captured[0]["format"]["oneOf"] and "tools" not in captured[0]
    assert captured[0]["think"] is False
    assert reply == {"name": "list_files", "arguments": {}}


def test_cpu_override_is_explicit_and_counted_in_request_size():
    messages = [{"role": "system", "content": "Trusted instructions"}]
    original = json.loads(json.dumps(messages))
    client = OllamaModelClient(Settings(num_gpu=0))
    from harness.repository import tool_schemas

    payload = client._payload(messages, tool_schemas())
    assert payload["options"]["num_gpu"] == 0
    assert client.request_size(messages) == len(json.dumps(payload).encode("utf-8"))
    assert messages == original
    assert "num_gpu" not in OllamaModelClient(Settings())._payload(messages, [])["options"]
