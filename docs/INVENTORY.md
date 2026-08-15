# Ist-/Soll-Inventar – Blind Control AP1

**Dokumentversion:** 0.1.0

Die Bestandsaufnahme trennt den aktuellen/letzten Stand von
`benni_blind_policy`, die lokalen Einhornzentrale-Referenzen und das
entschiedene Ziel. Jede Zeile hat eine AP1-Klassifikation:

- **übernommen** – als dokumentierte Grenze oder Regression weitergeführt;
- **fachlich ersetzen** – Zielsemantik ist entschieden, aber der alte Pfad
  bleibt bis zu den Gates erhalten;
- **technisch neu lösen** – gleicher Bedarf, neuer Contract-/Runtime-Pfad;
- **bewusst verwerfen** – nicht Teil des Zielbilds;
- **ungeklärt / Blocker** – kein belastbarer Owner-/Fachentscheid; AP1 stoppt
  dort.

## 1. Repository-, Modul- und Lifecycle-Inventar

| Altfläche / Ist | Soll in `blind_control` | Klassifikation | AP1-Ergebnis |
| --- | --- | --- | --- |
| Repo-/Domainname `benni_blind_policy` | Repo/Domain `blind_control`, Produktname Blind Control | fachlich ersetzen | Manifest und ConfigEntry-Rahmen angelegt |
| `__init__.py`, ConfigEntry-Setup/Unload | minimaler native Setup-/Unload-Lifecycle | technisch neu lösen | implementiert, nur Bootstrap-State |
| `config_flow.py`: Profil-/Source-/Options-Schritte | zuerst leerer, testbarer AP1-User-Step; Quellen erst nach Matrixentscheidung | technisch neu lösen | implementiert, keine Entity-Auswahl |
| `const.py` und alte Modulkonstanten | nur `DOMAIN` im Bootstrap | bewusst verwerfen | keine alten Regeln/IDs übernommen |
| `coordinator.py` | späterer Blind-Control-Koordinator mit Contract-Snapshot | technisch neu lösen | nicht implementiert |
| `policy.py` / alte First-Match-Kette | versionierte fachliche Decision Engine mit Winner/Trace | fachlich ersetzen | nicht implementiert |
| `migration.py` | explizite Shadow-/Cutover-Migration | technisch neu lösen | nur Gate- und Mapping-Plan |
| `sensor.py`, `binary_sensor.py`, `switch.py` | spätere öffentliche/diagnostische Projektionen nach Contract-Entscheid | technisch neu lösen | keine Plattform in AP1 |
| `view.py`, statisches Panel, WebSocket | spätere ADR-0001-UX mit read-only Diagnose und getrennten Commands/Events | technisch neu lösen | kein Frontend/API in AP1 |
| `diagnostics.py` | owner-lokale, feldbezogene Diagnose mit Freshness/Quality/Root Cause | technisch neu lösen | Contract-Anforderungen dokumentiert |
| `storage.py` / alte Runtime-State-Datei | neues versioniertes Runtime-Schema erst nach Fachentscheid | technisch neu lösen | keine Migration/kein Storage in AP1 |
| `services.yaml` und alte Services | spätere explizite Apply-/Override-Commands | bewusst verwerfen | keine Services in AP1 |

## 2. ConfigEntry, Optionen und persistenter Zustand

| Altfläche / Ist | Bestand | Ziel/Klassifikation |
| --- | --- | --- |
| ConfigEntry | Version 3, Profil `benni`/`eltern`, Source-Bindings und Options `apply_enabled`, Startup-Block, Invert | technisch neu lösen; AP1 erstellt keine Alt-Datenmigration |
| OptionsFlow | Source-/Options-Menü, editable Profile und Apply-Flags | technisch neu lösen; Werte/Versionen erst nach Owner-/UX-Vertrag |
| Storage | Privacy-Latch, Thermal-State, Override, Timer, letzte Entscheidung/Position | fachlich ersetzen; nur nach Shadow-Paritätsvertrag übernehmen |
| Profilrouting | alte `benni`-/`eltern`-Trennung | bewusst verwerfen für AP1; Issue #1 scope ist der neue Benni-Zielpfad, Eltern ist kein impliziter Scope |
| Produktionsdefault `apply_enabled=true` im alten Live-Bericht | alter produktiver Stand | bewusst verwerfen für AP1; neuer Bootstrap ist nicht aktiv und hat kein Apply-Flag |

## 3. Entities, Devices, Services, Events und WebSocket

| Altfläche | Bekannter Zweck | Klassifikation |
| --- | --- | --- |
| Mode-/Position-/Debug-Sensor | Entscheidung, effektive Position, Trace/Debug | fachlich ersetzen; Zielvertrag offen, AP1 keine Entity |
| Lux-Gate-/Privacy-Latch-/Override-/Writing-/Apply-Blocked-Binaries | Diagnose und interne Policy-Zustände | technisch neu lösen; kein alter State wird als Ziel-Contract kopiert |
| Privacy-Bed, Alarm-Wakeup, Apply-Enabled, Invert-Schalter | alte Bedien-/Optionsoberfläche | fachlich ersetzen; `waking` ersetzt den alten Alarm-Wakeup-Platzhalter, UI später |
| `apply_now`, Privacy-Bed, Override, Position-Profile | Mutations-Services | technisch neu lösen; kein Service/keine Coverfahrt in AP1 |
| Status-WebSocket plus Mutations-Commands | Panel-Snapshot und Admin-Schreibpfade | technisch neu lösen; spätere Commands/Events bleiben getrennt |
| altes Panel `benni_blind_policy` | Produktive UI-/Gateway-Fläche | fachlich ersetzen; ADR-0001-Frontend später, kein Panel in AP1 |
| altes Device/Entity-Naming | `benni_`-Policy-Outputs | bewusst verwerfen im neuen Produkt; externe Core-/Legacy-IDs bleiben nur in Inventar/Contracts |

## 4. Inputs und Quellen

| Ist-Input / alte Bindung | Soll-Vertrag | Klassifikation |
| --- | --- | --- |
| Bio-/Sleep-State | Core State `sensor.benni_core_state_bio_state`, Mapping v1.5.0; `waking` ist ein kanonischer Zustand derselben Quelle | übernommen |
| Activity/Media/PC/Gaming | Core State Activity Decision v1.0.0; Media ist Feed, nicht zweiter Owner | übernommen |
| Day State/Day Context | Core State Mapping v1.5.0 mit aktuellem Neun-Phasen-Vertrag | übernommen |
| Personal-/Haushaltsanwesenheit/Away | Core State Mapping; kein Blind-Recompute | übernommen |
| alte Opening-Combined-/Unsafe-IDs | `opening.v1`/Opening Owner; positive geschlossene Evidence notwendig, konkrete Living-Binding noch nicht freigegeben | fachlich ersetzen / ungeklärt / Blocker |
| aktuelle Cover-Entity `cover.wohnbereich_thermo_verdunklungsrollo` | technische Device-/Cover-Evidence; Position nur Evidence-only bis Device-Timestamp-/Owner-Gate | übernommen / ungeklärt / Blocker |
| alte konkurrierende ID `cover.living_blackout_blind` | keine aktuelle Binding-ID; nur historische Dokument-/Rollback-Evidence | bewusst verwerfen als aktuelle Quelle |
| alte externe Lux-Konfiguration | Solar Exposure statt Lux-Hard-Gate; konkrete Lux-Owner-/Freshness-Bindung offen | fachlich ersetzen / ungeklärt / Blocker |
| `sun.sun`/Sun-Elevation | Rohsonnenquelle bleibt externer Owner; kein eigener Blind-Sun-State | ungeklärt / Blocker |
| Außentemperatur | `weather_environment.v1`, Evidence-Kandidat `sensor.garden_climate_temperature`; Timestamp-/Owner-Gate offen | übernommen / ungeklärt / Blocker |
| Wetterstatus | `weather_environment.v1` dokumentiert aktuell `weather.dwd_home`-Beobachtung; Owner-/Freshness-Semantik offen | übernommen / ungeklärt / Blocker |
| Clouds/Rain/Wind/Gust/Warnings | keine freigegebene Blind-Binding in den gelesenen Verträgen; getrennte fachliche Entscheidung erforderlich | ungeklärt / Blocker |
| Wärme-/Kälte-/Solar-Signale | Heat, Cold Insulation, Solar Exposure und Cool-Air müssen getrennt modelliert werden | fachlich ersetzen |

## 5. Decision Tree, Trace und Diagnose

| Alt | Soll | Klassifikation |
| --- | --- | --- |
| flache R1–R11-First-Match-Kette | Grundzustand → Modus → Umwelt → Safety → Apply, inklusive compatible-min und exklusivem `waking` | fachlich ersetzen |
| alte `RuleEval.position`-Default-Profilabweichung | effektive normal/invertierte Position pro Candidate/Winner | übernommen als Regression; Ziel später |
| Debug-Sensor/WS-Trace | Winner, effektives Ziel, Candidates, Suppressors, Reason, Quality/Freshness und Zeitstempel | technisch neu lösen |
| fehlende/unklare Fallbackdiagnose | positive Opening-Gründe; unknown/stale/degraded/conflict sichtbar und blockierend | fachlich ersetzen |
| Privacy-Latch als interner Zustand | Lifecycle mit Quelle, Session, Startzeit und Reset-Grund; keine implizite Wiederherstellung | technisch neu lösen |

## 6. Apply, Cooldown, Writing guard und Override-Lifecycle

| Altmechanismus | Soll | Klassifikation |
| --- | --- | --- |
| Cover-Service `set_cover_position` | späterer freigegebener Apply-Layer | bewusst verwerfen in AP1 |
| `apply_enabled`, Startup-Block, Apply-Blocker | explizite technische Readiness-Gates vor jeder Fahrt | technisch neu lösen |
| 60-Sekunden-Auto-Cooldown | nur mit fachlicher/technischer Begründung und Tests übernehmen | ungeklärt / Blocker |
| Writing-Active mit Grace/Timeout | Apply-owned Fahrt-/Echo-Schutz, nicht Policy-Wahrheit | technisch neu lösen |
| ±3%-Recent-Apply-Guard und Warden-Sweep | Override-Schutz als eigener, testbarer Lifecycle | technisch neu lösen |
| Manual Override | session-bound; Idle→TV neu, TV→PS/PC gleich; Sleep/Away/Waking/Window supersede ohne Restore | fachlich ersetzen |
| Cover unavailable/stale/blocked | keine sichere Schließfahrt; Diagnose/positive Öffnungsgründe gemäß Contract | fachlich ersetzen |

## 7. Startup und Readiness

| Ist | Soll/Klassifikation |
| --- | --- |
| alter Startup-Block und `startup_ready` im Coordinator | technische Readiness mit aktuellen Source-Observations und feldbezogener Quality; technisch neu lösen |
| alter Master-/System-Ready-Template-Pfad | Core-Devices-/Core-Contracts-Evidence nicht als Blind-Policy-Ersatz duplizieren; technisch neu lösen |
| Setup-Evaluation beim HA-Start | AP1 führt keine Evaluation aus; später nur nach explizitem Startup-/Freshness-Vertrag |
| HA-Restart-/Restore-Zustand | Restore ist nicht fresh; Shadow/Cutover-Gate erforderlich; übernommen als Stop-Bedingung |

## 8. Aktuelle Defaults und Release-/Testbasis

Die verbindliche AP1-Migrationsbasis steht im [Lastenheft](LASTENHEFT.md):
Window Safety 100/0, Privacy Bed 40/60, Waking 100/0, Sleep 5/60, Privacy
40/60, Heat 15/55, TV Glare 60/40, PC Glare 75/25, Open 100/0.

Der alte GitHub-Main-Stand ist Manifest `v0.8.4`. Die gelesene Releasefolge
bleibt als historische Regressionsevidenz sichtbar:

- `v0.8.2`: Heat/Glare als unabhängige `ProtectionDemand`-Grundlage;
- `v0.8.3`: Regression beim direkten Solar-/`late_afternoon`-Gate;
- `v0.8.4`: Midday-/Afternoon-Heat-Phasen.

Adoptierbare Regressionen aus dem alten Teststand und den Issues sind Privacy
Latch/Sleep, Latch-Reset, effektive Profilposition, Window Safety, Away gegen
Sleep/Waking, Waking 100 %, Heat/Glare, Override-Kontinuität und Apply-
Cooldown/Writing-Guard. AP1 testet nur Bootstrap-/Boundary-Verhalten; der
Policy-Testumfang gehört in die spätere vertikale Slice.

## 9. Bekannte Consumer des aktuellen Covers und alten Masters

Local-First-Suche in der Einhornzentrale-Arbeitskopie, ohne `.git`, `.storage`,
Logs und Datenbankdateien, ergab:

| Consumer/Fläche | Befund | Klassifikation |
| --- | --- | --- |
| `custom/homekit.yaml` | exponiert `cover.wohnbereich_thermo_verdunklungsrollo` mit Anzeige-Name | übernommen; kein Rename in AP1 |
| `benni_core_devices/import.yaml` | `living_rollo` bindet Cover-State, Position, Batterie, Charging, Running/Motor und leitet `cover_entity_id` ab | Core-Devices-Contract; nicht in Blind Control duplizieren |
| `packages/system/templates/readiness.yaml` | `System Rollo Ready` liest `sensor.benni_master_living_rollo` und dessen Readiness-/Cover-/Policy-Attribute | bekannter Master-Consumer; Cutover-Gate |
| `packages/system/manual_bio_scripts.yaml` | `system_bedtime_mode` ruft aktuell `benni_blind_policy.apply_now` nach `mark_sleep` auf | alter Apply-Consumer; bleibt bis Cutover unangetastet |
| historische Integrations-/Handoff-Dokumente | verweisen teils auf `cover.living_blackout_blind`, Toolbox und alte YAML-Apply-Pfade | bewusst als historische/konfliktäre Evidence markieren, nicht aktiv verdrahten |

Die Suche beweist keine weiteren HA-Registry- oder extern gespeicherten
ConfigEntry-Consumer. Diese bleiben vor Cutover separat zu prüfen. AP1 ändert
keinen der genannten Consumer.

## 10. Offene Stop-Punkte

- Owner und Version für Solar/Sun, Cloud/Rain/Wind/Gust/Warnings;
- belastbarer Freshness-/Device-Timestamp-Pfad für Cover-Position und
  technische Availability;
- vollständige Living-Opening-Quellmenge und freigegebener `opening.v1`-
  Consumer-Vertrag;
- Parität von Legacy-Storage/Override-/Apply-Lifecycle;
- vollständiges Consumer-Inventar vor Shadow/Cutover.
