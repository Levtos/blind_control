# AP2 Shadow-Vertical-Slice

**Stand:** 15. August 2026
**Status:** technische Umsetzung im Draft-PR, `Not Live`
**Scope:** `blind_control#2` / AP2, kein Cutover

## 1. Umgesetzter Pfad

```text
ConfigEntry / OptionsFlow
        -> BlindControlConfig mit expliziten Normal-/Invertiert-Werten
        -> owner-bound BlindControlInputs mit Source/Quality/Freshness
        -> Solar Exposure + DecisionEngine
        -> DecisionTrace mit Kandidaten, Winner, Pausen und Safety
        -> ShadowRuntime / ShadowSnapshot
        -> optionaler feldweiser Legacy-Diff
```

`async_setup_entry` erzeugt nur den initialen Snapshot aus einem leeren,
konservativen Input-Contract. Es werden keine Input-/Observation-Listener,
Plattformen, Services, WebSocket-Kommandos oder Apply-Pfade registriert. Der standardmäßige
OptionsFlow-Update-Listener lädt ausschließlich die read-only Shadow-Auswertung
neu; er führt keinen Gerätebefehl aus. Eine spätere Input-Bindung
muss einen ausdrücklich bestätigten Owner- und Freshness-Contract liefern.

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
  Glare hat kein gemeinsames Lux-Hard-Gate mit Heat.
- `cloud_shadow` beendet Heat bei fortbestehender thermischer Last nicht.
  Gewitter und nutzbare kühle Luft sind getrennte Cooling-Kandidaten.
- Vollständiges Öffnen braucht einen positiven Grund. Fehlende oder unsichere
  Daten führen nicht still auf 100 %.
- Ein vollständig offenes Fenster verwendet die konfigurierte Safety-Position;
  eine unsichere Kippstellung oder unbekannte Opening-Lage blockiert.

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
- beendet einen alten Override beim Eintritt in den kanonischen Waking-Kontext,
  damit er Waking nicht blockiert.

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
forwardet keine Plattform und registriert keinen Service/Listener. Der
Boundary-Test prüft zusätzlich, dass kein produktiver Cover-/Apply-Schreibpfad
im Python-Paket vorhanden ist. ConfigEntry-/OptionsFlow-Speicherung ist davon
getrennt und betrifft nur Konfiguration, niemals ein Gerät.

## 7. Legacy-Diff und UX-Contract

`compare_legacy_snapshot` vergleicht nur tatsächlich gelieferte Felder
(`active_mode`, `effective_target`, `safety_status`, `apply_status`) und
klassifiziert jede Differenz als `expected`, `improved`, `unresolved` oder
`error`. Fehlende Legacy-Evidence wird nicht erfunden.

`ux_contract.py` stellt `blind_control.ux.v1` für Übersicht, Diagnose und
Einstellungen bereit. Die Projektion enthält Gewinner, effektives Ziel,
Kandidaten, pausierte Äste, Solar-Diagnose, Quality/Reason, Diffs und alle
editierbaren Konfigurationswerte. Die aktuelle Svelte-5-Oberfläche unter
`frontend/` bindet ausschließlich an diesen Contract. Es gibt in AP2 keine
UI-Command-Oberfläche und keinen Gateway-Schreibpfad.

## 8. Implementiert und offen

### Implementiert

- früh installierbarer ConfigEntry-Shadow-Snapshot;
- versionierte Backend-, Trace-, UX- und Shadow-Contracts;
- konfigurierte Normal-/Invertiert-Profile und Achseninvertierung;
- Solar-Geometrie mit Golden-Vector-Regressionen;
- Minimum-Komposition, exklusives Waking, Heat/Glare, Storm/Cool-Air/Cold;
- Opening-Safety, positive Open-Gründe und Unknown/Stale-Blockierung;
- Override-, Restart-, Konfigurations- und Cooldown-Regressionsschutz;
- feldweiser Legacy-Diff ohne alte Integration zu importieren;
- contract-getriebene Svelte-5/Vite/TypeScript-Ansicht für Übersicht, Diagnose
  und lokale Einstellungen ohne Command-/Gateway-Schreibpfad;
- keine produktive Coverfahrt und keine alte Policy-Änderung.

### Für spätere AP2-Batches beziehungsweise vor Cutover offen

- konkrete, owner-bestätigte Home-Assistant-Input-Bindings für Wohnzimmer-
  Opening, Lux, Sonne, Wetter, Temperatur und Cover-Readiness;
- laufende HA-Observation/Coordinator-Anbindung an diese Contracts;
- konkrete, owner-bestätigte HA-Input-Bindings und ein schlankes UX-Gateway/
  Transport für die contract-getriebene Oberfläche gemäß ADR 0001;
- native Entity-Projektionen über die noch nicht freigegebene HA-Binding;
- reale Shadow-Traces und feldweise Alt/Neu-Paritätsklassifikation;
- technische Migration alter Storage-/Override-Daten nach einem expliziten
  Verlustschutz-Contract;
- Cutover, Cover-Rename, produktiver Apply, Release und Live-Verifikation.

Diese offenen Punkte sind sichtbar dokumentiert und werden nicht durch
historische Entity-IDs oder private Topologie angenommen.

## 9. Gate-Status

Technische Tests und ein Draft-PR sind keine Live-Aussage. `Not Live` gilt
explizit bis zu Bennis getrennten Live-/Live-Verified-Gates.
