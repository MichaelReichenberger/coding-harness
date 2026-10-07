# Verifikation des Supermarket-POC

Dokumentiert am **2026-10-06**. Nachweise wurden am 05.10.2026 ausgeführt; Laufzeitstempel sind UTC.

## Echte Modellläufe

| Lauf | Start UTC | Ende UTC | Ergebnis |
|---|---|---|---|
| CLI `20261005T170915Z-539f048d` | 17:09:15 | 17:09:57 | passed; 3 Aktionen |
| UI `20261005T171122Z-bd74fa3a` | 17:11:22 | 17:11:56 | passed; 3 Aktionen |

Provider Ollama, Modell `qwen2.5-coder:7b`, ausdrücklich konfiguriertes `json_schema`-Protokoll.
Beide beginnen beim unveränderten Commit `c72d68abd77a417f84193b72a3b8d14177336066`,
Python-Unterordner. Modellaktionen: `replace_text`, `run_check(acceptance)`, `finish`.
Keine abgelehnten Aktionen oder Wiederholungen, nur `shopping_cart.py` geändert.

Baseline: 3, 5 und 7 Artikel liefern falsche Preise; leere/einzelne/gerade Mengen bestehen.
Nach Änderung bestehen alle sieben Akzeptanzfälle. Die vom Controller unabhängig gestartete
Endprüfung besteht ebenfalls einschließlich des unveränderten Upstream-Tests und fünf
zusätzlicher Preisregressionen. Alle Checks: Exit-Code 0, kein Timeout/Abbruch, Cleanup bestätigt.
Der fachliche Baseline-Fehlschlag hat Exit-Code 1 und enthält keine Infrastrukturfehler.

Der vollständige UI-Bericht, das Ereignisprotokoll und der echte Modelldiff stehen unter
`docs/examples/live-success/`. Lokale Originale: `.harness/runs/<Lauf-ID>/`.

## Manuelle Hilfe

Der Entwickler wählte die kleine Aufgabe, gab den exakten Ausdruck und dessen gewünschte
Korrektur vor und stellte einen kurzen Quellkontext bereit. Er erstellte Akzeptanztest
und fünf zusätzliche Preisprüfungen. Diese Hilfe ist im Bericht enthalten.
Die Modellarbeit besteht im Ausführen der angeleiteten Codeänderung über die Harness-Werkzeuge.
Das demonstriert eine vollständige echte Modell-/Tool-/Check-Schleife; es misst keine
autonome Fehlersuchleistung. Kein vorbereiteter Scripted-Patch wurde in echte Läufe eingespielt.

## Weitere ausgeführte Prüfungen

| Befehl | Ergebnis |
|---|---|
| `python -m harness setup --build` | Zielcommit vorhanden; schlankes neues Image gebaut |
| `python -m harness doctor` in freigegebener Ausführung | Docker Linux, Image, Commit und Ollama bereit |
| `python -m pytest -q` nach Zielwechsel | 54 bestanden; 4 Docker-Fälle ausdrücklich ausgelassen |
| `python -m pytest -q --docker -m docker` mit neuem Image | 4 bestanden, einschließlich Prozesskind-Timeout/Abbruch |
| `python -m ruff check harness app.py tests checks/entry.py checks/acceptance.py checks/scenario.py checks/pricing_regression.py` | erfolgreich |
| Streamlit-Start und echter UI-Lauf | neue Zielangaben sichtbar, Modellmodus echt, Start/Worker und Erfolg protokolliert |

Docker-Integration verwendete `--basetemp=.harness/supermarket-docker-tests` und
`-o cache_dir=.harness/supermarket-docker-cache`; Kerntests analoge separate Verzeichnisse.

## Umgebung

Windows, Python 3.12.14, Git 2.39.1.windows.1, Docker Desktop 4.40.0 / Engine 28.0.4,
Ollama 0.35.1, Streamlit 1.65.0, Pydantic 2.13.5, HTTPX 0.28.1, pytest 9.1.1.
Das eingeschränkte Codex-Konto erreicht Ollama, hat aber keinen Docker-Pipe-Zugriff.
Freigegebene Ausführung erreicht beide Dienste. Kein Host-Fallback.

Neues Image: `sha256:896dc65c1db5517c524ad115de04441e5e472589271f30b597926b186e4d192e`.
Basisimage ist in `sandbox/Dockerfile` per Digest fixiert. Zielcode und Tests verwenden
nur Standardbibliothek; keine zusätzlichen Image-Pakete oder Netzwerkverbindungen beim Check.

## Abgabe und Grenzen

Technischer POC erfolgreich nachgewiesen. Noch offen: Repository bereitstellen und Video ≤4 Minuten.
Frische Linux-Hostinstallation und optionale TextTest-Szenarien wurden nicht geprüft.
