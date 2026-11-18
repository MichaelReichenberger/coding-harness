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

    def start(self, task, *, model_name=None, project="supermarket", profile="bugfix"):
        self.started += 1
        self.active = True
        self.task, self.model_name = task, model_name
        self.project, self.profile = project, profile

    def sessions(self):
        return []

    def cancel(self):
        self.cancelled = True

    def snapshot(self):
        return {
            "active": self.active,
            "events": [],
            "report": self.report,
            "error": None,
            "run_id": "test-ui" if self.started else None,
            "path": self.path,
            "actions": 2 if self.started else 0,
            "state": "running" if self.active else "ready",
        }


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
    test.text_area[0].set_value("Korrigiere einen Preisfehler.").run()
    button(test, "Lauf starten").click().run()
    assert not test.exception
    assert fake.started == 1
    assert fake.task == "Korrigiere einen Preisfehler."
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
    fake.report = {
        "success": False,
        "state": "blocked",
        "reason": "Docker fehlt",
        "simulated": True,
        "changed_files": [],
        "checks": [
            {"phase": "final", "check_id": "acceptance", "status": "not_run", "exit_code": None}
        ],
    }
    (tmp_path / "report.json").write_text(json.dumps(fake.report), "utf-8")
    (tmp_path / "changes.diff").write_text("", "utf-8")
    test.run()
    assert not test.exception and not test.success
    assert any("Simulation" in item.value for item in test.warning)
    assert test.dataframe[0].value.iloc[0]["status"] == "not_run"
    assert len(test.get("download_button")) == 2


def test_diagnosis_can_display_missing_services(ui, monkeypatch):
    test, fake = ui
    monkeypatch.setattr(
        "harness.doctor.doctor",
        lambda settings: {"live_ready": False, "sandbox_ready": False, "checks": []},
    )
    button(test, "Umgebung prüfen").click().run()
    assert not test.exception
    assert any("Voraussetzungen fehlen" in item.value for item in test.warning)


def test_context_shortening_is_visible_in_history(ui, monkeypatch):
    test, fake = ui
    snapshot = fake.snapshot()
    snapshot["events"] = [
        {
            "at": "2026-11-17T20:00:00+00:00",
            "kind": "context_shortened",
            "source": "checkpoint",
            "bytes_before": 18000,
            "bytes": 15000,
            "limit_bytes": 16384,
        }
    ]
    monkeypatch.setattr(fake, "snapshot", lambda: snapshot)
    test.run()
    assert not test.exception
    assert any("Kontext gekürzt · 15000 Bytes" in item.label for item in test.expander)


def test_custom_prompt_is_sent_without_demo_task(ui):
    test, fake = ui
    assert test.text_area[0].value == ""
    assert button(test, "Lauf starten").disabled
    test.text_input[0].set_value("my-installed-model:latest").run()
    task = "Ändere die Überschrift auf Gesamt: in receipt_printer.py."
    test.text_area[0].set_value(task).run()
    button(test, "Lauf starten").click().run()
    assert not test.exception and fake.task == task
    assert fake.model_name == "my-installed-model:latest"
    assert fake.project == "supermarket" and fake.profile == "bugfix"


def test_feature_profile_and_saved_session_controls(ui, monkeypatch):
    test, fake = ui
    monkeypatch.setattr(fake, "sessions", lambda: [{"run_id": "saved", "state": "cancelled"}])
    opened = []
    monkeypatch.setattr(fake, "open", lambda run_id: opened.append(run_id), raising=False)
    test.run()
    button(test, "Sitzung öffnen").click().run()
    assert opened == ["saved"] and not test.exception
    next(box for box in test.selectbox if box.label == "Aufgabenart").set_value("feature").run()
    test.text_area[0].set_value("Optionale Servicegebühr ergänzen.").run()
    button(test, "Lauf starten").click().run()
    assert fake.profile == "feature"


def test_passed_checks_explain_limited_verification_scope(ui, tmp_path):
    test, fake = ui
    fake.report = {"success": True, "state": "passed", "reason": "done", "checks": []}
    fake.path = str(tmp_path)
    (tmp_path / "report.json").write_text(json.dumps(fake.report), "utf-8")
    test.run()
    assert not test.exception
    assert test.success[0].value == "Alle konfigurierten Checks bestanden."
    assert any("nicht automatisch geprüft" in item.value for item in test.info)


@pytest.mark.parametrize("state", ["passed", "baseline_checked"])
def test_completed_session_can_be_opened_but_not_resumed(ui, monkeypatch, state):
    test, fake = ui
    monkeypatch.setattr(fake, "sessions", lambda: [{"run_id": "saved", "state": state}])
    opened = []
    monkeypatch.setattr(fake, "open", lambda run_id: opened.append(run_id), raising=False)
    test.run()
    assert button(test, "Sicher fortsetzen").disabled
    assert not button(test, "Sitzung öffnen").disabled
    button(test, "Sitzung öffnen").click().run()
    assert not test.exception and opened == ["saved"]
