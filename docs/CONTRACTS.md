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
| Bio State | `sensor.benni_core_state_bio_state`, Mapping v1.5.0 plus Core-State Issue #59 | Core State | Mode/Waking/Sleep | `effective_sleep = bio_state in {provisional_sleep, sleep}`; missing/stale not silently awake | übernommen |
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
Telemetrie und zeitbezogene Cover-Evidence verwenden eine eigene Maximalalter-Policy und
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
Der bestehende `sleep`-Zweig ist aktiv, wenn der kanonische Bio-State
`provisional_sleep` oder `sleep` ist. Beide Werte verwenden denselben
Candidate-Key und das konfigurierte Sleep-Profil; es gibt keinen lokalen
Pre-Sleep-State und keine separate Zielposition.
Waking pausiert die festgelegten Umweltäste sichtbar. Ein nachgewiesener
fremder Override liefert `manual -> override`; Safety und der festgelegte
Lifecycle können dessen effektives Ziel technisch überstimmen, ohne daraus
eine neue freie Automatik abzuleiten.

Failure wird nur bei fehlender belastbarer Entscheidungsgrundlage gesetzt; ein
bekannter neutraler Context bleibt `normal`. Bei Failure wird eine frische,
nachweislich sichere aktuelle oder letzte Position gehalten, sonst Apply
blockiert. Nur positive Opening-Safety darf das logisch konfigurierte
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
den HA-EntitySelector verarbeitet. Ab v0.7.2 akzeptiert dessen privater optionaler
Adapter zusätzlich explizites `null`/Leerstring zum Leeren eines Slots.
Nicht leere Werte behalten HA-Entity-/UUID-Validierung; der Picker bleibt
unverändert. Omission erhält bestehende Bindings, explizites Leeren setzt
`intentionally_empty`. Die Sections heißen Core State,
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
`cover_position` liest ausschließlich das numerische `current_position`.
Ab v0.6.2 ist ein gültiges ruhendes Standard-Cover (`open`, `closed`, `stopped`)
ohne expliziten Device-Timestamp eine stationäre technische Baseline:
sein HA-Zeitstempel muss vorhanden sein, wird aber nicht nach 120 s verworfen.
`last_updated` bezeichnet eine Änderung, keinen periodischen Gerätebericht.
Während `opening`/`closing` bleibt die Positions-Telemetrie altersbegrenzt.

Timestamp-Precedence: erstes vorhandenes Attribut aus `device_timestamp`,
`source_timestamp`, `measurement_timestamp`, `observed_at`; nur wenn keines
vorhanden ist, HA `last_updated` beziehungsweise `last_changed`.
Explizit stale Zeit-Evidence bleibt stale; ungültige explizite Evidence wird
degraded, zukünftige Cover-Timestamps conflict. Kein Rückfall auf einen
frischeren HA- oder nachrangigen Timestamp. Die vorhandene Binding-TTL
(Default 120 s) bleibt für explizite Zeit-Evidence und bewegte Position gültig.

`cover_motion` liest denselben semantischen HA-Cover-State mit eigener Quality;
fehlende/ungültige numerische Position löscht keine bekannte Motion. Ohne
explizite Zeit-Evidence altert Motion nicht allein mit dem HA-Änderungszeitpunkt.
Negative allgemeine Owner-Quality, restored und ungültige Cover-States bleiben
für beide blockierend; explizite Device-Timestamps gelten auch für Motion.
Motion allein erlaubt keine Baseline oder Fahrt: der Coordinator benötigt
weiterhin **Position und Motion usable**, danach die vorhandene Ruhe-/Settling-
Evidence. `unknown`/`unavailable`, fehlende Position, boolesche/nicht endliche
Werte und Werte außerhalb 0–100 bleiben unbrauchbar; Bereichsfehler sind conflict.
Axis Inversion transformiert nur Zahlen, niemals Motion-Strings.
Keine Position wird aus `open` oder `closed` erfunden, kein neuer Device-Owner.

Readiness ab v0.7.1: Ein positiver technischer Readiness-Owner darf seine
allgemeine Wetter-Aggregatqualität projizieren, ohne damit Cover-Readiness
zu entwerten. Die eng begrenzte Adaption verlangt `cover_available=true`,
`policy_context_ready=true`, eine endliche numerische `current_position` in
0–100, keine fehlenden Sources und ausschließlich explizite Wettergründe
(`weather_contract_degraded`/`weather_degraded`). Feldspezifische
`cover_ready_quality`/`readiness_quality` bleiben vorrangig; andere negative
Quality oder gemischte Fehler werden nicht ignoriert. `off`, restored,
unknown/unavailable und erforderliche Timestamp-Evidence bleiben unverändert.
Die unabhängige aktuelle Cover-/Opening-/Baseline-Prüfung bleibt zwingend.

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

Der OptionsFlow hat exakt 89 sichtbare Felder: 24 allgemeine Konfigurations-
und Providerfelder, 32
Positionsdefaults, 28 aktuelle Input-Bindings, vier optionale Legacy-Bindings
und eine Opening-Safety-Polarität. Die 55 bisherigen Defaultfelder sind keine
Entity-Zuordnungen. Eine kleine installationslokale Discovery darf vorhandene
HA-States anhand publizierter Attribute und Source-Referenzen als
`suggested_value` anbieten und belastbare required/conditional Bindings als
echte Formular-Defaults vorausfüllen. Sie ist keine Registry und persistiert
keine zweite Owner-Wahrheit. Reihenfolge: gespeicherte Nutzerwahl vor bewusst
leerem Slot vor neuem Contract-Vorschlag; optionale Vorschläge werden nicht
ohne Nutzerbestätigung gebunden. Entity-IDs verlassen Config-/OptionsFlow nicht.

Statuswerte sind `required_resolved`, `required_unresolved`,
`conditional_resolved`, `conditional_unresolved`,
`conditional_not_applicable`, `optional_bound`,
`optional_intentionally_empty`, `internal_provider_active`,
`internal_provider_degraded`, `external_override_active`,
`provider_unavailable`, `provider_stale`, `legacy_bound` und
`legacy_not_available`. Die Providerstatuswerte gelten nur für die beiden
Modellstrahlungsfelder und enthalten keine URL oder Koordinaten.

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
| `cover_position` | required technical | Standard-Cover `current_position` | % | explizite/bewegte Telemetrie 120 s; stationäre HA-Baseline gemäß 7.1 nicht altersbegrenzt |
| `opening_safe_for_blind` | conditional | Opening-Safety-Owner; nur mit expliziter positiver oder negativer Polarität | boolean safe | Timestamp erforderlich, nicht altersbegrenzt |
| `lux_trend` | optional | eigener Owner oder intern aus zwei frischen Luxpunkten abgeleitet | lx/Beobachtung | 900 s bei Binding |
| `expected_direct_radiation` | optional | externes Binding vor internem Providerfeld `current.direct_normal_irradiance_instant` | W/m² | 1200 s |
| `expected_diffuse_radiation` | optional | externes Binding vor internem Providerfeld `current.diffuse_radiation_instant` | W/m² | 1200 s |
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

Die beiden Modellstrahlungswerte entstehen durch genau einen gemeinsamen,
internen und read-only Open-Meteo-Abruf. Die Provider-URL lebt ausschließlich
in ConfigEntry/OptionsFlow; es gibt keine YAML-, Package-, Secret-, API-Key-,
PV- oder Weather-State-Konfiguration. Der Provider veröffentlicht zwei native
Irradiance-Sensoren und speist automatisch denselben Datenstand in die Inputs.
Pro Feld gilt `externes Binding > interner Provider > missing/unavailable`.
Ein echter Wert 0 bleibt fresh; ein fehlgeschlagener Erstabruf ist unavailable,
ein letzter Erfolg wird nach 1200 Sekunden stale. Der vollständige öffentliche,
koordinatenfreie Vertrag steht in [OPEN_METEO_REST.md](OPEN_METEO_REST.md).
Entries ohne gespeicherte Provider-URL dürfen die aus den lokalen HA-
Standortdaten erzeugte URL bis zur bestätigten OptionsFlow-Speicherung nur im
Runtime-Kontext verwenden; fehlender Standort bleibt `provider_unavailable`.

### AP2 Quality-Gate-Nachbesserung v0.4.2

Die effektive Binding-Policy ist migrationssicher: historische Werte von 120
Sekunden dürfen die Mindestfenster nicht verkürzen. Außenlux, Sonnenhöhe und
Sonnenazimut haben mindestens 900 Sekunden; Temperatur- und Wetterfelder haben
mindestens 1800 Sekunden. Der Timer verwendet ausschließlich tatsächlich
gebundene Felder und bleibt durch den technischen 300-Sekunden-Cap ein
Refresh-Scheduler, kein abweichender Qualitätsvertrag.

Eine belastbare Owner-Quality (`healthy`, `available`, `operational` oder
`fresh`) darf einen stabilen Messwert nicht allein wegen unverändertem HA-
Zeitstempel stale machen. Das gilt nicht für sicherheitskritische Opening-,
Readiness- und Cover-Positionsfelder; dort bleibt die geforderte Zeit-Evidence
maßgeblich, für stationäre Standard-Cover mit der v0.6.2-Semantik aus 7.1.
Ein explizit `stale`, `unknown`, `unavailable`, `degraded` oder
`conflict` gemeldeter Owner bleibt blockierend.

Die Discovery ist eine deterministische, installationslokale Suggestion und
keine Registry. Sie bewertet alle Kandidaten und sortiert nach exakt
veröffentlichtem Slug/Rolle, Contract-Datentyp, Device Class und Owner-
Attributen; die Entity-ID ist nur der stabile Tie-Breaker. Privacy benötigt
einen dedizierten booleschen Privacy-Contract, Indoor-Temperatur einen
kanonischen numerischen Indoor-Contract und Outdoor-Temperatur entweder einen
kanonischen numerischen Outdoor-Contract oder bei `weather.*` das numerische
Attribut `temperature`. Die Reihenfolge der HA-State-Liste beeinflusst die
Vorauswahl nicht.

Activity bewertet die Quality der tatsächlich gewinnenden Evidence. Stale
Kandidaten, die nicht zum Winner beitragen, entwerten keinen frischen Winner.
Stale Private-Time-Evidence wird dagegen nicht als `false` weitergereicht;
der Wert bleibt unbrauchbar und blockiert die automatische Entscheidung.

Für `private_time` ist die Quality feldspezifisch: `private_time_quality`,
`private_quality`, `media_activity_feed_quality` beziehungsweise die
entsprechende Feed-Freshness und explizite Private-Time-Evidence haben Vorrang.
Eine frische Media-Feed-Evidence mit kanonischem `private`-Attribut bleibt
fresh, auch wenn `activity_decision.quality_status` wegen fachfremder
Homeoffice-/Haushaltsquellen `unknown` meldet. Stale, unavailable, degraded
oder conflict der Media-/Private-Time-Evidence bleibt ein Quality-Blocker;
die allgemeine Activity-Quality-Regel wird dadurch nicht abgeschwächt.

Dedizierte Privacy-Contracts werden vor generischen Blind-Mastern gewählt.
Zusätzlich zu den exakten Privacy-Slugs akzeptiert die Discovery einen
veröffentlichten Contract mit Slug-Suffix `*_privacy_candidate`,
`output_type=boolean`, booleschem `derived.privacy` und nicht degradiertem
Contract. Die Entity-ID ist weiterhin nur ein Tie-Breaker und wird nicht
produktseitig fest codiert.

## 8. AP3 Decision-, Runtime- und Apply-Contract

| Contract | Inhalt | Schreibgrenze |
| --- | --- | --- |
| blind_control.decision.v4 | Hierarchie, logische Kandidaten/Ziele, Quality/Safety/Apply | pure Entscheidung |
| blind_control.runtime.v3 | unveränderlicher Snapshot, physical_target, movement_status | kein eigener Writer |
| blind_control.ux.v4 | redigierte Projektion und ein logischer Profilwert | kein Command-Pfad |
| blind_control.automation_projection.v3 | read-only Statusattribute inklusive Modus, Owner und Bewegung | keine steuernde Entity |

Config v6: je Profil {logical}; alte Normal-Werte sind Migrationsbasis,
alte Paare bleiben als legacy_profile_values erhalten. Eingehende
Geräteposition wird numerisch normalisiert; opening/closing bleiben semantisch
unverändert. Ausgehendes fertig
bestimmtes Ziel wird allein am Adapter gegebenenfalls zu 100 - logical.
Invertierung verändert keine fachliche Arbitration.

Cloud Cover ist 0–100 %, Werte außerhalb werden conflict und unbrauchbar.
cloud_cover_threshold Default 75 %, alte cloud_shadow_ratio mal 100.
model_lux_ratio ist separat ein dimensionsloses Helligkeitsverhältnis.
Solar-Aggregat unknown blockiert normale Aktuation ohne neuen Open-Fallback.

Ab v0.6.3 ist `low_light` ein zusätzlicher valider Solarzustand. Bei vorhandenen,
freshen Pflichtwerten (Sonnenhöhe -90..90°, Azimut 0..360°, Lux >= 0, endlich)
und bekannter Geometrie wird der verbleibende niedrige Energie-Fall nicht mehr
`unknown`. Beispiel 299 lx / 5.88° / 88.07° / DNI 0 / Diffus 2.1 ergibt low_light.
Die bestehenden Klassifikationen night, solar_not_on_window, cloud_shadow,
direct_sun und diffuse_bright behalten ihre Bedeutung und Reihenfolge.
Pflicht-Evidence wird vor jeder Klassifikation geprüft; missing/stale/conflict
bleibt unknown, auch bei niedrigen Lux oder Sonnenhöhe unter dem Horizont.
Optionale Evidence bleibt ersetzbar. Low light erlaubt die normale aktuelle
Arbitration, besitzt keinen eigenen Kandidaten und hebt keine technischen Gates auf.

Cold benötigt zum Eintritt frischen Lux < cold_lux_enter_threshold (Default 400) und frische
Außentemperatur <= cold_outdoor_threshold (Default 8). Off-Window allein
reicht nicht. Bereits aktives Cold hält bis Lux > cold_lux_exit_threshold
(Default 500); Eintritt/Entlastung werden 10/120 s stabilisiert. Heat/Glare
verwenden getrennte Confidence-/Inzidenz-Haltebänder mit Faktor 0.8 und dieselben
Zeiten. Alle Werte sind konfigurierbar; LASTENHEFT Abschnitt 17 ist normativ.
Temperaturtrendfelder bleiben v1-Diagnose / mögliche v2-Arbeit,
ohne erfundene Einheit, Schwelle oder Gewichtung.
private_time bleibt Core-State-Wahrheit; kein zusätzlicher Waking-Filter.

Ein auswertbarer automatischer Zielwert braucht gleichzeitig:
belastbare Inputs, Safety, Readiness, stabile Restart-Baseline, keinen
blockierenden Override, Automation/Apply an, live + blind_control, Ruhe-/
Zielstabilität, Cooldown und ein Cover-Binding. Positive Opening-Safety
darf Override, Waking, normale Ruhe-Baseline und Cooldown überstimmen;
frische Position, Readiness und Arming bleiben zwingend.
Bei open ist das logische Safety-Ziel mindestens Istposition, nie abwärts.

ApplyDecision.status: blocked, manual_hold, cooldown, stable, shadow_ready,
live_ready, safety_ready, applied, error. Nur live_ready/safety_ready mit
unverbrauchter aktueller Freigabe erreichen den Adapter. Er überprüft Runtime-
Lebensdauer, Konfigurationsidentität und live/owner/apply unmittelbar erneut.
Gestoppte Runtimes bleiben widerrufen. Ein Snapshot ist höchstens einmal nutzbar.

movement_status unterscheidet baseline_pending, idle, settling, external_moving,
own_moving, own_settling, target_not_reached, command_error und position_unavailable.
Normale eigene Fahrt endet am tatsächlichen Ziel innerhalb Toleranz und in
bestätigter Ruhe. Bei command_error/target_not_reached bleibt Attribution
bis zu einem neuen stabilen Ruhefenster erhalten (movement_recovery_seconds,
Default 30 s, mindestens position_settle_seconds). Dann wird der Vorgang
abgebrochen und die tatsächliche Position zur Baseline. Kein Manual Override,
kein Nachholen des alten Ziels. movement_error hält den letzten Fehler,
recovery_status unterscheidet none, waiting_for_quiet, superseded_by_safety
und recovered. Diese additiven Diagnosefelder stehen in Runtime/UX/Statussensor.
Ein Servicefehler beweist nicht, dass kein Befehl beim Gerät ankam.
applied bestätigt HA-Handler-Erfolg mit blocking=True, nicht Zielerreichung
oder Live Verified; Exceptions erzeugen error und keinen erfolgreichen Cooldown.

Nur aktuelle Istnähe verhindert einen identischen Write. Cooldown startet bei
Handler-Erfolg; die aktuelle Gesamtentscheidung ersetzt Pending. Safety darf nach
erneuter Istabweichung dasselbe Ziel anfordern oder eine Abwärtsfahrt ersetzen.

Private Bindings/URLs erscheinen nicht öffentlich. Ab v0.7.0 sind runtime_mode,
apply_owner und apply_enabled zusätzlich im administrativen Panel bedienbar.
Staging, Revisionsprüfung und Legacy-Interlock: [AP3_OPERATOR.md](AP3_OPERATOR.md).
apply_owner=blind_control ist kein globaler fremder Writer-Lock:
AP3_CUTOVER.md verlangt vollständig deaktivierte Legacy plus HA-Prozessneustart.

Runtime/UX ergänzen `baseline_position` und `baseline_ready` aus dem tatsächlichen
OverrideTracker. Die `override.baseline` ist dagegen nur Teil eines aktiven
Fremd-Override-Nachweises. Baseline ready bedeutet initialisiert, nicht automatisch
fahrbereit: Quality, aktuelle Position/Motion, Recovery und übrige Gates gelten.
Die Übersicht zeigt bestätigte Optionswerte, Apply-Schalter, tatsächliche Baseline,
Schreibpfad und den konkreten Apply-Grund. Keine private Config wird projiziert.
Core Contracts ist ab v0.7.0 für vorhandene v1-Schemas primär angebunden;
die verbindliche Feldmatrix, Quality-Grenze und offenen Rollen stehen in
[AP3_OPERATOR.md](AP3_OPERATOR.md). Frühere Verschiebungsentscheidungen sind damit ersetzt.

Runtime environment und UX diagnosis.environment zeigen je heat/glare/cold
active, pending (boolean oder null) und since (monotone Startzeit oder null).
Es sind keine Zielcommands. environment_protection_stabilizing blockiert eine
weiter öffnende Freigabe während des Eintritts eines schließenden Schutzes;
Quality/Safety/Override und die harten Betriebs-/Writer-Gates bleiben vorrangig.
