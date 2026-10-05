# Abgleich mit der vollständigen Stage-1-Aufgabe

Quelle: `docs/assignment/stage-1-coding-harness.pdf`, vier Seiten einschließlich aller drei
Diagramme. Die PDF ist maßgeblich; die Streamlit-/Docker-/Ollama-Details stammen zusätzlich
aus `CODEX_PROMPT.md`. „Offen“ bedeutet ausdrücklich nicht bestanden.

| PDF-Pflicht | Implementierung | Prüfung / tatsächlicher Nachweis |
|---|---|---|
| S.1: eigenes Python-Harness, kein fertiges Harness als Basis | `harness/`, eigener Controller und Tools | Quellcode; keine Delegation an Coding-CLIs |
| S.1–2: Aufgabe über CLI/UI, Fortschritt, Dateien, Diff, Checks | `app.py`, `harness/__main__.py`, `service.py` | `test_ui.py`; Streamlit gestartet und Browseransicht visuell geprüft |
| S.2: Dependencies, Beispielsettings ohne Secrets, Startbefehl | `requirements.lock`, `config.example.toml`, README | Installation in frischer Python-3.12-venv; `pip check` |
| S.2: klare Verantwortlichkeiten | Controller, ModelClient, Workspace, RepositoryTools, DockerRunner, Verifier, RunStore | `docs/architecture.md`, zwei tatsächliche Mermaid-Diagramme |
| S.2: Kontext ans Modell, Anfragen prüfen, Ergebnisse/Fehler zurückgeben | `controller.py`, `models.py`, `repository.py` | Controller- und HTTP-Protokolltests mit Scripted/MockTransport |
| S.2–3: List/Read/Search/Edit im erlaubten Repository | feste Registry, Pydantic, eindeutiger Textaustausch | Datei-, Konflikt-, Binär-/Größen- und geschützte-Pfad-Tests |
| S.2–3: enthaltene Ausführung, Ausgabe und Exit-Codes | Docker Linux, feste Check-IDs, begrenztes Streaming | echte Docker-Tests; Baseline und Simulation |
| S.2–3: Aktions-/Ausgabelimits, Ablehnungen und Retries zählen | `Limits`, Controllerzähler, `BoundedOutput`, `RunStore` | Aktions-/Runden-/Retry-/Kontexttests, zeilenlose MiB-Ausgabe |
| S.2: fehlgeschlagene/nicht verfügbare Checks sichtbar | vier Checkzustände, objektive Gesamtauswertung | Ergebnisstatus-Tests, tatsächliche rote Baseline und fehlgeschlagene Modellläufe |
| S.3: wegwerfbare Kopie, Credentials und fremde Dateien schützen | Commit-Archiv pro Lauf, zwei Read-only-Mounts, kein Socket/Home/Secrets | Pfadtests und Docker-Mount-/UID-/Netztests |
| S.3: Worktree allein genügt nicht | echte Docker-Grenze mit Ressourcenlimits | Docker-Integration besteht |
| S.3: Anwendung validiert Rechte/Argumente, Texte sind untrusted | feste Tools, getrennte Konfiguration und Prüfdateien | unbekannte Tools, beschädigtes JSON, falsche Typen, Extra-Argumente abgewiesen |
| S.3: Push, Merge, Deployment deaktiviert | keine entsprechenden Tools oder Shell-Schnittstelle | Registry-Test/Quellprüfung; nichts veröffentlicht |
| S.3: hängenden Befehl samt Kindern stoppen, keine weiteren Writes | Stop/Force-remove/Abwesenheitsprüfung, Event-Abbruch, Toolgate | echte Timeout- und Abbruchtests mit schreibendem Kindprozess |
| S.3: wiederholbare Tests ohne Konto/API-Key | ScriptedModelClient, Runner-Doubles | Offline-Kerntests; Docker-Tests separat markiert |
| S.3 Tabelle: Dateiwerkzeuge, ungültige Anfrage, Controller | `tests/test_repository.py`, `test_controller.py` | bestanden; einschließlich Windows-Junction-Ausbruch |
| S.3 Tabelle: Nonzero sichtbar, kein falscher Erfolg | `test_process.py`, `test_controller.py`, `test_docker.py` | Exit-Code 7 und begrenzte Ausgabe bleiben erhalten |
| S.3 Tabelle: wiederholende Anfragen stoppen | Aktions-/Rundenlimit, Retrybudget | Kerntests; tatsächliche Live-Läufe endeten an Limits |
| S.3 Tabelle: große Ausgabe begrenzt und markiert | Lese-Cap für stdout+stderr, HTTP-Antwortcap, Artefaktcap | Kern- und echte Docker-Tests bestanden |
| S.3–4: Bug rot vor Fix, grün danach, vorhandene Tests grün | geschützte Akzeptanz und zwei Upstream-Regressionen | In der ausdrücklich simulierten Demonstration nachgewiesen; echter Modellnachweis offen |
| S.4: öffentliches Python-Ziel, lokal ausführbar, Tests, ≥2 Module, Geschäftsregeln | OpenStock Flask → Operations → SQLite | Docker-Baseline: Positivkontrolle + 23/22 Regressionseinzelprüfungen |
| S.4: exakter Commit, Aufgabe, Änderungsscope | `config/target.json`, `docs/task.md` | echter Git-Hash gespeichert, immer gleicher Commit |
| S.4: Akzeptanztest außerhalb Schreibbereich, enthaltene Endprüfung | `/trusted` read-only, Hashprüfung vor/nach, unabhängige Suite | Mount-/Integritätstests und Docker-Gesamtläufe |
| S.4: reale Modell-Demonstration mit erfolgreichem Diff und Checks | Ollama-Anbindung vorhanden, mehrere echte Versuche protokolliert | **Offen:** installiertes 7B-Modell erzeugte keinen erfolgreich verifizierten Fix |
| S.4: manuelle Hilfe benennen | Task/Prompt/Versuche und Hilfe im Bericht/Dokumentation | `docs/verification.md`; Simulation enthält offen vorbereitete Antworten |
| S.4 Abgabe: lauffähiger Code als Repository-Link, ggf. Commit | Quellcode vollständig im lokalen Projekt | **Nutzeraufgabe:** Commit und Repository bereitstellen; kein Push durchgeführt |
| S.4 Abgabe: Secrets falls erforderlich | lokal, ohne API-Key, nur Wegwerf-Testpasswort | Keine echten Secrets nötig |
| S.4 Abgabe: automatisierte Tests, kurze README, passende Diagramme | `tests/`, README, Architektur | vorhanden und geprüft |
| S.4 Abgabe: Video ≤4 Minuten | Drehbuch mit 3:40 Inhalt | **Nutzeraufgabe:** aufnehmen und abgeben |

Zusätzliche Prompt-Anforderungen (deutsche UI, Windows/Linux-Befehle, Docker-Ressourcenlimits,
unabhängige Endprüfung, feste Dependency-Versionen, Providerwechsel und Fortsetzungsstatus)
sind in README, Architektur, Task- und Verifikationsbericht beschrieben. Nicht behauptet:
erfolgreicher autonomer Live-Fix, sämtliche zusätzlichen Upstream-HTTP-Smokes oder eine
frische Linux-Hostinstallation. Containerprüfungen liefen tatsächlich unter Linux.
