# Implementierungsstand

Stand: **2026-10-05**. Umsetzung abgeschlossen. **Nicht vollständig verifiziert:**
Der erfolgreiche echte Modell-Fix bleibt offen. Nach dem Abschlusswunsch des Nutzers
wurden die Modellversuche beendet. Keine weiteren Implementierungsarbeiten sind aktiv.

## Plan
1. Vorgaben vollständig lesen, Umgebung prüfen, OpenStock-Commit fixieren.
2. Docker-Sandbox, synthetische Daten, geschützte Regression und Akzeptanz aufbauen.
3. Dateiwerkzeuge, Controller, Budgets, Scripted-/Ollama-Clients implementieren.
4. Streamlit-Worker, Fortschritt, Abbruch und Artefakte anbinden.
5. Kern-, UI-, Docker- und Live-Prüfungen ausführen; Dokumentation vervollständigen.

## Bereits festgestellt
- CODEX_PROMPT.md und alle vier PDF-Seiten gelesen, einschließlich Diagrammen.
- PDF zusätzlich nach docs/assignment kopiert; ursprüngliche Nutzerdatei erhalten.
- Projekt war bis auf Vorgaben leer; keine AGENTS.md gefunden.
- Git 2.39.1.windows.1; Python 3.12.14 aus bereitgestellter Laufzeit; lokale .venv angelegt.
- Docker 28.0.4 / Desktop 4.40.0, Linux/amd64 erreichbar in freigegebener Ausführung.
  Eingeschränkter Codex-Prozess: Zugriff auf Docker-Pipe verweigert. Kein Host-Fallback.
- Ollama unter 127.0.0.1:11434 erreichbar (curl --noproxy '*');
  qwen2.5-coder:7b installiert, Tool-Capability gemeldet. Kein Modell heruntergeladen.
- Öffentliches OpenStock geklont; Commit abc87dccab96c78917b35add542284e61adc5f37.
- Transferprüfung ohne positive Mengenprüfung; fachlicher Fehler inzwischen in Docker reproduziert.

## Implementiert und geprüft

- Eigener Controller, sichere Repository-Tools, validierte Konfiguration, frische Commit-Kopien.
- Scripted-/Ollama-Clients, native Toolcalls und ausdrücklich konfiguriertes JSON-Schema-Protokoll.
- Docker-Sandbox mit Ressourcenlimits, Read-only-Mounts, Netzsperre und verifiziertem Cleanup.
- Deutsche Streamlit-UI mit Worker, Abbruch, Doppelstartschutz, Verlauf, Checks und Downloads.
- Geschützte API-/Geschäftslogik-/SQLite-Akzeptanz, synthetische Daten und zwei unveränderte Regressionen.
- README, Architekturdiagramme, Task, PDF-Matrix, Verifikationsbericht und 3:40-Demo-Drehbuch.

| Abschlussprüfung | Tatsächliches Ergebnis |
|---|---|
| Frische Installation aus requirements.lock | erfolgreich in .harness/fresh-env, Python 3.12.14 |
| Kern-/UI-Tests in frischer venv | **54 bestanden**, **4 Docker-Fälle ausdrücklich ausgelassen** |
| Separater echter Docker-Testlauf | **4 bestanden**, einschließlich Timeout/Abbruch mit schreibendem Kindprozess |
| pip check | No broken requirements found |
| Ruff und Python-Kompilierung | erfolgreich |
| Streamlit | gestartet auf 127.0.0.1:8501 und Browseransicht visuell geprüft |
| Baseline | positive Kontrolle bestanden, vier Mengenverstöße fachlich rot, Regression 23 + 22 grün |
| Simulierter Gesamtlauf | Akzeptanz 5/5 und Regression 23 + 22 nach Fix grün; unabhängige Endprüfung bestanden |

## Ergebnisse und offene Schritte

- Fixierter Commit: **abc87dccab96c78917b35add542284e61adc5f37**.
- Aufgabe: atomare Ablehnung von Lagertransfers mit Mengen ≤0; Scope operations.py/app.py.
- Baseline: `.harness/runs/20261005T154625Z-09ee0eaa/report.json`.
- Erfolgreiche **Simulation**: `.harness/runs/20261005T161522Z-71017deb/`.
- Kleine vollständige Kopie: `docs/examples/scripted-success/` mit report.json, events.jsonl, changes.diff.
- Echte Fehlversuche: `docs/examples/live-attempts.json`, Details in `docs/verification.md`.
- Zwei Entwicklungsunterbrechungen sind als developer-interruption.json dokumentiert;
  Diffs separat gesichert. Kein Live-Erfolg fingiert, kein vorbereiteter Patch in echte Läufe eingespielt.

**Offen:** Ein geeignetes echtes Modell muss die Aufgabe noch erfolgreich lösen. Docker und
Ollama fehlen nicht; qwen2.5-coder:7b scheiterte in den dokumentierten Versuchen. Modell und
Protokoll über HARNESS_MODEL bzw. HARNESS_OLLAMA_PROTOCOL wählen, danach folgende Befehle
ausführen. Derselbe Commit und dieselben geschützten Checks bleiben bestehen. Hinweise,
Modellwechsel und Wiederholungen offenlegen.

```powershell
.\.venv\Scripts\python.exe -m harness doctor
.\.venv\Scripts\python.exe -m harness run --provider ollama
```

**Nutzeraufgaben:** Repository committen/bereitstellen und Video ≤4 Minuten nach
docs/demo-script.md aufnehmen. Kein Push, Merge oder Deployment durchgeführt.
Ein frischer Linux-Hostaufbau und weitere Upstream-HTTP-Smokes sind nicht verifiziert.

## Fortsetzung und Start

Der eingeschränkte Codex-Prozess hat keinen Docker-Pipe-Zugriff; die genehmigte Ausführung
erreicht Docker Desktop 4.40.0 / Engine 28.0.4 (Linux/amd64) und Ollama 0.35.1.
Unter wechselnden Windows-Benutzern getrennte pytest-Temp-/Cachepfade verwenden.
Python ist hier nicht über den Launcher registriert. Die funktionierende .venv verwendet
die bereitgestellte Codex-Python-3.12.14-Laufzeit. Git setzt safe.directory nur pro Befehl,
nicht global. Große Laufkopien und Umgebungen sind git-ignoriert.

```powershell
# UI
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
# Kerntests; Sandbox separat und ausdrücklich
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest -q --docker -m docker
```
