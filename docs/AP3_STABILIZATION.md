# AP3 Stabilisierung – Entscheidung vom 07.09.2026

**Verbindlicher Auftrag:** [blind_control#3](https://github.com/Levtos/blind_control/issues/3).
Diese Entscheidung ersetzt widersprechende ältere AP1/AP2/AP3-Texte.
Historische GitHub-Kommentare bleiben unverändert.

## Architekturentscheidung

Lokale Reparatur A hätte Command-Historie, Geräteachse, Override-Timer und
Coordinator-Callbacks mit weiteren Sonderfällen verbunden. Gewählt wurde B:
begrenzter Umbau dieser Grenzen, ohne neue Arbitration-/Registry-Plattform.

- Engine, Safety und Override verwenden ausschließlich logische Positionen.
  Input-Adapter normalisiert Geräteposition und Fahrtrichtung; allein der
  Actuation-Adapter rechnet das fertig bestimmte Ziel zurück.
- Cooldown startet bei Dispatch. Pending ist Diagnose der aktuellen
  Entscheidung; jede Auswertung ersetzt es. Keine Release-Methode für alte Ziele.
- Eigene Bewegung endet erst mit stabiler tatsächlicher Zielposition in Ruhe.
  Die konfigurierbare Frist meldet Fehler, niemals einen Benutzer-Override.
- Stop widerruft die konkrete Runtime endgültig. Adapter akzeptiert nur die
  neueste, unverbrauchte Freigabe derselben aktiven Konfiguration.
- Hierarchie, Candidate-Keys, Owner-Inputs, redigierte Diagnose und admin-only
  Options-Grenze bleiben. Positionssemantik/Settings ändern sich bewusst:
  Config v6, Decision v4, Runtime v3, UX v4, Automation Projection v3.

## Fachliche Entscheidungen

| Punkt | Verbindliches Verhalten |
| --- | --- |
| C1 | open ist nicht tilted; bei offen niemals logisch abwärts. Safety-Ziel mindestens Istposition; Default 100. Wiederholung aus Istabweichung unabhängig von Command-Historie, Override/Waking/Cooldown. Laufende Abwärtsentscheidung sofort ersetzen. |
| C2 | queued Callbacks, stopped/replaced Runtime und alte Freigaben können nicht schreiben. |
| H1 | Solar-Aggregat unknown blockiert automatische Fahrt; kein Base-Daylight-Open. Positive Opening-Safety separat. |
| H2 | Ziel tatsächlich erreicht und in Ruhe bestätigt; Zwischenposition/Nachlauf/Timeout/Restart sind kein Fremd-Override. |
| H3 | Core State besitzt private_time einschließlich zeitlicher Begrenzung. Waking pausiert Heat/Glare/Privacy/Cold, unterdrückt aber nicht zusätzlich private_time. |
| H4 | Cold braucht frischen Lux < cold_lux_threshold (Default 400 lx) und Outdoor-Temperatur <= cold_outdoor_threshold (Default 8 °C); nicht allein Off-Window/Trend. |
| H5 | Legacy dauerhaft deaktivieren/unloaden, installiert lassen. Wegen fehlender Legacy-Task-Revozierung zusätzlich genehmigter HA-Neustart vor Null-Writer-Gate. |
| H6 | Kontrollierter erster Lauf unter Beobachtung; keine One-Shot-Maschine. Nur aktuelle Gesamtentscheidung. |
| H7 | Exakte Consumer-Änderungen und Backups im Null-Writer-Fenster; kein automatisches Mitziehen gespeicherter Strings. |
| H8 | Frühere Shadow-/Installations-Evidence ersetzt keine neue Evidenz für diese Semantik. Erneuter Shadow und unabhängiges Gate vor Cutover. |
| H9 | Ein logischer Profilwert 0 geschlossen / 100 offen; Gerät bei invertierter Achse 100 - logical_target. Alte Normal-Werte gewinnen, alte Werte bleiben archiviert. |
| M1 | Cloud Cover 0–100 %. Alte 0–1-Schwelle wird mal 100 migriert; Helligkeitsverhältnis bleibt eigener dimensionsloser Wert. |
| M2 | Aktuelle Core-Contracts-API geprüft; Variante B, direkte Bindings vorerst behalten. |
| M3 | Temperaturtrends sind in v1 optionale diagnostische Evidence. Kein erfundenes Trend-/Feuchte-/Saisonmodell; Heat/Cold getrennt und kalibrierbar. |

## Core-Contracts-Readiness

Geprüft: benni-core-contracts Default def02cdf6db4daf24bb97ee36678eac090b9f863
(v0.2.1), Registry-/Service-/Consumer-/Profile-/Hardening-Arbeiten und Operations
#33, insbesondere Consumer API #20 sowie aktueller Release PR #35.

Die ConsumerApi ist reale, getestete Infrastruktur: resolve_binding,
lookup_contract, Profile, aktive Revision/LKG, defensive DTOs,
Quality/Freshness, gefilterte Subscriptions und Cleanup. Inaktive Runtime
liefert runtime_not_ready; uneindeutige Bindings werden abgelehnt.
27 bestehende Consumer-/Profil-/Listener-Tests lokal ausgeführt.

Entscheidend fehlt die aktivierte, fachlich vollständige Blind-Control-Matrix.
Die aktuelle Operations-Evidence meldet eine leere Registry ohne Aktivierung;
eine geladene Integration beweist kein aktives Profil. Der Published-Opening-
Pilot ist eine einzelne andere Öffnung, keine Wohnzimmer-Mehrfensterfusion.
technical_device.v1-Evidence allein modelliert noch nicht die vollständige
Cover-/Motion-/Readiness-/Policy-Input-Grenze.

Eine jetzige Umstellung würde neue Rolleninhalte und produktive Aktivierung
voraussetzen. Deshalb **Variante B**. CORE_CONTRACTS_MIGRATION steht an der
tatsächlichen Input-Adaptergrenze. Spätere Inventur: MIGRATION.md.
Keine parallele Registry oder API-Simulation im Produkt.
Der unbenutzte rekursive migration.py-Helper entfällt: Er war kein HA-Migrator
und seine Rückrichtung war bei Kollisionen nicht sicher.

## Opening-Owner-Audit

Aktueller Binding-Pfad: Core Devices Opening Domain Master → ausgewähltes
Opening-State-Binding → Blind-Control-Input → Safety. Keine Kontaktfusion
in Blind Control. Die versionierte HA-Master-Konfiguration verwendet ein OR
beider Fenster und einen getrennten Tilt-/Conflict-Pfad. Der öffentliche
Master-State ist konservativ umfassender als nur diese zwei Fenster.

Der tatsächliche Core-Devices-Evaluator am Stand
52c5e89aca086e10f5a506df481636db0bd35866 wurde mit der versionierten
Einhornzentrale-Konfiguration 6ae6121e1c5122130508857936e3ae3c5e549b29
ausgewertet: rechts offen, beide offen, nur links offen, beide geschlossen
lieferten open/open/open/closed. Zusätzlich 31 bestehende Contract-Hardening-/
Combined-Tests grün. Die read-only Live-Projektion enthielt beide Einzelfenster,
Aggregate und gesunde Quality.

Der beobachtete Legacy-Handoverfehler ist nicht als Fehler dieser versionierten
Fusion reproduziert. Ob reale Kontakte und aktive persistierte Master-
Konfiguration in jedem Übergang identisch liefern, muss das spätere Shadow-/
Kontakt-Gate zeigen. Keine heimliche Upstream-Korrektur.


## Kalibrierwert-Audit

Heat-Innen-/Außentemperatur, Cold-Temperatur/Lux, Radiation, Heat-/Glare-
Confidence, Cloud-Prozent, Modell-Lux-Verhältnis, minimale Fenstereinstrahlung,
Modellhelligkeit pro W/m², Wettertrends, Cooldown und Positionstoleranz sind
explizite Config-/UX-Werte. minimum_incidence_factor (Default 0.05) und
model_lux_per_watt (Default 120) ersetzen bisherige lokale Solar-Konstanten.
Die festen Confidence-Evidence-Gewichte beschreiben die Modellstruktur,
nicht eine wohnungsabhängige Freigabeschwelle. Der diffuse Faktor 0.5 ist die
bestehende vereinfachte vertikale Flächenprojektion, keine neue Wetterlogik.
