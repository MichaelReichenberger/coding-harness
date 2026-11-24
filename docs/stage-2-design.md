# Aufbau und Ablauf

Die Oberfläche in `app.py` und die CLI in `harness/__main__.py` verwenden beide `RunService`. Dieser startet einen Worker und stellt Start, Öffnen, Abbruch und Fortsetzen bereit. Die fachliche Ablaufsteuerung liegt im Controller. Dadurch führt die Oberfläche keine eigenen Dateiwerkzeuge oder Prüfungen aus.

Die README zeigt die Aufrufe für [Architektur](../README.md#architektur), [Navigation](../README.md#navigation) sowie [Kontext und Sitzungen](../README.md#kontext-und-sitzungen).

Bei einem neuen Lauf erstellt der Worker die Arbeitskopie des festgelegten Zielcommits. Der Controller prüft zuerst die Baseline. Danach fragt er das Modell nach jeweils einer strukturierten Werkzeugaktion. Das Werkzeugergebnis wird als Beobachtung zum Gespräch hinzugefügt. Nach einem Fehler kann das Modell seine Änderung korrigieren. Aktionen, Runden, Wiederholungen und Laufzeiten sind begrenzt. Nach `finish` entscheidet eine unabhängige Endprüfung über den Erfolg.

## Navigation

`Navigation` in `harness/navigation.py` untersucht Pythondateien mit `ast.parse`. Sie liest Klassen, Funktionen und Imports samt Zeilennummern, ohne Zielcode auszuführen. Die Übersicht untersucht bis zu 80 Module. Suchbegriffe aus dem Auftrag bewerten Dateinamen und Symbole. Bis zu vier passende Dateien werden ausgewählt und um direkte lokale Abhängigkeiten ergänzt. Die Auswahl enthält höchstens sechs Dateien. Das begrenzt die Auswahl für den Kontext, nicht die Anzahl der im Repository vorhandenen Dateien.

Die Navigation verwendet dieselben Pfad- und Größenprüfungen wie die Dateiwerkzeuge. Syntaxfehler werden als Ergebnis zurückgegeben. Das Modell kann mit `inspect_repository` eine neue Übersicht anfordern und mit den Dateiwerkzeugen weiter suchen. Die Startkarte des Featureprofils ist auf 4.096 Bytes begrenzt. Sie ist nicht dauerhaft angeheftet und kann später aus dem Kontext fallen.

Der Git-Zustand wird mit `git diff --no-index` zwischen der Ausgangskopie `base` und der Arbeitskopie `repo` ermittelt. Der Bericht nennt zusätzlich den festgelegten Ausgangscommit. In den Arbeitskopien liegen keine Git-Zugangsdaten.

## Kontextverwaltung

`ContextManager` in `harness/context.py` wird vom Controller vor Modellanfragen und beim Speichern aufgerufen. Im Featureprofil zählt das Budget den vollständigen serialisierten Modellrequest mit Werkzeugdefinitionen und JSON-Escaping. Es gilt höchstens 32.768 Bytes und bei ausdrücklich eingestelltem CPU-Betrieb höchstens 16.384 Bytes. Ein kleinerer konfigurierter Wert hat Vorrang. Das Bugfixprofil behält das bisherige Verhalten und stoppt bei seinem Kontextlimit.

Die ersten beiden Nachrichten enthalten Systemregeln und Originalauftrag mit Rechten und Akzeptanzkriterien. Sie bleiben erhalten. Repositorykarte, Quelltext und Werkzeugausgaben sind als nicht vertrauenswürdige Daten gekennzeichnet. Sie dürfen keine Regeln überschreiben.

Wenn der Request zu groß ist, erstellt der ContextManager eine kurze Beschreibung der letzten acht Schritte mit höchstens 1.024 Bytes. Dann entfernt er ältere Beobachtungen aus dem Modellkontext. Die letzte Beobachtung bleibt möglichst erhalten und wird nötigenfalls ebenfalls gekürzt. Auch die Kurzfassung bleibt ausdrücklich nicht vertrauenswürdig. Es wird kein zweites Modell zur Zusammenfassung aufgerufen. Passen Auftrag und Regeln nicht in das Budget, wird der Lauf gestoppt.

Der gekürzte Gesprächsstand wird im Checkpoint gespeichert und nach einer sicheren Fortsetzung wieder geladen. Das Ereignisprotokoll ist davon getrennt. Dort bleiben die bisherigen Aktionen innerhalb des Artefaktbudgets nachvollziehbar. Jede tatsächliche Kürzung erzeugt `context_shortened` mit Größe vorher und nachher, Limit und Auslöser. Die Oberfläche zeigt dafür „Kontext gekürzt“.

## Sitzungsspeicher und Checkpoints

`SessionStore` in `harness/sessions.py` schreibt zuerst `session.tmp`, sichert den Inhalt mit `flush` und `fsync` und ersetzt dann atomar `session.json`. Der Checkpoint enthält Auftrag, Projekt, Profil, Ausgangscommit, erlaubte Änderungen, Checks, Modellsettings, Limits, Zähler, Schritte, Gespräch und Dateihashes.

Vor einer Modellanfrage, einem Werkzeugaufruf oder einer Prüfung wird die laufende Aktion als `pending` gespeichert. Erst wenn ihr Ergebnis bekannt ist und erforderliche Prozesse sicher beendet wurden, wird dieser Eintrag entfernt. Bei einer Unterbrechung mitten in einer Aktion bleibt damit sichtbar, dass ihr Ausgang unsicher ist. Der Harness wiederholt sie nicht automatisch.

Ein sauberer Abbruch beendet laufende Anfragen und Container und speichert einen fortsetzbaren Zustand. Beim Fortsetzen werden die aktuelle Konfiguration, Rechte, Werkzeugdefinitionen, Akzeptanzkriterien, Testhashes, Ausgangskopie und Arbeitskopie mit dem Checkpoint verglichen. Eigene Änderungen des Modells gehören zum erwarteten Dateizustand und bleiben erhalten. Das Sandbox-Image wird ebenfalls geprüft. Die verbrauchten Zähler werden übernommen.

Bei Abweichungen oder einem unklaren `pending` pausiert der Lauf. Es gibt keinen Schalter zum ungeprüften Wiederholen einer unsicheren Aktion. Frühere Endchecks werden nach einer Fortsetzung als `previous_final` geführt. Aktuell noch nicht ausgeführte Endchecks bleiben `not_run`. Abgeschlossene Sitzungen können zur Prüfung geöffnet werden, ohne ihren Status zu verändern.

Die Sitzungsdateien sind für einen einzelnen vertrauenswürdigen lokalen Benutzer gedacht. Sie sind nicht signiert. Ein Benutzer mit Schreibzugriff auf den gesamten Projektordner kann sie verändern. Diese Grenze wird durch die Hashprüfung nicht aufgehoben.

## Werkzeuge und Ausführung

`RepositoryTools` in `harness/repository.py` enthält die Werkzeugregistrierung und prüft Argumente und Pfade. Nur die sechs Dateien aus `config/target.json` dürfen verändert werden. Das Modell kann keine Dateien anlegen oder löschen. Es erhält keine Shell und keine Werkzeuge für Netzwerkzugriffe, Push, Merge oder Deployment.

`Verifier` wählt die festgelegten Checks aus. `DockerRunner` führt sie in einem kurzlebigen Linux-Container aus. Der Container läuft ohne Rootrechte, ohne Netzwerk, mit schreibgeschütztem Dateisystem und festen Grenzen für CPU, Arbeitsspeicher, Prozesse, Zeit und Ausgabe. Geschützte Tests werden nur lesbar eingebunden. Symlinks, Junctions und unzulässige Pfade werden abgewiesen. Ein lokaler RunLock verhindert parallele Schreibläufe.

Ein Abbruch muss auch die Kindprozesse beenden. Ist das Containerende nicht bestätigt, darf der Controller keine weiteren Aktionen starten. Fehlende Infrastruktur wird als Fehler angezeigt. Es gibt keinen Ersatzlauf des Zielcodes auf dem Host. Docker begrenzt die Ausführung, ist aber keine virtuelle Maschine und kein allgemeiner Sicherheitsbeweis für absichtlich bösartigen Code.

## Ergebnisse und Tests

`RunStore` in `harness/store.py` schreibt Ereignisse, Bericht und Diff. Der Bericht hält geänderte Dateien, Prüfausgaben und offene Arbeit fest. Fehlgeschlagene, nicht verfügbare und noch nicht ausgeführte Prüfungen bleiben sichtbar. Die Modellbehauptung, fertig zu sein, reicht nicht für Erfolg.

`tests/test_stage2.py` prüft Navigation, Kontextkürzung, Wiederöffnen, erhaltene Änderungen und Zähler sowie sichere Ablehnung bei Abweichungen. `tests/test_controller.py` prüft die Modellschleife und ihre Grenzen. Die weiteren Tests prüfen Dateiwerkzeuge, Pfadschutz, Prozesse, Konfiguration und Oberfläche. `tests/test_docker.py` führt gesondert freigegebene echte Containerprüfungen aus. Dabei gibt es einen festen Bugfix und eine Feature-Reparatur nach einem fehlgeschlagenen Check. Diese Antworten sind ausdrücklich Testdaten. Der echte Modelllauf wird mit eigenen Rohdateien getrennt belegt.

Die Laufzeitabhängigkeiten sind Streamlit für die Oberfläche, httpx für den Modellzugang und Pydantic für Konfiguration und Werkzeugargumente. Navigation, Kontextkürzung und Sitzungsspeicher verwenden die Python-Standardbibliothek. Es wird kein Agentenframework verwendet.
