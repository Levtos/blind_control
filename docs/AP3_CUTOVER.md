# AP3 Cutover- und Rollback-Runbook

**Technischer Status:** `Installable / Shadow default / Not Live`

Der Betriebsstatus bleibt `Installed / Shadow / Not Live`.

Dieses Runbook bereitet den produktiven Wechsel vor. Es führt selbst keinen
Coverbefehl, HA-Reload, Registry-Rename oder Owner-Wechsel aus. Der Cutover
benötigt Bennis separates Gate und anschließend eine unabhängige Sol-High-
Abschlussprüfung.

## Redigiertes Consumer-Inventar

| Oberfläche | Abhängigkeit | Cutover-Aktion |
| --- | --- | --- |
| Blind-Control ConfigEntry/Options | Cover Availability und Position; später Actuatorgrenze | exakte Referenz auf dieselbe Registry-Entity aktualisieren |
| Legacy-Policy | produktiver Writer und eigener Cover-Default | vor Rename pausieren; für Rollback installiert lassen |
| HomeKit-Konfiguration | exponiert das physische Cover | Referenz atomar aktualisieren und Exposition prüfen |
| Core-Devices-Import | Coverzustand, Position und abgeleitete technische Readiness | Source-Referenzen aktualisieren und Master neu prüfen |
| Core-Contracts Source-Evidence | technische Source-Binding-Evidence | exakte Source-Referenz aktualisieren und Contracttests ausführen |
| System-Readiness | konsumiert den Rollo-Master indirekt | nach Core-Devices-Aktualisierung vollständig verifizieren |
| Bedtime-Skript | ruft den Legacy-Apply-Service auf | vor Owner-Wechsel entfernen/ersetzen; niemals parallel lassen |
| Automationen, Skripte, Szenen, Helper und Dashboards | live read-only Suche ohne direkten Treffer; YAML-Flächen separat inventarisiert | unmittelbar vor Cutover erneut exportieren/suchen |
| Recorder/History | History ist an die bisherige Entity-ID gebunden | Verlauf vor Rename sichern; keine automatische Historienkontinuität behaupten |
| weitere aktive Repositories | produktive Suche umfasst Policy, Core Devices, Core Contracts und HA-Konfiguration | PRs/Commits vor dem Live-Fenster vorbereiten, nicht vorab deployen |

Gespeicherte Strings folgen einem Entity-Registry-Rename nicht zuverlässig.
Deshalb werden alle obigen Flächen explizit geprüft. Die kanonische Ziel-ID ist
`cover.living_thermal_blind`; die aktuelle installationsspezifische ID bleibt
in öffentlichen Nachweisen redigiert.

## Preconditions

1. Dieses Release ist installiert und nach Restart weiterhin `shadow + legacy`.
2. Die unabhängige Sol-High-Prüfung hat keine offenen kritischen/hohen Findings.
3. Shadow ist `normal`, ohne Quality-Blocker; Opening, Readiness und Position
   sind fresh.
4. Fachliches und effektives Ziel sowie aktuelle Coverposition sind notiert.
5. Alle Consumer-Änderungen und ihre Rückänderungen liegen lokal bereit.
6. Benni gibt das konkrete Cutover-Fenster ausdrücklich frei.

## Atomarer Live-Cutover

1. Zeit, Ist-Position, Ziel, Opening- und Safety-Zustand protokollieren.
2. Blind Control auf `shadow + legacy` und Apply aus bestätigen.
3. Den Legacy-Apply-Pfad pausieren, die Integration aber installiert lassen.
4. Prüfen, dass kein aktiver Writer und keine laufende Coverbewegung existiert.
5. Das physische Cover in der Entity Registry auf
   `cover.living_thermal_blind` umbenennen.
6. Blind-Control-Binding sowie HomeKit-, Core-Devices-, Core-Contracts- und
   übrige gespeicherte Consumer-Referenzen atomar aktualisieren.
7. Nur die erforderlichen HA-Komponenten nach Bennis Gate neu laden; falls eine
   Fläche einen Restart verlangt, den Cutover stoppen und separat freigeben.
8. In Shadow Position, Availability, Readiness, Opening-Safety, Decision Trace
   und Override-Baseline prüfen. Kein Apply darf ausgeführt worden sein.
9. Blind Control zuerst mit Apply aus auf `live + blind_control` setzen. Der
   Legacy-Writer muss weiterhin pausiert sein; damit existiert genau ein
   designierter, aber noch gesperrter Writer.
10. Ziel und Ist-Position erneut vergleichen. Erst nach Bennis explizitem
    Fahrt-Gate Apply aktivieren und genau eine kontrollierte Bewegung zulassen.
11. Zielerreichung, Writing Guard, fehlenden Self-Override, Cooldown und
    Safety-Status prüfen. Erst danach setzt Benni `Live`.

## Rollback

1. Blind-Control-Apply sofort deaktivieren; danach `shadow + legacy` speichern.
2. Bestätigen, dass Blind Control keinen erreichbaren Write-Pfad mehr meldet.
3. Falls der Rename bereits erfolgte, Registry-ID und alle vorbereiteten
   Consumer-Referenzen exakt rückwärts migrieren.
4. Erforderliche Komponenten nur nach Bennis Gate neu laden und Position,
   Opening sowie technische Readiness prüfen.
5. Erst bei bestätigt null aktivem Blind-Control-Writer den Legacy-Apply-Pfad
   wieder aktivieren.
6. Zeit, Ist-Position, Safety, Ursache und rückgängig gemachte Referenzen
   dokumentieren. Keine History oder alte Integration löschen.

## Nachlauf

`Tests Pass`, `Merged`, `Released`, `Installed`, `Live` und `Live Verified`
sind getrennte Gates. Die Legacy-Integration bleibt bis `Live Verified`
installiert und rollback-fähig. Repository-Archivierung und Alt-Issue-Abschluss
erfolgen erst danach und sind nicht Teil dieses technischen Releases.
