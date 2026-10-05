# OpenStock Coding Harness

Eigenes Python-Harness für Stage 1: Streamlit-Oberfläche, begrenzter Modellcontroller,
Repository-Werkzeuge und echte Docker-Ausführungsgrenze. Ziel ist ausschließlich
[TMBeaver/openstock](https://github.com/TMBeaver/openstock), Commit
`abc87dccab96c78917b35add542284e61adc5f37`. Aufgabe: atomare Ablehnung von Lagertransfers
mit Mengen ≤ 0. Es wird kein fertiges Coding-Harness verwendet.

## Voraussetzungen und Einrichtung

- Python **3.12** (getestet: 3.12.14), Git, Docker Desktop mit **Linux-Containern**.
- Für echte Modellläufe: laufendes Ollama, lokal installiertes Modell mit Werkzeugunterstützung.
  Getesteter Kandidat: `qwen2.5-coder:7b`, ca. 4,7 GB Modelldatei. Kein automatischer Download.
- Freier Zugriff des startenden Benutzers auf Docker und die Ollama-Adresse.
- Einrichtung benötigt Internet für Python-Pakete, öffentliches Repository und Docker-Basisimage.
  Die eigentlichen Prüfcontainer haben **kein externes Netzwerk**.

PowerShell im Projektverzeichnis; Aktivierungsskripte sind nicht erforderlich:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m harness setup --build
.\.venv\Scripts\python.exe -m harness doctor
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Linux:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m harness setup --build
.venv/bin/python -m harness doctor
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
```

Die Anwendung läuft unter [localhost:8501](http://localhost:8501). `doctor` liefert Exit-Code 2,
solange externe Voraussetzungen fehlen. Kerntests und UI bleiben trotzdem nutzbar.
Das Repository muss beim Start das Arbeitsverzeichnis sein; keine Installation des Zielcodes auf dem Host.

Optional `config.example.toml` nach `config.local.toml` kopieren. Die Beispielwerte funktionieren
ohne Kopie. Umgebungsvariablen überschreiben Provider-Einstellungen:

```powershell
$env:HARNESS_OLLAMA_BASE_URL = 'http://127.0.0.1:11434'
$env:HARNESS_MODEL = 'qwen2.5-coder:7b'
$env:HARNESS_OLLAMA_PROTOCOL = 'json_schema'
```

Unter Linux: `export HARNESS_MODEL='qwen2.5-coder:7b'` usw. Ein Modell muss vorher vom Nutzer
passend zu RAM/Hardware installiert werden. `ollama list` zeigt vorhandene Modelle.
`json_schema` verwendet Ollamas dokumentierte strukturierte Ausgabe für genau einen
validierten Werkzeugaufruf. `native` unterstützt direkt Ollamas `tool_calls` einschließlich
Assistant-/Tool-Zuordnung. Das hier vorhandene Modell lieferte im nativen Modus nur Text;
dieser wird **nicht** nachträglich als ausführbarer Aufruf interpretiert. Details und Fehlversuche:
[Verifikationsbericht](docs/verification.md).

## Normaler Ablauf

1. „Umgebung prüfen“: Commit, Docker-Image und Modell kontrollieren.
2. Aufgabe prüfen/eingeben, echten Ollama-Modus auswählen und „Lauf starten“ drücken.
3. Baseline abwarten: positive Kontrolle erfolgreich, ungültige Mengen fachlich fehlerhaft,
   beide Regressionen erfolgreich. Bei fehlerhafter Infrastruktur wird der Lauf blockiert.
4. Verlauf verfolgen; „Abbrechen“ bleibt während Modellanfragen und Containerprüfungen bedienbar.
5. Diff, Baseline, unabhängige Endprüfungen und Bericht ansehen/herunterladen.
6. Ein neuer Lauf beginnt stets mit einer frischen Kopie desselben Commits.

Ein Betriebssystem-Lock verhindert zwei parallele Harness-Läufe, auch bei UI-Reruns oder
zusätzlicher CLI. Der Simulationsmodus führt ein offengelegtes festes Antwortskript zur
Mengenaufgabe aus; Docker und die Prüfungen sind dabei echt. Er zählt nicht als Modellnachweis.

## Prüf- und Demonstrationsbefehle

```powershell
# Ohne Docker, Live-Modell oder Konto; Docker-Tests ausdrücklich ausgelassen
.\.venv\Scripts\python.exe -m pytest -q
# Echte Ausführungsgrenze; fehlendes Docker ist hier ein Fehler, kein Skip
.\.venv\Scripts\python.exe -m pytest -q --docker -m docker
# Unveränderter Ausgangszustand, dann wahlweise Simulation oder echtes Modell
.\.venv\Scripts\python.exe -m harness baseline
.\.venv\Scripts\python.exe -m harness run --provider scripted
.\.venv\Scripts\python.exe -m harness run --provider ollama
.\.venv\Scripts\python.exe -m ruff check harness app.py tests checks/entry.py checks/acceptance.py
```

Unter Linux jeweils `.venv/bin/python` verwenden. CLI-Abbruch: `Ctrl+C`; das Programm wartet
auf das bestätigte Containerende. Erfolgreiche normale Läufe liefern Exit-Code 0; Abbruch,
Fehler, Limit oder blockierte Voraussetzungen liefern 2. `baseline` liefert 0 nur bei
fachlich korrekt reproduzierter Ausgangslage, nicht weil der Akzeptanztest grün wäre.

## Artefakte und weitere Dokumentation

Pro Lauf: `.harness/runs/<Lauf-ID>/report.json`, `events.jsonl`, `changes.diff`, `repo/`, `base/`.
Die UI exportiert Bericht und Diff. Referenz und Arbeitskopien bleiben aus Git ausgeschlossen;
das vom Nutzer gepflegte OpenStock-Projekt wird nicht verwendet oder überschrieben.

- [Architektur und Sicherheitsgrenzen](docs/architecture.md)
- [Aufgabe, Commit und Prüfadapter](docs/task.md)
- [PDF-Anforderungsmatrix](docs/requirements-matrix.md)
- [Verifikation](docs/verification.md) und [fortsetzbarer Implementierungsstand](docs/implementation-status.md)
- [Drehbuch für ein 3:40-Minuten-Video](docs/demo-script.md)

Repository-Bereitstellung und Videoaufnahme sind Nutzeraufgaben. Das Harness besitzt keine
Push-, Merge- oder Deployment-Werkzeuge.
