# Drehbuch: maximal vier Minuten

Geplante Inhaltsdauer **3:40**, 20 Sekunden Reserve. Aufnahme und Repository-Abgabe sind
Nutzeraufgaben. Die Implementierung erzeugt kein Video. Vor der Aufnahme `doctor` ausführen,
UI starten und die gewünschten lokalen Laufartefakte bereithalten.

| Zeit | Bild | Aussage / Aktion |
|---|---|---|
| 0:00–0:20 | UI mit Ziel und Commit | Eigenes Python-Harness; Modellcontroller außerhalb einer Linux-Docker-Sandbox. OpenStock-Commit zeigen. |
| 0:20–0:45 | Aufgabe und `docs/architecture.md` | Mengen ≤0 müssen HTTP 400 liefern; keine Teilbuchungen. App, Operations und SQLite arbeiten zusammen. |
| 0:45–1:10 | Baseline-Checks | Positivkontrolle grün. −1, 0 und gemischte Positionen erhalten vorher fälschlich HTTP 200. Bestehende Regressionen sind grün. |
| 1:10–2:05 | „Lauf starten“, Verlauf | Controller prüft strukturierte Anfragen, führt eigene Dateiwerkzeuge aus und gibt Beobachtungen zurück. Wartezeit nur sichtbar als Zeitraffer/Schnitt kürzen. Abbruchknopf zeigen. |
| 2:05–2:35 | Dateien & Diff | Kleinen Patch in der Transferlogik zeigen. Erlaubter Scope operations.py/app.py; keine Tests vom Agenten geändert. |
| 2:35–3:05 | Checks | Unabhängige Endprüfung: alle fünf Akzeptanzfälle und beide unveränderten Regressionen. Status/Exit-Codes und geschützte Checks zeigen. |
| 3:05–3:25 | Download/Report | Lauf-ID, Provider, Modell, Commit, Aktionen, Fehlversuche, manuelle Hilfe und Diff herunterladen. |
| 3:25–3:40 | Grenzen | Ein lokaler Nutzer, feste Checks, keine Host-Shell, keine Push-/Merge-Werkzeuge. Infrastruktur und Modellqualität begrenzen den Lauf. |

## Ehrliche Darstellung des aktuellen Stands

Der erfolgreiche deterministische Lauf ist **SIMULIERT**: Die Antworten einschließlich
Patch stammen aus `scripted_demo()`. Modellclient und Controller laufen dabei echt, ebenso
die Docker-Prüfungen; er erfüllt aber **nicht** die PDF-Forderung eines erfolgreichen echten
Modelllaufs. Diese Einblendung muss während einer simulierten Demonstration sichtbar sein.

Die realen Ollama-Versuche waren nicht erfolgreich. Soll das Video die vollständige
Abnahmeforderung erfüllen, muss vorher ein echter Lauf mit einem geeigneten Modell gelingen.
Dafür ein bereits vorhandenes geeignetes Modell über `HARNESS_MODEL` wählen, Protokoll
einstellen und `python -m harness run --provider ollama` ausführen. Ein neuer Lauf beginnt
vom fixierten Commit; der geschützte Akzeptanztest bleibt bestehen. Keinen Simulationspatch
als Modellarbeit ausgeben. Manuelle Hinweise, Modellwechsel und Wiederholungen nennen.

Bei einem weiter fehlschlagenden Live-Lauf dessen tatsächlichen Status vorführen und den
offenen Nachweis benennen. Kein „alle Tests grün“ behaupten, wenn Pflichtprüfungen fehlen.
