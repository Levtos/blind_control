# Konfiguration, Bindings und Cutover-Migration

**Stand:** Config v6 / AP3-Stabilisierung 2026-09-07. Testing / Shadow / Not Live.

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
