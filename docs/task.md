# Aufgaben und geschützte Prüfungen

Das freigegebene Ziel ist der Pythonteil der Supermarket Receipt Kata am Commit `c72d68abd77a417f84193b72a3b8d14177336066`. Projektkennung und erlaubte Dateien stehen in `config/target.json`. Das Modell darf `shopping_cart.py`, `teller.py`, `receipt.py`, `receipt_printer.py`, `model_objects.py` und `catalog.py` bearbeiten. Tests und Konfiguration bleiben geschützt. Neue Dateien und das Löschen von Dateien sind nicht erlaubt.

## Servicegebühr im Featureprofil

Die Kasse soll eine optionale Servicegebühr unterstützen. Die öffentlichen Aufrufe sind `Teller.checks_out_articles_from(cart, service_fee=0)` und `Receipt(service_fee=0)`. Ohne das neue Argument muss das bisherige Verhalten erhalten bleiben. Die Gebühr wird nach Preisen und Rabatten genau einmal addiert. Die Aufgabe erfordert Änderungen in mindestens zwei zusammenarbeitenden Modulen.

Erlaubt sind endliche Werte vom Typ `int` oder `float`, die mindestens null sind. Negative Werte, NaN, Unendlich, Strings, `None` und `bool` müssen einen `ValueError` mit einer nicht leeren Fehlermeldung auslösen. Mengen, Preise und Rabattregeln dürfen sich nicht ändern.

Auch Ganzzahlen wie `10**30` und `10**400` müssen funktionieren. Eine Umwandlung in `float` darf weder einen Überlauf verursachen noch den Warenbetrag oder dessen Nachkommastellen verlieren. Wenn ein ganzzahliger Gebührenwert bei der Addition zu einem Float Präzision verlieren würde, ist ein exakter rationaler Gesamtbetrag verlangt. Dafür darf `fractions.Fraction` aus der Standardbibliothek verwendet werden. Das bedeutet keine neue Berechnung aller Warenpreise mit Dezimalarithmetik. Erhalten werden soll der bereits berechnete Warenbetrag.

Der vollständige verwendete [Feature-Prompt](feature-prompt.txt) kann direkt in die Oberfläche kopiert werden. Er benennt die Schnittstellen und Geschäftsregeln. Er enthält keinen Patch und keine zu bearbeitenden Dateinamen. Der Hinweis auf `Fraction` wurde als Hilfe vorgegeben und ist in der README offengelegt.

`checks/feature.py` prüft 30 Fälle. Zwei Fälle sichern die bisherigen Aufrufe ab. Vier Fälle prüfen Gebühren an Kasse und Beleg, die Nullgebühr und die Addition nach einem Rabatt. Sechs Fälle prüfen sehr große Ganzzahlen am direkt erzeugten Beleg und beim Kassieren mit oder ohne Rabatt. Weitere 18 Fälle prüfen neun ungültige Werte jeweils an beiden Schnittstellen. Dazu gehören ein negativer kleiner und sehr großer Integer, NaN, beide Unendlichkeiten, ein String, `None` und beide booleschen Werte.

Die vier Checknamen sind `feature`, `regression_core`, `regression_pricing` und `lint`. `regression_core` führt den unveränderten Upstream-Test aus. `regression_pricing` prüft normale Preise, Gewichte, Prozentangebote, „3 für 2“ und einen Paketpreis für fünf Artikel. Solche Regressionstests sichern ab, dass bestehendes Verhalten durch die neue Änderung nicht beschädigt wird. `lint` prüft die Syntax aller Anwendungsdateien mit Python-AST. Es ist kein vollständiger Stil- oder Typchecker. Für das reine Pythonziel ist kein eigener Buildschritt nötig.

Die Feature-Baseline muss fachlich fehlschlagen, weil der Ausgangscommit die neue Schnittstelle noch nicht hat. Die Kontrollen für alte Aufrufe und die anderen drei Checks müssen funktionieren. Infrastrukturfehler gelten nicht als Nachweis des fehlenden Features. Nach `finish` führt der Harness alle vier Checks unabhängig erneut aus. Frühere Fehler bleiben im Bericht erhalten.

## Stückmengen im Bugfixprofil

Die Stage-1-Aufgabe betrifft den gedruckten Kassenbeleg. Stückmengen werden teilweise als Float übergeben. Der Drucker zeigt dann etwa `3.0` an. Stückzahlen sollen ohne Nachkommastellen erscheinen. Gewichte behalten drei Nachkommastellen. Die Berechnung von Preisen und Rabatten soll gleich bleiben.

Ein passender Auftrag lautet: „Fix receipt printing so quantities for EACH products are printed as integers, for example 2 instead of 2.0. Keep KILO quantities at three decimal places and preserve totals and discounts. Inspect the relevant code, run acceptance, regression_core and regression_pricing, and fix failing checks before finishing.“

`checks/acceptance.py` prüft sechs Belege. Ein leerer Warenkorb, ein einzelner Artikel und ein Gewicht von 1,5 Kilogramm dienen als Kontrollen. Bei zwei, drei und fünf Stück müssen die Mengenzeilen ohne `.0` erscheinen. Zusätzlich werden Gesamtbetrag und Gesamtzeile geprüft. Im unveränderten Ausgangscommit schlagen die drei Stückmengenfälle fehl. Das Profil verwendet `acceptance`, `regression_core` und `regression_pricing`.

Das Featureprofil behebt diesen unabhängigen Druckfehler nicht automatisch. Beide Profile starten mit demselben unveränderten Zielcommit und haben jeweils ihren eigenen fachlichen Prüfumfang.

## Andere Aufgaben testen

Ein frei eingegebener Auftrag ersetzt die vorbereiteten Prüfungen nicht. Für eine andere Geschäftsanforderung müssen die Akzeptanztests und die Baseline-Erkennung in `harness/verifier.py` passend angepasst werden. Danach muss ein Baselinelauf den erwarteten fachlichen Fehler bei funktionierenden Kontrollen nachweisen.

Alle Zielmodule werden nur im Docker-Container importiert. Die vorbereiteten Tests liegen außerhalb der für das Modell zugänglichen Arbeitskopie. Ihre Inhalte werden über Hashes geprüft und im Container nur lesbar eingebunden. Ein fester Reparaturpatch existiert ausschließlich als Testfixture in `tests/test_docker.py`. Er ist keine Funktion der Oberfläche oder CLI und wird dem echten Modell nicht mitgegeben.
