**Implementierungsauftrag: eigenes Python-Coding-Harness mit Web-UI für OpenStock**

Du sollst im geöffneten Projekt ein vollständiges, lokal ausführbares Coding-Harness für die Hochschulaufgabe „Stage 1: Build a working coding harness“ implementieren. Liefere funktionierenden Quellcode, überprüfbare Tests und verständliche Dokumentation. Arbeite nach einem kurzen Plan direkt an der Umsetzung und führe die verfügbaren Prüfungen aus.

**1. Auftrag, Quellen und Arbeitsweise**

- Lies zuerst `docs/assignment/stage-1-coding-harness.pdf` vollständig und beachte vorhandene Projektanweisungen. Die PDF ist die maßgebliche Quelle für die Bewertungskriterien. Erfinde keine zusätzlichen Abgabevorgaben.
- Dieser Prompt legt meine Umsetzungspräferenzen fest. Bei einer echten Unvereinbarkeit mit der Aufgabe beschreibe den Konflikt. Fehlt die PDF, arbeite an den unabhängig möglichen Teilen und kennzeichne, dass der Abgleich mit der Originalaufgabe noch offen ist.
- Setze das Harness selbst in Python um. Du bist der Entwicklungsassistent. Der später laufende Harness-Agent verwendet einen eigenen Controller und eigene Repository-Werkzeuge. Verwende kein bestehendes Coding-Harness als Projektbasis und delegiere seine Laufzeitaufgaben nicht an Codex CLI, Claude Code, OpenHands oder eine vergleichbare fertige Anwendung. Normale Bibliotheken und Modell-SDKs sind erlaubt.
- Arbeite im aktuellen Harness-Projekt und erhalte vorhandene Nutzerdateien. Prüfe vor Änderungen den Projektzustand. Triff gewöhnliche Implementierungsentscheidungen selbst und dokumentiere wesentliche Annahmen.
- Respektiere die Berechtigungen deiner Entwicklungsumgebung. Beschaffe keine geheimen Zugangsdaten aus fremden Dateien und umgehe keine Freigaben. Frage nur nach Informationen oder Freigaben, die tatsächlich fehlen. Bei einem externen Hindernis erledige zunächst alle davon unabhängigen Arbeiten.
- Baue eine überschaubare Anwendung für einen lokalen Nutzer und einen gleichzeitig aktiven Agentenlauf. Begrenze den Umfang auf Stage 1. Verwende klare Python-Module, Typannotationen und sinnvolle Fehlerklassen; vermeide unnötige Framework-Schichten.
- Führe keine Remote-Pushes, Merges oder Deployments aus. Das Bereitstellen des Abgabe-Repositories übernimmt der Nutzer separat.
- Halte den Fortschritt knapp fest und aktualisiere `docs/implementation-status.md`, damit eine Fortsetzung in einer späteren Codex-Sitzung möglich ist.

**2. Technische Entscheidungen**

| Bereich | Vorgabe |
|---|---|
| Sprache | Python 3.12 als dokumentierte Zielversion |
| Benutzeroberfläche | Streamlit, lokal im Browser |
| Kernlogik | Von Streamlit unabhängiges Python-Paket |
| Ausführung von OpenStock | Linux-Container über einen lokal erreichbaren Docker-Daemon |
| Reales Modell | Zunächst Ollama über eine austauschbare Modell-Schnittstelle |
| Wiederholbare Tests | Scripted/Fake Model Client mit festgelegten Antworten |
| Tests des Harness | pytest |
| Konfiguration | Validierte Konfigurationsdatei plus Umgebungsvariablen, Beispiel ohne Secrets |
| Lokale Laufartefakte | JSON/JSONL, Textprotokolle und Git-Diff in einem eigenen Verzeichnis pro Lauf |

Die Hauptumgebung ist Windows mit Docker Desktop und Linux-Containern. Die Python-Kernlogik soll auch unter Linux laufen. Dokumentiere PowerShell-Befehle und, soweit abweichend, Linux-Befehle. Vermeide eine Pflicht zur Aktivierung von PowerShell-Skripten: Aufrufe über `.venv\Scripts\python.exe` sind möglich.

Verwende aktuelle, miteinander kompatible Bibliotheksversionen, überprüfe benötigte APIs anhand offizieller Dokumentation und halte die tatsächlich getesteten Versionen in einer reproduzierbaren Dependency-Datei fest. Ein Node-/Frontend-Build ist für diese Streamlit-Lösung nicht erforderlich.

**3. Vorbereitung und Diagnose**

Prüfe zu Beginn Git, Python, Docker-Client, Erreichbarkeit des Docker-Daemons und dessen Containerplattform. Prüfe Ollama nur als separate Voraussetzung für die reale Modelldemonstration. Starte keinen großen Modell-Download ohne vorher festgestellte Eignung und erforderliche Freigabe.

Erstelle einen Diagnosebefehl, beispielsweise `python -m harness doctor`, der verständlich zwischen diesen Zuständen unterscheidet:

- Entwicklungsumgebung und Harness startbereit.
- Docker fehlt, ist nicht gestartet, verweigert Zugriff oder nutzt nicht die erwartete Plattform.
- Ziel-Repository oder fixierter Ausgangs-Commit fehlt.
- Ollama ist nicht erreichbar oder das konfigurierte Modell ist nicht vorhanden.
- Kerntests sind möglich, aber Sandbox- oder Live-Modell-Prüfungen sind blockiert.

Fehlende Infrastruktur darf niemals durch eine ungeschützte Ausführung des Zielcodes auf dem Host ersetzt werden. Die UI darf in einem Diagnosezustand starten. Sie darf einen nicht möglichen echten Lauf aber nicht als erfolgreich darstellen.

**4. Ziel-Repository und feste Ausgangsversion**

Ziel ist ausschließlich `https://github.com/TMBeaver/openstock`.

- Klone das öffentliche Repository in einen vom Harness verwalteten Referenzbereich oder verwende eine ausdrücklich konfigurierte vorhandene Referenzkopie.
- Ermittle den vollständigen tatsächlichen Commit-Hash und speichere URL und Hash in einer versionierten Task-/Target-Konfiguration. Erfinde keinen Hash.
- Verwende anschließend für reproduzierbare Läufe diesen Commit, nicht automatisch den späteren Stand von `main`.
- Jeder Lauf erhält eine frische, wegwerfbare Arbeitskopie. Überschreibe niemals das vom Nutzer gepflegte Originalprojekt. Ermögliche einen Neustart von derselben Ausgangsversion.
- Halte Harness-Quellcode, Akzeptanztests, Konfiguration, Referenzkopie, Laufprotokolle und beschreibbare Agenten-Arbeitskopie klar getrennt.
- Prüfe im tatsächlichen Code, dass das Projekt ausführbar ist, Tests besitzt und die Aufgabe mehrere zusammenarbeitende Module mit Geschäftsregeln betrifft.

Hinweise aus einer vorangegangenen Codeprüfung, die du am fixierten Commit verifizieren musst: OpenStock verwendet Flask und SQLite. `app.py` enthält Routen, `operations.py` Geschäftsoperationen und `db.py` den Datenzugriff. Die vorhandenen Tests sind überwiegend direkt ausführbare Skripte. `python tests/test_core.py` benötigt eine befüllte Datenbank. `seed_demo.py` kann eine leere Testdatenbank mit Beispieldaten befüllen. Die HTTP-Smoke-Tests können einen laufenden Server und Anmeldung benötigen. Übernimm diese Hinweise nicht ungeprüft als Testergebnis.

**5. Baseline und erste Coding-Aufgabe**

Bereite OpenStock und alle Prüfungen in der isolierten Umgebung reproduzierbar vor. Installiere die benötigten Abhängigkeiten vor dem Agentenlauf und verwende ausschließlich synthetische Testdaten. Lege vor der ersten Änderung einen Baseline-Bericht mit Commit, Befehlen, Ausgaben und Exit-Codes an.

Untersuche als bevorzugte erste Aufgabe die Mengenvalidierung von Lagertransfers:

„Lagertransfers müssen Mengen kleiner oder gleich null mit einem verständlichen HTTP-400-Fehler ablehnen. Enthält ein Transfer eine ungültige Position, dürfen keine Bestände verändert und keine Transferdokumente angelegt werden. Gültige positive Transfers müssen weiterhin korrekt funktionieren.“

Bei der bisherigen Codeprüfung schien die Transferlogik ausreichenden Bestand zu prüfen, jedoch keine positive Menge zu erzwingen. Das ist ein Bugfix-Kandidat und noch kein durch einen Lauf nachgewiesener Fehler. Reproduziere das Verhalten selbst.

Erstelle einen eigenständigen Akzeptanztest, der authentifizierte API-Aufrufe, Geschäftslogik und Datenbankwirkung zusammen prüft. Sichere mindestens diese Fälle ab:

| Fall | Erwartung |
|---|---|
| Menge -1 | HTTP 400, verständlicher Fehler, Bestände und Dokumentanzahl unverändert |
| Menge 0 | HTTP 400, keine Buchung |
| Gültige positive Menge | Erfolgreicher Transfer und korrekte Bestände an Quelle und Ziel |
| Erst gültige, dann ungültige Position | Keine teilweise Buchung und kein neues Transferdokument |

Ein Scheitern wegen fehlender Anmeldung, falscher Fixtures oder fehlender Abhängigkeiten zählt nicht als reproduzierter Bug. Der fehlgeschlagene Test muss die tatsächliche Verletzung der Geschäftsregel nachweisen. Eine erfolgreiche Positivkontrolle soll zeigen, dass der Test die vorgesehene Funktion erreicht.

Definiere für diese Aufgabe den erlaubten Änderungsbereich, vorzugsweise die relevanten Teile von `operations.py` und bei Bedarf `app.py`. Der Nachweis muss Verhalten über Modulgrenzen prüfen; ändere nicht künstlich mehrere Dateien, nur um eine Anzahl zu erreichen. Bestehende Geschäftsregeln, Berechtigungen und Datenbankschema bleiben außerhalb dieser Aufgabe.

Falls dieser Kandidat am fixierten Commit bereits korrekt funktioniert, wähle nach begrenzter Untersuchung einen vergleichbar kleinen, reproduzierbaren Bug oder eine kleine fachliche Erweiterung desselben Repositories. Dokumentiere die Entscheidung. Baue keinen künstlichen Fehler in den Ausgangscode ein, um anschließend einen Erfolg vorzutäuschen.

**6. Vertrauenswürdige Prüfungen**

- Speichere den Akzeptanztest im Harness-Projekt außerhalb des für den Laufzeit-Agenten beschreibbaren Bereichs.
- Binde die Prüfdateien in die Sandbox nur lesbar ein. Datei-Tools und ausgeführter Zielcode dürfen sie nicht verändern.
- Halte auch die festgelegten Regressionstests und deren Aufrufkonfiguration außerhalb der Änderungsrechte des Laufzeit-Agenten. Falls ein Test-Adapter notwendig ist, dokumentiere ihn und verwende denselben Adapter vor und nach dem Fix.
- Verwende vor und nach der Änderung dieselben Testdefinitionen und reproduzierbare frische Testdaten. Sichere die Integrität der Prüffiles, beispielsweise mit gespeicherten Hashes.
- Führe den Akzeptanztest auf der Ausgangsversion aus und speichere den fachlich erwarteten Fehlschlag.
- Führe vorhandene Regressionstests auf der Ausgangsversion aus. Sichtbare Baseline-Fehler müssen verstanden und dokumentiert werden; ändere oder entferne Tests nicht, um einen grünen Status zu erzeugen.
- Testcode und importierter OpenStock-Code laufen ausschließlich in der Sandbox. Lade zur Prüfung keine OpenStock-Module direkt in den Host-Prozess des Harness.
- Behandle `passed`, `failed`, `unavailable` und `not_run` als unterschiedliche Check-Ergebnisse. Nicht ausgeführte oder fehlgeschlagene Pflichtprüfungen schließen einen Gesamterfolg aus.

**7. Architektur und Repository-Werkzeuge**

Nutze beispielsweise folgende Aufteilung; gleichwertige klare Strukturen sind erlaubt:

| Bestandteil | Verantwortung |
|---|---|
| UI | Eingaben, Fortschritt, Abbruch und Ergebnisdarstellung |
| Controller | Modellschleife, Werkzeugvalidierung, Budgets und Zustände |
| Model Client | Modellkommunikation mit austauschbarer realer und simulierter Implementierung |
| Workspace Manager | Fixierter Commit, frische Kopien, Lauf-ID und Diff |
| Repository Tools | Begrenzte Dateioperationen |
| Sandbox Runner | Enthaltene Ausführung, Ausgabeerfassung, Exit-Codes, Timeout und Cleanup |
| Verifier | Akzeptanz-/Regressionsprüfungen und objektiver Gesamtstatus |
| Run Store | Nachvollziehbare Metadaten, Ereignisse und Ergebnisdateien |

Implementiere mindestens Werkzeuge zum Auflisten, Lesen, Durchsuchen und Bearbeiten von Dateien sowie zum Aufrufen fest konfigurierter Checks. Die genaue Benennung ist frei.

- Prüfe Werkzeugnamen und Argumente strikt in Anwendungscode. Verwende eine feste Registry erlaubter Werkzeuge und validierte Datentypen. Kein `eval` oder beliebiges dynamisches Ausführen von Modelltext.
- Verwende Repository-relative Pfade. Prüfe den tatsächlich aufgelösten Pfad und die Bereichszugehörigkeit. Weise absolute Pfade, Traversal, Symlink-/Junction-Ausbrüche und Zugriffe auf andere Laufverzeichnisse zurück. Ein String-Präfixvergleich reicht nicht.
- Berücksichtige Windows- und Linux-Pfadbesonderheiten. Halte `.git`, Harness-Dateien, Prüfdateien, Konfiguration und Secrets außerhalb der schreibbaren Tool-Bereiche.
- Begrenze gelesene Dateigrößen und Suchergebnisse. Behandle Binärdateien verständlich.
- Änderungen müssen deterministisch und überprüfbar sein. Bei Textersetzungen müssen erwarteter alter Inhalt und Eindeutigkeit geprüft werden. Bei Konflikten keine unsichere Teiländerung durchführen.
- Ein Check-Werkzeug nimmt eine erlaubte Check-ID entgegen. Die Zuordnung zu einem festen Programm und einer Argumentliste liegt in vertrauenswürdiger Konfiguration. Der Agent erhält keine beliebige Host-Shell.

**8. Sandbox und Abbruchverhalten**

Baue die Container-Ausführung als tatsächliche Grenze gegen Zugriffe des Zielcodes auf die Umgebung. Ein temporäres Verzeichnis, ein Git-Worktree oder eine Python-venv erfüllt das allein nicht.

- Der vertrauenswürdige Controller und der Model Client laufen außerhalb des Zielcode-Containers.
- Der Container sieht nur die erforderlichen Repository-Dateien, vertrauenswürdige Prüffiles und temporäre Laufdaten. Binde weder das gesamte Harness-Projekt noch Benutzerverzeichnisse, SSH-Dateien, reale Credentials oder den Docker-Socket ein.
- Lasse den Zielcode ohne privilegierten Modus und nach Möglichkeit unter einer eigenen Nicht-root-UID laufen. Setze passende Prozess-, Speicher- und CPU-Limits, entferne unnötige Capabilities und verhindere Privilegienerhöhung.
- Installiere Abhängigkeiten im vorbereitenden Image-/Setup-Schritt. Während eines normalen Prüf- oder Agentenlaufs ist externer Netzwerkzugriff des Zielcodes deaktiviert. API-Tests können Server und Client innerhalb desselben isolierten Containers verwenden.
- Gestalte Quell- und Testmounts für die Befehlsausführung möglichst nur lesbar. OpenStock benötigt beschreibbare temporäre Bereiche für Datenbank, Dokumente, Backups, Logs und gegebenenfalls Cache-Dateien. Beschränke diese auf laufbezogene Datenverzeichnisse. Dateiänderungen des Agenten erfolgen kontrolliert über die Repository-Tools.
- Verhindere gleichzeitige Dateiänderungen durch Tools und noch laufende Sandbox-Prozesse. Nach einem beendeten Check dürfen keine weiterlaufenden Kindprozesse zurückbleiben.
- Implementiere ein tatsächliches Laufzeitlimit pro Befehl und einen Abbruchknopf. Stoppe bei Abbruch oder Timeout den betreffenden Container einschließlich Kindprozessen, erzwinge das Beenden nötigenfalls nach kurzer Frist und prüfe das Ende. Nur den lokalen Docker-CLI-Prozess zu beenden genügt nicht.
- Stoppe nach Abbruch auch weitere Tool-Aufrufe und ausstehende Modellfortsetzungen. Entferne ausschließlich die vom jeweiligen Lauf erzeugten Container und temporären Ressourcen. Erhalte den Ergebnisbericht.
- Eine fehlende oder defekte Sandbox führt zu einem sichtbaren blockierten Zustand. Es gibt keinen automatischen Host-Ausführungsfallback.

**9. Controller, Limits und Modellkommunikation**

Implementiere die Schleife aus Aufgabe und Kontext, Modellantwort, validierter Werkzeuganfrage, erlaubter Ausführung und Rückgabe des Ergebnisses oder Fehlers an das Modell.

- Gib dem Modell Aufgabe, erlaubten Änderungsbereich, Werkzeugbeschreibungen, relevanten Dateikontext und bisherige Werkzeugergebnisse. Lade nicht pauschal alle Dateien oder Datenbanken in den Prompt.
- Behandle Repository-Texte und Modellantworten als nicht vertrauenswürdige Eingaben. Anweisungen in Repository-Dateien dürfen keine Tool-Berechtigungen, Sandbox-Einstellungen, Limits oder geschützten Pfade ändern.
- Unterstütze die vom gewählten Modell tatsächlich angebotenen strukturierten Werkzeugaufrufe. Bewahre die benötigten Assistant-/Tool-Nachrichten und Zuordnungen korrekt. Parallele Aufrufe dürfen für diesen POC seriell verarbeitet werden.
- Unbekannte Werkzeuge, beschädigtes JSON, unpassende Typen und unerlaubte Argumente liefern strukturierte Fehler ohne Nebenwirkungen. Fehler gehen, sofern das Budget noch reicht, als Beobachtung an das Modell zurück.
- Ein eindeutiger Abschlusswunsch des Modells löst die vertrauenswürdige Endprüfung aus. Eine freie Behauptung des Modells wie „alle Tests bestanden“ ist kein Prüfergebnis.
- Plane konfigurierbare Startwerte, beispielsweise 40 Werkzeugversuche, 50 Modellrunden, höchstens 2 Wiederholungen pro fehlgeschlagener Modellanfrage, 120 Sekunden pro Check und 64 KiB pro Werkzeugausgabe. Dokumentiere die konkreten Werte und ihre Bedeutung.
- Zähle auch abgelehnte Werkzeugversuche und Wiederholungen. Eine Antwort mit mehreren Werkzeugaufrufen verbraucht pro Aufruf Budget. Verhindere Endlosschleifen auch bei Antworten ohne verwertbaren Tool-Aufruf.
- Begrenze stdout und stderr bereits während des Einlesens, auch ohne Zeilenumbrüche. Markiere Kürzungen sichtbar. Begrenze außerdem gespeicherte Gesamtausgaben und den an das Modell zurückgegebenen Kontext.
- Erhalte Exit-Code, Timeout, Abbruchgrund und Check-Status unabhängig vom gekürzten Ausgabetext.
- Nach Erreichen eines Limits gibt es keine weiteren vom Modell ausgelösten Aktionen. Kennzeichne den Abbruch als solchen und erhalte vorhandene Ergebnisse und den Diff. Die kontrollierte Endprüfung nach normaler Fertigmeldung muss klar von Modellaktionen getrennt sein.

Implementiere zuerst einen `ScriptedModelClient`, danach einen echten `OllamaModelClient`. Der erste dient deterministischen Tests und einer ausdrücklich als simuliert markierten Demonstration.

Ollama-Adresse und Modellname sind konfigurierbar, beispielsweise über `HARNESS_OLLAMA_BASE_URL` und `HARNESS_MODEL`. Der Modellname darf nicht als bereits installiert angenommen werden. Prüfe Erreichbarkeit und Eignung für Werkzeugaufrufe. Lade keine Modelle automatisch beim Öffnen der UI herunter. Eine zusätzliche kostenpflichtige API-Anbindung ist für diese erste Version nicht erforderlich; die Schnittstelle soll sie später erlauben.

**10. UI und Ablauf für den Nutzer**

Baue eine übersichtliche deutsche Streamlit-Oberfläche. Der normale Ablauf soll ohne manuelle Dateibearbeitung möglich sein, sobald die dokumentierte Einrichtung erledigt ist.

- Zeige das ausgewählte Ziel-Repository, den fixierten Commit sowie Provider und Modell.
- Biete ein Aufgabenfeld mit der vorbereiteten OpenStock-Aufgabe als Beispiel und zeige den erlaubten Änderungsbereich.
- Biete „Lauf starten“ und „Abbrechen“. Ein erneut ausgeführtes Streamlit-Skript darf keinen doppelten Lauf starten.
- Zeige den aktuellen Zustand, verbrauchtes Aktionsbudget und eine chronologische Liste von Werkzeugaufrufen und Ergebnissen.
- Zeige getrennte Ansichten für Verlauf, geänderte Dateien/Diff und Checks. Markiere gekürzte Ausgaben, Fehler, übersprungene Checks und Abbrüche verständlich.
- Zeige Akzeptanztest vor der Änderung, Akzeptanztest nach der Änderung und vorhandene Regressionstests nachvollziehbar.
- Biete den Diff und einen Laufbericht zum Herunterladen an. Der Diff muss auch neue und gelöschte Dateien berücksichtigen, soweit die Task-Konfiguration solche Änderungen erlaubt.
- Ermögliche einen neuen Lauf vom unveränderten Ausgangs-Commit.
- Führe die lang laufende Controller-Arbeit außerhalb des blockierenden UI-Ablaufs aus, etwa als Worker mit Ereignis-Queue. Verwende Streamlit-UI-Aufrufe nur im dafür vorgesehenen UI-Kontext. Der Abbruchknopf muss während der Arbeit bedienbar bleiben.
- Zeige einen erfolgreichen Gesamtstatus nur, wenn alle vorgesehenen Pflichtprüfungen tatsächlich erfolgreich waren. Simulierte Läufe sind sichtbar von echten Modellläufen unterschieden.

**11. Automatisierte Prüfungen des Harness**

Erstelle aussagekräftige Kerntests ohne Live-Modell, Konto oder API-Key. Diese sollen mit einem simulierten Model Client und kontrollierten Runner-Doubles auch ohne laufenden Docker-Daemon ausführbar sein. Ergänze echte, separat aufrufbare Docker-Integrationstests für die Ausführungsgrenze.

| Prüfung | Erwarteter Nachweis |
|---|---|
| Datei-Tools | Auflisten, Lesen, Suchen und Bearbeiten funktionieren im erlaubten Bereich |
| Pfadgrenze | Traversal, absolute Pfade und Symlink-Ausbrüche werden ohne Änderung außerhalb des Bereichs abgelehnt |
| Controller | Vorgeschriebener Modellaufruf löst das richtige Werkzeug aus; sein Ergebnis wird zurückgegeben |
| Ungültige Anfrage | Unbekannte Werkzeuge und ungültige Argumente erzeugen klare Fehler ohne Aktion |
| Fehlgeschlagener Befehl | Nonzero-Exit-Code und Ausgabe bleiben sichtbar; kein falscher Erfolg |
| Aktions-/Rundenlimit | Wiederholte und abgelehnte Anfragen erreichen die Grenze; danach keine weiteren Aktionen |
| Ausgabelimit | Große und zeilenlose Ausgaben werden schon beim Erfassen begrenzt und als gekürzt markiert |
| Modellfehler | Verbindungsfehler, Timeout und fehlerhafte Antworten führen zu begrenzten Wiederholungen und verständlichem Ende |
| Abbruch/Timeout | Ein Testprozess mit Kindprozess beendet sich vollständig; danach finden keine weiteren Schreibvorgänge statt |
| Testschutz | Akzeptanztest und geschützte Testkonfiguration bleiben unverändert |
| Ergebnisstatus | Nicht ausgeführte oder fehlgeschlagene Pflichtprüfungen verhindern Gesamterfolg |
| UI | Start, Statusanzeige, Ergebnisdarstellung und die Verbindung zur Abbruchfunktion werden sinnvoll geprüft |
| Bugfix | Akzeptanztest scheitert fachlich vor dem Fix, besteht nachher; Regressionstests bestehen |

Prüfe die UI zusätzlich in einem verfügbaren Browser oder mit geeigneten Streamlit-Testwerkzeugen. Behaupte keine visuelle Prüfung, falls du sie nicht durchführen konntest.

Docker-Tests dürfen im normalen Offline-Kerntestlauf ausdrücklich ausgelassen werden. Ein gesondert angeforderter Sandbox-/Abnahmelauf muss fehlendes Docker jedoch als unvollständige Verifikation erkennen. „Übersprungen“ darf weder im Bericht noch in der UI mit „bestanden“ gleichgesetzt werden.

**12. Reale Demonstration und Nachweis**

Nach Fertigstellung führe bei vorhandenem Modellzugang mindestens einen vollständigen echten Modelllauf über das selbst implementierte Harness aus. Beginne dabei mit dem ursprünglichen fixierten Commit und dem vorab festgelegten Akzeptanztest.

Der demonstrierte Patch muss in diesem Lauf durch die eigenen Modell-/Tool-Schritte des Harness entstehen. Spiele keinen vorbereiteten Patch heimlich ein. Entwicklerseitige Änderungen an OpenStock sind kein Ersatz für diesen Nachweis. Wiederholungen und manuelle Hilfestellungen sind erlaubt, müssen aber offengelegt werden.

Speichere mindestens:

- Lauf-ID, Datum, Provider, Modellname und tatsächlichen Ausgangs-Commit.
- Aufgabe, erlaubte Änderungen und relevante Limit-Einstellungen.
- Baseline- und Endergebnisse einschließlich Befehlen, Ausgaben, Exit-Codes und Check-Status.
- Liste geänderter Dateien und vollständigen Diff, soweit innerhalb dokumentierter Artefaktgrenzen; Kürzungen müssen sichtbar sein.
- Gezählte Aktionen, Ablehnungen, Wiederholungen sowie Abschluss- oder Abbruchgrund.
- Manuelle Hilfestellungen und bekannte Einschränkungen.

Wenn Docker oder ein geeignetes Modell fehlt, implementiere und prüfe alle trotzdem möglichen Teile. Liefere genaue Nachholbefehle und markiere den echten Nachweis als offen. Erfinde keine grünen Prüfergebnisse, keinen erfolgreichen Agentenlauf und keine Leistungswerte.

**13. Dokumentation und Abgabevorbereitung**

Liefere mindestens:

- Vollständigen Harness-Quellcode und eine schlanke `.gitignore`.
- Reproduzierbare Abhängigkeiten und Beispielkonfiguration ohne echte Zugangsdaten.
- Dockerfile beziehungsweise kontrolliertes Image-Setup, Sandbox-Runner und Dokumentation der konkreten Isolationsgrenzen.
- Einen dokumentierten Befehl für Einrichtung, Diagnose, Start der UI, Kerntests, Sandbox-Prüfungen und Live-Demonstration. Gleichwertige klar benannte Skripte sind zulässig.
- Kurze README mit Voraussetzungen, exakten Startbefehlen für Windows und Linux sowie dem normalen Nutzerablauf.
- `docs/architecture.md` mit einem kompakten Komponenten- und einem Ablaufdiagramm in Mermaid, die die tatsächlich implementierte Architektur zeigen.
- `docs/task.md` mit Ziel-URL, vollständigem Ausgangs-Commit, fachlicher Aufgabe, erlaubten Änderungen und Akzeptanzkriterien.
- `docs/requirements-matrix.md`, die jede Pflichtanforderung der PDF auf Implementierung, Test und tatsächlichen Nachweis abbildet. Ungeprüfte Punkte bleiben erkennbar offen.
- `docs/implementation-status.md` mit erledigten Schritten, konkreten Blockern und den nächsten ausführbaren Aktionen.
- `docs/demo-script.md` mit einem Ablauf für ein maximal vierminütiges Abgabevideo: kurzer Projektüberblick, Aufgabe, Agentenlauf beziehungsweise transparent gekürzte Wartezeit, Diff, Akzeptanz-/Regressionstests und Grenzen/manuelle Hilfe. Plane etwa 3:40 Minuten Inhalt als Reserve. Falls eine echte Videoaufnahme in dieser Umgebung nicht möglich ist, liefere das Drehbuch und kennzeichne die Aufnahme als Nutzeraufgabe.
- Einen nachvollziehbaren Verifikationsbericht mit tatsächlich ausgeführten Befehlen und Ergebnissen. Große Laufartefakte und temporäre Arbeitskopien gehören nicht unkontrolliert in Git; eine kleine redigierte Beispieldemonstration darf gezielt versioniert werden.

**14. Umsetzungsreihenfolge**

1. PDF und Projektzustand lesen, Umgebung prüfen und kurzen Plan festhalten.
2. Harness-Struktur und Konfiguration anlegen; OpenStock beziehen und Commit fixieren.
3. Sandbox und reproduzierbare Testdaten einrichten; bestehende Tests als Baseline ausführen.
4. Fachlichen Bug reproduzieren, geschützten Akzeptanztest und Task-Scope festlegen.
5. Repository-Tools, Validierung und Grenzen mit den geforderten Kerntests umsetzen.
6. Controller mit simuliertem Modell, Budgets und strukturierten Ergebnissen implementieren.
7. Streamlit-UI einschließlich funktionsfähigem Abbruch anbinden.
8. Echte Ollama-Anbindung und unabhängige Endprüfung ergänzen.
9. Docker-Integration und vollständigen Lauf prüfen; Live-Demonstration durchführen, soweit die Voraussetzungen vorhanden sind.
10. README, Diagramme, Anforderungsmatrix, Demo-Drehbuch und Abschlussbericht fertigstellen.

Stoppe nicht nach einem Plan oder einem UI-Mockup. Arbeite die Umsetzung bis zu einem lauffähigen und überprüften Ergebnis durch. Bei Kontextunterbrechungen halte den Stand so fest, dass du denselben Auftrag fortsetzen kannst.

**15. Abschlusskriterien und Abschlussantwort**

Die Implementierung ist als vollständig verifiziert zu bezeichnen, wenn eine frische Einrichtung nach README funktioniert, die geforderten Harness-Tests bestehen, die Sandbox- und Abbruchprüfungen nachgewiesen sind und ein echter Modelllauf den zuvor fehlschlagenden Akzeptanztest bei weiterhin bestehenden Regressionstests erfolgreich macht. Der Abgabeumfang umfasst zusätzlich Repository-Bereitstellung und Video; unterscheide diese Nutzeraufgaben vom Implementierungsstand.

Nenne am Ende knapp:

1. Welche Komponenten implementiert wurden.
2. Den genauen Befehl zum Starten der UI.
3. Den fixierten OpenStock-Commit und die gewählte Coding-Aufgabe.
4. Welche Prüfungen tatsächlich bestanden, scheiterten oder nicht ausgeführt wurden.
5. Wo Diff, Laufbericht, Dokumentation und Demo-Drehbuch liegen.
6. Welche konkreten manuellen Schritte oder externen Voraussetzungen noch fehlen.

Beginne jetzt mit der Prüfung der vorhandenen Dateien und der Entwicklungsumgebung. Erstelle anschließend den kurzen Plan und setze ihn um.
