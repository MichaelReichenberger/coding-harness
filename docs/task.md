# Zielrepository und geschützte Akzeptanz

- URL: https://github.com/emilybache/SupermarketReceipt-Refactoring-Kata
- Ausgangs-Commit: `c72d68abd77a417f84193b72a3b8d14177336066`.
- Teilprojekt: `python/`, direkt aus dem Commit; kein künstlich eingefügter Bug.
- Änderbare Dateien: die sechs Anwendungsdateien in `config/target.json`.
- Tests und Konfiguration sind geschützt. Keine Dateien anlegen oder löschen.

## Kleine Aufgabe: Stückzahlen auf dem Kassenbeleg

Die Kasse (`Teller`) verarbeitet einen `ShoppingCart` und erzeugt einen `Receipt`.
`ReceiptPrinter` druckt diesen Beleg. Stückzahlen werden im Warenkorb auch als Float
übergeben. Der vorhandene Drucker zeigt deshalb beispielsweise `3.0` an. Fachlich
sollen Stückzahlen ohne Nachkommastellen erscheinen; Gewichte behalten drei Stellen.
Die Rechnung und Rabattregeln sollen unverändert bleiben.

Der echte Modellversuch verwendet folgenden Prompt ohne Reparaturhinweis:

> There is a bug in receipt printing: quantities for EACH products have decimal
> places, but must be displayed as whole numbers. KILO quantities must keep three
> decimal places. Change only the printing behavior, not the stored data or pricing.
> First use read_file to inspect the printing code. Then fix the formatting and run
> acceptance, regression_core and regression_pricing before finishing.

Das ist eine Verhaltensanforderung, keine Codekorrektur. Die UI beginnt weiterhin
leer. Der Harness setzt keinen Prompt und keinen Quellcodeausschnitt automatisch ein.
Das Modell muss Dateien selbst untersuchen; der tatsächlich gesendete Prompt steht im Bericht.

## Vorab festgelegte geschützte Akzeptanz

`checks/acceptance.py` prüft den kompletten Kassiervorgang und den gedruckten Beleg:

| Fall | Einheit | Menge | Erwartete Mengenzeile |
|---|---|---:|---|
| leer | EACH | 0.0 | keine |
| einzelner Artikel | EACH | 1.0 | keine zusätzliche Zeile |
| Gewicht | KILO | 1.5 | `1.25 * 1.500` |
| zwei Artikel | EACH | 2.0 | `1.25 * 2` |
| drei Artikel | EACH | 3.0 | `1.25 * 3` |
| fünf Artikel | EACH | 5.0 | `1.25 * 5` |

Der Einzelpreis beträgt jeweils 1,25. Die ersten drei Fälle sind Positivkontrollen.
Im Ausgangscommit scheitern ausschließlich die drei Stückmengenfälle. Der Test prüft
zusätzlich den unveränderten Gesamtpreis und eine vorhandene Gesamtzeile.
`baseline_bug_reproduced` dokumentiert diesen fachlichen Fehler, statt einen
Infrastrukturfehler als rote Baseline zu zählen. Es steuert keine Modellaktionen.

`regression_core` führt den unveränderten Upstream-unittest aus; Originalbytes,
Herkunft und Lizenz stehen in `checks/upstream/`. `regression_pricing` schützt
Normal-/Gewichtspreise, Prozentangebote, „3 für 2“ und „5 zum Paketpreis“.
Baseline und Endprüfung verwenden dieselben Checks und geschützten Dateihashes.

## Abgrenzung zur vorherigen Aufgabe

Seit dem 07.10.2026 ist der Belegdruck die ausgewählte kleine POC-Aufgabe. Die frühere
Akzeptanz der ungeraden Zweierpaketpreise wurde dafür ausdrücklich ersetzt. Der
bekannte Paarpreisfehler ist weiterhin im Ausgangscommit vorhanden und wurde nicht
repariert. Ein grüner Belegdruck-Lauf behauptet keine Fehlerfreiheit des ganzen Repos.
Historische Laufberichte und Diffs dokumentieren die vorherigen Prüfungen unverändert.

## Eigene Aufgaben des Professors

Eigene Prompts werden direkt im leeren Aufgabenfeld eingegeben. Für eine andere
fachliche Anforderung muss der Prüfer zuvor `checks/acceptance.py` anpassen und mit
`python -m harness baseline` den Fehler und funktionierende Kontrollen nachweisen.
Auch die erwarteten Fallnamen in `baseline_reproduces()` (`harness/verifier.py`)
müssen dann zur Aufgabe passen. Zielmodule werden ausschließlich in Docker importiert.
Die neue Aufgabe läuft mit demselben Harness, denselben Werkzeugen und Limits.
Geschützte Tests bleiben vom Modell unveränderbar. Grüne bestehende Tests allein
beweisen keine beliebige andere Anforderung.
