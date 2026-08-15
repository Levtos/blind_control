# AP2 Shadow-Vertical-Slice

**Stand:** 15. August 2026
**Status:** technische Umsetzung im Draft-PR, `Not Live`
**Scope:** `blind_control#2` / AP2, kein Cutover

## 1. Umgesetzter Pfad

```text
ConfigEntry / OptionsFlow
        -> BlindControlConfig mit Profilen, Kalibrierdefaults und Owner-Bindings
        -> ShadowCoordinator: State-Listener + Freshness-Timer
        -> owner-bound BlindControlInputs und LegacyEvidence mit Source/Quality/Freshness
        -> Solar Exposure + DecisionEngine
        -> DecisionTrace mit Kandidaten, Winner, Pausen und Safety
        -> ShadowRuntime / ShadowSnapshot
        -> feldweiser Legacy-Diff
        -> read-only WebSocket-Projektion / OptionsFlow-Update
```

`async_setup_entry` startet eine laufende, aber strikt nicht-aktuierende
Beobachtung. Entity IDs werden nicht im Produktcode erfunden, sondern als
Owner-Bindings über ConfigEntry/OptionsFlow gespeichert. Bei jeder gebundenen
State-Änderung und zusätzlich über den Freshness-Timer wird ein neuer Snapshot
berechnet und als `blind_control.ux.v1` im Runtime-Data-Projektionsobjekt
gehalten. Der WebSocket-Read-Befehl liefert genau diese Projektion; der einzige
UX-Update-Befehl validiert und speichert ausschließlich OptionsFlow-Konfiguration.

## 2. Contracts und Ownership

| Bereich | Vertrag im Slice | Owner-Annahme | Verhalten bei fehlender Qualität |
| --- | --- | --- | --- |
| Bio/Waking, Activity, Day, Context, Away | `BlindControlInputs` | Core State; Blind Control konsumiert nur kanonische Werte | nicht fresh bleibt inaktiv/diagnostisch; kein lokaler Recompute |
| Opening | `opening_state`, `opening_safe_for_blind` | Opening-/Core-Contracts-Owner, noch binding-offen | unknown, stale, conflict oder unavailable blockieren |
| Cover Availability/Readiness | technische Beobachtungen | technische Contract-Grenze | keine freigegebene Zielposition |
| Cover Position | `cover_position` | technischer Geräte-Contract | nur Diagnose/Baseline, keine Positionsinferenz |
| Sonne, Lux, Wettermodell | Solar-Input-Beobachtungen | jeweilige externe technische Owner | Solar `unknown`; keine Heat-/Open-Behauptung |
| Temperatur, Wettertrends, Luftbewegung | Umweltbeobachtungen | jeweilige Umwelt-/Klima-Owner | der betroffene Kandidat bleibt inaktiv |

Owner-/Freshness-Annahmen sind explizit und pro Input gebunden. Nur
`InputQuality.FRESH` ist für positive fachliche und technische Aussagen
verwendbar. `degraded` ist sichtbar, aber nicht automatisch fresh. Ein
`closed`-Opening darf ausschließlich aus einer fresh, positiven Opening-
Beobachtung kommen.

Die Default-Policy trennt stabile Contract-Zustände von zeitkritischer
Telemetrie: Core-State-Werte werden nicht allein wegen ihres HA-Alters stale,
während Solar-, Wetter-, Temperatur- und Coverpositionswerte eine
feldspezifische Zeit-Evidence benötigen. Opening-/Readiness-Felder benötigen
mindestens einen Geräte-/Contract-Zeitstempel, und fehlende geforderte
Timestamps bleiben konservativ `stale`. Jede Policy trägt Owner, zulässiges
Maximalalter und `require_timestamp`; einzelne Felder können diese Defaults
explizit überschreiben.

`activity_state = none` ist ein gültiger kanonischer Inaktivitätswert. Nur die
HA-Sentinels `unknown` und `unavailable` werden global verworfen.

## 3. Entscheidungssemantik

- Kompatible aktive Kandidaten liefern jeweils einen eigenen Zielwert; der
  kleinste Wert gewinnt.
- Öffnungsgründe (`base_daylight`, `storm_approaching`,
  `cool_air_available`) werden nur verwendet, wenn kein schließender Kandidat
  aktiv ist. Dadurch bleibt die Achseninvertierung mit expliziten Werten
  semantisch stabil.
- `waking` kommt nur aus `bio_state == waking`, ist bis `awake` exklusiv und
  pausiert Heat, Glare, Privacy und Cold Insulation. Safety, Readiness und
  deaktivierte Automatik bleiben übergeordnet.
- TV, Streaming und Konsolen verwenden `glare_tv`; PC verwendet `glare_pc`.
  Glare benötigt zusätzlich eine eigene, fensterbezogene Solar-Exposure mit
  Confidence; es teilt kein Lux-Hard-Gate mit Heat. Night und
  `solar_not_on_window` beenden Glare trotz Screen-Aktivität.
- Eine frische positive Sonnenhöhe darf durch niedrigen Lux nicht zu `night`
  werden. Der Lux-Night-Fallback gilt nur ohne frische Solar-Geometrie.
- `cloud_shadow` beendet Heat bei fortbestehender thermischer Last nicht.
  Gewitter und nutzbare kühle Luft sind getrennte Cooling-Kandidaten.
- Vollständiges Öffnen braucht einen positiven Grund. Fehlende oder unsichere
  Daten führen nicht still auf 100 %.
- Ein vollständig offenes Fenster verwendet die konfigurierte Safety-Position;
  eine unsichere Kippstellung oder unbekannte Opening-Lage blockiert.
- Ein aktiver, fremder Manual Override hält die Automatik auf der beobachteten
  Position. Nur Safety und der festgelegte Waking-Lifecycle dürfen ihn
  überstimmen; `apply_enabled = false` bleibt auch mit Override absolut.

## 4. Konfiguration und Kalibrierung

Die AP1-Migrationsdefaults sind in `config.py` versioniert und in ConfigFlow
und OptionsFlow editierbar:

| Profil | Normal | Invertiert |
| --- | ---: | ---: |
| Window Safety | 100 | 0 |
| Privacy Bed | 40 | 60 |
| Waking | 100 | 0 |
| Sleep | 5 | 60 |
| Privacy | 40 | 60 |
| Heat Protection | 15 | 55 |
| TV Glare | 60 | 40 |
| PC Glare | 75 | 25 |
| Open | 100 | 0 |

Zusätzliche Profile und die Achsen-Invertierung verwenden dieselbe sichere
Validierung. Temperatur-, Lux-, Strahlungs-, Confidence-, Temperatur-/Luxtrend-,
Wettertrend-, Cooldown- und Toleranzwerte sind konfigurierbare Defaults und
ausdrücklich für spätere Shadow-Kalibrierung vorgesehen; sie bilden keine neue
Grundsatzrunde.

## 5. Override und Cooldown

`OverrideTracker`:

- setzt nach Restart eine Ruhepositions-Baseline;
- unterdrückt eigene Beobachtungen innerhalb eines expliziten Writing Guards;
- ignoriert Attribut-Churn ohne Positionsänderung;
- erzeugt nur bei einer fremden Positionsänderung außerhalb des Guards einen
  sichtbaren Override;
- behandelt Konfigurationsänderung als Rechen-/Baseline-Ereignis;
- bindet einen aktiven Override an einen expliziten Context-Key aus Bio-,
  Activity-Gruppe, Day-, Household- und Opening-Feldern;
- hält ihn bei derselben explizit definierten Medien-/Nutzungssitzung;
- beendet ihn bei einem geänderten Context-Key mit dem deterministischen Grund
  `override_context_changed`;
- beendet ihn beim Eintritt in den kanonischen Waking-Kontext mit
  `waking_context_superseded`, damit er Waking nicht blockiert.

`CooldownTracker` hält während des Cooldowns ausschließlich das jüngste Ziel.
Die Engine berechnet Trace und Snapshot unmittelbar; Cooldown verzögert keine
Diagnose und führt selbst keine Aktion aus.

## 6. Shadow-Sicherheit

`ShadowSnapshot` kennzeichnet unveränderlich:

- `shadow_only = true`
- `actuation_executed = false`
- `write_path_reachable = false`

Der versionierte Snapshot-Contract heißt `blind_control.shadow.v1`.

Die Produktintegration importiert keine Home-Assistant-Aktor-/Service-API,
forwardet keine Plattform und registriert keinen Service. Die Coordinator-
Listener sind ausschließlich State-/Zeitbeobachtung; der WebSocket-Transport
liefert Snapshot-Daten oder validiert OptionsFlow-Konfiguration. Der
Boundary-Test prüft zusätzlich, dass kein produktiver Cover-/Apply-Schreibpfad
im Python-Paket vorhanden ist. Konfigurationsspeicherung ist davon getrennt
und betrifft niemals ein Gerät.

## 7. Legacy-Diff und UX-Contract

`ShadowCoordinator` liest für jede konfigurierte Legacy-Bindung die vier Felder
(`active_mode`, `effective_target`, `safety_status`, `apply_status`) und erzeugt
auch für eine fehlende/stale Beobachtung ein sichtbares Feld. `compare_legacy_snapshot`
klassifiziert feldweise als `expected`, `improved`, `unresolved` oder `error` und
trägt Quality/Source der Alt-Evidence mit. Fehlende Legacy-Bindings bleiben
explizit unkonfiguriert; Werte werden nicht aus der neuen Entscheidung erfunden.

`ux_contract.py` stellt `blind_control.ux.v1` für Übersicht, Diagnose und
Einstellungen bereit. Die Projektion enthält Gewinner, effektives Ziel,
Kandidaten, pausierte Äste, Solar-Diagnose, Quality/Reason, Alt/Neu-Diffs und
alle editierbaren Konfigurationswerte. `frontend/` wird als
`blind-control-panel.js` in der Integration ausgeliefert, über
`async_register_static_paths` erreichbar gemacht und als offizielles
HA-Custom-Panel registriert. Das Custom Element erhält den laufenden `hass`-
Context von HA; DOM-/Window-Probing ist kein Transportpfad. Die App lädt die
reale Projektion über `blind_control/get_snapshot`, pollt sie für laufende
Anzeige, speichert Änderungen über `blind_control/update_options` und enthält
keinen `sampleSnapshot`-Produktpfad. Status-Badges stammen aus dem Snapshot,
Coverposition und Haushalt werden in der Übersicht gezeigt, und alle Input-
und Legacy-Bindings bleiben im OptionsFlow-Formular sichtbar, auch wenn sie
noch leer sind. Die Copy-Aktion schreibt die redigierte Debug-Evidence in die
Clipboard-API.

## 8. Implementiert und offen

### Implementiert

- früh installierbarer ConfigEntry-Shadow-Snapshot;
- laufender HA-Observation-/Coordinator-Pfad mit konfigurierbaren Owner-
  Bindings, Freshness- und Legacy-Evidence;
- versionierte Backend-, Trace-, UX- und Shadow-Contracts;
- konfigurierte Normal-/Invertiert-Profile und Achseninvertierung;
- Solar-Geometrie mit Golden-Vector-Regressionen;
- Minimum-Komposition, exklusives Waking, Heat/Glare, Storm/Cool-Air/Cold;
- Opening-Safety, positive Open-Gründe und Unknown/Stale-Blockierung;
- Override-, Restart-, Konfigurations- und Cooldown-Regressionsschutz;
- Manual-Override-Hold mit Safety-/Waking-Ausnahmen und absolutem Apply-Gate;
- feldweiser Alt/Neu-Legacy-Diff mit `error` für nicht frische Evidence;
- contract-getriebene Svelte-5/Vite/TypeScript-Ansicht für reale Snapshotdaten,
  dynamische Status-Badges, OptionsFlow-Update und echte Copy-Aktion;
- installierbares HA-Custom-Panel mit offiziellem `hass`-Context und gebundener
  Static-/Panel-Registrierung;
- echte Contracttests für State-Listener, Freshness-Timer, WebSocket-Read/
  Update/Admin-Gate, OptionsFlow-Reload und Panel-Registrierung;
- keine produktive Coverfahrt und keine alte Policy-Änderung.

### Für spätere AP2-Batches beziehungsweise vor Cutover offen

- konkrete produktive Werte für die owner-bestätigten Home-Assistant-
  Input-/Legacy-Bindings müssen pro Installation über OptionsFlow gesetzt und
  fachlich bestätigt werden; der generische Laufzeitpfad ist implementiert;
- native Entity-Projektionen über die noch nicht freigegebene HA-Binding;
- die installierbare laufende Shadow-Auswertung und nutzbare Projektion sind
  technisch contract-getestet; reale HA-Live-Traces und feldweise
  Alt/Neu-Paritätsklassifikation müssen weiterhin als getrennte
  Installations-/Live-Evidence gesammelt werden;
- technische Migration alter Storage-/Override-Daten nach einem expliziten
  Verlustschutz-Contract;
- Cutover, Cover-Rename, produktiver Apply, Release und Live-Verifikation.

Diese offenen Punkte sind sichtbar dokumentiert und werden nicht durch
historische Entity-IDs oder private Topologie angenommen.

## 9. Gate-Status

Technische Tests und ein Draft-PR sind keine Live-Aussage. `Not Live` gilt
explizit bis zu Bennis getrennten Live-/Live-Verified-Gates.
