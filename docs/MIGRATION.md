# Konfiguration, Bindings und Cutover-Migration

**Stand:** Config v6 / AP3-Stabilisierung 2026-09-07. Testing / Shadow / Not Live.

## v0.6.1 → v0.6.2: Standard-Cover-Evidence

Keine Config-/Options-Migration und keine neuen Felder. Gespeicherte v6-Werte,
Bindings, Achse und Gates laden unverändert. Die vorhandene Positions-TTL
begrenzt weiter explizite Device-Zeit-Evidence und bewegte Positions-Telemetrie;
eine gültige stationäre Standard-Coverposition ohne solche Zeit-Evidence wird
nicht mehr allein durch einen alten HA-Änderungszeitpunkt stale.
Motion wird unabhängig von numerischer Positionsqualität gelesen.
Negative Evidence und normale Restart-/Recovery-/Safety-Gates bleiben wirksam.
Details: CONTRACTS.md Abschnitt 7.1 und AP3_STABILIZATION.md, Nachtrag v0.6.2.

Versionsrollback auf v0.6.1 ist mit denselben v6-Daten möglich; dabei kehrt die
alte 120-s-Alterung stationärer Position zurück. Vor Installation wie üblich
Original-Config sichern. Keine Installation/Reloads durch diesen Patch.
Bennis neue Installation, read-only Shadow-Evidence, Opening-OPEN- und
Movement-/Baseline-Reproduktion bleiben vor weiterer Cutoverplanung erforderlich.

## Additive v0.6.0 → v0.6.1-Konfiguration

Config bleibt v6. Bestehende Profile, Achse, Gates, Bindings, Freshness,
Provider und übrige Kalibrierung laden mit unveränderter Bedeutung.
Der Regressionstest lädt eine neutrale vollständige Konfiguration, die mit
dem unveränderten v0.6.0-Serializer (303d843) erzeugt wurde, und vergleicht alle Felder.

| Feld | Default / Übernahme | Validierung |
| --- | --- | --- |
| cold_lux_enter_threshold | bestehendes cold_lux_threshold unverändert, sonst 400 lx | 0–100000 |
| cold_lux_exit_threshold | max(Enter + 100 lx, Enter × 1.25), somit normalerweise 500 lx | strikt größer als Enter, höchstens 125000 |
| environment_hysteresis_ratio | 0.8; Haltefaktor für Heat-/Glare-Confidence und minimale solare Inzidenz | 0.01–0.99 |
| environment_enter_seconds | 10 s | 0.1–3600 |
| environment_exit_seconds | 120 s | mindestens Enter, höchstens 3600 |
| movement_recovery_seconds | max(30 s, bestehende position_settle_seconds) | mindestens Settling, höchstens 3600 |

Neue explizite Werte haben Vorrang vor diesen Defaults. Ein erneuter
JSON-/Config-Roundtrip skaliert nichts. Speichern verwendet den neuen
Cold-Enter-Namen; der alte Name ist ausschließlich ein Ladealias.
Native Formulare und Panel machen alle sechs Werte editierbar.
84 sichtbare Initialfelder / 86 Optionsfelder; Owner/Runtime bleiben nur im
nativen OptionsFlow. Keine automatische Änderung von Apply oder Ownership.

Die Zeiten und Bänder sind bewusste neue Flatter-/Recovery-Semantik, keine
Veränderung der alten Profile. Vor Versionsrollback auf v0.6.0 dessen
vollständigen Original-ConfigEntry-/Options-Export wiederherstellen:
v0.6.0 kennt den neuen Cold-Namen und die neuen Bänder nicht.
Das Versionsbackup bleibt daher notwendig.

**Reihenfolge für v0.6.1:** erst neues unabhängiges read-only Quality Gate
aus frischem Kontext mit PASS, dann Bennis Backup/Installation und neue
Shadow-Evidence. Dieses Release führt keinen dieser HA-Schritte aus.

## Persistierte Konfiguration

BlindControlConfig.from_mapping lädt vorhandene ConfigEntry-Daten und Options.
Options bleiben vorrangig. Laden allein schreibt keine Registry, Konfiguration
oder Aktoren. Erst bewusstes Speichern serialisiert v6.

- Profil v5 {normal, inverted} → v6 {logical: normal}. Alle gelieferten alten
  Profilpaare werden in legacy_profile_values verlustfrei erhalten.
- Alter invertierter Wert ist kein zweites editierbares Profil mehr.
  Die beschlossene Änderung ist sichtbar: z. B. Heat normal 15 /
  alt invertiert 55 wird logisch 15 / physisch invertiert 85.
- cloud_shadow_ratio (0–1) → cloud_cover_threshold (0–100) mit Faktor 100.
  Sein Helligkeitsvergleich wird als model_lux_ratio separat erhalten.
  Ein v6-Roundtrip skaliert nicht erneut.
- Neue Defaults: Cold-Lux 400 lx, Positionsruhe 2 s, Bewegungsfehlerfrist 120 s.
  Temperaturen und bestehende Heat-/Solar-/Cooldown-/Toleranzwerte bleiben
  kalibrierbar. Unbekannte zukünftige Schemaversionen werden abgelehnt.
- Modus, Owner, Apply, Bindings und private Providerkonfiguration werden nicht
  aus historischen Dokument-IDs neu erfunden.

Vor Installation vollständige ConfigEntry-/Options-Backups sichern.
Für Versionsrollback die **Originalkonfiguration** zum alten Code wiederherstellen;
v6-Daten nicht blind in v0.5.1 laden. legacy_profile_values erhält Profilwerte,
ersetzt aber kein vollständiges Backup. Erst disarmen, dann Rollback.
Neue Achsenspezifikation bewusst prüfen, bevor Apply jemals aktiviert wird.

## Entity-Rename

Keine automatische Startup-Migration. cover.living_thermal_blind bleibt Ziel
des separat freizugebenden Fensters. Aktueller privater Name wird lokal als
OLD_ID verifiziert, Zielkollision und Registry-Identität unmittelbar vorher
geprüft. Gespeicherte Strings werden pro Consumer angepasst.
Der rekursive Rename-Helper entfällt; er war kein produktiver HA-Pfad und
konnte weder Transaktionen noch kollisionssicheren Rollback beweisen.

Vollständige Schritte, notwendige Neustarts, Vorher/Nachher und exakte Rückwege:
[AP3_CUTOVER.md](AP3_CUTOVER.md). Rollback verwendet Snapshots/Originalexporte,
keine pauschale inverse Textersetzung. Legacy bleibt installiert, während des
Cutovers vollständig deaktiviert und durch Prozessneustart entkoppelt.

## Core Contracts – spätere Binding-Migration

Readiness-Ergebnis: [AP3_STABILIZATION.md](AP3_STABILIZATION.md).
Für AP3 gelten direkte, explizit gespeicherte Bindings. Suchmarker:
CORE_CONTRACTS_MIGRATION in coordinator.py:build_inputs_from_states.

| Direkte Grenze | Später benötigter kanonischer Inhalt | Voraussetzung |
| --- | --- | --- |
| Bio, Activity, Day, Away, Private Time, Privacy | eindeutige Core-State-Rollen mit feldweiser Quality | aktives passendes Profil, unveränderte Owner-Semantik |
| Opening / Safety | Mehrfenster-Aggregat, Tilt-Polarität, Freshness, Conflict | relevanter Scope; Published-Einzelöffnungs-Pilot reicht nicht |
| Coverposition, Motion, Availability, Readiness | Gerätevertrag plus sichere Actuator-Auflösung | gleiche Geräteidentität, logische Achse nur einmal normalisieren |
| Lux, Sun, Cloud, Temperaturen, Wetter | eindeutige Einheiten und Feldqualitäten | aktivierte Quellen und TTL/LKG-Vertrag |
| optionale interne Modellstrahlung | kanonische Rollen statt privatem Provider | Quelle vorhanden; externe Precedence erhalten |

Migration erst nach fachlich belegtem aktivem Inhalt, vollständigen Rollen,
Revision/LKG-/Subscription-/Unsubscribe-Tests und erneutem Shadow-Diff.
Keine produktiven Registry-Inhalte werden in diesem Auftrag verändert.
