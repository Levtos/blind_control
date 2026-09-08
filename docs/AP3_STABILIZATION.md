# AP3 Stabilisierung – Entscheidung vom 07.09.2026

**Verbindlicher Auftrag:** [blind_control#3](https://github.com/Levtos/blind_control/issues/3).
Diese Entscheidung ersetzt widersprechende ältere AP1/AP2/AP3-Texte.
Historische GitHub-Kommentare bleiben unverändert.

## Aktueller Nachtrag v0.7.0 – Operator und primäre Consumer API

[AP3_OPERATOR.md](AP3_OPERATOR.md) ist der aktuelle verbindliche Vertrag:
Core Contracts für vorhandene Schemas, sichtbare Fallback-Gaps und direktes
administratives Panel-Staging. Die frühere Variante B und ausschließlich native
Betriebsfreigabe sind damit abgelöst. Solar-/Cover-/Movement-/Safety-Verträge
aus v0.6.3 bleiben bestehen. Keine automatische zusätzliche Shadow-Runde;
nach Installation folgt Bennis kontrollierter Writer-Cutover.

## Historischer Nachtrag v0.6.3 – Solar und kontrollierter Writer-Cutover

Benni meldet v0.6.2 installiert im Shadow, Position 100 %, idle und keinen
position_unavailable-Fehler. Sein Auftrag in #3 supersediert die frühere
Low-Light-Bewertung B und die automatische Forderung nach einer weiteren
theoretischen Shadow-Runde. Das nächste reale Gate nach dieser technischen
Lieferung ist Bennis kontrollierter Writer-Cutover gemäß AP3_CUTOVER.md.
Testing / Not Live; keine Installation oder HA-Aktion durch den Agenten.

Ursache Solar: der abschließende Klassifikationszweig vermischte valide geringe
Energie mit fehlender Evidence. Er liefert jetzt `low_light`, ohne neue Schwelle,
Solarengine oder Provideränderung. Fehlende/stale/conflicting Pflicht-Evidence
bleibt UNKNOWN; der frühere Lux-Nachthinweis ohne Sonnenhöhe entfällt. Pflichtwerte
werden vor night geprüft und auf physikalische Zahlenbereiche begrenzt.
Heat/Glare, Cloud Shadow, Hysterese und Cold-Lux/Temperatur bleiben unverändert.

Input-Audit: bestehende feldspezifische Floors und negative Owner-Quality werden
beibehalten. Alte persistierte 120-s-Bindings werden für Sonne/Lux, Temperaturen,
Cloud und Strahlung mit realer Grenzüberschreitung regressiert; kein weiterer
reproduzierter False-Stale-Fehler und keine pauschale TTL-Erhöhung. Stationäre
Coversemantik aus v0.6.2 bleibt einschließlich negativer Device-Evidence erhalten.

Native Optionen konnten Modus/Owner/Apply bereits speichern. Neue Regression
prüft die drei Cutover-Zustände und Rückkehr zu Shadow durch OptionsFlow und
ConfigEntry-Load. Die UI ergänzt Apply AN/AUS, konkrete Apply-Begründung,
Schreibpfad und tatsächliche Ruhebaseline. Das bisherige override.baseline ist
bei inaktivem Override leer und deshalb kein Runtime-Baseline-Nachweis.
Additive Runtime-/UX-Felder projizieren den Tracker; keine neue State Machine.

Kein softwareseitiges Fremdwriter-Lock behauptet: vollständiges Legacy-Disable
plus Prozessneustart und Null-Writer-Prüfung sind vor Arming zwingend. Safety,
Recovery, Override, Lifecycle-Revozierung und ein einziger Adapter bleiben.
Low light ist keine Fahrtfreigabe; normale aktuelle Arbitration und alle Gates
entscheiden. Service-Erfolg bleibt von realer Position/Ruhe getrennt.

Die nachfolgenden versionsbezogenen Nachträge bleiben historische Provenienz;
bei Widerspruch gilt dieser aktuelle Nachtrag.

## Architekturentscheidung

Lokale Reparatur A hätte Command-Historie, Geräteachse, Override-Timer und
Coordinator-Callbacks mit weiteren Sonderfällen verbunden. Gewählt wurde B:
begrenzter Umbau dieser Grenzen, ohne neue Arbitration-/Registry-Plattform.

- Engine, Safety und Override verwenden ausschließlich logische Positionen.
  Input-Adapter normalisiert die numerische Geräteposition; HA-Fahrtrichtung
  bleibt semantisch unverändert (v0.6.1-Nachtrag unten). Allein der
  Actuation-Adapter rechnet das fertig bestimmte Ziel zurück.
- Cooldown startet bei Dispatch. Pending ist Diagnose der aktuellen
  Entscheidung; jede Auswertung ersetzt es. Keine Release-Methode für alte Ziele.
- Eigene Bewegung endet erst mit stabiler tatsächlicher Zielposition in Ruhe.
  Die konfigurierbare Frist meldet Fehler, niemals einen Benutzer-Override.
  v0.6.1 ergänzt den unten beschriebenen kontrollierten Fehlerabbruch in Ruhe.
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

## Fokussierter Hardening-Nachtrag v0.6.1

Scope bleibt ausschließlich der Follow-up aus #3 zu PR #16 / v0.6.0 und
Implementierungsabschluss 5575618821. Die folgenden Verträge supersedieren
ältere Aussagen zu Fehlerabschluss, unmittelbaren Umweltwechseln und Text-Motion.
Kein neues Fachfeature, kein Core-Contracts-Cutover, kein HA-Eingriff.

| Review-Punkt | Ursache | Umsetzung / technische Regression |
| --- | --- | --- |
| High: echter Handlerfehler nicht erkannt | HA non-blocking startet den Handler in einer Task mit Exception-Catcher | blocking=True im einzigen Adapter; FakeServices modelliert Hintergrundfehler getrennt. Kein applied, Erfolgs-Cooldown oder actuation_executed bei Handler-Exception. |
| High: Bewegungsfehler blockiert dauerhaft | Own-Target wurde ausschließlich bei erreichtem Soll gelöscht | Fehler latchen; neues frisches Ruhefenster bricht den Vorgang ab, rebasiert auf Ist und meldet recovered. Keine Zielqueue, aktuelle Entscheidung neu prüfen; positive Safety darf vorher ersetzen. |
| High: Flatter-Schutz fehlt | unmittelbare Umwelt-Gates und Motor-Cooldown besitzen keine Hysterese | drei Umwelt-Transitionen, Cold-Lux-Band, Solar-/Confidence-Halteband, asymmetrische Stabilität. Profil-/Activity-Ziele werden nie gespeichert. |
| Evidence: Achsen-Motion | Text wurde zusätzlich zu Zahlen invertiert, ohne HA-Vertrag | opening/closing unverändert aus HA; nur numerische Werte werden gespiegelt. Acht Kombinationen aus Motion und Achse plus Safety-Regressionspfad. |

### HA-Primärevidence

Geprüft am 07.09.2026: [Cover-Entity-Vertrag](https://developers.home-assistant.io/docs/core/entity/cover/),
[ServiceRegistry.async_call](https://github.com/home-assistant/core/blob/e85b8a256e3b8e402eb862333cdf5738477ea8c3/homeassistant/core.py)
und [CoverEntity.state](https://github.com/home-assistant/core/blob/e85b8a256e3b8e402eb862333cdf5738477ea8c3/homeassistant/components/cover/__init__.py).

Zusätzlich gegen den aktuellen stabilen Core **2026.9.1** geprüft:
[ServiceRegistry](https://github.com/home-assistant/core/blob/2026.9.1/homeassistant/core.py)
und [CoverEntity](https://github.com/home-assistant/core/blob/2026.9.1/homeassistant/components/cover/__init__.py)
besitzen dieselbe relevante Handler- und Motion-Semantik.
Die ServiceRegistry erwartet bei blocking=True den Handler direkt; non-blocking
verwendet eine Hintergrundtask mit Fehlerprotokollierung. Das bestätigt
Handler-Erfolg, niemals physische Zielerreichung. Unterdrückt eine Geräteintegration
intern einen Fehler, kann der Caller ihn nicht nachträglich als Exception erkennen.
Position/Motion/Settling und Timeout bleiben deshalb unabhängig notwendig.

CoverEntity.state verwendet is_opening/is_closing vor is_closed. Es berechnet
keine Richtung aus current_cover_position. Die HA-Semantik ist eindeutig;
eine abweichende Geräteintegration ist gesondert zu prüfen. Axis Inversion
bezieht sich nur auf numerische Gerätewerte. Kein globales Erraten eines
abweichenden Gerätevertrags; reale Motion-/Achsenplausibilität bleibt Shadow-Gate.

### Recovery-Vertrag

command_error oder target_not_reached bleibt movement_error. Während
recovery_status=waiting_for_quiet sperrt die Motion-Grenze normale Applys.
Ein **neues** ruhiges Istpositionsintervall nach dem Fehler ist notwendig;
laufende Bewegung, fehlende/ungültige/stale Evidence und eine Positionsänderung
außerhalb Toleranz verwerfen seinen Anfang. Default 30 s
(movement_recovery_seconds, mindestens position_settle_seconds).
Dieser konservative Abstand verhindert den Rückfall in die bisher mögliche
sofortige Wiederholung; er ist eigenständig kalibrierbar und kein Fake-Cooldown-Erfolg.

Danach: alte Attribution abbrechen, Istposition übernehmen, movement_status=idle,
recovery_status=recovered. Der letzte Fehler bleibt lesbar bis zum nächsten
Fehler oder Runtime-Neustart. Es gibt keine automatische Wiederholung des alten
Ziels: allein die nächste aktuelle Gesamtentscheidung darf alle Gates durchlaufen.
Safety kann die Attribution vorher ersetzen (superseded_by_safety); normaler
erfolgreicher Safety-Abschluss führt ebenfalls zu recovered.

### Umweltbänder und Stabilität

Cold-Enter 400 lx / Exit 500 lx: die zusätzliche 100-lx-Lücke deckt die
konkreten Schwankungen bis 420 lx ab, ohne eine weit entfernte Tageslichtschwelle
einzuführen. Migration abweichender Altwerte: max(Enter + 100, Enter × 1.25).
Dies ist eine konservative Kalibrierung, keine neue Sensorphysik.

environment_hysteresis_ratio=0.8 senkt bei bereits aktivem Heat/Glare die
Confidence-Halteschwelle und die minimale geometrische Inzidenz auf 80 % des
Eintrittswerts: Heat 0.55/0.44, Glare 0.35/0.28, Inzidenz 0.05/0.04.
Das kleine relative Band skaliert mit vorhandener Benutzerkalibrierung;
0 als bewusst gespeicherte Confidence-Grenze bleibt 0.
Die rohe Solar-Klassifikation bleibt unverändert sichtbar; unknown blockiert
weiter normale Aktuation. Cloud Shadow bleibt schutzrelevant.

environment_enter_seconds=10, environment_exit_seconds=120: Schutz entsteht
schnell, einzelne Wolken oder kurze Entlastungen lösen ihn nicht. Gegenläufige
Evidence verwirft die laufende Transition. Fehlende Quality unterbricht die
Zeitmessung. Alle drei Modi verwenden dieselbe kleine Datenstruktur.
Waking und harte Personen-/Betriebszustände, Quality/Failure, technische Safety
und Writer-Gates warten nicht auf Umweltzeiten. Glare-Aktivität TV→PC→none
wird immer aus dem aktuellen Contract gelesen; alte Profile werden nicht nachgeholt.
Der vorhandene Recompute-Timer übernimmt die Zeitfortschreibung (normal 10 s);
keine zusätzlichen Timer pro Modus. Grenzübertritt erfolgt bei der ersten
frischen Auswertung nach der Mindestdauer.

Alle neuen Werte sind nativ und im bestehenden Kalibrierbereich editierbar.
Validierung, Config-v6-Kompatibilität und exakter Versionsrollback:
[MIGRATION.md](MIGRATION.md). Neue Regressionen: tests/test_ap3_hardening.py.

**Testing / Shadow / Not Live. Neues unabhängiges read-only Quality Gate aus
frischem Kontext erforderlich.** Erst nach dessen PASS installiert Benni
v0.6.1 und erhebt neue Shadow-Evidence. Keine Selbstzertifizierung durch diesen
Implementierungsdurchgang; das spätere Cutover-/Live-Gate bleibt separat.

## Fokussierter Hardening-Nachtrag v0.6.2 – 08.09.2026

Ausgang exakt v0.6.1/main `9987f198346422a9e39da06db6db6c62b65e19a5`.
Nur der reproduzierte Standard-Cover-Contractfehler wird korrigiert.

| Finding | Ergebnis gegen unverändertes v0.6.1 | Behandlung |
| --- | --- | --- |
| A: Outdoor-Temperatur nach etwa 120 s stale | Config v6 mit global/Binding 120 s und 600 s altem Weather-Temperaturwert ergibt effektive 1800 s und fresh. Default, from_mapping, Roundtrip, Options und ConfigEntry verwenden binding_policy / _effective_max_age. | **not reproduced in v0.6.1 source; requires fresh HA runtime evidence**. Kein Produktfix, keine neue TTL. |
| B: 299 lx / 5.88° / 88.07° / DNI 0 / Diffus 2.1 | Bei Standardfenstergeometrie unknown, reason insufficient_radiation_or_lux_evidence_with_known_geometry; Failure solar_aggregate_unknown. | **expected behavior**. Solar, optionale Evidence, Provider 900/1200 s und Fail-Closed bleiben unverändert. |
| C: ruhendes Cover open / Position 100 / HA-State acht Stunden alt | Position stale → kopierte Motion-Quality stale → observe_cover_position(None) → position_unavailable / keine Baseline. | **reproduced bug**. Kleine Korrektur ausschließlich an der vorhandenen Adaptergrenze. |

### Entscheidung und Grenze

HA `last_updated` ändert sich nur bei verändertem State oder Attribut,
nicht bei jedem Bericht. Deshalb darf sein Alter eine unveränderte stationäre
Position nicht allein entwerten. Primärquellen:
[HA State Object](https://www.home-assistant.io/docs/configuration/state_object/)
und [Cover-Entity-Vertrag](https://developers.home-assistant.io/docs/core/entity/cover/).

Für nicht restored Standard-Cover mit gültigem numerischem current_position,
semantischem Ruhezustand open/closed/stopped und ohne negative Evidence gilt
die stationäre Baseline ohne HA-Alterslimit. Kein Ersatzwert und keine riesige TTL.
Vorhandener HA-Zeitstempel bleibt erforderlich. Während opening/closing bleibt
die numerische Position Telemetrie mit vorhandener TTL. Motion bleibt ein
semantischer State mit eigener Quality, nicht die kopierte Qualität einer Zahl.

Explizite Device-/Source-Zeit-Evidence hat Vorrang, auch wenn sie stale oder
ungültig ist. Kein Fallthrough auf frischere nachrangige Evidence. Reihenfolge
und fail-closed Regeln stehen in CONTRACTS.md 7.1. Keine neue Owner-/Registry-
oder Core-Contracts-Ersatzlogik. Ein gültiger HA-State beweist keinen unabhängig
gemessenen physischen Zustand, wenn die Geräteintegration falsche Werte liefert;
reale Geräteplausibilität bleibt Shadow-Gate.

Restart, eigene Fahrt und Recovery benötigen weiterhin gültige Position plus
Motion und das bestehende Ruhefenster. Keine alten Ziele werden nachgeholt.
Opening OPEN kann weiterhin nur logisch aufwärts wirken und bleibt über
Cooldown, Override, Waking und normalen Movement-Gates.

Regressionen: tests/test_cover_evidence.py und ConfigEntry-/Options-Fall in
tests/test_bootstrap.py. Bestehende v0.6.1-Safety-/Recovery-Tests bleiben erhalten.
Config bleibt v6 ohne neue Felder. **Testing / Shadow / Not Live.**
Offen: Bennis v0.6.2-Installation, frische read-only Shadow-Evidence,
Opening-OPEN- und Movement-/Baseline-Reproduktion; erst danach Cutoverplanung.
