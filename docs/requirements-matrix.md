# Abgleich mit der Stage-1-PDF

Alle vier Seiten wurden erneut gelesen. Die PDF ist maßgeblich. Stand: 07.10.2026.
**Die aktuelle Version ist offline und mit fünf echten Docker-Tests geprüft. Die neue kleine
Aufgabe prüft Stückzahlen im Belegdruck; echte 3B-Versuche sind separat dokumentiert. Ein erfolgreicher
echter Bugfix und die vollständige Abgabe bleiben offen.**

| PDF-Anforderung | Implementierung / Prüfung | Aktueller Stand |
|---|---|---|
| S.1 eigenes Python-Harness | eigenes `harness/`, kein fertiges Agentenprodukt | implementiert |
| S.1–2 Eingabe, Fortschritt, Dateien, Diff, Checks | freie CLI-/UI-Eingabe, Worker, AppTest | offline geprüft |
| S.2 Setup, Dependencies, Beispielsettings | README, Lockdatei, TOML, `setup`, `doctor` | vorhanden; frischer Gesamtaufbau nach Bereinigung noch offen |
| S.2 klare Verantwortlichkeiten | kommentierte Module, Lernleitfaden und Diagramme | vorhanden |
| S.2 Controller: Kontext, Validierung, Aktion, Beobachtung | Controller + Registry + Ollama-JSON | Scripted-/HTTP-Tests bestanden |
| S.2 List/Read/Search/Edit im erlaubten Scope | RepositoryTools | Dateitests bestanden |
| S.2 enthaltene Commands/Tests, Output/Exit-Code | DockerRunner + feste Check-IDs | 5 echte Docker-Tests bestanden |
| S.2 Limits, Ablehnungen/Retrys zählen | Controller, Process, Store | Offline-Limit-/Ausgabetests bestanden |
| S.2 failed/unavailable sichtbar trotz finish | Verifier, Bericht/UI | Offline-Statusprüfungen bestanden |
| S.3 disposable copy, Hostdaten/Secrets außerhalb | Git-Archiv, getrennte Laufordner und minimale Mounts | echte Mount-/Isolationsprüfung bestanden |
| S.3 echte Sandbox, keine reine Worktree-Grenze | nicht-root Linux-Container, Ressourcen-/Netz-/Mountgrenzen | aktuelle Docker-Prüfung bestanden |
| S.3 Anwendungscode prüft Rechte, untrusted Eingaben | Pydantic, Registry, Pfadauflösung | Offline-Tests bestanden |
| S.3 Push/Merge/Deployment deaktiviert | keine solchen Tools/keine freie Shell | implementiert |
| S.3 festgefahrenen Command samt Kindern stoppen | Container entfernen und Abwesenheit prüfen | echte Timeout-/Abbruchtests bestanden |
| S.3 Scripted-Tests ohne Konto/API-Key | ScriptedModelClient + FakeRunner nur für Tests | bestanden |
| S.3 Testtabelle: Dateiwerkzeuge/Pfadgrenze | `test_repository.py` | bestanden |
| S.3 Testtabelle: Controller/ungültige Requests | `test_controller.py`, `test_models.py` | bestanden |
| S.3 Testtabelle: Nonzero mit Ausgabe | Prozess-, Controller-, Docker-Tests | offline und mit Docker bestanden |
| S.3 Testtabelle: Aktionslimit | wiederholende/abgelehnte Tools und Retrys | bestanden |
| S.3 Testtabelle: große Ausgabe begrenzt/markiert | Stream-, Kontext- und Artefakttests | offline und mit Docker bestanden |
| S.3–4 Testtabelle: Rot-Grün + Regressionen | neuer deterministischer Docker-Bugfix-Test | Scripted-Rot-Grün-Bugfix mit Docker bestanden |
| S.4 öffentliches lokales Pythonrepo, Tests, Module/Geschäftsregeln | Supermarket Receipt: Teller → Cart → Receipt; `docs/task.md` | erfüllt |
| S.4 Repo/Commit/Task/Scope dokumentieren | Target-Konfiguration, frei eingegebener Prompt im Bericht, Task-Dokument | implementiert |
| S.4 vorbereitete geschützte Akzeptanz | unveränderte Prüffiles außerhalb Kopie, read-only, Hashvergleich | rote Baseline am 07.10.2026 erneut nachgewiesen |
| S.4 echter Modelllauf, Diff, grüne Akzeptanz/Regressionen, Hilfe offenlegen | Belegdruck-Aufgabe mit 3B und geschützter Akzeptanz; aktueller Befund in `docs/verification.md`, erfolgreicher Modellnachweis noch offen | **für aktuelle Version offen** |
| S.4 Quellcode per Repositorylink | lokal vorhanden | **Veröffentlichung offen** |
| S.4 Secrets falls nötig | lokales Ollama benötigt keine | nicht nötig |
| S.4 README und passende Diagramme | aktualisierte README/Architektur/Lernleitfaden | vorhanden |
| S.4 Video höchstens vier Minuten | Drehbuch vorhanden | **Aufnahme offen** |

## Auflösung des Anforderungskonflikts

Entfernt: Lösung im Prompt, gezielter Startausschnitt, Reparaturskript als Laufmodus und
Demo/Frei-Sonderbehandlungen. Eigene Eingaben und ein stärkeres Modell sind möglich.

Erhalten: fixierter Commit, erlaubte Dateien, geschützte Akzeptanz, feste Checkbefehle,
Limits und deterministische Testantworten. Diese sind von der PDF gefordert oder bilden
die ausführbare Berechtigungsgrenze. Sie garantieren keinen echten Modellerfolg.

Ein echter erfolgreicher Bugfix-Nachweis bleibt laut PDF erforderlich, auch wenn der
Lernschwerpunkt beim Harness liegt. Ein korrekter Limit-Abbruch demonstriert die Grenzen,
ersetzt aber nicht den auf S.4 geforderten erfolgreichen Modellnachweis.
