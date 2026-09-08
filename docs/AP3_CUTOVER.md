# AP3 Cutover- und Rollback-Runbook

**Stand:** v0.6.3. **Status:** Testing / Not Live.
Benni meldet v0.6.2 installiert im Shadow, Position 100 %, idle. Nach technischer
v0.6.3-Lieferung ist das nächste reale Gate sein kontrollierter Writer-Cutover.
Keine automatisch vorgeschaltete weitere theoretische Shadow-Runde.
Dieses Dokument führt nichts aus; Installation, Neustarts, reale Tests, Live und
Live Verified bleiben ausschließlich Bennis Gates.

## Aktueller Writer-Cutover über normale HA-Optionen

Dieser Ablauf benötigt keinen Entity-Rename. Der frühere kombinierte
Rename-/Consumer-Plan unten bleibt für ein separat vorbereitetes Rename-Fenster
erhalten. Ohne Rename bleiben aktuelle Cover-Bindings unverändert. Direkte
Legacy-Serviceconsumer bleiben bei deaktivierter Legacy unwirksam; sie dürfen
keine zweite Writer-Freigabe erzeugen. Bio-/Sleep-Entscheidungen konsumiert BC
bereits aus den kanonischen Ownern.

1. Benni sichert den Ausgang und installiert v0.6.3 über HACS. In
   **Einstellungen → Geräte & Dienste → Blind Control → Konfigurieren**
   `runtime_mode=shadow`, `apply_owner=legacy`, **Apply AUS** speichern.
   Options-Reload abwarten; Übersicht bestätigt genau diese geladenen Werte,
   `write_path_reachable=false`, Position/Motion und konkrete Blocker.
2. Fremde Coverbefehle während des Fensters ausschließen. Alle Legacy-Entries
   dauerhaft über HA deaktivieren, Integration installiert lassen. Erforderlichen
   HA-Prozessneustart durchführen; Disable allein beseitigt alte Tasks nicht.
3. Null-Writer bestätigen: Legacy disabled/unloaded, alte Services nicht mehr
   verfügbar, BC Shadow/Apply AUS, Cover in Ruhe. Bei Rest-Writer, Bewegung oder
   unklarer Evidence abbrechen; nicht durch Owner-Umschalten weitergehen.
4. In denselben nativen Optionen **live + blind_control, Apply weiterhin AUS**
   speichern. Neue Runtime abwarten: Owner/Modus korrekt, Apply AUS, kein Write,
   gültige Position/Motion, bestätigte Ruhebaseline, Readiness und Opening.
   `low_light` ist gültig; unknown/stale/conflict oder unklare Safety blockieren.
5. Benni kontrolliert aktuelles Ziel, Achse und Fenster. Erst dann **Apply AN**
   in denselben Optionen speichern. Reload/Baseline abwarten und reale Fahrt
   beobachten. Apply ist Dauerautomatik, keine Einzelbefehl-Queue. Nur aktuelle
   Entscheidungen fahren; Safety kann sofort aufwärts eingreifen.
6. Reale Zielposition innerhalb Toleranz und stabile Ruhe bestätigen; Opening
   OPEN darf niemals logisch abwärts wirken. Eigenfahrt darf keinen Override
   auslösen. Fehler, unerwartete Richtung oder fehlende Evidence: Apply AUS,
   nötigenfalls BC deaktivieren. Erst Benni entscheidet Live/Live Verified.

**Rückweg ohne Rename:** zuerst BC Apply AUS und deaktivieren, erfolgreichen
Unload/Null-Writer und sichere Ruhe bestätigen. Legacy bleibt bis dahin disabled.
Danach Legacy mit ursprünglicher Konfiguration laden, zunächst Apply AUS;
Benni gibt erst nach Positions-/Opening-Prüfung wieder frei. Ohne Rename gibt
es keine Rückmigration von Entity-IDs. Ein Options-Reload startet eine neue
Baseline; eine bereits laufende physische Fahrt endet nicht durch Unload.
Kein HA-Schritt wird vom Implementierungsagenten ausgeführt.

## Separat vorbereiteter kombinierter Rename-/Consumer-Plan

Die folgenden zusätzlichen Preconditions gelten nur, wenn Benni auch den
Rename beauftragt. Sie sind keine neue allgemeine Shadow-Runde für den obigen
Writer-Cutover. Bei Rename bleiben Backups, konkrete Consumeränderungen und
deren inverser Rückweg zwingend.

## 1. Lokales Änderungspaket und Consumer-Inventar

OLD_ID wird unmittelbar vorher aus der tatsächlichen Entity Registry gelesen.
NEW_ID = cover.living_thermal_blind. Dieselbe Registry-Entity und unveränderte
Unique-ID müssen erhalten bleiben. OLD_ID, Unique-ID, ConfigEntries und Backups
bleiben installationslokal; öffentliche Evidence enthält nur redigierte Ergebnisse.

Read-only am 07.09.2026: das physische Cover ist vorhanden, NEW_ID fehlt sowohl
in der vollständigen Cover-Suche als auch im Registry-Einzelabruf. Das ist keine
dauerhafte Reservierung. Vor Rename erneut prüfen, einschließlich deaktivierter
Entities; bei Kollision abbrechen, niemals eine bestehende Entity überschreiben.

| Consumer / Fundstelle | Vorher → nachher | Anwendung / Prüfung | Rollback |
| --- | --- | --- | --- |
| Blind Control ConfigEntry **und** Options | alle Cover-Position-/Availability-Bindings OLD_ID → NEW_ID; sonstige Owner unverändert | native Optionen speichern; Reload abwarten; tatsächliche Runtime prüfen | gesicherten vollständigen Stand über native Optionen wiederherstellen, Apply aus |
| Legacy Policy ConfigEntry/Options und installierter Default | OLD_ID bleibt als rollbackfähiger Altstand gesichert | vollständig deaktiviert lassen; nicht an NEW_ID binden und parallel laden | erst nach Rückrename und Null-Writer mit ursprünglicher Referenz laden, zunächst Apply aus |
| Einhornzentrale custom/homekit.yaml | beide Vorkommen in Include-Filter und Entity-Konfiguration OLD_ID → NEW_ID | YAML prüfen; dokumentierter HA-Neustart lädt Bridge neu; Exposition und Identität prüfen | beide Originalstellen wiederherstellen, beim Rückweg neu starten |
| Einhornzentrale benni_core_devices/import.yaml | drei Cover-Referenzen in Zustands-/Positions-Sources und abgeleiteter Ausgabe OLD_ID → NEW_ID | Datei allein reicht **nicht**: Core-Devices-Import-Dry-Run, Diff kontrollieren, dann bestehender Import-Apply; persistierte Master-Konfiguration prüfen; Reload/Restart | exakten Master-/ConfigEntry-Export und Originaldatei wiederherstellen; Dry-Run/Import erneut prüfen |
| System Readiness packages/system/templates/readiness.yaml | indirekter Master-Verbrauch bleibt | Rollo-/Opening-/Availability-/Positionsattribute und Gesamtergebnis prüfen; keinen Readiness-Helper manuell auf wahr setzen | alte Master-Bindings wiederherstellen, Readiness erneut berechnen |
| Bedtime packages/system/manual_bio_scripts.yaml und zugehöriger Sleep-Contract-Test | Legacy-Apply-Serviceaufruf entfernen; kanonische Bio-State-Übergänge beibehalten | keinen neuen Blind-Control-Apply-Service erfinden: Runtime konsumiert Bio bereits; Änderung vorbereiten, Skripte beim Neustart laden; keine Testfahrt | Originalskript und Originaltest wiederherstellen, erst mit Legacy reaktivieren |
| Core Contracts source_binding_evidence.py | historische Evidence enthält OLD_ID | historische Evidence **nicht** als Runtime-Binding migrieren; aktive Registry/Profile gesondert exportieren und nach OLD_ID suchen | nur tatsächlich geänderte aktive Einträge aus Snapshot zurücksetzen; historische Evidence unverändert |
| Automationen / Skripte / Szenen | alle direkten und dynamischen Cover-/Legacy-Serviceverwendungen prüfen | read-only HA-Referenzgraph plus YAML und Templates; aktivierbare Apply-Consumer vorab stilllegen | gesicherte Konfiguration und Aktivierungszustände gezielt wiederherstellen |
| Helper / Dashboards / Voice / externe Apps | persistierte Strings, Include-Filter und Karten prüfen | vollständige Exporte inkl. nicht angezeigter Dashboards/disabled Entities; keine automatische Stringmigration annehmen | exakte Exporte wiederherstellen |
| Weitere aktive Levtos-Repositories | am 07.09.2026 alle nicht archivierten Repos untersucht | aktuelle Defaults erneut nach OLD_ID, NEW_ID, Legacy-Services und dynamischen Cover-Zielen suchen; vorbereitete Diffs versionieren, separat deployen | je Repo gesicherter Commit / exakter Rückdiff |
| Recorder / History / Statistik | Entity-ID-Zuordnung kann betroffen sein | vollständiges HA-Backup einschließlich Recorder; History vor/nach Rename lesen; abgeleitete Statistik-/Utility-Meter-IDs getrennt inventarisieren | Backup bleibt verfügbar; keine SQL-Umschreibung, Löschung oder erfundene Historienkontinuität |

Die Live-Suche ergab keine zusätzlichen direkten UI-Consumer, war aber wegen
acht YAML-Automationen und sieben YAML-Skripten **partial**. Diese wurden im
GitHub-YAML abgeglichen. Dynamische Templates und beliebige Storage-Inhalte
sind dadurch nicht vollständig bewiesen. Deshalb ist der lokale Exportabgleich
ein Eintrittsgate, kein behaupteter bereits erledigter Cutover-Schritt.
Keine direkten .storage-Dateiedits bei laufendem HA.

„Atomar“ bedeutet: alle Consumer ändern sich innerhalb eines gesperrten
Null-Writer-Fensters. HA bietet keine gemeinsame Transaktion für Registry,
YAML, ConfigEntries und externe Apps. Bis sämtliche Postconditions erfüllt
sind, wird kein Writer freigegeben.

## 2. Preconditions

- Technische Release-/Test-Evidence geprüft, keine ungeklärten technischen Blocker.
- Aktuelle Version separat durch Benni installiert; bestätigtes shadow + legacy,
  Apply **aus**, keine automatische Übernahme historischer Apply-Freigaben.
- Frische Opening-/Positions-/Motion-/Readiness-Evidence. Cover steht
  nachweislich in Ruhe; relevante Fenster sind für den Beginn geschlossen.
- Opening-Owner-Pfad samt beiden Fensterseiten und Handover geprüft.
  Source-Audit und vier synthetische Owner-Auswertungen bestanden;
  das ist noch kein realer Kontakt-/Fahrttest.
- Lokales Vorher-/Nachher-/Rollback-Paket für jede Tabellenzeile vorbereitet,
  vollständiges HA-/Recorder-Backup verfügbar und Wiederherstellung bekannt.
- Vollständige Suche einschließlich dynamischer Consumer abgeschlossen.
  Während des Fensters keine HomeKit-, Dashboard-, Hand- oder Fremdautomation-
  Befehle; deren Aktivierungszustände sind gesichert.
- Benni bestätigt das Fenster, Neustarts und später gesondert die erste Fahrt.

## 3. Sequenz mit Abbruch und Rückweg

Jeder Schritt setzt den erfolgreichen vorherigen voraus. Bei fehlender
Postcondition sofort abbrechen; kein „weiter und später reparieren“.

| Schritt | Aktion und Precondition | Postcondition | Abbruch / Rückweg |
| --- | --- | --- | --- |
| 1 Ausgang erfassen | Preconditions erfüllt; Zeit, Version, Registry-Identität, Ist/Ziel, Opening beider Seiten, Gates und Consumer-Revisionen lokal sichern | überprüfbarer Ausgangsstand | unvollständige Evidence: kein Fenster beginnen |
| 2 Blind Control disarmen | shadow + legacy, Apply aus speichern; Options-Reload vollständig abwarten | neue Runtime shadow, write_path_reachable=false, keine Aktuation; persistiertes Apply aus | nicht bestätigt: Blind-Control-Entry deaktivieren; R0 |
| 3 Legacy stilllegen | Fremdbefehle/Bedtime stillgelegt; Legacy Apply aus, dann **alle** Legacy-ConfigEntries über HA „Deaktivieren“ dauerhaft deaktivieren | Entries disabled, erfolgreich unloaded, Legacy-Services entfernt, Panel ohne Coordinator | Unloadfehler: kein Rename/Owner-Wechsel; R0 |
| 4 Prozessgrenze / Null-Writer | Legacy dauerhaft disabled, BC shadow/Apply aus; genehmigten HA-Neustart durchführen | neuer HA-Prozess, Legacy weiterhin disabled/unloaded, keine Legacy-Services; BC shadow/Apply aus, Cover in Ruhe | Rest-Writer oder Bewegung: sperren, R0 |
| 5 Registry-Rename | Null-Writer bestätigt, NEW_ID erneut frei | dieselbe Unique-ID unter NEW_ID, OLD_ID nicht mehr registriert | Kollision/Identitätswechsel: nichts überschreiben, R1 |
| 6 Consumer migrieren | lokales Änderungspaket vollständig | alle tatsächlichen Referenzen gemäß Tabelle angepasst; kein Legacy-Aufruf aktiv | Teilfehler: Null-Writer beibehalten, R1 |
| 7 Persistieren und laden | Core-Devices-Dry-Run/Diff korrekt, Import angewendet; YAML geprüft | genehmigter HA-Neustart lädt YAML/HomeKit/persistierte Masters; Legacy disabled; BC shadow/Apply aus | Source-/Configfehler: R1 |
| 8 Shadow neu prüfen | Cover in Ruhe und Inputs frisch | logische Istposition, physisches Ziel, Opening-Polarität, beide Fensterseiten, Readiness, Failure, Baseline, Overrides und Diff plausibel; keine Aktuation | ungeklärte Differenz / fehlende Evidence: R1 |
| 9 Owner benennen | Schritt 8 belegt; Legacy disabled | live + blind_control, Apply weiterhin **aus**; Reload abgeschlossen, kein Write erreichbar | unerwarteter Write/Reloadfehler: sofort BC deaktivieren; R2 |
| 10 Fahrt-Gate | Benni prüft **aktuelle** Gesamtentscheidung, Achse, Fenster, Ziel und Istposition | gesonderte ausdrückliche Freigabe zur ersten beobachteten Bewegung | ohne Freigabe bleibt Apply aus |
| 11 Erster realer Lauf | Apply bewusst aktivieren; Reload/Baseline abwarten | kontrollierte erste Bewegung unter Beobachtung; stets neueste Gesamtentscheidung | unerwartete Richtung, Gegenfahrt, Quality-/Motionfehler: Apply aus / BC deaktivieren; R2 |
| 12 Technisch verifizieren | frische Ziel-/Motion-Evidence | tatsächliches Ziel innerhalb Toleranz **und** stabile Ruhe für position_settle_seconds; kein Self-Override, plausibler Cooldown und Safety | bloßes Service-Ergebnis oder Timer reicht nicht; Fehler: R2 |
| 13 Benni setzt Live | technische Verifikation und Verhalten akzeptiert | Benni setzt Live; Live Verified folgt erst nach seinen realen Pflichtszenarien | keine Agenten-Selbstzertifizierung |

Keine technische One-Shot-Pflicht: Apply bleibt ein laufender Regler;
bei neuen Inputs darf eine neue gültige Entscheidung entstehen. Für Pause
Apply aus oder Integration deaktivieren. Es gibt keine Bewegungshistorie,
die nach einer Pause abgearbeitet wird.

v0.6.1: applied bestätigt nur den ohne Exception abgeschlossenen HA-Handler,
nicht die Bewegung. command_error/target_not_reached bleiben diagnostisch
sichtbar und sperren normale Automatik zunächst. Nach einem neuen durchgehend
frischen, stabilen Ruhefenster (Default 30 s) endet die alte Attribution;
recovery_status=recovered und die Istposition als neue Baseline machen den
Regler wieder bewertungsfähig. Nur die aktuelle Entscheidung kann anschließend
unter allen Gates fahren; Safety bleibt vorher sofort möglich.
Während des beobachteten ersten Laufs bleibt jeder solche Fehler trotzdem
Abbruchgrund nach Schritt 11/R2: eine automatische Recovery ersetzt Bennis
technische Abnahme nicht.

Vor dem Fahrt-Gate numerische Achse und semantisches opening/closing unabhängig
prüfen. HA-konforme Motion wird nicht invertiert. Ein Gerät mit widersprüchlicher
Motion-/Positions-Evidence erhält keine Freigabe über eine globale Textumkehr.
Umwelt-Hysterese und Eintritt-/Entlastungszeiten in der Shadow-Diagnose prüfen;
Cooldown ist kein Ersatz. Werte und Rückweg stehen in MIGRATION.md.

### Warum Disable allein für die Legacy nicht genügt

Geprüfter Legacy-Stand: 9cbd1f0d7915849f9a3f4f60bf2fe7d88c483abd.
async_unload_entry entfernt Entries, Listener, Services und View.
BlindPolicyCoordinator.async_stop widerruft bereits erzeugte Tasks jedoch
nicht mit einem Lifecycle-Gate; manuelle Methoden umgehen den einzelnen
Apply-Schalter. Deshalb ist Schritt 4 **verpflichtend**. Erst ein neuer Prozess
mit persistiert deaktivierter Legacy beweist, dass alte Coordinator-Referenzen,
queued Callbacks und gestartete Service-Tasks nicht mehr existieren.
Der Code bleibt installiert. Keine zusätzliche Legacy-Kompatibilitätsschicht.

## 4. Deterministischer Rollback

R0 ist der Rückweg vor Rename; R1 nach Rename; R2 nach Owner-/Apply-Freigabe.

1. Für alle Rückwege zuerst Blind Control Apply aus und Entry deaktivieren.
   Erfolgreichen Unload / widerrufene Runtime bestätigen. Legacy bleibt disabled.
   Eine bereits physisch laufende Bewegung wird dadurch nicht rückgängig:
   stabile Ruhe und sichere Fensterlage abwarten; bei unsicherer Bewegung
   Bennis physische Sicherheitsintervention, keine automatische Gegenfahrt.
2. Null-Writer belegen. Bei R0 entfällt nur die Rückmigration; bei R1/R2
   erst Ziel-ID-Kollision für OLD_ID prüfen, dieselbe Registry-Entity zurückbenennen,
   dann **exakte Backups** aller geänderten Consumer wiederherstellen.
   Kein globales NEW_ID→OLD_ID-Ersetzen und keine History-Löschung.
3. Core-Devices-Originalexport per bestehendem Dry-Run/Import wiederherstellen,
   YAML/HomeKit/Skripte zurücksetzen. Beide Integrationen während des genehmigten
   HA-Neustarts disarmt halten. OLD_ID/Unique-ID, Master, Readiness, tatsächliche
   Position und beide Opening-Seiten erneut prüfen.
4. Nur bei belegtem Null-Writer und sicherer Geräte-/Opening-Lage: Legacy
   wieder aktivieren/laden, zunächst **Apply aus**. Erst Benni gibt deren
   ursprünglichen Apply-Zustand wieder frei. Fremdconsumer aus gesicherten
   Aktivierungszuständen restaurieren. BC bleibt deaktiviert oder separat
   bestätigt shadow + legacy, Apply aus.
5. Zeitpunkt, Ursache und Rückänderungen dokumentieren. Bei Restore-/Safety-
   Fehlern bleibt Null-Writer bestehen. Das vorbereitete vollständige Backup
   ist der letzte Rückweg; niemals einen Owner blind aktivieren.

## 5. Getrennte Abschlussgates

Tests Pass, Merged, Released, HACS sichtbar, Installed, Live und Live Verified
bleiben getrennt. Legacy, Config- und Recorder-Backups bleiben bis Live Verified
erhalten. Archivierung/Entfernung ist kein Teil dieses Releases.
