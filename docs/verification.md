# Abschließende Verifikation

Stand: 07.10.2026. Prüfung nach Bereinigung und Zusammenführung der Dokumentation.
Windows, Python 3.13.2, Streamlit 1.65.0, Ollama 0.40.0,
`qwen2.5-coder:7b`, Docker Desktop 4.39.0 mit Linux-Engine.

| Prüfung | Ergebnis |
|---|---|
| Lockdatei-Pakete, `pip check` | keine Paketkonflikte |
| `harness setup --build` | fixierter Zielcommit und Sandbox-Image vorhanden |
| `harness doctor` | `core_tests_ready`, `sandbox_ready`, `live_ready` true |
| Offline-Tests | 59 bestanden, 5 Docker-Fälle explizit übersprungen; 4.8 s einschließlich Prozessstart |
| Echte Docker-Tests | 5 bestanden, 59 abgewählt; 27.6 s einschließlich Prozessstart |
| Gesamtsuite nach abschließender Bereinigung | **64 bestanden**, inklusive aller echten Docker-Tests; 32,91 s |
| Mermaid-Diagramme | beide mit Mermaid 11.17.2 erfolgreich geparst; Semikolon im Sequenztext korrigiert |
| Ruff | bestanden |
| `harness baseline` | fachlich rote Akzeptanz, grüne Regressionen; Exit-Code 0 |
| Streamlit | Health `ok`, Webseite HTTP 200 auf Testport 8502; UI-Tests in Offline-Suite enthalten |
| Echter 7B-Lauf | `passed`, 30.0 s, 6 Aktionen/Anfragen, 0 Retrys, 0 Ablehnungen |

Der Docker-Test prüft Mount-/Netzisolation, geschützte Dateien, begrenzte Ausgabe mit
Nonzero-Exit sowie Timeout/Abbruch mit Kindprozessen. Der Scripted-Rot-Grün-Test ist
eine Testfixture und wird nicht als echter Modellnachweis ausgegeben.
Python 3.13 meldet die vorhandene `PurePath.is_reserved`-Deprecation; alle Tests bestehen.

## Echter Modellnachweis

Lauf `20261007T171054Z-a4859127`: `simulated=false`,
`baseline_bug_reproduced=true`, nur `receipt_printer.py` geändert.
Alle drei Checks beim Agenten und in der unabhängigen Endprüfung bestanden;
alle neun Container-Checks bestätigten Cleanup. Keine Harness-Container verblieben.

- [Unveränderter Laufbericht](evidence/report.json): Prompt, Limits, Ausgangscommit,
  Checkhashes, Image-ID, Zähler und tatsächliche Ergebnisse.
- [Modelldiff](evidence/changes.diff): ausschließlich EACH-Mengenanzeige.
- [Unveränderte Ereignisse](evidence/events.jsonl): Modellantworten und Werkzeugaufrufe.
- [Prüfprotokoll](evidence/checks.json): Befehle, Exit-Codes, Laufzeiten und Ausgaben.

**Manuelle Hilfe:** vorhandene kleine Aufgabe, erlaubter Scope und geschützte Tests
wurden vorab festgelegt. Der Nutzerprompt wurde nach einem früheren gescheiterten
Versuch präzisiert und nennt die zu lesende Druckdatei. Der vollständige Prompt steht
in der [README](../README.md#beispielprompt) und im Feld `task` des Berichts.
Kein fertiger Patch und kein Quellcodeausschnitt wurde dem Modell gegeben.
Die Referenz und die geschützten Checks bleiben unverändert.

## Bereinigung und Aussagegrenzen

Historische Versuche, redundante Status-/Architekturdokumente, doppelte PDF-Kopie,
alter Implementierungsauftrag, Installations-Testkopie, alte Logs und Testcaches
wurden entfernt. Klassen, Ablauf und Diagramme stehen zentral in der README.
Die kanonische Spezifikation, Code, Tests, Konfiguration und Upstream-Lizenznachweise
bleiben erhalten. Nur die aktuelle Nachweissammlung ist Teil der Abgabe.
Der vorherige Dokumentationsstand wurde vor der Löschung außerhalb des Projekts gesichert.

Die frische Clone-/Einrichtungsprüfung vom selben Tag lief auf demselben Rechner;
Python/Git/Docker/Ollama waren bereits installiert, Downloadcache war erlaubt.
Andere Hardware und Linux als Host wurden nicht geprüft. Echte Modellerfolge bleiben
auch bei identischem Prompt und Temperatur 0 nicht garantiert.

Veröffentlichen des aktuellen Quellstands und Demo-Video bis vier Minuten bleiben
für die vollständige Abgabe erforderlich. [PDF-Abgleich](requirements-matrix.md).
