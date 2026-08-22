# AP2 Shadow-Vertical-Slice

**Stand:** 15. August 2026
**Status:** `Installed / Shadow / Not Live`; AP2-Nachbesserung im Draft-PR
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
        -> read-only WebSocket-/Panel-Projektion, OptionsFlow-Update
        -> eine native diagnostische Status-Sensorprojektion
```

`async_setup_entry` startet eine laufende, aber strikt nicht-aktuierende
Beobachtung. Entity IDs werden nicht im Produktcode erfunden, sondern als
Owner-Bindings über ConfigEntry/OptionsFlow gespeichert. Bei jeder gebundenen
  State-Änderung und zusätzlich über den Freshness-Timer wird ein neuer Snapshot
  berechnet und als `blind_control.ux.v2` im Runtime-Data-Projektionsobjekt
gehalten. Der WebSocket-Read-Befehl liefert genau diese Projektion; der einzige
UX-Update-Befehl validiert und speichert ausschließlich OptionsFlow-Konfiguration.
Die native Sensorentität erhält denselben redigierten Contract aus dem
Coordinator und schreibt nur bei einem neuen Snapshot ihren read-only Zustand.

## 2. Contracts und Ownership

| Bereich | Vertrag im Slice | Owner-Annahme | Verhalten bei fehlender Qualität |
| --- | --- | --- | --- |
| Bio/Waking, Activity, Day, Context, Away | `BlindControlInputs` | Core State; Blind Control konsumiert nur kanonische Werte | nicht fresh kann keine automatische Freigabe begründen; Quality-Gate/Fallback-Hold |
| Opening | `opening_state`, `opening_safe_for_blind` | Opening-/Core-Contracts-Owner, noch binding-offen | unknown, stale, conflict oder unavailable blockieren |
| Cover Availability/Readiness | technische Beobachtungen | technische Contract-Grenze | keine freigegebene Zielposition |
| Cover Position | `cover_position` | technischer Geräte-Contract | nur Diagnose/Baseline, keine Positionsinferenz |
| Sonne, Lux, Wettermodell | Solar-Input-Beobachtungen | jeweilige externe technische Owner | Solar `unknown`; kein Heat-/Open-Target wird technisch freigegeben |
| Temperatur, Wettertrends, Luftbewegung | Umweltbeobachtungen | jeweilige Umwelt-/Klima-Owner | fehlende Evidence sperrt jede neue automatische Öffnung über das Quality-Gate |

Owner-/Freshness-Annahmen sind explizit und pro Input gebunden. Nur
`InputQuality.FRESH` ist für positive fachliche und technische Aussagen
verwendbar. `degraded` ist sichtbar, aber nicht automatisch fresh. Ein
`closed`-Opening darf ausschließlich aus einer fresh, positiven Opening-
Beobachtung kommen.

Die Default-Policy trennt stabile Contract-Zustände von zeitkritischer
Telemetrie: Core-State-Werte werden nicht allein wegen ihres HA-Alters stale,
während Solar-, Wetter-, Temperatur- und Coverpositionswerte eine
feldspezifische Zeit-Evidence benötigen. Opening-/Readiness-Felder benötigen
mindestens einen zulässigen Contract-Zeitstempel, und fehlende geforderte
Timestamps bleiben konservativ `stale`. Für `cover_position` hat ein
Source-/Device-Zeitstempel aus `device_timestamp`, `source_timestamp`,
`measurement_timestamp` oder `observed_at` Vorrang. Bei einer Standard-Cover-
Entität ist alternativ HA-`last_updated`/`last_changed` zulässige Freshness-
Evidence; Restore-Marker bleiben degradiert. Jede Policy trägt Owner,
zulässiges Maximalalter und `require_timestamp`; einzelne Felder können diese
Defaults explizit überschreiben. Der Beobachtungstimer läuft höchstens mit der
Hälfte des kürzesten konfigurierten feldweisen Maximalalters.

Die Nachbesserung ab v0.4.2 wendet die Feld-Floors auch auf migrierte
ConfigEntry-Werte an: Solar/Lux mindestens 900 Sekunden, Temperatur/Wetter
mindestens 1800 Sekunden. Ein stabiler Owner-Messwert mit explizit gesunder
Owner-Quality bleibt verwendbar; sicherheitskritische Opening-, Readiness- und
Cover-Positionsfelder benötigen weiterhin ihre eigene Zeit-Evidence.

Die Binding-Prefill-Auswahl ist vollständig datengetrieben und deterministisch:
exakte Slugs und Rollen, Contract-Datentyp, Device Class und Owner-Attribute
werden vor der Entity-ID als Rangfolge verwendet. Ein generischer Blind- oder
Climate-Master ist kein Ersatz für den dedizierten Privacy- beziehungsweise
Indoor-Contract. Für `weather.*` wird das numerische Attribut `temperature`
als Outdoor-Temperatur unterstützt. Bei Activity zählt die Quality des
tatsächlichen Winners; stale Neben-Kandidaten bleiben Diagnose, solange der
Winner fresh ist. Stale Private-Time-Evidence wird nie als `false` verwendet.

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
- Das automatische Quality-Gate wird auch dann geprüft, wenn die
  Kandidatenkomposition bereits `base_daylight` oder ein anderes fachliches
  Target gebildet hat. `missing`, `unknown`, `unavailable`, `stale` oder
  `conflict` von Innen-/Außentemperatur, Activity/Belegung sowie der zwingenden
  Solar-Kombination aus Sonnengeometrie und Außenlux erzeugt `failure` mit
  `quality_blockers[]`; die sichere aktuelle/letzte Position wird gehalten,
  andernfalls Apply blockiert. Ein zufällig gehaltenes 100-%-Target ist kein
  neuer Öffnungsbefehl.
- Lux-Trend, direkte/diffuse Modellstrahlung und Bewölkung sind ersetzbare
  Zusatz-Evidence. Lux-Trend wird ohne eigenes Binding aus zwei verschiedenen
  frischen Luxbeobachtungen abgeleitet. Solar-Diagnose nennt Capabilities,
  fehlende optionale Capabilities, verwendete/abgeleitete Evidence, Confidence
  und tatsächliche Blocker.
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
forwardet ausschließlich die einzelne read-only Sensorplattform und registriert
keinen Service. Die Coordinator-Listener sind ausschließlich State-/
Zeitbeobachtung; der WebSocket-Transport liefert Snapshot-Daten oder validiert
OptionsFlow-Konfiguration. Der Boundary-Test prüft zusätzlich, dass kein
produktiver Cover-/Apply-Schreibpfad im Python-Paket vorhanden ist.
Konfigurationsspeicherung ist davon getrennt und betrifft niemals ein Gerät.

## 7. Legacy-Diff und UX-Contract

`ShadowCoordinator` liest für jede konfigurierte Legacy-Bindung die vier Felder
(`active_mode`, `effective_target`, `safety_status`, `apply_status`) und erzeugt
auch für eine fehlende/stale Beobachtung ein sichtbares Feld. `compare_legacy_snapshot`
klassifiziert feldweise als `expected`, `improved`, `unresolved` oder `error` und
trägt Quality/Source der Alt-Evidence mit. Fehlende Legacy-Bindings bleiben
explizit unkonfiguriert; Werte werden nicht aus der neuen Entscheidung erfunden.

`ux_contract.py` stellt `blind_control.ux.v2` für Übersicht, Diagnose und
Einstellungen bereit. Die Projektion enthält Mastermodus, Gewinnerkategorie
und -variante, effektives und fachliches Ziel, kompatible aktive oder pausierte
Äste, Solar-Diagnose, Quality/Reason, Alt/Neu-Diffs und editierbare
Nicht-Binding-Konfigurationswerte. `frontend/` wird als
`blind-control-panel.js` in der Integration ausgeliefert, über
`async_register_static_paths` erreichbar gemacht und als offizielles
HA-Custom-Panel registriert. Das Custom Element erhält den laufenden `hass`-
Context von HA; DOM-/Window-Probing ist kein Transportpfad. Die App lädt die
reale Projektion über `blind_control/get_snapshot`, pollt sie für laufende
Anzeige, speichert Nicht-Binding-Konfiguration über
`blind_control/update_options` und enthält keinen `sampleSnapshot`-
Produktpfad. Status-Badges stammen aus dem Snapshot, Coverposition und
Haushalt werden in der Übersicht gezeigt. Input- und Legacy-Bindings werden
allein über native Entity-Selectoren im OptionsFlow gepflegt, gruppiert als
Core State, Opening/Safety/Cover, Solar, Temperatur/Wetter und
Legacy-Vergleich. Die exakt 89 sichtbaren Felder bestehen aus 55 Defaults,
einer internen Open-Meteo-URL, 28 aktuellen Bindings, vier Legacy-Bindings und
einer Safety-Polarität. Der
Status unterscheidet `required_resolved|required_unresolved`,
`conditional_resolved|conditional_unresolved|conditional_not_applicable`,
`optional_bound|optional_intentionally_empty`,
`internal_provider_active|internal_provider_degraded|external_override_active`,
`provider_unavailable|provider_stale` und
`legacy_bound|legacy_not_available`. Leere optionale Slots sind bewusst leer;
konfigurierte Binding-Werte werden in der Snapshot-Projektion nie
zurückgegeben. Der Snapshot-Read und Options-Update sind admin-geschützt; der
WebSocket lehnt Binding-Mappings und die private Provider-URL ausdrücklich ab.
Source-, Legacy- und
Entity-Werte werden in der öffentlichen Projektion und in der Copy-Aktion
wertbasiert redigiert; die Copy-Aktion schreibt diese redigierte Debug-Evidence
in die Clipboard-API.

Bei einer neuen oder bestehenden Installation werden entdeckte, belastbare
Pflicht- und Conditional-Owner-Bindings als echte OptionsFlow-Defaults gesetzt;
das betrifft nicht die 55 Konfigurations-/Positionsdefaults. Ein bewusst
gewähltes Binding bleibt maßgeblich, und ein bewusst leeres Feld wird nicht
wieder vorgefüllt. Optionale Evidence bleibt ohne ausdrückliche Auswahl leer.
Für alte Entries ohne Provider-URL nutzt der Runtime-Start die aus den lokalen
HA-Standortdaten erzeugte URL nur vorübergehend. Nach erfolgreichem Abruf sind
die internen Strahlungssensoren verfügbar; bei fehlendem Standort, Erstfehler
oder abgelaufener Freshness bleiben sie sicher `unavailable` beziehungsweise
`stale`, ohne Defaultwert.

Der Einstellungsentwurf verwendet eine inhaltsbasierte Revision statt der
Objektidentität des alle fünf Sekunden neu empfangenen Snapshots. Ohne lokale
Änderung wird ein neuer Serverstand übernommen; während einer Bearbeitung
bleibt der Draft erhalten. Nach erfolgreichem Speichern wird er gegen den
bestätigten Serverstand bereinigt, bei einem Fehler bleibt er unverändert.

`blind_control.automation_projection.v1` wird zusätzlich über genau eine
native, diagnostische Status-Sensorentität in der Entity Registry veröffentlicht.
Ihr Zustand ist `master_mode` (`normal`, `manual`, `failure`); Attribute tragen
aktive Kategorie/Variante, Failure-Status/-Grund/-Blocker, Ziele,
Safety-/Apply-Blockade und die Shadow-Flags. Die Unique-ID wird aus der
ConfigEntry-Instanz abgeleitet, daher gibt es keine vorgegebene oder private
Entity-ID. Sensor, WebSocket und Panel nutzen die identische redigierte
Projektion. Die Sensorplattform besitzt weder Service noch Schreibpfad.

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
- eine native read-only Status-Sensorentität mit redigiertem
  `automation_projection.v1`-Contract, Registry-Lifecycle und keinen Services;
- echte Contracttests für State-Listener, Freshness-Timer, WebSocket-Read/
  Update/Admin-Gate, OptionsFlow-Reload und Panel-Registrierung;
- contract-basierte, installationslokale OptionsFlow-Suggestions ohne feste
  Entity-IDs oder zweite Registry; gespeicherte/geleerte Nutzerentscheidungen
  haben Vorrang;
- isolierter interner Open-Meteo-`DataUpdateCoordinator`: ein read-only Abruf
  liefert beide aktuellen Modellstrahlungswerte und speist zwei native
  Irradiance-Sensoren sowie die interne Evidence-Projektion;
- keine produktive Coverfahrt und keine alte Policy-Änderung.

### Für spätere AP2-Batches beziehungsweise vor Cutover offen

- die contract-basiert vorgeschlagenen produktiven Input-/Legacy-Bindings
  müssen von Benni im nativen OptionsFlow geprüft und gespeichert werden;
- Benni kann im nativen Blind-Control-OptionsFlow die aus dem HA-Standort
  vorgeschlagene Open-Meteo-URL prüfen und speichern oder eine eigene gültige
  URL einsetzen; alte Entries können bis dahin nur temporär im Runtime-Kontext
  arbeiten. YAML, Package und `secrets.yaml` sind ausdrücklich kein
  Installationsschritt;
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

## 10. Nachbesserung: Hierarchie, Failure und Thread-Safety

### Fachliche Darstellung

Der Decision-Contract ist `blind_control.decision.v2`. Sein Mastermodus ist
nur `normal`, `manual` oder `failure`. Er wird nicht für Safety, Apply,
Opening, Cover-Readiness oder Shadow/Live wiederverwendet. Unter `normal`
zeigt der Contract Kategorie und Variante (`glare -> general|tv|pc`,
`climate -> heat|cold|storm|cool_air`) sowie den Original-Candidate-Key. Die
Minimum-Komposition bleibt erhalten: Heat 15 % und PC-Glare 75 % werden als
`normal -> climate -> heat` mit aktivem Nebenast `glare -> pc` dargestellt.
Endet Heat, gewinnt PC-Glare. Waking bleibt exklusiv und hält die pausierten
Heat-, Glare-, Privacy- und Cold-Äste sichtbar, sofern sie vor der Pause
tatsächlich aktiv waren. Fachlich inaktive Diagnosekandidaten erscheinen nicht
als pausierte Nebenäste.

Ein nachgewiesener Override ist `manual -> override` und hält die Automatik;
das Apply-Gate bleibt absolut. `failure` steht ausschließlich für fehlende
Entscheidungsqualität oder Contractfehler. Es hält eine frische nachweislich
sichere aktuelle/letzte Position oder blockiert Apply. Es gibt dabei nie einen
stummen 100-%-Fallback. Nur positiv bestätigte Opening-Safety darf die
achsenspezifisch konfigurierte Safety-Open-Position freigeben. Ein bekannter
neutraler Context ohne Spezialkandidat bleibt `normal`. Ein schon bestehendes
fachliches Target überspringt das Quality-Gate nicht: unklare Temperatur-,
Activity-/Belegungs- oder Lux-/Solar-Evidence wird als
`failure.quality_blockers[]` ausgewiesen und sperrt eine neue automatische
Bewegung.

### Laufzeit- und Daten-Sicherheit

Der `ShadowCoordinator` markiert State-, Zeit- und Refresh-Callbacks als
Home-Assistant-Callbacks und reicht jede Task-Erzeugung über `hass.add_job`
beziehungsweise den Event Loop weiter. Dadurch ruft kein Callback aus einem
Worker-Thread direkt `hass.async_create_task` auf. Der entsprechende
Regressionstest simuliert den Worker-Callback bis zur tatsächlichen
Task-Erzeugung im HA-Loop.

Die kleine `blind_control.automation_projection.v1` veröffentlicht
Mastermodus, aktive Kategorie/-variante, Failure-Status/-Grund/-Blocker, Ziele,
Safety-/Apply-Status und Shadow-Flags. Sie wird über genau eine read-only
diagnostische Sensorentität sowie über UX/WebSocket angeboten. Die öffentliche
UX, Sensorattribute und Clipboard-Evidence sind entity-ID-redigiert; es gibt
keine Services und keinen Cover-/Apply-Schreibpfad.

## 11. Live-Shadow-Contract-Korrekturen

- Home Assistant 2026.8 lädt Optionsänderungen mit `async_reload(entry_id)`.
  Der Lifecycle-Test belegt Stop/Unload, genau einen neuen Listener-/Timer-Satz,
  neue Runtime-Optionen, aktualisierten Snapshot und Statussensor.
- Presence nutzt `away_gate` oder kanonische Home-/Away-Werte mit korrekter
  Away-Polarität. Activity adaptiert Core-State-State und dokumentierte
  Attribute in `tv > pc > screen > none`; `music` verdeckt PC-Evidence nicht.
- Day State verwendet exakt `early_night`, `late_night`, `early_morning`,
  `forenoon`, `midday`, `afternoon`, `late_afternoon`, `evening`,
  `late_evening`. Die ersten fünf Tagesphasen ab `early_morning` bis
  `late_afternoon` sind Daylight, Evening-Phasen Übergang, Night-Phasen Nacht.
- Opening-Safety-Polarität ist explizite OptionsFlow-Konfiguration. Standard-
  Cover-Verfügbarkeit folgt HA-Verfügbarkeit statt der Positionssemantik;
  `current_position` plus Source-/HA-Zeitstempel ist zulässig, Restore nicht.
- Das Panel entkoppelt Svelte-5-Deep-State mit `$state.snapshot` und einer
  JSON-förmigen Kopie. Poll, Save-Erfolg und Save-Fehler erhalten damit den
  kontrollierten Dirty-Draft-Vertrag ohne `DataCloneError`.

Der Status bleibt `Installed / Shadow / Not Live`. Diese Korrekturen führen
keinen HA-Reload, keine Coverfahrt und keinen Apply-Owner-Wechsel aus.

## 12. Installationsfähige Binding-Nachbesserung

Der OptionsFlow kann vorhandene Owner-Contracts read-only aus dem aktuellen
HA-Statebestand erkennen. Verwendet werden Contractattribute, Rollen und
Source-Referenzen; es gibt keine öffentliche oder zentrale Binding Registry.
Eine gespeicherte Nutzerwahl bleibt unverändert, ein explizit geleerter Slot
wird als `intentionally_empty` gemerkt und nicht erneut vorgeschlagen.
Suggestions werden erst durch Bennis OptionsFlow-Save zu Runtime-Bindings.

Die 16 Pflichtbindungen besitzen feste fachliche Ownerklassen: Core State für
Bio, Activity, Day, Day Context, Presence und Private Time; der bestehende
Privacy-Owner; Opening Domain Owner; Standard-Cover; technische Readiness;
lokaler Außenlux; geeigneter Sun-State; Climate- und Weather-Owner. Das
bedingte Kipp-Signal wird nur zusammen mit expliziter Polarität verwendet.
Fehlende optionale Trends bleiben bewusst leer. Lux-Trend kann weiterhin aus
zwei verschiedenen frischen Außenluxbeobachtungen entstehen.

Für aktuelle direkte und diffuse Modellstrahlung ist der öffentliche,
koordinatenfreie Vertrag in `docs/OPEN_METEO_REST.md` festgelegt. Blind Control
führt intern genau einen gemeinsamen Abruf im 15-Minuten-Rhythmus aus und liest
`current.direct_normal_irradiance_instant` sowie
`current.diffuse_radiation_instant`. Die private URL wird ausschließlich in der
ConfigEntry gespeichert und niemals in UX, Diagnose oder Logs projiziert. Die
beiden read-only Sensoren besitzen die stabilen `unique_id`-Werte
`blind_control_dni_instant` und `blind_control_diffuse_radiation_instant`.
Explizite externe Bindings haben Vorrang; ohne sie speist der interne Provider
beide weiterhin optionalen Confidence-Evidence-Felder. Ein Erstfehler ist
`unavailable`, ein letzter Erfolg wird nur innerhalb 1200 Sekunden genutzt und
danach `stale`; ein real gelieferter Nachtwert 0 bleibt gültig.

Der OptionsFlow umfasst damit 89 Felder: 24 allgemeine Konfigurations-/
Providerfelder, 32 Positionswerte, 28 Input-Bindings, vier Legacy-Bindings und
eine Opening-Safety-Polarität. 55 bestehende Defaultfelder plus das neue
Providerfeld sind keine Entity-Zuordnungsaufgaben. Die zwei Strahlungsbindings
sind bei gesundem internen Provider `internal_provider_active`; ein explizites
Entity-Binding wird `external_override_active`.

## 13. v0.4.3 Live-Contract-Korrekturen

Der Core-State-Activity-Contract veröffentlicht die Quality für `private_time`
über die tatsächlich verwendete Media-/Private-Time-Evidence. Ein frischer
Media-Feed mit kanonischem `private`-Attribut bleibt `fresh`, auch wenn
`activity_decision.quality_status` wegen fachfremder unbekannter
Homeoffice-/Haushaltsquellen `unknown` ist. Stale, unavailable, degraded oder
conflict der Media-/Private-Time-Evidence bleibt unverändert ein blockierender
Quality-Zustand; das allgemeine Quality-Gate wird nicht abgeschwächt.

Die Binding-Discovery erkennt dedizierte Privacy-Contracts zusätzlich über den
veröffentlichten Slug-Suffix `*_privacy_candidate` zusammen mit
`output_type=boolean`, booleschem `derived.privacy` und nicht degradiertem
Contract. Diese Contractklasse wird vor generischen Blind-Mastern priorisiert;
installationsspezifische Entity-IDs bleiben unbekannt und werden nicht im
Produktcode hinterlegt.
