# Coding Harness zum Lernen

Ein eigener Python-Controller verbindet Ollama mit begrenzten Dateiwerkzeugen und
Docker-Checks. Du gibst einen Prompt ein; das Modell untersucht und verändert eine
frische Repositorykopie. Der Harness kontrolliert Rechte, Budgets und Ergebnisse.
Er enthält **keine vorgegebene Reparatur, keinen vorbereiteten Codeausschnitt und
keinen automatisch ausgefüllten Aufgabenprompt**.

Start zum Verstehen: [Dateien, Klassen und Ablauf](docs/learning-guide.md).
Maßgebliche Spezifikation: [Stage-1-Aufgabe](docs/assignment/stage-1-coding-harness.pdf).

## Einrichtung und Start

Voraussetzungen: Python 3.12, Git, Docker mit Linux-Engine und Ollama mit einem
bereits installierten Modell. Kein API-Key und kein automatischer Modell-Download.

PowerShell im Projektordner:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m harness setup --build
.\.venv\Scripts\python.exe -m harness doctor
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Linux: mit `python3.12 -m venv .venv` beginnen und in allen weiteren Befehlen
`.venv/bin/python` statt `.\.venv\Scripts\python.exe` verwenden.
UI: http://127.0.0.1:8501/.

1. In der Seitenleiste den Namen deines installierten Ollama-Modells eingeben.
2. „Umgebung prüfen“, eigenen Bugfix-Prompt schreiben, „Lauf starten“.
3. Werkzeugaufrufe, Zähler und Checks verfolgen; bei Bedarf „Abbrechen“.
4. Diff und Bericht prüfen/herunterladen. Ein neuer Lauf beginnt beim selben Commit.

Optional `config.example.toml` nach `config.local.toml` kopieren. Für CLI/Standardmodell
`HARNESS_MODEL`, für den Server `HARNESS_OLLAMA_BASE_URL` setzen. Beispiel:

```powershell
$env:HARNESS_MODEL = 'NAME-DEINES-INSTALLIERTEN-MODELLS'
.\.venv\Scripts\python.exe -m harness run --task 'Dein Bugfix-Auftrag'
```

## Was wird geprüft?

Ziel ist der Python-Teil der öffentlichen
[Supermarket Receipt Kata](https://github.com/emilybache/SupermarketReceipt-Refactoring-Kata),
Commit `c72d68abd77a417f84193b72a3b8d14177336066`. Sechs Anwendungsdateien dürfen
geändert werden. Geschützte Tests prüfen gedruckte Stückmengen sowie bestehende Preisregeln.
Der Ausgangsstand druckt Stückmengen mit einer unerwünschten Nachkommastelle.
Die frühere Paarpreis-Aufgabe wurde ausdrücklich ersetzt; ihr Fehler bleibt bestehen.

**„Alle konfigurierten Checks bestanden“ bewertet diese Tests, nicht automatisch
jeden beliebigen Prompt.** Für eine andere fachliche Aufgabe muss der Prüfer einen
passenden Akzeptanztest in `checks/` hinterlegen und dessen Fehlschlag vorab nachweisen.
Die PDF verlangt diese Vorbereitung. [Task und Vorgehen](docs/task.md).

## Reproduzieren

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest -q --docker -m docker
.\.venv\Scripts\python.exe -m harness baseline
.\.venv\Scripts\python.exe -m ruff check harness app.py tests checks/entry.py checks/acceptance.py checks/scenario.py checks/pricing_regression.py
```

Offline-Tests benötigen weder Modell noch Docker; fünf Docker-Fälle werden ausdrücklich
übersprungen. `--docker` behandelt fehlende Infrastruktur als Fehler. Scripted-Antworten
existieren nur für automatisierte Tests und sind kein bedienbarer Reparaturmodus.
`baseline` prüft ohne Modell; Exit-Code 0 bestätigt den dokumentierten fachlichen Fehler.
`run` liefert 0 nur nach bestandenen Endchecks, sonst 2. `Ctrl+C` fordert einen Abbruch an.

Artefakte: `.harness/runs/<ID>/report.json`, `events.jsonl`, `changes.diff` und Laufkopie.
Standardgrenzen: 40 Aktionen, 50 Runden, 2 Wiederholungen, 120 s je Check, 180 s je
Modellanfrage und 64 KiB Ausgabe. Details: [Architektur](docs/architecture.md).

## Stand und Abgabe

Die aktuelle Version ist offline geprüft. Am 07.10.2026 bestanden alle fünf echten
Docker-Tests. Der echte Lauf mit `qwen2.5-coder:7b`
endete ohne Codeänderung; die unabhängige Endakzeptanz blieb rot. Ein erfolgreicher
echter Modell-Bugfix ist weiterhin offen.
Der spätere 27B-Lauf endete nach wiederholten Anfrage-Timeouts mit `model_error`.
Der neueste Vergleich mit `qwen2.5-coder:3b` lief in 30,5 Sekunden ohne Timeouts:
Das Modell änderte Code, behob den Fehler jedoch nicht. Die geschützte Endakzeptanz
erkannte dies; beide Regressionen bestanden. Keine Container blieben zurück.
Historische erfolgreiche Läufe mit exakter Lösungshilfe sind als solche erhalten und
kein Nachweis für die neue Version. Siehe [Verifikation](docs/verification.md).

[Anforderungsmatrix](docs/requirements-matrix.md) · [Arbeitsstand](docs/implementation-status.md) ·
[Video-Drehbuch](docs/demo-script.md). Repository-Veröffentlichung und Video sind noch offen.
`CODEX_PROMPT.md` beschreibt den aktuellen Implementierungsauftrag. Bei Konflikten gilt die PDF.
