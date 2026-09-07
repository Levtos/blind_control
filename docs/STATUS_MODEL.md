# Blind Control Statusmodell und Live-Shadow-Contracts

**Contract:** `blind_control.decision.v4`
**Status:** `Installed / Shadow / Not Live`

## Mastermodus und Hierarchie

Der Mastermodus ist ausschließlich:

- `normal`: belastbare automatische Auswertung;
- `manual`: nachgewiesener fremder Override hält die Position;
- `failure`: Input-, Freshness-, Quality- oder Contractlage ist nicht belastbar.

Unter `normal` bleibt der fachliche Pfad `category -> variant` getrennt von
Safety und Apply. Beispiele sind `glare -> pc`, `glare -> tv`,
`climate -> heat` und `climate -> cold`. Kompatible aktive Nebenäste bleiben
sichtbar; nur tatsächlich aktive Äste dürfen pausiert werden. Waking ist
exklusiv und pausiert ausschließlich aktive Heat-, Glare-, Privacy- und
Cold-Anforderungen. Der kanonische Core-State-Input private_time erhält keinen zusätzlichen Waking-Filter.

Failure erzeugt keine neue Fahrt. Die aktuelle oder letzte nachweislich sichere
Position wird gehalten und Apply bleibt blockiert. Ohne belastbare Position
wird Apply vollständig blockiert. Ein 100-%-Ziel ist kein Failure-Fallback;
nur positive Opening-Safety darf die logisch konfigurierte
Safety-Open-Position freigeben.

## Day-State-Kontext

Der Owner-Vertrag enthält exakt neun Phasen:

| Kontext | Phasen | Base-Daylight |
| --- | --- | --- |
| Tageslicht | `early_morning`, `forenoon`, `midday`, `afternoon`, `late_afternoon` | positiver Öffnungskandidat, sofern alle Gates belastbar sind |
| Übergang | `evening`, `late_evening` | neutral |
| Nacht | `early_night`, `late_night` | neutral |

Ein Daylight-State bei bestätigter Sonne unter dem Horizont ist ein
`day_solar_consistency`-Conflict und blockiert eine neue Öffnung.

## Presence und Activity

Presence wird feldspezifisch normalisiert. Ein gültiges `away_gate`-Attribut
hat Vorrang. `away`, `not_home`, `abwesend` bedeuten `away=true`; `home`,
`zuhause` bedeuten `away=false`. Unbekannte Werte werden `degraded`.

Der blind-spezifische Glare-Kontext konsumiert Core State, berechnet aber keinen
neuen globalen Activity State. Dokumentierte Zustände und Attribute werden mit
`tv > pc > screen > none` ausgewertet. TV-/Konsolenplattformen und
Entertainment werden `tv`, PC-Evidence wird `pc`, allgemeine Bildschirm-
Evidence wird `screen`. `music` allein ist `none`, löscht aber ein positives
`pc_active` oder `entertainment_active` nicht.

Die Activity-Quality bezieht sich auf die Evidence des ausgewählten Winners,
nicht auf irrelevante stale Kandidaten. Ein stale `private_time`-Contract wird
nicht zu `false` normalisiert, sondern bleibt als blockierende Evidence sichtbar.
Beim Core-State-Activity-Contract wird `private_time` separat aus der
Media-/Private-Time-Evidence bewertet. Ein frischer Media-Feed mit
kanonischem `private`-Attribut ist deshalb nutzbar, auch wenn eine
fachfremde Gesamtqualität in `activity_decision` unbekannt ist; stale,
unavailable, degraded oder conflict der tatsächlich verwendeten
Private-Time-Evidence bleibt blockierend.

## Mandatory und optionale Evidence

Zwingende automatische Owner-Wahrheiten sind Bio, Activity, Day State,
Day Context, Away, Private Time, Privacy sowie Innen-/Außentemperatur. Für eine
Tageslicht-Solarentscheidung sind Sonnenhöhe, Sonnenazimut und Außenlux die
zwingende Kombination.

Technisch zwingend sind Opening State, Cover Availability, technische
Cover-Readiness und Coverposition. `opening_safe_for_blind` ist bedingt: ohne
benötigte Kipp-Safety darf es `not applicable` bleiben, mit Binding ist eine
explizite Signalpolarität zwingend.

Lux-Trend, direkte/diffuse Modellstrahlung und Bewölkung sind optionale oder
ersetzbare Evidence. Ein ungebundener Lux-Trend wird aus zwei verschiedenen
frischen Luxbeobachtungen abgeleitet. Optionale Evidence erhöht Confidence und
erweitert Diagnose; ihr einzelnes Fehlen blockiert nicht, solange die gesamte
Kombination belastbar bleibt.

Direkte und diffuse Modellstrahlung folgen je Feld der Precedence `externes
Binding > interner Open-Meteo-Provider > missing/unavailable`. Ein gemeinsamer
Providerabruf speist beide Werte atomar; ein echter Nachtwert 0 ist fresh, ein
fehlgeschlagener Erstabruf unavailable, ein letzter Erfolg innerhalb der
Freshness-Grenze degraded/fresh und danach stale. Der Providerstatus ändert den
fachlichen Mastermodus nicht selbst, bleibt aber als Evidence-Quality sichtbar.

`SolarExposure` veröffentlicht redigiert:

- `capabilities` und `missing_optional_capabilities`;
- `used_evidence` und `derived_evidence`;
- `confidence` und `quality_blockers`.

## Technische Gates

Opening-Safety benötigt über `opening_safety_polarity` eine explizite Polarität:
`positive_safe` oder
`negative_unsafe`. `unspecified` blockiert eine Kippfreigabe. Entity-Namen
werden niemals zur Invertierung verwendet.

Ein Standard-Cover mit `open`, `closed`, `opening`, `closing` oder `stopped`
ist verfügbar, solange HA es nicht als `unavailable` markiert. Position kommt
aus `current_position`. Ein Source-/Device-Timestamp hat Vorrang; der normale
HA-Zeitstempel des Standard-Covers ist zulässig. Restore-Evidence ist
degradiert. Fehlende frische Positions-Evidence blockiert Apply.

Safety, Cover-Readiness, Apply und Shadow/Live überschreiben den fachlichen
Mastermodus nicht. Die einzige native Statusentität bleibt read-only und
redigiert. Im Shadow ist der Apply-Adapter technisch unerreichbar.

## Runtime und UX

Optionsänderungen verwenden unter HA 2026.8 `async_reload(entry_id)` und bauen
Coordinator, Listener, Timer, Snapshot und Statussensor aus den gespeicherten
Optionen neu auf. Das Panel entkoppelt Svelte-5-Proxies mit `$state.snapshot`
und einer JSON-förmigen Kopie. Polls überschreiben Dirty Drafts nicht;
Save-Fehler behalten lokale Änderungen, Save-Erfolg synchronisiert mit dem
bestätigten Serverstand.

Die OptionsFlow-Suggestion ist installationslokal und contract-basiert. Sie
ändert keine Runtime-Bindings, bevor Benni den Flow speichert, überschreibt
keine Nutzerwahl und respektiert bewusst leere optionale Slots. Die private
Open-Meteo-URL wird ausschließlich im nativen Flow gespeichert und nie in UX,
WebSocket, Sensorattribute oder Debug kopiert. Speichern lädt nur die
Blind-Control-ConfigEntry neu. Der alte Provider wird beendet; genau ein neuer
Coordinator-, Listener- und Timer-Satz übernimmt die URL. Zwei read-only
Irradiance-Sensoren und die bestehende Statusentität teilen sich das
Blind-Control-Gerät. Beide Sensorflächen bleiben read-only und besitzen keinen
Command-Pfad.

## AP3 Runtime- und Apply-Status

Der Mastermodus bleibt unverändert `normal|manual|failure`; technische Gates
dürfen ihn nicht überschreiben. `runtime_mode=shadow|live` und
`apply_owner=legacy|blind_control` sind getrennte technische Zustände.

Nur die Kombination `live + blind_control + apply_enabled` kann nach
erfolgreicher Safety-, Readiness-, Restart-, Override- und Cooldown-Prüfung
`write_path_reachable=true` erzeugen. Shadow und Legacy-Owner bleiben
fail-closed. `manual_hold` blockiert Automatik, während eine positiv belegte
Safety-Position Override und Cooldown überstimmen darf. Failure hält die
belegte Position ohne neuen Befehl und bleibt blockiert.

Der Apply-Lifecycle ist `blocked|manual_hold|cooldown|stable|shadow_ready|
live_ready|safety_ready|applied|error`. `applied` bedeutet, dass der isolierte
Adapter den freigegebenen HA-Aufruf angenommen hat; es ist keine Aussage über
`Live Verified`. Modus, Owner, Ausführungsstatus und Reachability werden über
`blind_control.automation_projection.v3` und `blind_control.ux.v4` redigiert
projiziert. Änderungen der drei kritischen Gates bleiben dem nativen
OptionsFlow vorbehalten.


## Bewegungs- und Positionscontract v0.6.0

Alle fachlichen und effektiven Ziele sowie cover_position sind logisch
(0 geschlossen / 100 offen). physical_target zeigt den erst am Adapter
invertierten Gerätewert. movement_status trennt Ruhe, Settling, eigene/fremde
Bewegung, fehlende Positions-Evidence und target_not_reached/command_error.
Ein Service-Dispatch ist keine Zielerreichung. Eigene Fahrt endet erst bei
stabiler tatsächlicher Zielposition in Ruhe; ein Timeout erzeugt keinen Override.
Restart während Bewegung wartet auf eine ruhende Baseline. Positive Opening-
Safety darf vorher aufwärts reagieren, sofern frische Positions-/Readiness-
Evidence und sämtliche Arming-Gates vorliegen.

Ein historisch identisches Ziel sperrt Safety nicht. Pending enthält nur den
aktuellen Gesamtentscheid, keinen später freizugebenden historischen Command.
Solar unknown bleibt auch bei einzeln frischen Inputs ein automatischer Blocker.
Config v6 / Cloud 0–100 / Cold-Lux-Gate: siehe CONTRACTS.md und MIGRATION.md.
