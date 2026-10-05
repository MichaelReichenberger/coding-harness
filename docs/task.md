# Fixierte OpenStock-Aufgabe

- Quelle: https://github.com/TMBeaver/openstock
- Tatsächlich geklonter Commit: `abc87dccab96c78917b35add542284e61adc5f37`
- Versionierte Konfiguration: `config/target.json`
- Erlaubte Änderungen: bestehende `operations.py`, bei Bedarf `app.py`.
- Außerhalb des Scopes: Berechtigungen, Datenbankschema, andere Geschäftsregeln, Tests und Konfiguration.

## Fachliche Anforderung

Lagertransfers müssen Mengen ≤ 0 mit verständlichem HTTP 400 ablehnen. Eine ungültige
Position macht den gesamten Transfer ungültig: keine Bestandsänderung, kein Dokument,
keine Dokumentzeile. Positive Transfers funktionieren weiterhin.

| Fall | Erwartung |
|---|---|
| Menge −1 | HTTP 400, Mengenfehler; alle Bestände/Dokumente/Zeilen unverändert |
| Menge 0 | HTTP 400, Mengenfehler; keine Buchung |
| Menge +2 | HTTP 200, Bestand 4000→3998 und 500→502, ein Dokument/eine Zeile |
| Erst +2, dann −1 | HTTP 400; vollständiger Rollback |
| Erst +2, dann 0 | HTTP 400; vollständiger Rollback |

Die Prüfung durchläuft echten Login (`/api/operator/login`), Sessionheader und
`/api/transfer` über Flask `test_client`, dann `Operations.transfer` und echte SQLite-Tabellen.
`app.py` prüft Berechtigungen und übersetzt `OperationError` in HTTP 400.
`operations.py` führt die Transaktion aus; `db.py` verwaltet Verbindung, Schema und Daten.
Das sind mehrere zusammenarbeitende Module mit realen Bestands- und Transaktionsregeln.

Am Ausgangs-Commit gibt es nur die Bestandsobergrenze in `_transfer`, keine positive
Mengenprüfung. Die Docker-Baseline bestätigt für alle vier ungültigen Fälle HTTP 200
und ein neues Transferdokument. Bei −1 steigt der Quellbestand sogar auf 4001.
Die positive Kontrolle besteht. Dies ist kein Authentifizierungs- oder Fixturefehler.
Ein Ersatzkandidat war deshalb nicht nötig.

## Reproduzierbare Daten und geschützte Regression

Jeder Check läuft in einem neuen Container mit frischem tmpfs. Das unveränderte
`seed_demo.py` erzeugt 14 synthetische Produkte, sechs Firmen und einen Testbenutzer.
Der öffentliche Testwert `synthetic-test-only` ist ausschließlich ein Wegwerfpasswort.
Vor jedem Akzeptanzfall stellt eine SQLite-Backupkopie denselben Ausgangsdatenbestand her.
Session-IDs werden nicht protokolliert. Es werden keine echten Geschäftsdaten gelesen.

Die festen Regressionen sind `tests/test_core.py` (**23 Einzelprüfungen**) und
`tests/test_reversal_advances.py` (**22 Einzelprüfungen**) aus dem fixierten Repository.
Ihre Kopien in `checks/upstream/` sind dem Agenten nicht zugänglich. Herkunft und SHA-256
stehen in `provenance.json`; die Upstream-Lizenz liegt daneben.

Diese Skripte berechnen Quell-/Datenpfade aus `__file__`. Der dokumentierte Adapter
`checks/entry.py` kompiliert die unveränderten Skriptbytes mit deren ursprünglichem
`/repo/tests/...`-Dateinamen und setzt `__file__` entsprechend. So importieren sie die
Agenten-Arbeitskopie und verwenden `/repo/data`, während ihre Assertions aus dem
geschützten Mount stammen. Vorher wird die leere Datenbank mit dem Upstream-Seed gefüllt.
Derselbe Adapter und dieselben Testdateien werden vor und nach Änderungen verwendet.

Zusätzliche Upstream-HTTP-Smokes sind nicht als Pflichtregression ausgewählt: sie erwarten
einen eigenständigen laufenden Server und teils alte Authentifizierungs-/Datenannahmen.
Sie werden weder geändert noch als bestanden dargestellt. Der neue Akzeptanztest deckt
den authentifizierten HTTP-Transferpfad ab. `python tests/test_core.py` ohne Seed wäre
kein aussagekräftiger Baseline-Lauf.

## Integrität und Bewertung

Der Runner speichert Prüffile-Hashes und prüft sie vor/nach jedem Check; die festen
Checkbefehle erhalten einen eigenen Hash im Bericht. Akzeptanz- und Regressionstests
werden niemals direkt in den Host-Prozess importiert. Ein Lauf gilt nur mit fachlich
reproduzierter Baseline und sämtlichen tatsächlich bestandenen Endprüfungen als erfolgreich.
Ein erfolgreicher Simulationslauf bleibt ausdrücklich als simuliert gekennzeichnet.
