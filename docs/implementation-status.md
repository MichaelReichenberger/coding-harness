# Implementierungsstand

## Einfachere POC-Aufgabe am 07.10.2026

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

## Neuester Vergleich: qwen2.5-coder:3b am 07.10.2026

Das installierte Modell und Ollama waren erreichbar. Docker meldete zunächst erneut
HTTP 500, war bei der direkten Nachprüfung aber wieder verfügbar. Ein bereits aktiver
UI-Lauf verhinderte zunächst korrekt einen parallelen CLI-Start.

Nach dessen Ende lief derselbe Prompt wie beim früheren 7B-Modell ohne Lösungshilfe:
`20261007T151255Z-a166e6a4`, **30,5 Sekunden, failed**, 6 Aktionen/Anfragen,
keine Wiederholungen, Timeouts oder Ablehnungen. Das Modell las Code und ersetzte
`int(quantity)` durch `math.floor(quantity)` in `shopping_cart.py`. Dies behebt die
falsche Paarpreisberechnung nicht. Die unabhängige Endakzeptanz blieb bei den drei
ungeraden Mengen rot; beide Regressionen bestanden. Alle sieben Container-Checks
bestätigten Cleanup; `docker ps -a` zeigte anschließend keine Container.

Der vorherige UI-Lauf `20261007T151156Z-84c15522` verwendete ebenfalls 3B mit einem
anderen Nutzerprompt: 32,2 Sekunden, 4 Aktionen, failed. Seine Änderung der
Mindestmenge von 2 auf 3 ließ zusätzlich den Test für ein einzelnes Paar scheitern.
Beide Änderungen bleiben ausschließlich in ihren wegwerfbaren Laufkopien.

3B antwortete hier deutlich schneller als 27B. Ein RAM-Mangel beim 27B-Modell wurde
nicht nachgewiesen. Der erfolgreiche echte Modell-Bugfix bleibt offen; für einen
weiteren Versuch in der UI `qwen2.5-coder:3b` als Modell eingeben. Berichte und Diffs:
`.harness/runs/20261007T151255Z-a166e6a4/` und
`.harness/runs/20261007T151156Z-84c15522/`.

## Abgeschlossener 27B-Lauf mit erreichbarer Sandbox: 07.10.2026

Docker und `qwen3.8:27b` waren für `20261007T145028Z-32ae6491` tatsächlich erreichbar.
Die unveränderte Baseline reproduziert den Preisfehler; beide Regressionen bestanden.
Modellanfragen erreichten wiederholt das 180-Sekunden-Limit. Nach zwei anfänglichen
Timeouts lieferte das Modell einen gültigen `list_files`-Aufruf. Der Lauf endete nach
17 Minuten 13,7 Sekunden mit **model_error**: 6 Anfragen, 4 Wiederholungen,
5 gezählte Aktionen einschließlich Wiederholungen, keine Codeänderungen.
Fünf Anfragen scheiterten am Zeitlimit; Endchecks wurden nicht ausgeführt.
Ollama meldete rund 19 GB Modellspeicher, davon etwa 4,5 GB im GPU-Speicher.
Der endgültige Laufbericht liegt unter `.harness/runs/20261007T145028Z-32ae6491/`.

## Letzter Versuch: qwen3.8:27b am 07.10.2026

Das ausdrücklich ausgewählte Modell `qwen3.8:27b` ist inzwischen installiert und
über Ollama erreichbar. Der identische Bugfix-Prompt wurde erneut über die CLI gestartet.
Lauf `20261007T144809Z-a0d8b44d` endete mit **blocked** vor dem Modellaufruf:
Docker meldete erneut HTTP 500 für die Linux-Engine. Keine Modellanfrage, keine Aktionen,
keine Änderungen. Der Vergleich der Modelle ist daher noch offen. Vor einem erneuten
Versuch muss die Docker-Linux-Engine wieder erreichbar sein.

Bericht: `.harness/runs/20261007T144809Z-a0d8b44d/report.json`.
Die folgenden erfolgreichen Docker-Prüfungen beschreiben den vorherigen Zustand.

## Aktueller Stand: 07.10.2026, Docker wieder erreichbar

- `doctor`: Docker Linux, Sandbox-Image, Zielcommit und Ollama tatsächlich erreichbar.
- Alle **5 echten Docker-Tests bestanden**, einschließlich geschützter Mounts,
  zeilenloser Ausgabe/Nonzero, Timeout/Abbruch mit Kindprozess und Scripted-Rot-Grün-Bugfix.
  Eine Windows-Cachewarnung beeinflusste die Tests nicht.
- Echter Lauf ohne Lösungshinweis: `20261007T142611Z-3ff946cd`,
  Modell `qwen2.5-coder:7b`, 7 Aktionen, 54,3 Sekunden, **failed**.
- Das Modell suchte nach einem nicht vorhandenen Funktionsnamen und beendete ohne Patch.
  Die unabhängigen Endchecks erkannten die unverändert fehlerhaften Zweierpreise.
  Beide Regressionen bestanden; Cleanup aller sechs Checks bestätigt, keine Container übrig.
- Der Infrastrukturblocker ist behoben. Der erfolgreiche echte Modell-Bugfix-Nachweis
  bleibt offen; dieser frühere Lauf verwendete ausschließlich `qwen2.5-coder:7b`.
- Die zuvor blockierte Bereinigung des alten Projekt-Images ist jetzt abgeschlossen.

Bericht: `.harness/runs/20261007T142611Z-3ff946cd/report.json`.
Der folgende Stand dokumentiert die früheren Versuche und wird historisch gelesen.

## Bereinigung am 07.10.2026

Das frühere Zielprojekt wurde aus dem aktuellen Arbeitsverzeichnis vollständig entfernt:
alte Referenzkopie, zehn Laufkopien einschließlich unvollständiger Läufe, Beispielberichte,
archivierte Tests/Konfigurationen und veraltete Test-/Umgebungsartefakte. Der Auftragstext
wurde auf das aktuelle Ziel aktualisiert; alte Verweise in der Dokumentation sind entfernt.
Fünf nicht mehr benötigte Pakete wurden auch aus der lokalen Projekt-venv deinstalliert.

Kontrolle: keine Treffer für frühere Repositorybezeichnungen in Projekt-/Artefakttexten;
die unveränderte Originalaufgabe und vorhandene Git-Historie bleiben erhalten.
59 Offline-/UI-Tests bestanden, fünf Docker-Tests ausdrücklich ausgelassen.
Die externe Image-Bereinigung war zunächst durch die Engine blockiert und wurde bei
der späteren erfolgreichen Docker-Nachprüfung abgeschlossen.

Stand: **06.10.2026, nach Vereinfachung für den Lernzweck**.
Die Stage-1-PDF ist Source of Truth. Die vorherige Aussage „vollständig verifiziert“
gilt nicht für die aktuelle überarbeitete Version.

## Erledigt

- Ein Ablauf mit leerem Promptfeld; frei wählbares installiertes Ollama-Modell.
- Demo-/Freimodus, automatisch eingesetzte Aufgabe, exakte Lösungsvorgabe,
  vorab ausgewählter Codeausschnitt und bedienbarer Scripted-Reparaturmodus entfernt.
- Modellschleife mit genau einer JSON-Aktion je Runde; kein zweites Toolcall-Protokoll.
- Geschützte Checks identisch vor/nach jedem Lauf; Ergebnis behauptet nur die geprüften Regeln.
- 40 Aktionen/50 Runden als konfigurierbare Standards; Fehler, Ablehnungen, Wiederholungen,
  Ausgabe, Zeit, Kontext und Containerressourcen bleiben begrenzt.
- Deutsche Modul-/Klassenkommentare und Erklärungen an Validierungs-/Abbruchstellen.
- Vollständige Datei-/Klassenübersicht und Lesereihenfolge in `docs/learning-guide.md`.
- README, Task, Architektur, PDF-Matrix, Verifikation und Drehbuch überarbeitet.
- Unbenötigte Abhängigkeiten aus der Lockdatei entfernt; 49 verbleibende
  Laufzeit-/Testpakete gegen installierte Metadaten geprüft.
- Deterministischer Rot-Grün-Docker-Test ergänzt. Die feste Reparatur ist ausschließlich
  eine Testfixture, kein echter Lauf und kein Leistungsnachweis eines LLM.

## Verifiziert und blockiert

- **59 Offline-/UI-Tests bestanden; 5 Docker-Fälle ausdrücklich übersprungen.**
- Ruff bestanden; Dependency-Dry-run ohne Netzwerk erfolgreich (keine Neuinstallation).
- Ollama erreichbar, bisheriges Modell installiert. Kein Modell heruntergeladen.
- Docker aus tatsächlicher freigegebener Ausführung mit HTTP 500 nicht funktionsfähig.
- Expliziter Docker-Test scheitert beim Setup. Neue erfolgreiche Dockerabnahme offen.
- Echter Versuch `20261006T201836Z-e6d5917b`: `blocked`, **0 Modellanfragen**, keine Änderungen.
  Bericht/Diff/Ereignisse unter `.harness/runs/20261006T201836Z-e6d5917b/`.
- UI auf `http://127.0.0.1:8501/` neu gestartet und im Browser geprüft: leeres Aufgabenfeld,
  Modellauswahl und Aktionsbudget sichtbar. Screenshot: `.harness/ui-simplified.png`.
- Alte erfolgreiche angeleitete Modellläufe bleiben historische Artefakte, kein neuer Nachweis.

## Nächste ausführbare Schritte

1. Docker Desktop/Linux-Engine reparieren bzw. neu starten; `docker info --format '{{.OSType}}'`
   muss `linux` liefern. Kein Host-Fallback und kein stilles Überspringen.
2. `python -m harness setup --build`, `python -m harness doctor`.
3. `python -m pytest -q --docker -m docker` und `python -m harness baseline`.
4. Stärkeres installiertes Modell auswählen; eigenen fachlichen Prompt in der UI eingeben.
5. Für den PDF-Nachweis einen echten erfolgreichen Lauf mit roter Baseline, Diff,
   grüner Endakzeptanz und Regressionen sichern. Bei anderen Aufgaben zuerst geschützte
   Akzeptanz anpassen; Verfahren in `docs/task.md`.
6. Frische Einrichtung prüfen, Abgabe-Repository/Commit bereitstellen und Video ≤4 Minuten aufnehmen.

PowerShell verwendet `.\.venv\Scripts\python.exe`; Linux `.venv/bin/python`.
Keine Pushes, Merges oder Deployments durchgeführt. Benutzerdateien und frühere
Laufberichte wurden erhalten; keine alten Erfolgsmeldungen in aktuelle umgeschrieben.
