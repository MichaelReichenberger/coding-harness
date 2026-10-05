import json

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from harness.config import ROOT


class FakeService:
    def __init__(self, settings):
        self.active = False
        self.started = 0
        self.cancelled = False
        self.report = None
        self.path = None

    def start(self, task, provider):
        self.started += 1
        self.active = True
        self.task, self.provider = task, provider

    def cancel(self):
        self.cancelled = True

    def snapshot(self):
        return {"active": self.active, "events": [], "report": self.report,
                "error": None, "run_id": "test-ui" if self.started else None,
                "path": self.path, "actions": 2 if self.started else 0,
                "state": "running" if self.active else "ready"}


@pytest.fixture
def ui(monkeypatch):
    st.cache_resource.clear()
    fake = FakeService(None)
    monkeypatch.setattr("harness.service.RunService", lambda settings: fake)
    test = AppTest.from_file(str(ROOT / "app.py"), default_timeout=10)
    test.run()
    yield test, fake
    st.cache_resource.clear()


def button(ui, label):
    return next(button for button in ui.button if button.label == label)


def test_start_status_rerun_and_cancellation(ui):
    test, fake = ui
    assert not test.exception
    button(test, "Lauf starten").click().run()
    assert not test.exception
    assert fake.started == 1
    assert fake.provider == "ollama"
    assert "TWO_FOR_AMOUNT" in fake.task
    assert button(test, "Lauf starten").disabled
    assert not button(test, "Abbrechen").disabled
    test.run()
    assert fake.started == 1
    button(test, "Abbrechen").click().run()
    assert fake.cancelled


def test_result_check_status_and_downloads(ui, tmp_path):
    test, fake = ui
    fake.started = 1
    fake.path = str(tmp_path)
    fake.report = {"success": False, "state": "blocked", "reason": "Docker fehlt",
                   "simulated": True, "changed_files": [], "checks": [
                       {"phase": "final", "check_id": "acceptance", "status": "not_run", "exit_code": None}]}
    (tmp_path / "report.json").write_text(json.dumps(fake.report), "utf-8")
    (tmp_path / "changes.diff").write_text("", "utf-8")
    test.run()
    assert not test.exception and not test.success
    assert any("Simulation" in item.value for item in test.warning)
    assert test.dataframe[0].value.iloc[0]["status"] == "not_run"
    assert len(test.get("download_button")) == 2


def test_diagnosis_can_display_missing_services(ui, monkeypatch):
    test, fake = ui
    monkeypatch.setattr("harness.doctor.doctor", lambda settings: {"live_ready": False, "sandbox_ready": False, "checks": []})
    button(test, "Umgebung prüfen").click().run()
    assert not test.exception
    assert any("Voraussetzungen fehlen" in item.value for item in test.warning)
