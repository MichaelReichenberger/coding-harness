# Verifikation der vereinfachten Version

## Prüfung der einfacheren Belegdruck-Aufgabe am 07.10.2026

Auf Nutzerwunsch wurde die aktive Akzeptanz ausdrücklich auf einen einfacheren,
im unveränderten öffentlichen Commit bereits vorhandenen Fehler umgestellt:
Stückmengen auf dem Beleg ohne Nachkommastellen; Gewichte weiterhin mit drei.
`Teller → ShoppingCart → Receipt → ReceiptPrinter` bleibt echtes Verhalten über Module.
Es wurde kein künstlicher Fehler eingebaut und keine Reparatur im Modellprompt hinterlegt.
Der alte Paarpreisfehler bleibt bestehen und ist nicht Teil dieser neuen Akzeptanz.
Task, README, Lernleitfaden, Diagrammtext und deterministische Testfixture wurden angepasst.

- Baseline `20261007T151642Z-287617f6`: fachlich rot, drei Positivkontrollen grün,
  beide Regressionen grün, `baseline_bug_reproduced=true`.
- Offline: **59 bestanden, 5 Docker-Fälle übersprungen**, 9,80 s; Ruff bestanden.
- Docker: **5 bestanden**, 27,11 s; nur eine Cache-Schreibwarnung unter Windows.
  Der deterministische Rot-Grün-Test verwendet die neue Aufgabe, ausschließlich als Testfixture.
- Echter 3B-Versuch `20261007T151803Z-9c20b765`: 29,5 s, 6 Aktionen, failed.
  Das Modell rundete die gespeicherte Menge statt die Anzeige zu korrigieren.
  Endakzeptanz blieb rot, beide Regressionen grün.
- Zweiter echter Versuch `20261007T151855Z-fae2077a`: limit_reached nach 40 Aktionen.
  Alle 40 Änderungsversuche wurden wegen fehlendem Quelltext abgelehnt; keine Änderung.
  Endchecks nicht ausgeführt. Der präzisierte Nutzerprompt ist vollständig im Bericht.
- Dritter Versuch mit kürzerem Verhaltensprompt: `20261007T152040Z-55037850`;
  endgültiger Befund wird nach dem begrenzten Lauf ergänzt.

Manuelle Hilfe: Auswahl der kleineren Aufgabe, geschützte Tests und zwei Änderungen
an der Verhaltensbeschreibung. Keine Quellcodekorrektur und kein fertiger Patch wurde
in einen echten Modelllauf eingefügt. Die folgenden Abschnitte dokumentieren die ältere
Paarpreis-Aufgabe; ihre Berichte behalten ihre ursprünglichen Tests und Diffs.

## Neuester Vergleich mit qwen2.5-coder:3b

Lauf `20261007T151255Z-a166e6a4` am 07.10.2026 verwendete den unveränderten Prompt
des 7B-Vergleichs, ohne Reparaturhinweis. Docker, Image und Ollama waren tatsächlich
erreichbar. **30,5 Sekunden, 6 Aktionen/Anfragen, 0 Wiederholungen/Ablehnungen,
keine Timeouts, failed.** Das Modell ersetzte `int(quantity)` durch
`math.floor(quantity)`; der Fehler bei ungeraden Zweiermengen blieb bestehen.
Baseline und Endakzeptanz rot, beide Regressionen jeweils grün. Sieben ausgeführte
Checks bestätigten Container-Cleanup; danach keine Container in `docker ps -a`.
Bericht und Diff: `.harness/runs/20261007T151255Z-a166e6a4/`.

Ein zuvor in der UI gestarteter 3B-Lauf `20261007T151156Z-84c15522` endete ebenfalls
failed (32,2 s, 4 Aktionen). Er änderte die Mindestmenge von 2 auf 3 und verschlechterte
damit zusätzlich den Paarpreis. Kein Patch wurde in die Referenzkopie übernommen.

Der tatsächlich gestartete 27B-Lauf `20261007T145028Z-32ae6491` ist inzwischen beendet:
17 Minuten 13,7 Sekunden, **model_error**, 6 Anfragen, 4 Wiederholungen, 5 Aktionen,
ein gültiger `list_files`-Aufruf und fünf Anfrage-Timeouts, keine Änderungen.
Baseline fachlich rot, Regressionen grün; Endchecks nicht ausgeführt.
Die beobachteten Timeouts belegen keinen RAM-Mangel. Ein erfolgreicher echter
Modell-Bugfix ist weiterhin offen.

## Früherer blockierter Versuch mit qwen3.8:27b

Am 07.10.2026 war `qwen3.8:27b` tatsächlich installiert und Ollama erreichbar.
Der identische Prompt des früheren Laufs wurde ohne Ergänzungen mit
`HARNESS_MODEL=qwen3.8:27b` übergeben. Lauf `20261007T144809Z-a0d8b44d`:
**blocked** bei der Docker-Vorprüfung (erneut HTTP 500), 0 Modellanfragen,
keine Änderungen. Baseline/Endchecks nicht ausgeführt. Dies ist kein Ergebnis
zur Leistungsfähigkeit dieses Modells; der echte Vergleich steht noch aus.

Bericht lokal unter `.harness/runs/20261007T144809Z-a0d8b44d/report.json`.

## Nachprüfung am 07.10.2026

Docker und Ollama sind wieder erreichbar. `python -m harness doctor` meldete
`sandbox_ready=true` und `live_ready=true`.

`python -m pytest -q --docker -m docker -o cache_dir=.harness/retry-docker-cache
--basetemp=.harness/retry-docker-tests`: **5 bestanden, 59 abgewählt**, 29,08 s.
Eine Windows-Dateirechtewarnung betraf nur das Schreiben des pytest-Caches.
Die echte Isolations-/Prozessprüfung und der deterministische Rot-Grün-Bugfix sind bestanden.

Echter Ollama-Lauf `20261007T142611Z-3ff946cd`: 14:26:11–14:27:06 UTC,
54,3 s, `qwen2.5-coder:7b`, 7 Aktionen/Anfragen, keine Ablehnungen/Wiederholungen.
Der Nutzerprompt beschreibt Zweierpreise und verlangt Untersuchung/Tests, ohne Lösungsvorgabe.
Das Modell suchte in sechs Dateien nach `calculate_total_price`, fand keine Treffer
und rief `finish` auf. **Keine Änderungen, leerer Diff, Ergebnis failed.**

Baseline: Akzeptanz fachlich rot, beide Regressionen grün, `baseline_bug_reproduced=true`.
Endprüfung: Akzeptanz weiterhin rot, beide Regressionen grün. Alle sechs Checks bestätigten
Cleanup; keine Container blieben zurück. Bericht/Ereignisse/Diff liegen lokal unter
`.harness/runs/20261007T142611Z-3ff946cd/`.

Damit ist die aktuelle Sandbox nachgewiesen. Der erfolgreiche echte Modell-Bugfix
bleibt offen. Es wurde kein Patch eingespielt und kein stärkeres Modell heruntergeladen.
Die nachfolgenden Abschnitte beschreiben den früheren Stand vom 06.10.2026.

Stand: **06.10.2026**. Windows, Python 3.12.14, Streamlit 1.65.0,
Pydantic 2.13.5, HTTPX 0.28.1, pytest 9.1.1. Alle vier PDF-Seiten wurden erneut gelesen.

## Tatsächlich ausgeführt

| Prüfung | Ergebnis |
|---|---|
| `python -m pytest -q` (eigene Temp-/Cacheordner) | **59 bestanden, 5 Docker-Tests ausdrücklich übersprungen**, 8,11 s |
| `python -m ruff check harness app.py tests checks/entry.py checks/acceptance.py checks/scenario.py checks/pricing_regression.py` | **bestanden** |
| `python -m pip install --dry-run --no-index -r requirements.lock` | **bestanden**, alle 49 benötigten fixierten Pakete in vorhandener venv; keine frische Installation |
| Streamlit AppTest | innerhalb der 59 Tests: leeres Aufgabenfeld, eigener Prompt/Modell, Start/Rerun/Abbruch, Ergebnisse/Downloads |
| `python -m harness doctor` aus freigegebener tatsächlicher Ausführung | Python/Pakete/Git/Commit bereit; Ollama erreichbar, `qwen2.5-coder:7b` installiert; **Docker HTTP 500** |
| `python -m pytest -q --docker -m docker -x` | **1 Setupfehler**, anschließend gestoppt: keine nutzbare Linux-Engine; kein grüner Sandbox-Nachweis |
| Neuer echter Harness-Versuch | **blocked**, vor Modellaufruf; Lauf `20261006T201836Z-e6d5917b` |
| Streamlit-Server und Browser | auf `http://127.0.0.1:8501/` neu gestartet; leeres Aufgabenfeld, Modellauswahl, sechs erlaubte Dateien und 0/40 Aktionen sichtbar geprüft |

Der endgültige Offline-Befehl war:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -o cache_dir=.harness/readable-final-cache --basetemp=.harness/readable-final-tests
```

Der explizite Docker-Versuch verwendete `.harness/readable-docker-cache` und
`.harness/readable-docker-tests`. Der zusätzliche fünfte Docker-Test für den
Scripted-Rot-Grün-Bugfix wurde danach ergänzt und offline nur gesammelt, nicht ausgeführt.

## Echter Versuch ohne Lösungsvorgabe

Prompt:

> Bei einem Zweierangebot werden ungerade Artikelmengen falsch berechnet. Drei Artikel
> mit Einzelpreis 1,00 und einem Angebotspreis von 1,50 je Paar sollen insgesamt 2,50
> kosten. Korrigiere das Verhalten und erhalte die anderen Preisregeln.

Artefakte: `.harness/runs/20261006T201836Z-e6d5917b/`.
Status `blocked`, 0 Aktionen, keine Modellanfrage, keine Codeänderung.
Baseline und Endchecks sind `not_run`. Docker antwortete auf `/v1.48/info`:
`request returned 500 Internal Server Error ... dockerDesktopLinuxEngine`.
Das ist weder eine Modellniederlage noch ein erfolgreicher Modellnachweis.

Ollama war tatsächlich erreichbar; ein stärkeres Modell wurde nicht heruntergeladen.
Der frei gewählte Modellname lässt sich in der Seitenleiste oder per `HARNESS_MODEL` setzen.

## Historische Nachweise sauber getrennt

`docs/examples/live-success/` enthält einen echten Lauf vom 05.10.2026 mit genauer
Reparaturanweisung und vorbereitetem Quellkontext. Dieser Bericht wird nicht verändert
oder als Erfolg der aktuellen Version ausgegeben. Der damalige Verifikationsbericht
steht unter `docs/history/assisted-version/verification.md`.

Damals bestanden vier echte Docker-Tests und zwei angeleitete Modellläufe. Seitdem wurden
Controller, Bedienung und Prüfablauf vereinfacht. Das ersetzt keine erneute Abnahme.

## Reproduktion nach Beheben der Docker-Engine

```powershell
# Docker Desktop muss eine funktionsfähige Linux-Engine anzeigen.
docker info --format '{{.OSType}}'
.\.venv\Scripts\python.exe -m harness setup --build
.\.venv\Scripts\python.exe -m harness doctor
.\.venv\Scripts\python.exe -m pytest -q --docker -m docker
.\.venv\Scripts\python.exe -m harness baseline
# Name eines tatsächlich installierten Modells wählen, keinen Platzhalter belassen.
$env:HARNESS_MODEL = 'NAME-DEINES-INSTALLIERTEN-MODELLS'
.\.venv\Scripts\python.exe -m harness run --task 'Bei Zweierangeboten ist der Preis ungerader Mengen falsch. Drei Artikel à 1,00 mit Paarpreis 1,50 müssen 2,50 kosten. Korrigiere dies und erhalte andere Preisregeln.'
```

Erwarteter Harness-Nachweis: begrenzte Werkzeuge und nachvollziehbare Fehler auch bei
Modellmisserfolg. Zusätzlich erforderlicher PDF-Erfolgsnachweis: fachlich rote Baseline,
echter Modelldiff, danach grüne geschützte Akzeptanz und Regressionen. Das Modell darf
scheitern; diese Abgabeanforderung bleibt dann offen. Manuelle Hilfen im Bericht/Video benennen.

Noch nicht geprüft: neue frische Installation, Linux als Host, neue erfolgreiche reale
Bugfix-Demonstration. Repositorylink und Video bis vier Minuten müssen noch eingereicht werden.
