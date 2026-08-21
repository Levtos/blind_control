# Owner- und Contract-Matrix – Blind Control AP1

**Dokumentversion:** 0.1.0

> Die Abschnitte 1 bis 5 konservieren die historische AP1-Inventur und ihre
> damaligen offenen Punkte. Für AP2-Laufzeit und Installation ist ausschließlich
> der redigierte Contract ab Abschnitt 6, insbesondere 7.3, maßgeblich; die
> historischen IDs sind keine Suggestions oder Defaults.

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
| Cover position | same cover, `attributes.current_position`, special evidence-only record | device owner open | diagnostics/apply safety later | Source-/device timestamp from `device_timestamp`/`source_timestamp`/`measurement_timestamp`/`observed_at` required; HA-only state change is not enough; missing/stale position unknown | ungeklärt / Blocker |
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

## 6. AP2-Contracts

Der frühe AP2-Slice versioniert zusätzlich:

| Contract | Inhalt | Sicherheitsgrenze |
| --- | --- | --- |
| `blind_control.decision.v2` | Kandidaten, hierarchischer Gewinner, aktive/pausierte Äste, Failure-Quality, fachliches Ziel, Safety, Apply-Intent | kein ausführbarer Gerätepfad |
| `blind_control.shadow.v1` | Inputs, Trace, Legacy-Diffs und Shadow-Flags | `shadow_only=true`, `actuation_executed=false`, `write_path_reachable=false` |
| `blind_control.ux.v2` | laufende Snapshot-Projektion für Übersicht, Diagnose und OptionsFlow-Einstellungen | kein Geräte-/Cover-Command und kein Service-Pfad |
| `blind_control.automation_projection.v1` | kleine redigierte Automations-/Diagnoseprojektion über genau eine Sensorentität | kein Service, kein Gerätepfad |

Alle externen Inputwerte werden als `InputObservation` mit `source`,
`quality`, `reason` und optionalem Zeitbezug übergeben. Nur `fresh` ist für
positive fachliche oder technische Aussagen verwendbar. Die Fachmodule
erzeugen keine externe Rohwahrheit und enthalten keine produktiven Entity-IDs.
Die laufende HA-Anbindung liest ausschließlich über owner-konfigurierte
Bindings; fehlende oder stale Inputs bleiben sichtbar und werden nicht als
positive Werte ersetzt. Die UX erhält den aktuellen `blind_control.ux.v2`
Snapshot über den read-only WebSocket-Read-Pfad; Konfigurationsänderungen
werden ausschließlich als validierte ConfigEntry-/OptionsFlow-Daten gespeichert.

Das automatische Quality-Gate wird nicht durch ein schon gebildetes
fachliches Target umgangen. Sobald Temperatur, Activity/Belegung oder die
zwingende Solar-Kombination aus Sonnengeometrie und Außenlux nicht fresh und
vollständig belastbar ist, führt
das Ergebnis `quality_blockers[]` mit Feld, Quality und Reason und setzt den
Mastermodus auf `failure`. Damit ist ein `base_daylight`-Target kein
Öffnungsbefehl: die letzte nachweislich sichere Position wird gehalten oder
Apply bleibt blockiert.

`lux_trend`, `expected_direct_radiation`, `expected_diffuse_radiation` und
`cloud_cover` sind ersetzbare Evidence. Ihr Fehlen beziehungsweise ihre nicht
frische Quality blockiert nicht einzeln, solange Geometrie, Sonnenstand und
Außenlux die Solarentscheidung belastbar tragen. Der Solar-Contract enthält
`capabilities`, `missing_optional_capabilities`, `used_evidence`,
`derived_evidence`, `confidence` und `quality_blockers`. Ein intern abgeleiteter
Lux-Trend benötigt zwei verschiedene frische Lux-Zeitpunkte.

AP2 konkretisiert die Freshness feldweise: stabile Core-State-Contracts sind
nicht allein wegen eines alten `last_updated`-Werts stale; zeitkritische
Telemetrie und die Coverposition verwenden eine eigene Maximalalter-Policy und
benötigen die geforderte Timestamp-Evidence. Fehlende erforderliche Zeit-
Evidence bleibt `stale`. Jede Bindung führt Owner, `max_age_seconds` und
`require_timestamp` im effektiven Options-/UX-Contract.
Publizierte Owner-Qualität (`quality_status`, `quality`, `source_quality`,
`fresh`, `degraded`) wird vor der HA-Zeitprüfung ausgewertet; ein aktueller
HA-Zeitstempel kann deshalb ein degradiertes Owner-Signal nicht gesund machen.
Die feldspezifischen Defaultfenster entsprechen den realen Owner-Kadenzen und
können weiterhin pro Binding explizit kalibriert werden.

`activity_state = none` ist der blind-spezifische, aus Core State abgeleitete
Inaktivitätswert. `music` mit `pc_active=true` wird `pc`; `gaming` mit einer
TV-Konsole und `entertainment` werden `tv`. Die Präzedenz bei gleichzeitig
positiven Signalen lautet `tv > pc > screen > none`. Nur
`unknown` und `unavailable` sind globale HA-Sentinels; die fachliche
Gültigkeit übriger Strings bleibt feldspezifisch.

Presence verwendet ein gültiges `away_gate`-Attribut vorrangig. `away`,
`not_home`, `abwesend` bedeuten `true`; `home`, `zuhause` bedeuten `false`.
Unbekannte Werte werden `degraded`. Der Day-State-Contract umfasst exakt die
neun Owner-Werte; Tageslicht sind `early_morning`, `forenoon`, `midday`,
`afternoon`, `late_afternoon`, Übergang sind `evening`, `late_evening`, Nacht
sind `early_night`, `late_night`.

Der aktive Fremd-Override erhält einen deterministischen Context-Key aus den
explizit festgelegten Bio-, Activity-Gruppen-, Day-, Household- und Opening-
Feldern. Innerhalb desselben Keys bleibt der Override aktiv; ein Key-Wechsel
endet ihn mit `override_context_changed`, der Eintritt in kanonisches Waking
mit `waking_context_superseded`. Das ist ein Lifecycle-Ereignis, kein
heuristischer Zustandsersatz.

## 7. AP2 Decision- und UX-Contract v2

`blind_control.decision.v2` ersetzt für neue Consumer die flache
Entscheidungsdarstellung. `active_mode` und `winner_keys` bleiben nur
abwärtskompatible Diagnosefelder; sie dürfen nicht als alleinige
Entscheidungshierarchie interpretiert werden.

| Feld | Semantik |
| --- | --- |
| `master_mode` | ausschließlich `normal`, `manual` oder `failure` |
| `winner.category`, `winner.variant`, `winner.candidate_key`, `winner.target_position` | fachlicher Gewinner; `pc`/`tv` sind Varianten von `glare`, Climate-Varianten sind `heat`, `cold`, `storm`, `cool_air` |
| `active_branches[]` | nur fachlich aktive oder bewusst pausierte aktive Anforderungen mit Kategorie, Variante, Candidate-Key, `active`, `paused`, `winner`, Ziel, Quality, redigierter Source, Reason und `suppressed_by`; inaktive Diagnosekandidaten gehören nicht hinein |
| `failure.status`, `failure.reason`, `failure.hold_target`, `failure.quality_blockers[]` | konkrete Entscheidungsunfähigkeit mit allen fehlenden Quality-Evidences, Position halten oder Apply blockiert; kein unsichtbarer Open-Fallback |
| `fachlicher_target` | Ergebnis der unveränderten Minimum-Komposition kompatibler Anforderungen |
| `effective_target` | gehaltenes, technisch zugelassenes oder durch positiv bestätigte Safety bestimmtes Ziel |
| `safety`, `apply` | technische Entscheidungen, ausdrücklich getrennt vom fachlichen Mastermodus |

`normal` projiziert `neutral`, `waking`, `sleep`, `away`, `privacy`,
`glare -> general|tv|pc` oder `climate -> heat|cold|storm|cool_air`.
Waking pausiert die festgelegten Umweltäste sichtbar. Ein nachgewiesener
fremder Override liefert `manual -> override`; Safety und der festgelegte
Lifecycle können dessen effektives Ziel technisch überstimmen, ohne daraus
eine neue freie Automatik abzuleiten.

Failure wird nur bei fehlender belastbarer Entscheidungsgrundlage gesetzt; ein
bekannter neutraler Context bleibt `normal`. Bei Failure wird eine frische,
nachweislich sichere aktuelle oder letzte Position gehalten, sonst Apply
blockiert. Nur positive Opening-Safety darf das konfigurierte, achsenspezifische
Safety-Open-Profil freigeben. Opening-Quality `unknown`, `stale`,
`unavailable` oder `conflict` führt nie zu einer Öffnungsfahrt. Ebenso darf
`base_daylight` bei `missing`, `unknown`, `unavailable`, `stale` oder
`conflict` in Temperatur-, Activity-/Belegungs- und Lux-/Solar-Evidence keine
neue Öffnung auslösen.

`blind_control.ux.v2` enthält den v2-Entscheidungsbaum, die getrennte
technische Ebene, die flache Diagnoseansicht, Solar-/Quality-/Alt-Neu-Evidence
und den Settings-Status. Public Source-Werte werden zu Owner-Kategorien
redigiert; Bindings und Entity-IDs erscheinen nicht in Snapshot-,
WebSocket- oder Clipboard-Payloads.

### 7.1 Binding- und OptionsFlow-Contract

Bindings werden im nativen Home-Assistant-OptionsFlow ausschließlich über
`selector({"entity": {}})` verarbeitet. Die Sections heißen Core State,
Opening/Safety/Cover, Solar, Temperatur/Wetter und Legacy-Vergleich. Leere
optionale Werte werden beim Persistieren entfernt. Der WebSocket-Optionspfad
ist admin-geschützt, akzeptiert aber keine Binding-Mappings; dafür ist allein
der OptionsFlow zuständig. Die Panel-Projektion enthält für jedes Feld nur
`configured`, `requirement`, den unten definierten Binding-`status`,
Gruppen-Readiness, `owner`, `max_age_seconds` und `require_timestamp`.
`opening_safety_polarity` ist `unspecified`,
`positive_safe` oder `negative_unsafe`; nur die beiden expliziten Polaritäten
dürfen ein Kipp-Safety-Signal auswerten.

Ein Standard-Cover ist bei den Zuständen `open`, `closed`, `opening`, `closing`
oder `stopped` verfügbar; `unknown`/`unavailable` bleiben nicht nutzbar.
`cover_position` liest `current_position`. Ein expliziter Source-/Device-
Timestamp hat Vorrang, andernfalls ist der HA-Zeitstempel des Standard-Covers
zulässig. `restored` bleibt degradiert; fehlende Positions-Evidence blockiert
Apply und erfindet keine Position.

### 7.2 Kleine Automations-/Diagnoseprojektion

`blind_control.automation_projection.v1` ist ein read-only, versioniertes
Objekt mit `master_mode`, `active_category`, `active_variant`, kompatiblen
`winner_*`-Feldern, `failure_status`, `failure_reason`,
`failure_quality_blockers`, `fachlicher_target`, `effective_target`, Safety-,
Apply- und Shadow-Flags. Die Integration stellt exakt eine diagnostische native
Status-Sensorentität bereit. Deren Zustand ist `master_mode`; der übrige
redigierte Contract liegt in den Attributen. Sie erhält nur einen stabilen
Unique-ID-Suffix aus der ConfigEntry-Instanz, keine vorab erfundene Entity-ID,
und besitzt weder Service noch Write-/Coverpfad. WebSocket, Panel und Sensor
verwenden dieselbe redigierte Projektion.

### 7.3 AP2-Installations- und Suggestion-Contract

Der OptionsFlow hat exakt 88 sichtbare Felder: 23 allgemeine Defaults, 32
Positionsdefaults, 28 aktuelle Input-Bindings, vier optionale Legacy-Bindings
und eine Opening-Safety-Polarität. Die 55 Defaultfelder sind keine
Entity-Zuordnungen. Eine kleine installationslokale Discovery darf vorhandene
HA-States anhand publizierter Attribute und Source-Referenzen als
`suggested_value` anbieten. Sie ist keine Registry und persistiert keine zweite
Owner-Wahrheit. Reihenfolge: gespeicherte Nutzerwahl vor bewusst leerem Slot
vor neuem Contract-Vorschlag. Entity-IDs verlassen Config-/OptionsFlow nicht.

Statuswerte sind `required_resolved`, `required_unresolved`,
`conditional_resolved`, `conditional_unresolved`,
`conditional_not_applicable`, `optional_bound`,
`optional_intentionally_empty`, `legacy_bound` und
`legacy_not_available`.

| Feld | Klasse | Owner-/Wertvertrag | Einheit | Default-Freshness |
| --- | --- | --- | --- | --- |
| `bio_state` | required automatic | Core State, kanonischer Bio-State | Zustand | stateful, Owner-Quality |
| `activity_state` | required automatic | Core State plus blind-spezifischer Glare-Adapter | `none|screen|pc|tv` | stateful, Owner-Quality |
| `day_state` | required automatic | Core State, neun kanonische Phasen | Zustand | stateful, Owner-Quality |
| `day_context` | required automatic | Core State; `werktag|wochenende|frei` wird kanonisch adaptiert | Zustand | stateful, Owner-Quality |
| `away` | required automatic | Core State Presence; `away_gate` hat Vorrang | boolean, `true` = abwesend | stateful, Owner-Quality |
| `private_time` | required automatic | Core State Activity/Private-Attribut | boolean | stateful, Owner-Quality |
| `privacy` | required automatic | bestehender Privacy-Owner/-Kandidat | boolean | stateful, Owner-Quality |
| `outdoor_lux` | required automatic | lokaler normalisierter Außenlux | lx | 900 s, Timestamp plus Owner-Quality |
| `sun_elevation` | required automatic | geeigneter Sun2-State oder Standard-Sun-Attribut | Grad | 900 s, Timestamp erforderlich |
| `sun_azimuth` | required automatic | geeigneter Sun2-State oder Standard-Sun-Attribut | Grad | 900 s, Timestamp erforderlich |
| `indoor_temperature` | required automatic | bestehender Climate-Owner, `temperature` oder numerischer State | °C | 1800 s, Timestamp plus Owner-Quality |
| `outdoor_temperature` | required automatic | bestehender Weather-/Umwelt-Owner | °C | 1800 s, Timestamp plus Owner-Quality |
| `opening_state` | required technical | Opening Domain Owner, `closed|open|tilted` | Zustand | Timestamp erforderlich, nicht altersbegrenzt |
| `cover_available` | required technical | Standard-Cover-HA-Verfügbarkeit; `open|closed` sind verfügbar | boolean | Timestamp erforderlich, nicht altersbegrenzt |
| `cover_ready` | required technical | bestehender technischer Readiness-Owner | boolean | Timestamp erforderlich, nicht altersbegrenzt |
| `cover_position` | required technical | Standard-Cover `current_position` | % | 120 s, Source- oder HA-Timestamp |
| `opening_safe_for_blind` | conditional | Opening-Safety-Owner; nur mit expliziter positiver oder negativer Polarität | boolean safe | Timestamp erforderlich, nicht altersbegrenzt |
| `lux_trend` | optional | eigener Owner oder intern aus zwei frischen Luxpunkten abgeleitet | lx/Beobachtung | 900 s bei Binding |
| `expected_direct_radiation` | optional | HA-Core-REST-Projektion von `current.direct_normal_irradiance_instant` | W/m² | 1200 s bei Binding |
| `expected_diffuse_radiation` | optional | HA-Core-REST-Projektion von `current.diffuse_radiation_instant` | W/m² | 1200 s bei Binding |
| `cloud_cover` | optional | bestehender Weather-/Umwelt-Owner | % | 1800 s bei Binding |
| `indoor_temperature_trend` | optional | vorhandener Owner, sonst leer | °C/Trend | 1800 s bei Binding |
| `outdoor_temperature_trend` | optional | vorhandener Owner, sonst leer | °C/Trend | 1800 s bei Binding |
| `weather_alert` | optional | vorhandener Owner, sonst leer | boolean | 1800 s bei Binding |
| `precipitation_trend` | optional | vorhandener Owner, sonst leer | Owner-Einheit | 1800 s bei Binding |
| `wind_trend` | optional | vorhandener Owner, sonst leer | Owner-Einheit | 1800 s bei Binding |
| `pressure_trend` | optional | vorhandener Owner, sonst leer | Owner-Einheit | 1800 s bei Binding |
| `air_movement` | optional | vorhandener Owner, sonst leer | boolean | 1800 s bei Binding |
| `active_mode` | legacy optional | alte Policy-Diagnose | Zustand | 120 s, Timestamp erforderlich |
| `effective_target` | legacy optional | alte Policy-Diagnose | % | 120 s, Timestamp erforderlich |
| `safety_status` | legacy optional | alte Policy-Diagnose/Blockerprojektion | Zustand | 120 s, Timestamp erforderlich |
| `apply_status` | legacy optional | alte Policy-Diagnose/Applyprojektion | Zustand | 120 s, Timestamp erforderlich |

Die beiden Modellstrahlungswerte entstehen installationsseitig durch einen
gemeinsamen Home-Assistant-Core-REST-Abruf. Blind Control enthält weder
Open-Meteo-Client noch API-Key-, Forecast-, PV- oder Standortlogik. Der
vollständige koordinatenfreie Vertrag steht in
[OPEN_METEO_REST.md](OPEN_METEO_REST.md).
