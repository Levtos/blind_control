# Konfiguration, Bindings und Cutover-Migration

## v0.7.3 → v0.7.4

Config bleibt v6. Profile, Kalibrierung, Bindings und Explicit-Empty-Intents
roundtrippen unverändert; keine neue Dependency oder Core-Contracts-Anbindung.
Privacy verwendet jetzt den vorhandenen Core-State-Day-State statt des alten
booleschen Privacy-Bindings. Die vier aktiven Phasen sind evening, late_evening,
early_night, late_night. Kein zusätzlicher Sensor und keine neue Optionsauswahl
sind bei korrekt vorhandenem Day-State nötig. Die alte Privacy-Auswahl bleibt
nur für Rollback erhalten und wird nicht konsumiert oder neu vorgeschlagen.
Verhaltensänderung: In diesen Phasen kann nach Freigabe das bestehende Privacy-
Ziel sofort wirksam werden. Betreiber prüft nach Installation zunächst Apply AUS.
Rollback auf v0.7.3 lädt dieselbe v6-Konfiguration und verwendet wieder den alten
Privacy-Boolean; der bekannte fehlende abendliche Sichtschutz kehrt damit zurück.
Statusentity bleibt stabil; Consumer müssen neuen Apply-Status idle berücksichtigen.
Keine HA-Live-Änderung durch Codex; reale Ausführung bleibt unbestätigtes Live-Gate.


## v0.7.2 → v0.7.3: additive Decision-Härtung

Verbindlich: [Issue #3 Contract](https://github.com/Levtos/blind_control/issues/3#issuecomment-5609119991).
Config bleibt **v6**: Profile, Kalibrierwerte, Binding-Intents, bewusst leere
Bindings, ausgewählte Core Contracts und Options roundtrippen unverändert.
Keine automatische Änderung von Owner, Runtime Mode, Automation oder Apply.
Sun-Horizon wird aus dem bereits gewählten Sun-Binding abgeleitet; kein neues
Pflichtbinding, keine neue Registry oder erfundene Schema-ID.

Decision/UX/Automation-Versionen sind additiv erhöht, siehe [Contracts](CONTRACTS.md).
LegacyProjection und Statusentity bleiben bestehen; neue Verbraucher sollen
die Dimensionen verwenden. Generationszähler sind flüchtige Runtime-Identitäten,
keine persistierten Commands. Reload/Restart verwirft sämtliche alten Freigaben
und verlangt erneut die bestehende ruhige Coverbaseline.

Rollback durch Betreiber: vollständiges HA-/ConfigEntry-Backup sichern,
Apply AUS und aktuelle Bewegung separat behandeln, technische Release-Version
v0.7.2 wiederherstellen, erforderlichen HA-Neustart durchführen, Manifest,
Config-Roundtrip, Owner, Safety und Null-Writer prüfen. Erst danach bewusst
freigeben. Config-v6 benötigt keinen Down-Migrator. Rollback stellt jedoch auch
die bekannten Solar-/PC-Contract-Fehler von v0.7.2 wieder her.

Codex installiert, konfiguriert oder startet HA in diesem Auftrag nicht.
Nachfolgende ältere Migrationsabschnitte bleiben historische Evidence.

**Stand:** Config v6 / AP3-Stabilisierung 2026-09-07. Testing / Shadow / Not Live.

## v0.6.2 → v0.6.3: Solar und native Cutover-Optionen

Config bleibt v6 ohne neue Felder oder automatische Gate-Änderung. Alle
gespeicherten Bindings, Profile, Kalibrierwerte und Gates bleiben erhalten.
`low_light` erweitert die Solar-Zustände; Consumers dürfen ihn nicht als unknown
interpretieren. Runtime/UX ergänzen baseline_position/baseline_ready.
Rollback mit denselben v6-Optionen ist möglich, stellt aber den alten
Low-Light-Blocker und die bisherige Diagnose wieder her; zuerst Apply disarmen.

HA Einstellungen → Geräte & Dienste → Blind Control → Konfigurieren:
runtime_mode, apply_owner und apply_enabled sind native Optionsfelder.
Nach Speichern Options-Reload und geladene Runtime prüfen. Ablauf und Rückweg:
[AP3_CUTOVER.md](AP3_CUTOVER.md). Keine DevTools, .storage- oder YAML-Änderung
für diese drei Optionen. Nächstes reales Gate ist Bennis kontrollierter
Writer-Cutover nach Installation, keine automatische weitere Shadow-Runde.

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

## Core Contracts – verbleibende Plattform-Gaps nach v0.7.0

Ab v0.7.0 gelten [AP3_OPERATOR.md](AP3_OPERATOR.md) und der Consumer-API-Pfad für
Opening, Raumklima und Weather/Environment. Config v6 wird additiv erweitert:
`core_contract_profile=benni`, `core_contracts={}`. Bestehende Auswahl/Profile/
Freshness/Gates bleiben erhalten; ohne gewählte Contract-ID bleibt der explizite
kompatible Owner-Fallback. Keine automatische Auswahl oder Registry-Migration.

| Direkte Grenze | Später benötigter kanonischer Inhalt | Voraussetzung |
| --- | --- | --- |
| Bio, Activity, Day, Away, Private Time, Privacy | eindeutige Core-State-Rollen mit feldweiser Quality | aktives passendes Profil, unveränderte Owner-Semantik |
| Opening / Safety | Mehrfenster-Aggregat, Tilt-Polarität, Freshness, Conflict | relevanter Scope; Published-Einzelöffnungs-Pilot reicht nicht |
| Coverposition, Motion, Availability, Readiness | Gerätevertrag plus sichere Actuator-Auflösung | gleiche Geräteidentität, logische Achse nur einmal normalisieren |
| Lux, Sun, Cloud, Temperaturen, Wetter | eindeutige Einheiten und Feldqualitäten | aktivierte Quellen und TTL/LKG-Vertrag |
| optionale interne Modellstrahlung | kanonische Rollen statt privatem Provider | Quelle vorhanden; externe Precedence erhalten |

Weitere Rollen erst nach fachlich belegtem aktivem Inhalt und geprüfter
Consumer-Semantik migrieren. Dies ist kein zusätzliches pauschales Cutover-Gate.
Keine produktiven Registry-Inhalte werden in diesem Auftrag verändert.
