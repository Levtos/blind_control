# Architektur – Blind Control AP1

**Dokumentversion:** 0.1.0

## 1. Zielbild

Blind Control wird eine eigenständige Home Assistant Integration mit internem
Policy-/Apply-Schnitt. Die fachliche Berechnung gehört in Blind Control; rohe
technische Fakten und kanonische Zustände werden von ihren Ownern bezogen.

```text
Home Assistant raw entities
        |
        v
Core State / Core Contracts (owner-bound, versioned, quality/freshness)
        |
        v
Blind Control: Grundzustand -> Modus -> Umwelt -> Safety -> Apply
        |                                      |
        |                                      +--> later: owning actuator path
        +--> later: effective target / winner / trace / diagnostics
```

AP1 realisiert davon nur den ConfigEntry-Lifecycle:

```text
ConfigEntry -> blind_control bootstrap bucket -> unload removes bucket
```

Es wird keine HA-Plattform weitergeleitet, kein Service registriert, kein
WebSocket-Befehl registriert, kein Listener angeschlossen und kein Cover
angesprochen.

## 2. Ownership-Grenzen

### Core State

Core State ist Owner von Bio-/Sleep-/Waking-, Activity-, Presence-, Away- und
Day-State-Verträgen. Blind Control konsumiert diese Verträge und rekonstruiert
keinen zweiten Activity-, Sleep-, Waking- oder Presence-State.

### Core Contracts

Core Contracts liefert technische Fakten mit Quelle, Freshness, Quality,
Fallback und Safety. `opening.v1` bleibt feldbezogen; bei fehlender belastbarer
Evidence wird kein positiver physischer Zustand erfunden. Der veröffentlichte
Küchen-Terrassentür-Pilot ist kein automatisch freigegebener Wohnzimmer-
Opening-Vertrag.

### Blind Control

Blind Control besitzt später die Blind-spezifische Entscheidung, den Gewinner,
das effektive Ziel, die Unterdrückungs-/Reason-Kette, Konfiguration, Override-
Lebensdauer und die Apply-Gates. Es besitzt nicht die rohen Lux-, Sonnen-,
Wetter-, Temperatur- oder Opening-Wahrheiten.

### Apply

Der spätere Apply-Pfad führt eine freigegebene Entscheidung sicher zum
Actuator. Apply ist nicht Teil von AP1. Ein separates `blind_apply` oder
`core_apply` wird in AP1 nicht angelegt.

## 3. Vertragsschichten

Jeder zukünftige Input braucht vor Implementierung:

1. konkreten Owner und Vertrags-/Mapping-Version;
2. konkrete Quelle oder bewusst offene Quelle;
3. Consumer und Feldsemantik;
4. Freshness-/Quality-/Conflict-Regeln;
5. Verhalten bei unknown, unavailable, stale, degraded und restore;
6. einen negativen Test für den jeweiligen Safety-/Fallback-Fall.

Eine dokumentierte Evidence-Kandidatur ist keine produktive Binding-
Autorisierung. Besonders Cover-Position und Opening-Safety bleiben solange
blockiert, bis der jeweilige Owner-/Freshness-Nachweis vorliegt.

## 4. UX- und Sicherheitsrahmen

Eine spätere UI folgt ADR 0001: Svelte 5, Vite, TypeScript, statischer Bundle-
und Gateway-Schnitt, versionierte typed Contracts, explizite Statuswerte,
Graphite Dark, Tastatur-/Touch-Ziele, Fokus und Reduced Motion. AP1 enthält
kein Frontend und startet keine Preview- oder Browserprüfung.

Secrets bleiben serverseitig. Keine Tokens, lokalen URLs oder Credentials
gehören in Frontend, Entity-Attribute, Logs, Issues oder Dokumente.

## 5. Normative Statuswerte

Künftige Diagnose-/UX-Verträge müssen mindestens `loading`, `ready`, `empty`,
`stale`, `degraded`, `unavailable`, `reconnecting`, `offline`, `error` und
`blocked` unterscheiden. `degraded` ist nicht automatisch Totalausfall; ein
Safety-relevantes Feld kann trotzdem blockiert sein.

## 6. AP1 Stop-Bedingungen

Die Implementierung stoppt vor fachlicher Logik, wenn eine Entscheidung die
Owner-/Contract-Matrix verändert oder wenn eine Quelle nur aus alter YAML,
einem veralteten README, einem Snapshot oder einem Entity-Alias abgeleitet
werden könnte. Das offene Ergebnis wird in [CONTRACTS.md](CONTRACTS.md) und
[MIGRATION.md](MIGRATION.md) als Gate dokumentiert.

## 7. AP2-Fortschreibung

Der frühe AP2-Slice implementiert die Fachschicht als HA-unabhängige Module:
`contracts.py` (owner-bound observations), `solar.py` (window-specific
exposure), `engine.py` (decision tree), `override.py`, `cooldown.py` und
`shadow.py`. `ux_contract.py` stellt den versionierten read-only Contract für
spätere Übersicht, Diagnose und Einstellungen bereit.

`async_setup_entry` erstellt ausschließlich einen initialen
`ShadowSnapshot`. Es gibt weiterhin kein Plattform-Forwarding, keinen
Input-/Observation-Listener, keinen Service und keinen Aktuatorzugriff. Der
standardmäßige OptionsFlow-Update-Listener lädt bei Konfigurationsänderungen
nur die read-only Auswertung neu. Ein technischer Shadow-Target ist eine
Diagnose-/Apply-Intent-Aussage, keine ausführbare Home-Assistant-Aktion.

Die vollständige AP2-Implementierungs- und Owner-/Freshness-Beschreibung steht
in [AP2_SHADOW.md](AP2_SHADOW.md). Nicht belegte externe Bindings bleiben
Blocker und werden nicht aus historischen IDs rekonstruiert.

## 8. AP2-Laufzeitfortschreibung v0.2

Die folgenden Aussagen supersedieren die vorläufige Beschreibung in Abschnitt
7, soweit sie den laufenden AP2-Shadow-Coordinator betreffen. Status ist
`Installed / Shadow / Not Live`; `benni_blind_policy` bleibt alleiniger
produktiver Apply-Owner.

```text
Owner-selected ConfigEntry bindings
        -> ShadowCoordinator (state listener + freshness timer, event loop)
        -> BlindControlInputs / LegacyEvidence
        -> Solar Exposure + DecisionEngine v2
        -> DecisionTrace v2 / fieldwise Legacy diff
        -> ShadowSnapshot v1
        -> read-only UX v2, WebSocket and one diagnostic sensor projection v1
```

Der Coordinator beobachtet nur die im OptionsFlow gewählten Bindings und
erstellt ausschließlich die einzelne read-only Sensorplattform für die
Diagnoseprojektion, keinen Service und keinen Aktuatorpfad. Seine
State-, Zeit- und Refresh-Callbacks sind Home-Assistant-Callbacks; ein
gegebenenfalls fremder Thread übergibt die Task-Erzeugung über den
thread-sicheren HA-Scheduler zurück an den Event Loop. Dadurch entsteht kein
`async_create_task`-Aufruf aus einem Worker-Thread.

`blind_control.decision.v2` trennt den fachlichen Mastermodus
`normal|manual|failure` von Safety und Apply. Unter `normal` enthält der Trace
Kategorie, Variante, Original-Candidate-Key, Gewinner und alle kompatiblen
aktiven oder bewusst pausierten Nebenäste; fachlich inaktive Kandidaten bleiben
rein diagnostisch. Das automatische Quality-Gate läuft auch bei bereits
gebildetem fachlichem Target: nicht frische oder fehlende Temperatur-,
Activity-/Belegungs- sowie Lux-/Solar-Evidence wird als konkreter
`quality_blocker` dokumentiert und macht den Mastermodus `failure`. Bei
Failure hält die Laufzeit nur eine nachweislich sichere Position; ohne diesen
Nachweis wird Apply blockiert. Sie erzeugt niemals einen pauschalen
Open-Fallback. Positiv bestätigte
Opening-Safety verwendet weiterhin das achsenspezifisch konfigurierte
Safety-Profil.

Die installierbare Panel-UX erhält den offiziellen `hass`-Context und konsumiert
allein den admin-geschützten Snapshot-Contract. Sie zeigt den fachlichen Baum
und die technische Ebene getrennt. Binding-Bearbeitung bleibt im nativen
OptionsFlow mit Entity-Selectoren und den Gruppen Core State,
Opening/Safety/Cover, Solar, Temperatur/Wetter und Legacy-Vergleich; die
öffentliche Projektion enthält nur Status und Owner-/Freshness-Policy, nie
Entity-IDs. Eine kleine installierte-State-Discovery liefert anhand
publizierter Contractattribute und Source-Referenzen `suggested_value`s und
setzt belastbare required/conditional Bindings als echte Formular-Defaults.
Sie ist keine Registry: gespeicherte Nutzerwerte und bewusst leere Slots haben
Vorrang, optionale Evidence wird nicht ungefragt gebunden, und die Engine
konsumiert weiterhin nur die tatsächlich persistierten Bindings.

`blind_control.automation_projection.v1` ist bewusst klein: Mastermodus,
aktive Kategorie/-variante, Failure-Status/-Grund/-Blocker, fachliches und
effektives Ziel sowie Safety-, Apply- und Shadow-Status. Die Integration
publiziert diesen redigierten Contract über genau eine native diagnostische
Statusentität. Ihr Zustand ist `master_mode`; alle weiteren Felder sind
read-only Attribute. Die Entity Registry bestimmt ihren installationsbezogenen
Namen aus der ConfigEntry-Instanz, daher ist keine Entity-ID vorgegeben. Die
Projektion hat keine Services, keinen Aktuatorzugriff und umgeht den
Apply-Owner nicht.

## 9. Live-Shadow-Contract-Fortschreibung

Der OptionsFlow-Listener lädt unter Home Assistant 2026.8 ausschließlich mit
`async_reload(entry_id)` neu. Der Reload entlädt Sensorplattform, Coordinator,
State-Listener und Timer vollständig und baut danach Runtime, Snapshot und die
read-only Statusentität aus den gespeicherten Optionen neu auf.

Vor der Engine liegt eine feldspezifische Adaptergrenze:

- Presence: `away_gate` beziehungsweise kanonische Home-/Away-Zustände;
- Activity: Core-State-State und dokumentierte Media-/PC-/Gaming-Attribute mit
  der Glare-Präzedenz `tv > pc > screen > none`;
- Day State: exakt neun kanonische Phasen, getrennt in Tageslicht, Übergang und
  Nacht;
- Opening: explizite positive/negative Safety-Polarität;
- Standard-Cover: HA-Verfügbarkeit, `current_position`, Source- oder
  HA-Zeitstempel und Restore-Ablehnung.

Solar Exposure ist capability-basiert. Sonnenhöhe, Sonnenazimut und Außenlux
sind die zwingende Tageslicht-Kombination. Lux-Trend wird bei ungebundenem
Trend-Owner aus zwei zeitlich verschiedenen frischen Luxbeobachtungen
abgeleitet. Direkte/diffuse Modellstrahlung und Bewölkung sind optionale
Confidence-Evidence. `SolarExposure` projiziert vorhandene und fehlende
Capabilities, verwendete und abgeleitete Evidence, Confidence und tatsächliche
Quality-Blocker. Nicht frische optionale Evidence blockiert nur dann, wenn die
verbleibende Kombination insgesamt nicht belastbar ist.

Optionale aktuelle DNI-/Diffus-Evidence folgt dem gekapselten Pfad
`Open-Meteo -> interner Blind-Control-Provider -> Evidence-Adapter -> Solar
Exposure`. Der Provider verwendet die offizielle HA-HTTP-Client-Infrastruktur
und einen `DataUpdateCoordinator`. Ein gemeinsamer read-only Abruf im
15-Minuten-Rhythmus liest die beiden `current.*_instant`-Felder des Modells
`dwd_icon_seamless`; die letzte erfolgreiche Evidence ist höchstens 1200
Sekunden nutzbar. Derselbe Datensatz speist zwei native Sensorentitäten am
Blind-Control-Gerät.

Die URL ist private ConfigEntry-/OptionsFlow-Konfiguration und wird nicht in
Snapshot, WebSocket, Sensorattributen oder Logs veröffentlicht. Externe
Bindings überschreiben je Feld den internen Provider. Hinter dieser Precedence
bleibt die Solar-Engine providerneutral, sodass Core Contracts den Provider
später übernehmen kann. Es gibt keine YAML-/Package-/Secret-Konfiguration,
keinen API-Key-, PV-, Forecast- oder Weather-State-Pfad und keine Änderung an
Core State. Unload und Options-Reload beenden Coordinator, Listener und Timer,
bevor genau eine neue Runtime aufgebaut wird. Entries ohne gespeicherte URL
verwenden die HA-Standort-Suggestion bis zur bestätigten OptionsFlow-Speicherung
nur im Runtime-Kontext; ohne Standort oder bei Providerfehler bleibt die
Strahlungsevidence unavailable/stale und wird nicht ersetzt.

Die Panel-Draft-Grenze verwendet `$state.snapshot` und eine rekursive
JSON-Entkopplung. Dadurch erreicht kein Svelte-5-Proxy `structuredClone`; Dirty
Drafts bleiben bei Polls erhalten und erfolgreiche Saves synchronisieren erst
gegen den bestätigten Server-Snapshot.
