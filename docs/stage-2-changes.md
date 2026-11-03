# Stage-2-Änderungsnachweis

Stand: 03.11.2026. Ausgang: `08aad834732bbddf397c5c446f8844722bc7f147`.
GitHub besitzt keinen main-Branch; der Hauptbranch master wurde mit --ff-only gepullt.
Die Nutzer-PDF wurde vorher gesichert und bytegleich wieder eingefügt (SHA256
2aa3d4062e51f031386ae349eada55bf9590529e7285ef41faa8443117b999f9).

## Plan und Anforderungskennungen

- S2-N (S.2–3): Module, Symbole, Abhängigkeiten und Git-Zustand finden.
- S2-C (S.2–3): Repositorykarte, relevante Dateien, begrenzte Historie; vertrauenswürdige
  Aufgabe/Rechte/Akzeptanz erhalten, Quelltext und Ausgaben untrusted halten.
- S2-T (S.2): Aufgabe, Commit, Rechte, Checks und Schritte speichern; begrenzte Edit-Test-Fix-Schleife.
- S2-S (S.2–3): Öffnen, Abbrechen, sichere Checkpoints, Fortsetzen mit verbrauchten Limits,
  Rechte/Dateien einschließlich eigener Änderungen revalidieren; bei Unsicherheit pausieren.
- S2-V (S.2–3): Diff, Test-/Lintstatus, Fehler und offene Arbeit sichtbar erhalten.
- S2-I (S.2): Erlaubtes Projekt wählen, starten/öffnen/abbrechen/fortsetzen; getrennte Oberfläche.
- S2-F (S.4): Servicegebühr über Teller und Receipt, Legacy-Aufrufe und Fehlerfall;
  geschützte rote/grüne Akzeptanz, echte Modellprüfung, Hilfe offenlegen.
- S2-D (S.4): Anleitung, Modelleinstellungen, Diagramme, Entscheidungen/Grenzen, Credits,
  versionierter Quellstand und Video bis vier Minuten.
- S1 (S.1/3): Bestehende Werkzeuge, Rechte, Dockergrenze und Stage-1-Tests erhalten.

## Dateien

Die Tabelle ordnet jede bearbeitete oder neue Quelldatei ihrem Zweck, der Änderung,
dem Grund und der PDF-Anforderung zu. Kommentare und Docstrings erklären die
entscheidenden Grenzen zusätzlich direkt im Python-Code.

| Datei | Zweck | Was und warum geändert | Anforderung |
|---|---|---|---|
| docs/assignment/stage-2-coding-harness.pdf | Unveränderte Aufgabenstellung | Vor Pull gesichert und danach bytegleich wieder eingefügt; keine Inhaltsänderung | S2-D |
| docs/stage-2-changes.md | Dateiweiser Änderungsnachweis | Plan, PDF-Zuordnung und Begründung aller Dateianpassungen | Nutzerauftrag, S2-D |
| README.md | Einstieg, Startbefehle und Verantwortlichkeiten | Stage-2-Bedienung, Kontext-/Resume-Design, Grenzen und Credits erläutert; Stage-1-Befehle bleiben dokumentiert | S2-C/S/T/I/D, S1 |
| app.py | Streamlit-Oberfläche ohne eigene Toolausführung | Allowlist/Profil auswählen, Sitzungen öffnen/fortsetzen, Auftrag/Schritte/Unsicherheit und aktuellen Diff zeigen | S2-I/S/V |
| checks/entry.py | Geschützter Einstieg für Tests im Container | Featuredispatch und Standardbibliothek-Syntaxlint ergänzen; vorhandene Checkbefehle erhalten | S2-F/V, S1 |
| checks/feature.py | Geschützte fachliche Gebühren-Akzeptanz | Legacy-Aufrufe, Gebühren über zwei APIs, Rabatt und ungültige Werte prüfen; eindeutige rote Baseline | S2-F |
| config.example.toml | Secrets-freie Beispielsettings | Effektives Feature-Kontextlimit und optionalen CPU-Override dokumentieren | S2-C/D |
| docs/demo-script.md | Drehbuch für das Nutzer-Video | Stage-2-Navigation, Abbruch/Resume, Grenzen und echte Feature-Nachweise in unter vier Minuten planen | S2-D |
| docs/requirements-matrix.md | Nachvollziehbarer PDF-Abgleich | Jede Stage-2-Anforderung einer Implementierung und Prüfung zuordnen; offene Abgaben ehrlich markieren | S2-D, alle |
| docs/stage-2-design.md | Ausführliche Designentscheidungen und Ablaufdiagramm | Kontextvertrauen, Checkpointprotokoll, Git-Archivvergleich, Grenzen und Budgets begründen | S2-C/S/D |
| docs/stage-2-task.md | Versionierter Featureauftrag mit Akzeptanzbefehlen | Geschäftsregeln, Fehlerfälle, erlaubte APIs, Scope, Startcommit und tatsächlichen Modellprompt festlegen | S2-T/F |
| docs/implementation-status.md | Aktueller Arbeits- und Prüfstand | Ausgeführte Tests, echte Läufe, manuelle Hilfe und konkrete Restschritte festhalten | S2-D/F |
| docs/verification.md | Prüfergebnisse und Reproduktion | Stage-2-Ergebnisse voranstellen; alten Stage-1-Nachweis als historisch erhalten | S2-D/V, S1 |
| harness/__main__.py | CLI als schmale Benutzerschnittstelle | Allowlist/Profil, projects/sessions/inspect/cancel/resume ergänzen; alte run/baseline erhalten | S2-I, S1 |
| harness/config.py | Trusted Settings und Target-Allowlist | Explizite Projekt-/Profilwahl, festgehaltene Featurekriterien und optionales num_gpu hinzufügen | S2-I/T/C/D |
| harness/context.py | Begrenzte Nachrichten für das Modell | Historie deterministisch kürzen, trusted Auftrag vollständig erhalten, untrusted Daten getrennt halten | S2-C |
| harness/controller.py | Kernschleife und Ergebnisbewertung | Navigation/Kontext, Checkpoints vor/nach Aktionen, Wiederherstellung von Zählern/Edits, Fehlchecks nach Resume und offene Arbeit integrieren | S2-T/C/S/V, S1 |
| harness/models.py | Ollama-HTTP-Transport und Scripted-Testdouble | Payload zur vollständigen Größenmessung abtrennen und expliziten CPU-Requestoverride unterstützen; Abbruch bleibt erhalten | S2-C/D, S1 |
| harness/navigation.py | Sprachbewusste Repository-Navigation | AST-Symbole/Imports, relevante Dateien und sicheren Git-Diff ohne Ausführung von Zielcode liefern | S2-N/C |
| harness/repository.py | Toolregistry und tatsächliche Rechteprüfung | inspect_repository registrieren, bekannte Feature-/Lintcheck-IDs validieren; vorhandene Pfad-/Editgrenzen bewahren | S2-N/V, S1 |
| harness/sandbox.py | Feste Commands und Linux-Containerschutz | Eigene Feature-Checkliste ergänzen; bestehende Bugfix-Checkliste und Containerrechte unverändert erhalten | S2-V/F, S1 |
| harness/service.py | UI-/CLI-gemeinsame Sitzungssteuerung mit Worker | Sitzungen starten/öffnen/validieren/fortsetzen, externe Abbruchanforderung beobachten, Quellen nie zurücksetzen | S2-I/S |
| harness/sessions.py | Atomare Checkpoints und Resume-Vertrauensprüfung | pending-Protokoll, Arbeit/Base-Hashes, Policy-/Zählerprüfung, Pausen und Größenlimit implementieren | S2-S/T |
| harness/store.py | Begrenzte Ereignisse und Endberichte | Vorhandene Ereignisse nach Neustart öffnen und nur vollständige Zeilen lesen; Budget für Checkpoint reservieren | S2-S/C/V |
| harness/verifier.py | Unabhängige Checkausführung und Erfolgskriterien | Pro Aufgabe freigegebene Checks, Checkpointhooks und fachlichen Feature-Baseline-Nachweis ergänzen | S2-V/F, S1 |
| harness/workspace.py | Git-Export, disposable Kopien, Diff und RunLock | Bestehende Arbeitskopie ohne Reset wieder öffnen; Diff vor Link-/Hardlink-/Größenabweichungen schützen | S2-S/N, S1 |
| pyproject.toml | Paketversion und Test-/Lintkonfiguration | Version 0.2.0 und Stage-2-Beschreibung für das versionierte Abgabepaket setzen; keine Dependencies hinzugefügt | S2-D |
| tests/test_docker.py | Echte Isolations-/Cleanup- und Bugfixtests | Zusätzlichen ausdrücklich simulierten Featuretest mit zwei Fehlchecks und erfolgreicher Korrektur über zwei Module ergänzen | S2-F/T, S1 |
| tests/test_models.py | HTTP-/JSON-/Timeout-/Cancelverträge ohne Livekonto | CPU-Override, unveränderte Nachrichten und vollständige Requestgrößenmessung prüfen | S2-C/D, S1 |
| tests/test_stage2.py | Offline-Verträge der neuen Kernfunktionen | Navigation, Kontext, Neustart, eigene Edits, Zähler, Cancel, Fehlerrückmeldung, Scope-/Hash-/Hardlink-/Budgetabweichungen prüfen | S2-N/C/S/T/V |
| tests/test_ui.py | Streamlit-AppTest ohne echtes Modell | Testdouble um Projekt-/Profil-/Sitzungsfunktion ergänzen und neue Auswahl/Öffnung testen; bestehende Aussagen erhalten | S2-I, S1 |

## Automatisch erzeugte Artefakte

`.harness/` ist nicht Agenten-Arbeitsbereich und nicht Teil des Git-Quellstands.
`session.json` speichert Aufgabe/Policy/Checkpoint, `events.jsonl` die begrenzte Historie,
`report.json` Checks/Ergebnis/offene Arbeit und `changes.diff` den Diff. `repo` ist die
Agentenkopie, `base` der unveränderte Vergleich. Testtempordner und PDF-Vorschaubilder
sind automatisch erzeugte Prüfartefakte, keine manuell reparierten Zielmodule.
Das Release-ZIP enthält die Quelldateien, PDF und einen generierten VERSION.json-
Hashmanifest; es dient dem auf S.4 zugelassenen versionierten ZIP-Nachweis.

## Bewusst unverändert

Die öffentlichen Anwendungsdateien der Referenz werden vom Implementierungsassistenten
nicht repariert. Nur der echte Modelllauf bzw. explizite Testfixtures ändern disposable
Kopien. Stage-1-Akzeptanz, Preisregressionen und lizenzierte Upstream-Tests bleiben erhalten.
Die ursprünglichen Stage-1-Nachweise unter docs/evidence bleiben getrennt bestehen.
Keine zusätzliche Bibliothek, kein Driver-/Ollama-Update, keine neue freie Shell oder
untrusted Konfiguration, kein Push/Merge/Deployment und keine garantierte Modellreparatur.

## Nachweise und Abgabedateien

| Datei | Zweck | Was und warum geändert | Anforderung |
|---|---|---|---|
| docs/evidence/stage-2/report.json | Unveränderter echter Laufbericht | Tatsächlichen Modellstatus mit Zählern/Checks getrennt von Scripted-Tests sichern | S2-F/V/D |
| docs/evidence/stage-2/events.jsonl | Unverändertes echtes Ereignisprotokoll | Modellaktionen, Fehlchecks, Abbrüche und Fortsetzungen nachvollziehbar halten | S2-T/S/F |
| docs/evidence/stage-2/changes.diff | Tatsächlich erzeugter Modelldiff | Review über die beiden Module ermöglichen; keine nachträgliche manuelle Reparatur | S2-F/V |
| docs/evidence/stage-2/session.json | Tatsächlicher Endcheckpoint | Gespeicherte Policy, Historie, Schritte, eigene Edits und verbrauchte Zähler zeigen | S2-S/T |
| docs/evidence/stage-2/checks.json | Zusammenfassung der ausgeführten Abnahme | Befehle, tatsächliche Testergebnisse, Umgebung und bekannte Restnachweise erfassen | S2-D/V |

Bei der abschließenden Prüfung wurden zusätzlich zwei konkrete Grenzfälle abgesichert:
Kontextkürzung muss dieselbe Gesprächsliste verwenden, damit folgende Toolantworten
nicht verloren gehen; alte Endchecks werden nach Resume zu previous_final, damit
fehlende aktuelle Endchecks korrekt not_run bleiben. Modellmetadaten/Windows-
Zeilenumbrüche können die Artefaktbudgets nicht umgehen. Diese Änderungen gehören
zu controller.py/store.py und ihren bereits genannten Stage-2-Regressionstests.

## Nachtrag: angeforderter GPU-Versuch vom 03.11.2026

- `docs/implementation-status.md`: Status-/Nachweisdokument; tatsächlichen Lauf mit
  qwen3.8:27b, GPU-Offloading, CUDA-Warmupfehler und kontrolliertem Abbruch ergänzt,
  damit ein Infrastrukturfehler nicht als Modellergebnis erscheint (S2-V/D).
- `docs/stage-2-changes.md`: Änderungsregister; diesen Eintrag ergänzt, um Zweck,
  Grund und Anforderungsbezug der Dokumentationsänderung nachvollziehbar zu halten
  (S2-D und ausdrücklicher Nutzerwunsch). Harness-Code und Tests unverändert.

## Nachtrag: lokale GPU-Reparatur vom 03.11.2026

- `docs/implementation-status.md`: Status-/Nachweisdokument; RAM-Bereinigung,
  signiertes NVIDIA-Treiberupdate einschließlich unvollständiger Nachbereitung,
  Reparatur des unvollständigen Ollama-CUDA-Backends und gemessenen echten GPU-Test
  ergänzt. Grund: reproduzierbare Umgebungsdiagnose und ehrliche Abgrenzung zum
  noch offenen Feature-Erfolg (S2-V/D).
- `docs/stage-2-changes.md`: Änderungsregister; Zweck, Grund und Anforderungsbezug
  dieses Nachtrags erfasst. Keine Änderung am Harness-Code, an Limits oder Checks.
