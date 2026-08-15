# Owner- und Contract-Matrix – Blind Control AP1

**Dokumentversion:** 0.1.0

Diese Matrix bindet keine produktive ConfigEntry. Evidence-Matrix,
historische Entity-IDs und Live-Snapshots sind keine automatische
Aktivierungsfreigabe. Ein Feld ohne Owner-/Freshness-Nachweis bleibt
`ungeklärt / Blocker`.

## 1. Versionierte Leitverträge

| Contract | Version/Quelle | Owner | Blind-Verwendung | Unknown/stale/degraded/conflict |
| --- | --- | --- | --- | --- |
| Core-State Mapping | mapping contract v1.5.0, `benni-core-state` Mapping-Entscheid | Core State | Bio, Day, Context, Presence/Away als Konsument | kein Recompute; Quelle/Quality muss sichtbar bleiben |
| Activity Decision | activity decision v1.0.0, Core-State-Entscheid | Core State | Activity-/Media-/Gaming-Kontext | unknown/unavailable/stale/degraded gewinnt nicht; Reason bleibt sichtbar |
| Bio/Waking | Core-State Bio-/Waking-Lifecycle | Core State | `sensor.benni_core_state_bio_state`, `state=waking` bis `awake` | kein eigener Prewake-/Wake-Source; fehlender Zustand blockiert fachlich relevante Entscheidung |
| Opening | `opening.v1`, Core Contracts Published-/Evidence-Gate | Core Contracts / Opening Owner noch zu bestätigen | positive Öffnungs-/Safety-Evidence | physischer Zustand bei fehlender/staler/retained/restored/conflict-Evidence `unknown`, Fallback `reject` |
| Weather environment | `weather_environment.v1`, Source Binding Matrix v1 | technische Quellen-/Contract-Owner noch zu bestätigen | Outdoor-Temperatur, Wetterbeobachtung, optionale Helligkeit | Feldqualität getrennt; Required-Feld ohne zulässige Freshness blockiert |
| Technical device | `technical_device.v1`, Source Binding Matrix v1 | Core Contracts Evidence; Geräteowner offen | Cover-Availability/State nur diagnostisch | keine Positions-/Power-Inferenz; fehlende Evidence `unknown`/`reject` |

## 2. Input-Matrix

| Input/Feld | Konkrete Quelle / Version | Owner | Consumer | Freshness/Quality/Conflict-Semantik | Status |
| --- | --- | --- | --- | --- | --- |
| Bio State | `sensor.benni_core_state_bio_state`, Mapping v1.5.0 | Core State | Mode/Waking/Sleep | canonical; no alias; missing/stale not silently awake | übernommen |
| Activity State | `sensor.benni_core_state_activity_state`, Activity v1.0.0 | Core State | Media/Activity Modes | valid local candidate may win; rejected feed cannot win; reason/quality required | übernommen |
| Day State | `sensor.benni_core_state_day_state`, Mapping v1.5.0 | Core State | Grundzustand/solar windows | exact current nine-state vocabulary; unknown remains diagnosable | übernommen |
| Day Context | `sensor.benni_core_state_day_context`, Mapping v1.5.0 | Core State | weekday/weekend/holiday/vacation mapping | no local calendar rederive; missing is a gate | übernommen |
| Household presence | `sensor.benni_core_state_presence_household`, Mapping v1.5.0 | Core State | Away/Privacy context | no personal-vs-household recompute; quality visible | übernommen |
| Away | `binary_sensor.benni_core_state_presence_away`, Mapping v1.5.0 | Core State | Away mode | consume canonical projection; do not infer from missing presence | übernommen |
| Waking | `sensor.benni_core_state_bio_state`, value `waking`, Waking Lifecycle | Core State | exclusive Waking mode | 100 % default until `awake`; no separate prewake source | übernommen |
| Living Opening | `opening.v1`; living contact candidates in Core Contracts Matrix v1 | Opening/technical owner open | Safety/Climate/Blind | positive closed evidence only; unknown/stale/unavailable/conflict blocks; no silent open fallback | ungeklärt / Blocker |
| Cover device state | `cover.wohnbereich_thermo_verdunklungsrollo`, `technical_device.v1` evidence | device/Core Contracts evidence | diagnostics only | real device or non-retained event evidence; state vocabulary open | Evidence-only / Blocker |
| Cover position | same cover, `attributes.current_position`, special evidence-only record | device owner open | diagnostics/apply safety later | device timestamp required; HA-only state change is not enough; missing/stale position unknown | ungeklärt / Blocker |
| Cover availability | derived availability gate in `technical_device.v1` | Core Contracts gate; failure set open | Apply readiness later | safe default false only for availability; exact failure set open | ungeklärt / Blocker |
| External illuminance | Evidence candidate `sensor.garden_light_sensor_illuminance`, `weather_environment.v1` | source owner/timestamp open | blind Solar Exposure later | informational candidate, no old Lux hard gate, no hold-last-as-fresh | ungeklärt / Blocker |
| Sun elevation / raw sun | old config recorded `sun.sun`; no approved new contract binding | sun/source owner open | Solar Exposure later | no own raw sun truth; stale/missing blocks solar judgment | ungeklärt / Blocker |
| Room/outdoor temperatures | outdoor candidate `sensor.garden_climate_temperature`, `weather_environment.v1` | technical source owner open | Heat/Cold/Climate consumers | required outdoor field needs permitted fresh event/device timestamp; reject otherwise | ungeklärt / Blocker |
| Weather state/clouds/rain | `weather.dwd_home` weather-state evidence; no separate blind field contract for clouds/rain | weather owner open | Heat/Glare/Storm later | no implicit DWD attribute meaning; conflicts stay field-local and visible | ungeklärt / Blocker |
| Wind/gust/warnings | no binding in the read contracts | weather/safety owner open | `storm_approaching` later | separate decision and quality semantics required | ungeklärt / Blocker |
| Cool air | no approved binding | climate/weather owner open | `cool_air_available` later | separate from storm; no inferred inverse of temperature | ungeklärt / Blocker |
| Cold Insulation | policy-owned demand, no raw source decided | Blind Control later | environment stage | separate demand; no alias to Heat/Privacy | ungeklärt / Blocker |

## 3. Contract examples

### Waking

```text
source: sensor.benni_core_state_bio_state
contract: Core-State mapping v1.5.0 / Waking Lifecycle
when state == waking: exclusive=true, target=editable(default=100)
exit: canonical state becomes awake
fallback: no second wake source; missing/stale => diagnosed blocker
```

### Opening safety

```text
source: opening.v1 field opening_state
healthy evidence: positive, fresh, non-conflict source observations
closed assertion: allowed only from the positive closed contract result
missing/stale/retained/restore/conflict: opening_state=unknown, fallback=reject
consumer effect: safety gate blocks unsafe close/apply path
```

### Cover position

```text
source: cover.wohnbereich_thermo_verdunklungsrollo.attributes.current_position
contract: technical-device evidence-only special record
freshness: device timestamp required; HA-only state change is not enough
missing/stale: position=unknown, no target inference, no apply
```

## 4. Boundary rules

- A Core-State entity ID in this document is an external consumed contract,
  not a new `blind_control` entity.
- The Core Contracts kitchen-patio Published pilot is not silently reused as
  the living-room Opening binding.
- `cover.living_thermal_blind` is a later target identifier only; it is not
  present in AP1 code, ConfigEntry data, or live configuration.
- The old `cover.living_blackout_blind` identifier is historical evidence and
  is not a current source binding.
- No product Python code contains an entity ID, private URL, token, or apply
  call; the boundary is enforced by tests.

## 5. Gelesene verbindliche Quellen

- [control#31](https://github.com/Levtos/control/issues/31), [ADR 0001](https://github.com/Levtos/control/blob/main/docs/adr/0001-ux-frontend-standard.md) und [ADR 0002](https://github.com/Levtos/control/blob/main/docs/adr/0002-github-only-governance.md);
- [Core-State Entity-Mapping-Entscheid](https://github.com/Levtos/benni-core-state/blob/main/docs/architecture/2026-08-05-core-state-entity-mapping-decision.md), [Activity-State-Entscheid](https://github.com/Levtos/benni-core-state/blob/main/docs/architecture/2026-08-07-activity-state-decision.md), [Waking-Lifecycle](https://github.com/Levtos/benni-core-state/blob/main/docs/architecture/2026-08-06-waking-lifecycle-contract.md) und [Activity-Consumer-Inventar](https://github.com/Levtos/benni-core-state/blob/main/docs/architecture/2026-08-07-activity-state-consumer-inventory.md);
- [Core-Contracts-Architektur](https://github.com/Levtos/benni-core-contracts/blob/main/docs/architecture.md), [Source-Binding-Matrix v1](https://github.com/Levtos/benni-core-contracts/blob/main/docs/source-binding-matrix-v1.md) und [Published Opening Contract v1](https://github.com/Levtos/benni-core-contracts/blob/main/docs/published-opening-contract-v1.md);
- die historische [benni_blind_policy-Implementierung](https://github.com/Levtos/benni_blind_policy) sowie die gelesenen Issues [#4](https://github.com/Levtos/benni_blind_policy/issues/4), [#6](https://github.com/Levtos/benni_blind_policy/issues/6), [#8](https://github.com/Levtos/benni_blind_policy/issues/8), [#9](https://github.com/Levtos/benni_blind_policy/issues/9), [#10](https://github.com/Levtos/benni_blind_policy/issues/10), [#11](https://github.com/Levtos/benni_blind_policy/issues/11), [#12](https://github.com/Levtos/benni_blind_policy/issues/12) und [#13](https://github.com/Levtos/benni_blind_policy/issues/13);
- die historischen Releases [v0.8.2](https://github.com/Levtos/benni_blind_policy/releases/tag/v0.8.2), [v0.8.3](https://github.com/Levtos/benni_blind_policy/releases/tag/v0.8.3) und [v0.8.4](https://github.com/Levtos/benni_blind_policy/releases/tag/v0.8.4).
