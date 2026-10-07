# Implementierungsauftrag: verständliches Python-Coding-Harness

Maßgeblich ist docs/assignment/stage-1-coding-harness.pdf. Bei Konflikten hat die PDF Vorrang.
Das Projekt ist ein lokales Hochschul-POC zum Lernen der Modell-/Werkzeugschleife und ihrer Grenzen.

## Ziel und Eingaben

- Repository: https://github.com/emilybache/SupermarketReceipt-Refactoring-Kata
- Commit: c72d68abd77a417f84193b72a3b8d14177336066; Teilprojekt python/.
- Nutzer und Prüfer formulieren ihren eigenen Auftrag im leeren Aufgabenfeld.
- Das installierte Ollama-Modell ist frei wählbar. Keine automatischen Downloads.
- Keine hinterlegte Reparatur, kein automatisch ergänzter Lösungshinweis oder gezielter Quellkontext.
- Erlaubte Dateien stehen in config/target.json; Tests und Konfiguration sind geschützt.

## Ablauf und Grenzen

Implementiere das Harness selbst in Python 3.12. Streamlit zeigt Eingaben, Fortschritt,
Abbruch, geänderte Dateien, Diff und Checks. Erhalte klare Zuständigkeiten und deutsche Kommentare.

Controller: Baseline ausführen, je Runde eine strukturierte Modellaktion validieren,
Budget zählen, erlaubtes Werkzeug ausführen und Ergebnis oder Fehler zurückgeben.
Nach finish unabhängig erneut prüfen. Modellbehauptungen ersetzen keine Testergebnisse.

Werkzeuge: Dateien auflisten, lesen, suchen, eindeutig bearbeiten und feste Checks starten.
Argumente, Pfade und Rechte werden in Anwendungscode geprüft. Repository- und Modelltext
sind nicht vertrauenswürdig. Keine freie Shell, Pushes, Merges oder Deployments.

Jeder Lauf beginnt mit einer frischen Commitkopie. Zielcode läuft ausschließlich in
Linux-Docker-Containern mit Ressourcenlimits, geschützten Quell-/Testmounts und ohne Netzwerk.
Fehlende Sandbox blockiert den Lauf. Timeout/Abbruch müssen Container-Kindprozesse beenden.

Aktionen, Ablehnungen, Wiederholungen, Zeiten und Ausgaben begrenzen. Diff und Bericht auch
bei Abbruch sichern. Unbestätigtes Containerende verhindert weitere Aktionen. Failed,
unavailable und not_run bleiben sichtbar.

## Prüfungen und Dokumentation

- Geschützte Akzeptanz für den Stückmengen-Druckfehler: fachlich rote Baseline, nach erfolgreichem
  echtem Modellfix grün; vorhandene Regressionen bleiben grün.
- Andere Aufgaben benötigen passende vorab vorbereitete geschützte Akzeptanztests.
- Scripted-Antworten dienen ausschließlich reproduzierbaren automatisierten Tests.
- Kerntests ohne Modell, Konto oder Docker; separat ausführbare echte Docker-Grenztests.
- Erfolgreicher echter Modelllauf mit Diff und Checks für den PDF-Nachweis. Fehler und
  manuelle Hilfen transparent dokumentieren; keine erfundenen Erfolge.

Erkläre alle Python-Dateien/Klassen im Lernleitfaden. Pflege README, Diagramme, PDF-Matrix,
Verifikation und docs/implementation-status.md. Dokumentiere PowerShell-/Linux-Aufrufe
und konkrete Nachholschritte bei externen Blockern.

Repositorylink/Commit und Video bis vier Minuten gehören zur Abgabe. Keine Veröffentlichung
oder Remote-Pushes ohne entsprechenden Auftrag.
