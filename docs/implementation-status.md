# Implementierungsstand · Stage 2

Stand: 03.11.2026, Version 0.2.0. Die Stage-2-PDF ist Source of Truth; alle vier Seiten
wurden vollständig gelesen und visuell einschließlich Diagrammen geprüft.

## Quellstand und Sicherung

Der GitHub-Hauptbranch heißt master; ein main-Branch existiert dort nicht.
Fetch und pull --ff-only erfolgten auf master, Ausgangscommit:
`08aad834732bbddf397c5c446f8844722bc7f147`. Der Arbeitsbaum war bis auf die neue
Stage-2-PDF sauber. Die PDF wurde vor dem Pull gesichert, danach wieder eingefügt:
SHA256 `2aa3d4062e51f031386ae349eada55bf9590529e7285ef41faa8443117b999f9`.
Keine Nutzeränderungen zurückgesetzt, kein Push/Commit ohne Auftrag.

## Implementiert und automatisiert geprüft

- Erlaubtes Projekt supermarket und getrennte Profile bugfix/feature in CLI und UI.
- AST-Navigation für Module/Symbole/Imports, relevante Dateiauswahl und Git-Archivdiff.
- Featurekontext auf höchstens 32 KiB, bei CPU-Override 16 KiB begrenzt, einschließlich
  vollständiger JSON-Payload/Tooldefinitionen. Deterministische Kompression erhält
  trusted Auftrag, Scope und Kriterien; Quellen/Tooltexte bleiben untrusted.
- Aufgabe, Startcommit, Policy, Checks, Schritte, begrenzte Historie, Fehler/Resultate,
  eigene Dateihashes und alle Zähler in atomaren Sitzungscheckpoint gespeichert.
- Öffnen nach Neustart, externer Abbruch während HTTP, sicherer Resume ohne Reset.
  Rechte/Settings/Testhashes und base/repo einschließlich eigener Edits werden neu
  geprüft. Unsicheres pending, Links/Hardlinks, neue Dateien, Abweichungen oder
  verbrauchte Limits pausieren; keine unsichere Aktion wird automatisch wiederholt.
- Vorherige Endchecks nach Resume sind previous_final. Fehlende aktuelle Endchecks
  bleiben not_run. Eine rote Endprüfung wird beim Fortsetzen als Beobachtung übergeben.
- Servicegebühr als geschütztes Feature über Teller/Receipt, Legacy-Aufrufe/Fehlerfälle;
  zusätzliche Syntaxlintprüfung. Alter Bugfix und alle Stage-1-Grenzen bleiben erhalten.
- Kommentare, README, Diagramme, Task, Anforderungsmatrix und vollständiger
  Dateiänderungsnachweis unter docs/stage-2-changes.md.

## Ausgeführte Abnahme

| Prüfung | Tatsächliches Ergebnis |
|---|---|
| Gesamtsuite auf finalem Code: pytest -q --docker | **86 bestanden**, 158,94 s |
| Ruff-Check | bestanden |
| Ruff-Formatprüfung | **30 Dateien korrekt formatiert** |
| pip check | keine Paketkonflikte |
| Geschützte Feature-Baseline 20261103T152449Z-5472de68 | erwartete fehlende Gebühren-API, Legacy-Kontrollen grün, Regressionen/Lint grün |
| Deterministischer Docker-Featuretest | failed → failed → passed, danach alle vier Endchecks grün; ausdrücklich Scripted |
| Docker-Grenzen und Stage-1-Bugfix | alle bisherigen fünf echten Docker-Fälle weiter bestanden |
| Session-/Kontext-/Resume-Grenzen | Restart, eigene Edits, erhaltene Limits, Cancel, unsicherer Abbruch, Hash-/Policy-/Hardlink-/Budgetabweichungen bestanden |
| PDF-Hash und Dateiänderungsnachweis | PDF bytegleich; keine geänderte Quelldatei ohne Zuordnung |

Die ersten eingeschränkten Windows-Testprozesse hingen bereits beim asyncio-
Socketpair-Aufbau, noch vor Mock-HTTP. Sie wurden nach Identifikation gezielt beendet.
Die komplette Offline-/Docker-Abnahme erfolgte deshalb in der freigegebenen Umgebung;
Mocktests benötigen weiterhin weder Livekonto noch API-Key oder externe Modellantworten.

## Tatsächliche Umgebung und echter Modelllauf

Python 3.12.14, Streamlit 1.65.0, Ollama 0.40.7. Sandbox-Image:
`sha256:896dc65c1db5517c524ad115de04441e5e472589271f30b597926b186e4d192e`.
Zielcommit `c72d68abd77a417f84193b72a3b8d14177336066`.
Modell qwen2.5-coder:7b, Q4_K_M, Digest
`dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`.

GPU-Versuch `20261103T152754Z-36b4686b`: model_error nach drei Anfragen,
zwei gezählten Retrys, keine Modelltools/Edits. Serverlog: CUDA error „device kernel
image is invalid“ beim Warmup, Runner exit 0xc0000409. RTX 3070 Laptop GPU,
8.192 MiB VRAM, Treiber 560.70. Dies ist ein Modellserver-/CUDAfehler vor dem Coding.
Weder Treiber noch Ollama wurden vom Implementierungsassistenten aktualisiert.

Separater CPU-Versuch `20261103T153055Z-1ebf09b6`: gleicher dokumentierter Auftrag,
gleiches 7B-Modell, explizit HARNESS_NUM_GPU=0; API bestätigt size_vram=0.
Mehrere saubere Abbruch-/Open-/Resume-Versuche demonstrierten echte Checkpoints mit
eigenen Edits. Der erste Abbruch stand bei 5 Aktionen/5 Requests und pending=null;
die erste Fortsetzung lief mit diesen Zählern weiter. Eine falsche Erfolgsmeldung
nach bloßen API-Signaturen wurde durch die unabhängige Endprüfung als failed erkannt.
Weitere Fortsetzungen bekamen gespeicherte Fehlchecks, ohne einen Patch vorzugeben.
Bei einem 180-s-CPU-Timeout wurde das Kontextlimit strenger auf 16 KiB reduziert,
keine Zähler oder Aktions-/Zeitgrenzen wurden erhöht. Generische Korrekturen der
Kontext-/Checkpoint-Beobachtung und historischer Checkstatus wurden separat getestet
und per sicherer Fortsetzung übernommen. Keine manuelle Reparatur der Zielmodule.

Endgültiger CPU-Laufstatus: **limit_reached**, 40 Aktionen, 42 Runden, 43 Requests,
1 Transportretry, 9 abgelehnte Aktionen, pending=null. Gesamtdauer einschließlich
Abbruch-/Resume-Demonstrationen: 2.307,05 s (38 min 27 s). Geändert wurden receipt.py
und teller.py; die Gebührenberechnung/Validierung ist nicht erfolgreich umgesetzt.
Vier saubere Abbrüche wurden protokolliert, ohne Zählerreset oder verlorene eigene Edits.
Die aktuellen Endchecks sind alle not_run; ältere Endchecks sind previous_final.
18 Checkaufrufe sind protokolliert, alle mit bestätigtem Cleanup. Die gespeicherten
Arbeitskopie-Hashes stimmen mit den tatsächlichen Dateien überein. Kein Harness-
Container blieb zurück; ein fremder vorhandener Container wurde nicht angefasst.
**Ein erfolgreicher echter Feature-Nachweis wird ausdrücklich NICHT behauptet.**

## Abgabe und verbleibende Schritte

Das versionierte ZIP mit Source-Hashmanifest liegt unter
`.harness/releases/coding-harness-stage2-20261103.zip`;
die aktuelle Implementierung wird nicht ungefragt gepusht. Stage-1-Nachweise unter
docs/evidence bleiben erhalten; Stage-2-Nachweise werden getrennt abgelegt.

Noch offen: echter erfolgreicher Featurelauf, Videoaufnahme bis vier Minuten und
Moodle-Abgabe durch den Nutzer. Für den GPU-Lauf zuerst die kompatible NVIDIA-/
Ollama-CUDA-Kombination herstellen und eine kurze Modellanfrage prüfen. Alternativ
auf dem bereits funktionierenden Stand-PC mit demselben versionierten Quellstand
und geschützten Tests ausführen. CPU-Betrieb ist über HARNESS_NUM_GPU=0 möglich,
kann aber das Zeitlimit erreichen; ein schnellerer Rechner garantiert keinen Fix.

Für Starts/Resume einer CPU-Sitzung dieselbe CPU-Einstellung verwenden. Nach Ende
am Aktionslimit ist diese Sitzung nur noch zur Prüfung zu öffnen; ein neuer Versuch
braucht einen neuen Lauf. Die Limits werden niemals zurückgesetzt.

## GPU-Nachversuch mit installiertem Qwen3.8 (03.11.2026)

Auf Nutzerwunsch Lauf `20261103T162026Z-618e22ee` mit `qwen3.8:27b`,
HARNESS_NUM_GPU=8 und unverändertem Feature-Prompt gestartet. Ollama bestätigte
8/66 Schichten auf CUDA0 (2653,94 MiB Modellpuffer); der restliche Modellpuffer
lag im Hostspeicher. Beim Warmup scheiterte der Runner erneut mit
`CUDA error: device kernel image is invalid` in ggml_cuda_kernel_can_use_pdl.
Es gab keine erfolgreiche Modellantwort und keine Änderungen der Zieldateien.
Nach erstem Fehler und Beginn des automatischen Retrys kontrolliert abgebrochen:
state=cancelled, requests=2, retries=1. Baseline: Feature erwartungsgemäß rot,
Regressionen und Syntaxlint grün. Kein Harness-Container blieb zurück;
`ollama ps` zeigte nach Abschluss kein geladenes Modell.

Dieser Versuch belegt einen Fehler im GPU-Runner vor der Coding-Aufgabe, keine
fehlende Problemlösefähigkeit dieses Modells. GPU-Betrieb bleibt bis zur Reparatur
der lokalen CUDA/Ollama-Umgebung blockiert. Kein Treiber-/Serverupdate vorgenommen.
Nachweis: `.harness/runs/20261103T162026Z-618e22ee/`.
Das bisherige Release-ZIP bleibt der unveränderte Snapshot vor diesem Nachtrag.

Zweck dieser Datei: tatsächlichen Implementierungs- und Nachweisstand festhalten.
Änderungsgrund dieses Nachtrags: angeforderten GPU-Versuch reproduzierbar dokumentieren,
auch bei Infrastrukturfehler; Anforderungen S2-V (Fehler sichtbar) und S2-D (Umgebung/Nachweis).

## Lokale GPU-Reparatur (03.11.2026, nach dem Nachversuch)

Auf ausdrücklichen Nutzerwunsch Razer Central einschließlich zugehöriger Browser-
Unterprozesse und den Photos-Reserveprozess beendet; Razer-Synapse-Fenster regulär
geschlossen. Unmittelbar rund 250 MiB zusätzlich frei. Docker/WSL, offene Arbeits-
anwendungen, Sicherheitsdienste und Modelle nicht entfernt. Mit gesicherter
Stromversorgung und 100-W-GPU-Limit trat derselbe CUDA-Warmupfehler erneut auf.

Offiziellen NVIDIA-Notebook-Studio-Treiber 617.42 heruntergeladen, gültige NVIDIA-
Signatur und Unterstützung der Hardwarekennung DEV_249D/SUBSYS_20141A58 geprüft.
SHA256: d929d8b4587cc49717357b7ef3f60582304568c198f90f8263e1177a8c963b2f.
Installation über `setup.exe -s -n Display.Driver`: Grafiktreiber 617.42 aktiv,
Windows-Gerätestatus 0. Der Installer meldete jedoch bei AfterInstall einen
Registry-Zugriffsfehler (0x80070005); daher keine vollständig fehlerfreie
Treiberinstallation behaupten. Kein automatischer Windows-Neustart durchgeführt.

Treiberupdate allein behob den CUDA-Fehler nicht. Ollamas CUDA-13-Verzeichnis war
unvollständig (nur zwei DLLs und eine temporäre Installerdatei); Ollama wählte
weiter CUDA 12. Offizielles Ollama 0.40.14 mit geprüfter Release-SHA256 und gültiger
Ollama-Signatur installiert. SHA256 des Installers:
e069c7cc7d4808f77684e81efa0b1f853a5190b4b8f070bc8fd63041180e3eba.
Ollama-Installer Exit 0, kein Neustart nötig; Modelle erhalten. CUDA-13-Bibliotheken
vollständig vorhanden und laut Serverlog tatsächlich geladen.

Echte Modellanfrage: qwen3.8:27b, num_gpu=24, num_ctx=2048, num_predict=16,
think=false, temperature=0, Prompt `Reply with OK only.`. Antwort `OK`, done=true,
HTTP-Erfolg; 172,71 s gesamt, 98,26 s Laden, 60,41 s Promptauswertung,
13,95 s für zwei Ausgabetokens. Ollama bestätigt 62%/38% CPU/GPU; 24/66 Schichten
auf GPU. Damit ist GPU-Inferenz für dieses Modell nachgewiesen, noch kein
erfolgreicher Featurelauf. Ein großer Teil des 27B-Modells liegt weiterhin im
knappen Hostspeicher; die Rechenzeit bleibt ein separates Problem.

Nachweise und Installationslogs lokal unter `.harness/gpu-repair/`.
Der anschließende Harness-Nachversuch ist `20261103T165509Z-bf277162` mit gleicher
Featureaufgabe, unveränderten Limits und automatischer GPU-Verteilung.
Zweck/Grund dieses Nachtrags: Umgebung, Reparaturschritte, tatsächlich gemessene
Ergebnisse und verbleibende Einschränkungen nachvollziehbar halten (S2-V/D).
Das ältere Release-ZIP enthält diesen späteren Dokumentationsnachtrag nicht.

Ergebnis des Harness-Nachversuchs: Baseline Feature erwartungsgemäß rot,
regression_core/regression_pricing/lint grün. Automatische Verteilung 15/66
Schichten auf GPU bei 16384 Kontexttokens; 3046 Prompttokens. Modellstart und
Promptverarbeitung ohne bisherigen CUDA-Absturz, aber keine Werkzeugantwort
innerhalb von 180 s. Ereignisse: Anfrage 16:55:25 UTC, Fehler 16:58:26 UTC.
Den beginnenden automatischen Retry kontrolliert abgebrochen: cancelled,
requests=2, retries=1, keine Zieldateiänderungen. Kein erfolgreicher Feature-
Nachweis. Das Modell danach über `ollama stop qwen3.8:27b` entladen.
RAM-Freigabe allein behebt weder unvollständige CUDA-Bibliotheken noch den hohen
Speicher-/Rechenbedarf dieses 27B-Modells. Für weitere POC-Läufe auf diesem Laptop
ein kleineres bereits installiertes Modell explizit auswählen oder den 27B-Lauf
auf Hardware mit ausreichend RAM/VRAM durchführen; die Limits bleiben bestehen.
