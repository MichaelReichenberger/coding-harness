# Stage-2-Feature und geschützte Akzeptanz

Ziel: https://github.com/emilybache/SupermarketReceipt-Refactoring-Kata
Startcommit: `c72d68abd77a417f84193b72a3b8d14177336066`, Teilprojekt `python/`.
Projekt-ID: `supermarket`. Profil: `feature` (das bestehende Profil `bugfix` bleibt erhalten).

## Geschäftsanforderung

Eine Kasse darf optional eine nicht negative Servicegebühr berechnen. Alte Aufrufe
bleiben unverändert. Die Gebühr wird nach Waren- und Rabattberechnung genau einmal
auf den Gesamtbetrag aufgeschlagen. Auch ein direkt erzeugter Beleg unterstützt sie.

Öffentliche Schnittstellen: `Teller.checks_out_articles_from(cart, service_fee=0)` und
`Receipt(service_fee=0)`. Erlaubte Werte sind endliche int/float-Werte ab null.
Negative Werte, NaN, Unendlich, Strings, None und bool führen zu ValueError mit
nicht leerer Fehlermeldung. Keine neue Abhängigkeit, keine Änderung vorhandener
Mengen oder Preisregeln. Die Umsetzung muss mindestens zwei interagierende Module ändern.

Die sechs Anwendungsdateien aus `config/target.json` sind editierbar. Das Modell
muss relevante Module selbst über Navigation/Dateiwerkzeuge finden und ändern;
es erhält keinen Quellcodeausschnitt, Patch oder ausführbaren Lösungsplan.

## Tatsächlicher Feature-Prompt

```text
Add an optional service_fee to supermarket checkout and receipts. Public APIs must support Teller.checks_out_articles_from(cart, service_fee=0) and Receipt(service_fee=0). Existing calls without the argument must keep working. Add the fee exactly once after existing item prices and discounts. Accept finite int/float values greater than or equal to zero; reject negative values, NaN, infinity, strings, None and bool with a clear ValueError. Preserve existing quantities, prices and discounts. Find the relevant modules yourself with the repository tools, implement the feature across the interacting modules, run feature, regression_core, regression_pricing and lint, and fix any failed checks before finishing.
```

Der Text wird nicht automatisch in der UI eingesetzt. Er benennt das gewünschte
öffentliche API, aber keine Quelldateien oder Codekorrekturen. Er wird unverändert
mit dem jeweiligen Auftrag, Commit, Scope und den Checks im Checkpoint gespeichert.

## Vorbereitete Checks

- `feature`: `python -I /trusted/entry.py feature`. Geschützte Prüfungen für alte
  Aufrufe, Gebühren über Kasse/Beleg, Nullgebühr, Gebühr mit Prozentangebot und
  alle ungültigen Eingaben an beiden Schnittstellen.
- `regression_core`: unveränderter Upstream-unittest.
- `regression_pricing`: vorhandene fünf Normal-/Gewichts-/Rabattregeln.
- `lint`: Standardbibliothek-Syntaxlint aller Python-Anwendungsdateien (AST), kein
  vollständiger Stil-/Typchecker. Für dieses reine Pythonprojekt ist kein Build nötig.

Die Baseline muss bei fehlendem Gebühren-API fachlich scheitern. Ihre Legacy-Kontrollen,
Regressionen und Syntaxprüfung müssen funktionieren. Die Featuretests liegen außerhalb
der Laufkopie, sind read-only im Container und werden über Hashes geschützt.
Nach finish werden alle vier Checks unabhängig erneut ausgeführt. Historische Fehler
und fehlende Endchecks bleiben sichtbar; die Featureprüfung behauptet keine globale
Fehlerfreiheit. Insbesondere wird der bekannte Stage-1-Stückmengenfehler durch dieses
Feature nicht behoben. Für ihn bleiben Bugfix-Profil und seine bisherigen Tests erhalten.

## Reproduzieren

```powershell
$env:HARNESS_MODEL = 'qwen2.5-coder:7b'
.\.venv\Scripts\python.exe -m harness baseline --project supermarket --profile feature
.\.venv\Scripts\python.exe -m harness run --project supermarket --profile feature --task 'Eigenen Featureauftrag hier eingeben'
.\.venv\Scripts\python.exe -m harness sessions
.\.venv\Scripts\python.exe -m harness inspect SITZUNGS_ID
.\.venv\Scripts\python.exe -m harness cancel SITZUNGS_ID
.\.venv\Scripts\python.exe -m harness resume SITZUNGS_ID
```

Ein echter erfolgreicher Modelllauf ist zusätzlich zum deterministischen Test nötig.
Der feste Patch existiert ausschließlich in `tests/test_docker.py` als ausdrücklich
simulierte Rot-Grün-/Fehlerbehebungstestfixture. Er ist nicht aus UI/CLI ausführbar
und wird dem echten Modell weder als Prompt noch Kontext übergeben.
