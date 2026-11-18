# Prüfung und Modellnachweis

Am 18. November 2026 wurden mit Python 3.13.2 alle 91 Tests bestanden. Darunter sind sechs echte Docker-Fälle und neun Prüfungen der Oberfläche. Die Suite lief in rund 59 Sekunden. Ruff, die Formatprüfung für 30 Pythondateien und `pip check` waren ebenfalls erfolgreich.

Die Tests melden 133 Warnungen zur späteren Entfernung von `PureWindowsPath.is_reserved` in Python 3.15. Auf der geprüften Pythonversion ist dadurch kein Test fehlgeschlagen.

Die aktuelle Prüfung wird in [verification.json](evidence/stage-2/verification.json) mit Befehlen, Ausgaben und Exit-Codes festgehalten. [junit.xml](evidence/stage-2/junit.xml) enthält die einzelnen Testergebnisse. Die Anleitung zum Wiederholen steht in der [README](../README.md).

Die vollständige Suite wird mit `python -m pytest -q --docker` ausgeführt. Sie umfasst die Offlineprüfungen und sechs echte Docker-Fälle. Die Oberfläche wird dabei mit Streamlit AppTest geprüft. Ein Modellkonto ist dafür nicht erforderlich. Zusätzlich werden Ruff, die Formatierung und die installierten Paketabhängigkeiten geprüft.

Die Abhängigkeiten wurden außerdem mit `pip install -r requirements.lock` in einer neuen Pythonumgebung installiert. Die anschließende Paketprüfung bestand. Ein neuer Baselinelauf am 18. November endete mit `baseline_checked`. Der Featurecheck schlug erwartungsgemäß fehl, beide Regressionen und die Syntaxprüfung bestanden.

## Echter Featurelauf

Der Lauf `20261116T164810Z-6e87ce83` wurde mit dem lokalen Modell `qwen3.8:27b` auf der Grafikkarte ausgeführt. Er ist nicht simuliert. Nach 20 Werkzeugaktionen und 21 Modellanfragen waren `feature`, `regression_core`, `regression_pricing` und `lint` in der unabhängigen Endprüfung bestanden. Der Modelldiff verändert `receipt.py` und `teller.py`.

Nach der ersten eigenen Dateiänderung wurde der Lauf bei zwölf verbrauchten Aktionen sauber abgebrochen. Ein neuer RunService öffnete denselben Checkpoint und setzte die Sitzung mit erhaltenen Änderungen und Zählern fort. Es gab dabei keine unsicher laufende Aktion. [lifecycle.json](evidence/stage-2/lifecycle.json) hält diese Beobachtungen und die damalige GPU-Belegung fest.

[report.json](evidence/stage-2/report.json), [events.jsonl](evidence/stage-2/events.jsonl), [session.json](evidence/stage-2/session.json) und [changes.diff](evidence/stage-2/changes.diff) sind die unveränderten Rohdateien dieses Laufs. Sie beziehen sich auf den damaligen Code- und Konfigurationsstand. Sie sind Belege und keine Sitzung, die auf einem anderen Rechner unmittelbar fortgesetzt werden soll. Lokale Pfade und Zeitstempel darin bleiben deshalb erhalten.

Ein früherer Modellpatch verlor bei großen Gebühren den Warenbetrag oder dessen Nachkommastellen. [previous-model-regression.json](evidence/stage-2/previous-model-regression.json) zeigt die betreffenden Fehlprüfungen. Daraufhin wurden die Präzisionsfälle und die Anforderung einer exakten rationalen Summe ergänzt. Der erfolgreiche Lauf erhielt den Hinweis auf `fractions.Fraction`, aber keinen fertigen Patch. Unterstützung und Herkunft sind in der README offengelegt.

## Was die Prüfung aussagt

Die geschützten Featuretests prüfen 30 Fälle für die Servicegebühr. Die beiden Regressionen sichern bestehende Preisregeln ab. Der zusätzliche Check `lint` ist eine Syntaxprüfung mit Python-AST. Die genaue Aufgabenbeschreibung steht in [task.md](task.md).

Diese Checks decken die vorbereiteten Geschäftsregeln ab. Sie beweisen keine beliebigen Zusatzanforderungen eines anderen Prompts und keine allgemeine Fehlerfreiheit. Ein echter Modelllauf muss auf einem anderen Rechner nicht dieselben Aktionen oder dasselbe Ergebnis liefern. Die deterministischen Harness-Tests prüfen den Ablauf unabhängig davon.

Der historische Modelllauf und die aktuelle automatische Abnahme sind getrennte Nachweise. Die Bereinigung verändert keine Rohdateien des Modelllaufs und enthält keine manuelle Korrektur seines Zielcodes. Das selbst geschnittene Video gehört separat zur Abgabe.
