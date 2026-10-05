"""Streamlit entry point; the controller worker never calls Streamlit APIs."""
from pathlib import Path

import streamlit as st

from harness.config import load_settings, load_target
from harness.doctor import doctor
from harness.service import RunService

st.set_page_config(page_title="Supermarket Coding Harness", page_icon="🛠️", layout="wide")


@st.cache_resource
def get_service():
    return RunService(load_settings())


def main():
    st.title("Supermarket Coding Harness")
    st.caption("Stage 1 · Python-Controller · isolierte Linux-Container · nachvollziehbare Prüfungen")
    try:
        settings = load_settings()
        service = get_service()
        target = load_target()
    except Exception as exc:
        st.error(f"Konfiguration ungültig: {exc}")
        return
    with st.sidebar:
        st.subheader("Ziel und Umgebung")
        st.write(target.name)
        st.write(target.url)
        st.caption("Teilprojekt: " + target.subdirectory)
        st.code(target.commit, language=None)
        st.write("Änderungsbereich: " + ", ".join(target.editable))
        st.write("Provider: Ollama · Modell: " + settings.model)
        st.caption("Werkzeugprotokoll: " + settings.ollama_protocol)
        st.caption("Modellwechsel über HARNESS_MODEL vor dem UI-Start; kein automatischer Download.")
        if st.button("Umgebung prüfen", disabled=service.active):
            with st.spinner("Docker, Referenz und Ollama prüfen …"):
                st.session_state["diagnosis"] = doctor(settings)
        if "diagnosis" in st.session_state:
            diagnosis = st.session_state["diagnosis"]
            (st.success if diagnosis["live_ready"] else st.warning)(
                "Echter Lauf startbereit" if diagnosis["live_ready"] else "Externe Voraussetzungen fehlen")
            st.json(diagnosis)
    task = st.text_area("Coding-Aufgabe", value=target.task, height=130, max_chars=12000,
                        key="task_supermarket", disabled=service.active)
    st.caption("Die Vorlage legt die geschützten Akzeptanztests fest. Änderungen am Text ändern diese Tests nicht.")
    provider = st.selectbox("Modellmodus", ["Echtes Modell (Ollama)", "Simulation (festes Antwortskript)"],
                            disabled=service.active)
    if provider.startswith("Simulation"):
        st.warning("SIMULIERT: vorbereitete Werkzeugantworten für die Paketpreis-Aufgabe. Kein echter Modellnachweis.")

    @st.fragment(run_every=0.5)
    def monitor():
        snapshot = service.snapshot()
        was_active = st.session_state.get("worker_was_active", False)
        st.session_state["worker_was_active"] = snapshot["active"]
        if was_active and not snapshot["active"]:
            st.rerun()
        left, right = st.columns(2)
        if left.button("Lauf starten", type="primary", disabled=snapshot["active"] or not task.strip()):
            try:
                service.start(task, "scripted" if provider.startswith("Simulation") else "ollama")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        if right.button("Abbrechen", disabled=not snapshot["active"]):
            service.cancel()
            st.warning("Abbruch angefordert. Der Controller beendet die Sandbox und erhält den Bericht.")
        st.write(f"Zustand: **{snapshot['state']}** · Aktionen: {snapshot['actions']} / {settings.limits.actions}")
        if snapshot["run_id"]:
            st.caption("Lauf-ID: " + snapshot["run_id"])
        report = snapshot["report"]
        if report:
            if report.get("simulated"):
                st.warning("Dieser Lauf ist eine Simulation.")
            (st.success if report["success"] else st.warning)(f"{report['state']}: {report['reason']}")
        history, changes, checks = st.tabs(["Verlauf", "Dateien & Diff", "Checks"])
        with history:
            for event in snapshot["events"]:
                title = f"{event['at'][11:19]} · {event['kind']} · {event.get('name', event.get('state', ''))}"
                with st.expander(title):
                    st.json(event)
        with changes:
            if report:
                st.write("Geänderte Dateien:", report.get("changed_files", []))
                diff_path = Path(snapshot["path"]) / "changes.diff"
                diff = diff_path.read_text("utf-8") if diff_path.exists() else ""
                if report.get("diff_truncated"):
                    st.warning("Diff wegen Artefaktlimit gekürzt.")
                st.code(diff or "Keine Änderungen", language="diff")
                st.download_button("Diff herunterladen", diff, file_name="changes.diff", mime="text/plain")
                st.download_button("Laufbericht herunterladen", (Path(snapshot["path"]) / "report.json").read_bytes(),
                                   file_name="report.json", mime="application/json")
            else:
                st.info("Der vollständige Diff steht nach Laufende bereit, auch nach Abbruch.")
        with checks:
            records = report.get("checks", []) if report else [e for e in snapshot["events"] if e["kind"] == "check"]
            if records:
                st.dataframe([{k: r.get(k) for k in ("phase", "check_id", "status", "exit_code", "timed_out", "cancelled", "cleanup_verified")}
                              for r in records], hide_index=True, width="stretch")
                for index, check in enumerate(records):
                    with st.expander(f"{index+1}. {check['phase']} · {check['check_id']} · {check['status']}"):
                        st.code(" ".join(check.get("command", [])), language=None)
                        if check.get("truncated"):
                            st.warning("Ausgabe gekürzt; Status und Exit-Code bleiben erhalten.")
                        st.code(check.get("stdout", "") + "\n" + check.get("stderr", ""), language=None)
                        st.write(check.get("reason", ""))
            st.caption("passed = bestanden · failed = fehlgeschlagen · unavailable = nicht verfügbar · not_run = nicht ausgeführt")
    monitor()


main()
