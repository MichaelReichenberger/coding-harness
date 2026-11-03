# Stage-2-Anforderungsmatrix

Source of truth: [alle vier Seiten der Stage-2-PDF](assignment/stage-2-coding-harness.pdf),
am 03.11.2026 vollständig als Text gelesen und einschließlich Diagrammen visuell geprüft.
Basis: Stage 1 auf Commit `08aad834732bbddf397c5c446f8844722bc7f147`.
Dateiweise Begründungen: [stage-2-changes.md](stage-2-changes.md).

| Kennung / PDF | Umsetzung | Nachweis / Grenze |
|---|---|---|
| S2-N · S.2–3 Navigation | inspect_repository: Python-AST, Symbole, Imports, direkte Abhängigkeiten, Git-Diff/Startcommit | tests/test_stage2.py: Navigation mit erwartetem sauberem/geändertem Zustand |
| S2-C · S.2–3 Karte und Dateiauswahl | Namensscore plus direkte lokale Imports, maximal sechs ausgewählte Dateien | Navigationstest findet Teller/Receipt; Quelltext wird nicht ausgeführt |
| S2-C · S.2–3 begrenzte Historie | ContextManager, vollständiger Request ≤ min(context_bytes,32768) Bytes (CPU höchstens 16384), deterministische Kompression | Tests erhalten Auftrag/Scope/Kriterien, untrusted Rollen und Kürzungsmarker |
| S2-T · S.2 gespeicherter Auftrag | Checkpoint mit Projekt/Profil, Nutzertext, Startcommit, Rechte, Kriterien, Checks, Settings, Schritten und Checkresultaten | Wiederöffnen nach neuem RunService in tests/test_stage2.py |
| S2-T · S.2 Edit-Test-Fix | Fehler gehen als Beobachtungen ans Modell; Aktionen/Retrys/Runden bleiben begrenzt | echter Docker-Test: feature failed → failed → passed mit Scripted-Antworten |
| S2-S · S.2–3 Sitzungen | atomare session.json, Ereignisse, Bericht/Diff, Open/Cancel/Resume | Neustart-/Resume-Test mit eigenen Edits und erhaltenen Zählern |
| S2-S · S.2–3 Cancel | Event + externe cancel.request, Watcher während HTTP, Container-Cleanup | externer Cancel-Test verwirft späte Schreibantwort; bestehender echter Kindprozess-Canceltest |
| S2-S · S.2–3 Safe Resume | aktuelle Allowlist, Rechte/Checks/Testhashes/Settings, base/repo inklusive eigener Edits vergleichen | Tests für fremden Edit, Baselineänderung, Policyänderung, bool-Zähler, verbrauchte Limits |
| S2-S · S.2–3 Unsicherheit | pending vor Aktion; nach hartem Abbruch pausieren, nie automatisch replayen | Fault-Injection vor Edit; Originaldatei bleibt unverändert, Resume lehnt ab |
| S2-V · S.2–3 Verifikation | Diff, geänderte Dateien, Test-/Syntaxlintstatus, Schritte und unfinished_work | fehlgeschlagene/unavailable/not_run Checks bleiben im Bericht und UI sichtbar |
| S2-I · S.2 CLI/UI | erlaubtes Projekt/Profil wählen; run/sessions/inspect/cancel/resume; UI-Worker getrennt | AppTest für Auswahl und Öffnen; gemeinsame RunService-Logik |
| S1 · S.1/3 Erhalten | bestehende Tools, Argument-/Pfadgrenzen, Docker- und Limitlogik, Bugfixprofil | alle bisherigen Offline-Tests und fünf bisherige Docker-Fälle weiter bestanden |
| S2-F · S.4 Feature | optionale Servicegebühr in Teller/Receipt, Legacy-API und ungültige Werte | geschützte Feature-Baseline rot bei grünen Kontrollen; Scripted-Endchecks grün |
| S2-F · S.4 selbst finden/ändern | keine Codeausschnitte/Patches im echten Prompt; Modell nutzt Navigation/Dateitools | tatsächliche Modellaktionen und Diff getrennt protokolliert |
| S2-F · S.4 echter Featurelauf | echtes installiertes 7B-Modell; eigene Sitzung mit dokumentierten Settings | GPU: CUDAfehler; echter CPU-Lauf: limit_reached ohne Fix. Echter erfolgreicher Feature-Nachweis offen; Scripted-Test zählt nicht als Modellleistung |
| S2-D · S.4 Setup/Design/Credits | README, Settingsbeispiel, Design, Task, Matrix und Änderungsnachweis | keine zusätzlichen Runtime-Abhängigkeiten, KI-Hilfe und CPU-Fallback offengelegt |
| S2-D · S.4 Quellstand | Ausgangscommit dokumentiert; abschließendes versioniertes ZIP als lokale Abgabe | nicht ohne Nutzerauftrag gepusht |
| S2-D · S.4 Video ≤4 min | aktualisiertes Drehbuch | Aufnahme/Moodle-Abgabe durch Nutzer noch offen |

## Abgrenzung der Nachweise

Automatisierte Tests beweisen Controller-/Grenzverhalten reproduzierbar ohne Modellkonto.
Echte Featureleistung, GPU-Probleme und manuelle Hilfe werden separat aufgeführt. Ein
CUDA-/Transportfehler ist kein fachlich roter Featuretest. Grüne Prüfungen behaupten
nur die konfigurierte Aufgabe; der bekannte unabhängige Stage-1-Druckfehler bleibt im
Featureprofil bestehen. Der Stage-1-Nachweis unter docs/evidence/ bleibt unverändert.
