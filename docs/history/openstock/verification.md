# Verifikationsbericht

Datum: **2026-10-05**, lokale Zeitzone Europe/Vienna. Lauf-IDs und JSON-Zeitstempel verwenden UTC.

## Tatsächliche Umgebung

- Windows, Git `2.39.1.windows.1`, Python `3.12.14` aus der bereitgestellten Codex-Laufzeit.
  `py -0p` fand im eingeschränkten Prozess keinen registrierten Interpreter; die lokale
  `.venv` wurde mit dem vorhandenen absoluten Python-Pfad erstellt.
- Docker-Client/Engine `28.0.4`, Desktop `4.40.0`, Linux/amd64.
  Im eingeschränkten Prozess: Zugriff auf Docker-Konfiguration/Pipe verweigert.
  In der genehmigten Ausführung: Daemon erreichbar und Container ausführbar.
- Ollama `0.35.1`, `http://127.0.0.1:11434`, `qwen2.5-coder:7b` vorhanden
  (4.683.087.561 Bytes, Quantisierung Q4_K_M). Kein Modell heruntergeladen.
  HTTPX nutzt `trust_env=False`; ein direkter Aufruf mit `curl --noproxy '*'` bestätigte Zugriff.
- Streamlit `1.65.0`, Pydantic `2.13.5`, HTTPX `0.28.1`, pytest `9.1.1`, Ruff `0.16.10`.
  Alle aufgelösten Versionen stehen in `requirements.lock`; Image-Abhängigkeiten separat
  in `sandbox/requirements.lock` (ReportLab 4.5.1 entspricht der Upstream-Bedingung `<5`).
- Basisimage: `python:3.12-slim@sha256:02108f5d322dd89f1c9e552442c25acb0543dfdbc455693a5599624f20d9155d`.
  Gebautes Image: `sha256:1d24aae80df4a1feb858d870c9ff76bff86a769008a0d96789b992d3be0f1242`.
  Docker Desktop löste hier den kurzen Namen nicht zuverlässig auf; der vollständige
  Standardname `docker.io/library/openstock-harness:stage1` funktioniert.

## Ausgeführte Prüfungen

Die exakten abschließenden Ergebnisse stehen zusätzlich in `docs/implementation-status.md`.

| Befehl / Handlung | Ergebnis |
|---|---|
| Git-Klon + `rev-parse HEAD` | Commit `abc87dccab96c78917b35add542284e61adc5f37` tatsächlich ermittelt |
| `docker build --tag openstock-harness:stage1 sandbox` | erfolgreich, Bibliotheken innerhalb der Upstream-Versionsbereiche |
| `python -m harness doctor` mit Dockerrechten | alle Komponenten erreichbar, Linux-Daemon, fixierter Commit und Modell vorhanden |
| `python -m pytest -q` | Offline-Tests erfolgreich; vier Docker-Fälle ausdrücklich ausgelassen |
| `python -m pytest -q --docker -m docker --basetemp .harness/docker-pytest-1 -o cache_dir=.harness/docker-pytest-cache` | **4 bestanden**: Read-only/UID/Netz/Capabilities, Nonzero/Ausgabelimit, Timeout mit Kindprozess, Abbruch mit Kindprozess |
| Frische `.harness/fresh-env` + `pip install -r requirements.lock` | vollständige Installation erfolgreich; keine vorhandene `.venv` wiederverwendet |
| Streamlit-Start auf 127.0.0.1:8501 | Server gestartet; UI im Browser geladen und visuell geprüft |
| Streamlit AppTest | Start, Rerun ohne Doppelstart, Status, Abbruchverbindung, fehlende Checks, Simulation und Downloads geprüft |
| Abschließender Lauf in frischer venv | **54 bestanden, 4 ausdrücklich ausgelassen**; pip check und Ruff erfolgreich |
| `python -m harness run --provider scripted` | Lauf `20261005T161522Z-71017deb`: 5 Aktionen, Akzeptanz 5/5, Regression 23 + 22, unabhängige Endprüfung bestanden; **simuliert** |

Der erste Docker-Testversuch scheiterte an den Windows-Rechten des von einem anderen
Ausführungsbenutzer erstellten pytest-Tempordners. Ein eigenes `--basetemp` im Projekt
behebt diesen Umgebungsfehler. Keine Tests wurden entfernt oder mit falschem Erfolg markiert.
Eine anfänglich fehlende tmpfs-Mountpoint-Struktur wurde im Workspace-Setup korrigiert;
die anschließende echte Baseline lief erfolgreich. Ein Testparameter brauchte einen kurzen
pytest-ID-Namen, weil ein 300-KiB-Wert als automatischer Testname die Windows-Pfadgrenze traf.

## Fachliche Baseline und reale Modellversuche

| Lauf-ID | Modus | Tatsächliches Ergebnis |
|---|---|---|
| `20261005T154625Z-09ee0eaa` | Baseline ohne Agentenänderung | Positivkontrolle bestanden; vier ungültige Fälle fachlich fehlgeschlagen; 23 + 22 Regressionseinzelprüfungen bestanden |
| `20261005T155128Z-94136bb0` | echtes Ollama, natives Toolprotokoll | 50 Runden, keine ausführbaren nativen Toolcalls, sicher am Rundenlimit beendet; kein Fix |
| `20261005T155940Z-2f092428` | echtes Ollama, JSON-Schema | 40 gezählte/abgewiesene Werkzeugversuche, Aktionslimit; kein Fix |
| `20261005T160314Z-d380f53e` | echtes Ollama, verbesserte Beobachtungen | Modell erzeugte einen fehlerhaften Patch (Variable außerhalb ihrer Schleife); HTTP-500-Fehler korrekt erkannt. Nach 18 Aktionen zur Diagnoseentwicklung manuell beendet |
| `20261005T160835Z-17fe5fe5` | echtes Ollama, offengelegter fachlicher Hinweis | Modell kopierte Zeilennummern/ungeeignete Textblöcke; Ersetzungen sicher abgewiesen. Auf Nutzerwunsch zum Abschluss beendet; kein erfolgreicher Live-Nachweis |

Die Entwicklungs-Terminalunterbrechungen der letzten beiden Versuche waren **kein Test
des UI-Abbruchpfads**. Ereignisse, tatsächlicher Diff und `developer-interruption.json`
bleiben lokal erhalten. Die produktive Abbruchfunktion und Container-Kindprozessbeendigung
sind separat getestet. Kein echter Lauf wird als erfolgreich dargestellt.

Eine vollständige kleine Kopie des simulierten Erfolgs liegt in
`docs/examples/scripted-success/` (Bericht, Ereignisse und Diff). Die Übersicht der echten
Fehlversuche liegt in `docs/examples/live-attempts.json`. Die großen Arbeitskopien bleiben
unter `.harness/` und gehören nicht in die Abgabehistorie.

## Manuelle Hilfe und Grenzen des Nachweises

Der Entwickler erstellte Aufgabenformulierung, initialen Quellkontext, geschützte Akzeptanz,
synthetische Fixtures, unveränderten Regressionstest-Adapter und die Werkzeugdefinitionen.
Nach dem nativen Protokollfehlschlag wurde der JSON-Schema-Modus ausdrücklich eingeführt.
Die dritte Version benennt die Kontextdatei eindeutig und liefert Beobachtungen für dieses
Protokoll als benannte User-Nachrichten. Im letzten Versuch gab ein zusätzlicher, im Task
gespeicherter Hinweis die Validierungsstelle **innerhalb der Transfer-Schleife und Transaktion**
an. Es wurde kein vorbereiteter Patch in einen echten Lauf eingespielt.

Ein vorbereitetes Patchskript existiert nur im eindeutig gekennzeichneten Scripted-Modus.
Ein dort erfolgreicher Akzeptanz-/Regressionslauf bestätigt die gesamte technische Kette,
aber nicht die Leistungsfähigkeit des echten Modells. Ein erfolgreicher echter Fix ist
weiter offen. Daher lautet der Gesamtstand **implementiert und weitgehend geprüft,
nicht vollständig nach den Abnahmekriterien verifiziert**.

Nicht ausgeführt: alle weiteren Upstream-HTTP-Smokes, ein vollständiger frischer Linux-
Hostaufbau, Videoaufnahme, Remote-Push/Merge/Deployment. Die Linux-Dockerprüfungen wurden
tatsächlich durchgeführt; sie ersetzen keine Linux-Hostinstallation.

## Konkrete Fortsetzung

1. Docker Desktop starten und im Benutzerprozess `python -m harness doctor` prüfen.
2. Ein geeignetes lokal vorhandenes Modell konfigurieren; bei anderem Modell natives
   Toolprotokoll erproben oder den ausdrücklich ausgewiesenen JSON-Schema-Modus verwenden.
3. `python -m harness run --provider ollama` ausführen. Derselbe Commit, Akzeptanztest und
   Adapter bleiben bestehen. Fehlversuche und manuelle Hilfe dokumentieren.
4. Nur wenn Baseline fachlich rot, unabhängige End-Akzeptanz und beide Regressionen grün
   sind, den Live-Nachweis als erfüllt markieren und dessen Bericht/Diff sichern.
5. Repository selbst bereitstellen und Video gemäß `docs/demo-script.md` aufnehmen.

Bei unbestätigtem Cleanup nennt `.harness/runs/<ID>/active-container.json` ausschließlich
den betreffenden Laufcontainer. Namen und `harness.run`-Label mit `docker inspect` prüfen,
diesen Container gezielt mit `docker rm --force <Name>` entfernen, Abwesenheit mit
`docker ps -a --filter name=<Name>` bestätigen. Erst danach die betreffende Registry-Datei
entfernen. Niemals pauschal fremde Container oder Docker-Ressourcen löschen.
