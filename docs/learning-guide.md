# Den Harness Schritt für Schritt verstehen

## Die Grundidee

Das Sprachmodell schlägt eine Aktion vor. Es besitzt selbst weder Dateizugriff noch
Shell. Unser Python-Programm prüft diesen Vorschlag und entscheidet, ob es ihn ausführt.
Anschließend erhält das Modell das Ergebnis oder einen Fehler und schlägt die nächste
Aktion vor. Deshalb liegen Rechte und Limits im Harness und nicht nur im Systemprompt.

Lies zuerst `controller.py`, danach `repository.py`, `models.py` und `sandbox.py`.
Die übrigen Dateien unterstützen diesen Ablauf. Die Aufteilung hält Oberfläche,
Modelltransport und Sicherheitsgrenzen voneinander getrennt; es gibt kein Agentenframework.

```python
baseline = verifier.suite("baseline")
while budget_vorhanden:
    aktion = model.chat(nachrichten)
    versuch_zaehlen()                  # Auch eine verbotene Aktion kostet Budget.
    ergebnis = tools.execute(aktion)   # Prüft Namen, Argumente, Pfade und Rechte.
    if ergebnis.ist_fertigmeldung:
        break
    nachrichten.append(ergebnis)
final = verifier.suite("final")        # Nicht die Erfolgsbehauptung des Modells!
bericht_und_diff_speichern()
```

Das ist vereinfachter Pseudocode. Im echten Code beenden Abbruch, Limit oder Fehler die
Schleife mit eigenem Status; nach einem solchen Ende werden keine weiteren Checks gestartet.
Fehlende Endchecks erscheinen ausdrücklich als `not_run`.

## Welche Python-Datei macht was?

| Datei | Klassen/Funktionen | Verantwortung |
|---|---|---|
| `app.py` | `get_service`, `main`, `monitor` | Leeres Aufgabenfeld, Modellauswahl, Start/Abbruch, Verlauf, Diff und Checks. Keine Werkzeugausführung. |
| `harness/__main__.py` | `main` | CLI-Befehle `setup`, `doctor`, `baseline`, `run --task`. |
| `harness/controller.py` | `Controller` | Reihenfolge des Laufs, Modellgespräch, Zähler, Abbruchgründe und Endbericht. |
| `harness/models.py` | `OllamaModelClient` | Sendet Nachrichten/JSON-Schema per HTTP und liefert genau eine Aktion. |
| `harness/models.py` | `ScriptedModelClient`, `tool_reply` | Nur Tests: vorgegebene Antworten/Fehler ohne LLM. Kein UI-/CLI-Modus und kein eingebauter Reparaturplan. |
| `harness/repository.py` | `RepositoryTools` | Auflisten, Lesen, Suchen, eindeutiges Ersetzen, Checkaufruf und Fertigmeldung. |
| `harness/repository.py` | `ListArgs`, `ReadArgs`, `SearchArgs`, `EditArgs`, `CheckArgs`, `FinishArgs` | Kleine Datenschemata der sechs Werkzeuge. Keine Geschäftslogik; lehnen falsche Typen/Zusatzfelder ab. |
| `harness/repository.py` | `REGISTRY`, `validate_call`, `tool_schemas` | Eine erlaubte Werkzeugliste dient sowohl Modellbeschreibung als auch tatsächlicher Validierung. |
| `harness/sandbox.py` | `DockerRunner`, `CheckResult`, `CHECKS` | Feste Testbefehle in eingeschränkten Containern ausführen, strukturierten Befund sammeln und Cleanup bestätigen. |
| `harness/process.py` | `capture`, `BoundedOutput`, `ProcessResult` | Vertrauenswürdige Git-/Docker-CLI-Prozesse starten, Ausgabe schon beim Lesen begrenzen. Keine Sandbox für Python-Zielcode. |
| `harness/verifier.py` | `Verifier`, `all_passed` | Baseline, angeforderte Checks und Endsuite protokollieren; nur reale vollständige Erfolge akzeptieren. |
| `harness/verifier.py` | `acceptance_evidence`, `baseline_reproduces` | Den fachlichen Rot-Nachweis des gewählten Belegdruck-Tests im Bericht bestätigen. |
| `harness/workspace.py` | `Workspace` | Frische Commitkopie `repo`, Vergleichskopie `base`, eindeutige Lauf-ID und Diff. |
| `harness/workspace.py` | `RunLock` | Betriebssystem-Sperre gegen parallele CLI-/UI-Läufe. |
| `harness/workspace.py` | `prepare_reference`, `export_commit`, `tree_hashes`, Git-Helfer | URL/Commit prüfen, sicher exportieren und Dateiintegrität vergleichen. |
| `harness/service.py` | `RunService` | Genau einen Worker starten; Zustand an UI liefern und Abbruchsignal setzen. |
| `harness/store.py` | `RunStore`, `clip` | Begrenzte Ereignisdatei, thread-sichere UI-Snapshots und atomarer JSON-Bericht. |
| `harness/config.py` | `StrictModel`, `Limits`, `Settings`, `Target`, Ladefunktionen | Einstellungen und erlaubten Zielbereich streng validieren. Keine Aufgabe/keine Reparatur hinterlegt. |
| `harness/doctor.py` | `doctor` | Tatsächliche Erreichbarkeit von Docker und Ollama sowie Git, Commit, Pakete und Image prüfen. |
| `harness/errors.py` | `HarnessError` und fünf Unterklassen | Fehler unterscheiden: Tool, Sandbox, Modell, Abbruch, Limit. Keine zusätzliche Verarbeitungsschicht. |
| `harness/__init__.py` | keine | Kennzeichnet das Python-Paket; importiert keinen Zielcode. |
| `checks/entry.py` | `main` | Geschützter Testadapter innerhalb von Docker; lädt Zielcode und geschützte Tests. |
| `checks/scenario.py` | `checkout` | Frische synthetische Produkte/Preise anlegen und echte Kasse/Warenkorb/Beleg verbinden. |
| `checks/acceptance.py` | `main` | Sechs Belegdruckfälle mit Stückzahlen, Gewichten, Kontrollen, Befund und Exit-Code. |
| `checks/pricing_regression.py` | `PricingRegression` | Fünf weitere Preisregeln vor Nebenwirkungen schützen. |
| `checks/upstream/tests/*.py` | ursprünglicher `FakeCatalog`, `SupermarketTest`, Paketdatei | Unveränderte Testkopie aus dem öffentlichen Ausgangscommit. Absichtlich nicht umkommentiert; Herkunft/Hashes/Lizenz daneben. |

## Ein konkreter Werkzeugaufruf

Das Modell könnte folgende Antwort liefern:

```json
{"name": "read_file", "arguments": {"path": "receipt.py"}}
```

1. `Controller._chat()` prüft die äußere Form und Antwortgröße.
2. `Controller.loop()` erhöht den Aktionszähler.
3. `RepositoryTools.execute()` sucht den Namen in `REGISTRY` und validiert `ReadArgs`.
4. `path()` prüft den tatsächlich aufgelösten Pfad; `read()` begrenzt Dateigröße und Zeichensatz.
5. Das Ergebnis wird protokolliert, gekürzt und als Beobachtung an das Modell zurückgegeben.

Bei `../../secret.txt` wird nichts gelesen. Stattdessen erhält das Modell einen
`invalid_tool_request`-Fehler. Der Versuch bleibt gezählt. Bei einer erlaubten Änderung
muss der alte Text genau einmal vorkommen; eine fehlende/mehrdeutige Stelle wird nicht geraten.

## Warum gibt es mehrere Limits?

- **Aktionen:** verhindert endlose Toolschleifen; Ablehnungen und Wiederholungen zählen.
- **Runden:** zusätzliche Grenze für Modellfortsetzungen.
- **Zeit:** verhindert endloses Warten auf Modell oder Testprozess.
- **Ausgabe/Datei/Kontext:** verhindert, dass ein großer Text den Speicher oder Prompt flutet.
- **Containerressourcen:** begrenzt Prozesse, RAM, CPU und temporären Speicher des Zielcodes.

`ensure_active()` läuft vor Aktionen und nach Modellantworten. Ein spät antwortendes Modell
kann nach einem Abbruch keine neue Dateiänderung auslösen. Timeout der HTTP-Verbindung
beendet den lokalen Request. Eventuell serverseitig auslaufende Modellberechnung hat selbst
keinen Dateizugriff. Das Stoppen eines Docker-CLI-Prozesses reicht dagegen nicht:
`DockerRunner._cleanup()` entfernt den Container und prüft seine Abwesenheit.

## Warum ein Worker und zwei Sperren?

Streamlit zeichnet die Seite bei Eingaben neu. Der gecachte `RunService` bleibt bestehen;
sein Worker führt den Controller aus. Das UI-Fragment liest nur Snapshots und setzt bei
Abbruch ein `threading.Event`. Ein Mutex verhindert parallele Starts im Prozess, `RunLock`
auch Starts aus einem zweiten CLI-/UI-Prozess. Der gemeinsame `gate`-Lock in Tools und
Runner verhindert eine Dateiänderung während eines laufenden Checks.

## Welche Tests gehören wozu?

| Datei | Nachweis |
|---|---|
| `tests/conftest.py` | Gemeinsame Testkopie, `FakeRunner` und Factory für den Controller; Docker nur mit expliziter Option. |
| `tests/test_controller.py` | Rückgabe von Ergebnissen/Fehlern, frei eingegebener Prompt, Limits, Abbruch, Fehlstatus und Endchecks. |
| `tests/test_repository.py` | Dateifunktionen, eindeutige Änderungen, falsche Argumente und Pfadausbrüche. |
| `tests/test_models.py` | HTTP-JSON, fehlerhafte/große Antworten, Timeout und Abbruch ohne echten Server. |
| `tests/test_process.py` | Ausgabe-/Prozessgrenzen einschließlich Nonzero-Exit. |
| `tests/test_sandbox_safety.py` | Containerkonfiguration und Fehler/Cleanup anhand kontrollierter Prozessantworten. |
| `tests/test_workspace_store.py` | Lock, Diff, Konfigurationsvalidierung und Artefaktbudget. |
| `tests/test_ui.py` | Leeres Aufgabenfeld, Prompt/Modell weiterreichen, Start ohne Doppelstart, Abbruch und Ergebnisdarstellung. |
| `tests/test_docker.py` | Echte Mount-/Netzgrenze, Nonzero/große Ausgabe, Timeout/Abbruch mit Kindprozess und deterministischer Rot-Grün-Bugfix. |

Der feste Patch in **einem Integrationstest** ist eine Testfixture, kein Laufmodus.
So lässt sich der Harness reproduzierbar prüfen, selbst wenn ein Modell die Aufgabe
nicht löst. Die PDF verlangt daneben einen echten Modelllauf; dieser bleibt unabhängig
vom deterministischen Test und darf nie durch ihn als erledigt gelten.

## Was wurde bewusst vereinfacht?

Ein leeres Aufgabenfeld, eine Schleife, ein JSON-Protokoll und eine Checkliste für alle
Läufe. Entfernt wurden Demo-/Freimodus-Verzweigungen, automatische Aufgabentexte,
Startausschnitte, der ausführbare feste Reparaturplan und unbenötigte Abhängigkeiten.
Es gibt keine allgemeine Plugin-/Agentenabstraktion und keine zweite Toolcall-Übersetzung.

Fest bleiben Repositorycommit, erlaubte Dateien, Werkzeugnamen, Testbefehle und Limits.
Das sind reproduzierbare Berechtigungen und Prüfkriterien. Die PDF verlangt sie;
sie verraten dem Modell keine Codekorrektur und garantieren keinen Erfolg.
Die ausführlicheren Sicherheits- und Abbruchfunktionen bleiben erhalten, weil ein
kürzerer ungeschützter Shell-Aufruf die geforderte Ausführungsgrenze nicht erfüllt.
