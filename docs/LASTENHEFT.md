# Lastenheft Blind Control

**Dokumentstatus:** v0.3 – fachlich grundsätzlich abgenommen, Ergänzungen für frühen Produktstart
**Stand:** 07. September 2026
**Zielprodukt:** Home-Assistant-Integration `blind_control`  
**Übergeordnete Entscheidung:** [Levtos/control#31](https://github.com/Levtos/control/issues/31)

Die fachliche Fortschreibung vom 07.09.2026 ist in [AP3_STABILIZATION.md](AP3_STABILIZATION.md) begründet und ersetzt widersprechende frühere Entscheidungen.

## 1. Zweck des Dokuments

Dieses Lastenheft beschreibt, **was** Blind Control leisten muss. Es ist die fachliche Grundlage für Repository-Gründung, Architektur, Umsetzung, Shadow-Betrieb, Migration und Abnahme.

Die bestehende Integration `benni_blind_policy` wird nicht weiter zur Zielarchitektur umgebaut. Bewährte Funktionen und nachgewiesene Fehlerkorrekturen werden übernommen, die neue Integration wird jedoch neu entwickelt.

## 2. Zielbild

Blind Control soll ein nachvollziehbares, kontextsensitives und robustes Rollo-System sein. Es darf nicht aufgrund eines einzelnen starren Grenzwerts eine offensichtlich unpassende Aktion ausführen.

Das System muss:

- den fachlichen Rollo-Zustand und die Zielposition bestimmen,
- kompatible Schutz- und Komfortanforderungen nachvollziehbar zusammenführen,
- technische Sicherheit getrennt von der fachlichen Entscheidung behandeln,
- die Zielposition kontrolliert selbst ausführen,
- manuelle Eingriffe zuverlässig erkennen und respektieren,
- alle Entscheidungen und unterdrückten Alternativen erklären,
- vollständig konfigurierbare Profilpositionen besitzen,
- eine vollwertige, in der UI steuerbare Achsen-Invertierfunktion besitzen,
- zunächst ohne Aktorzugriff im Shadow-Modus gegen die alte Integration laufen,
- erst nach Bennis separatem Fahrt-/Cutover-Gate produktiver Apply-Owner werden; die Legacy erst nach Live Verified entfernen.

Blind Control ist ein deterministisches Regelsystem. Ein nicht erklärbares KI- oder Blackbox-Modell ist nicht Bestandteil des Zielbilds.

## 3. Benennung und Abgrenzung

### 3.1 Kanonischer Name

- Repository: [`Levtos/blind_control`](https://github.com/Levtos/blind_control), am 15. August 2026 angelegt und für den Bootstrap bereit
- Home-Assistant-Domain: `blind_control`
- Produkt- und UI-Name: **Blind Control**
- Der Präfix `benni_` wird für das neue Produkt nicht verwendet.
- Der bestehende Name `benni_blind_policy` bleibt ausschließlich für das alte Repository und die alte Integration bestehen, bis beide nach erfolgreicher Migration archiviert beziehungsweise entfernt werden.

### 3.2 Kein Rename

Blind Control ist kein Rename und kein schrittweiser Umbau der alten Integration. Es wird als eigenständige native Home-Assistant-Integration aufgebaut.

## 4. Fachliche Grundprinzipien

### 4.1 Ebenenmodell

Die Entscheidung folgt grundsätzlich diesen Ebenen:

1. Grundzustand und Tageskontext
2. Personen- beziehungsweise Betriebsmodus
3. Umwelt- und Nutzungsschutz
4. technische Safety- und Apply-Prüfung

Frei vergebbare Prioritätsnummern sind nicht vorgesehen.

### 4.2 Komposition kompatibler Anforderungen

Für normale, miteinander kompatible Anforderungen gilt:

- `0 %` bedeutet geschlossen.
- `100 %` bedeutet vollständig geöffnet.
- Jede aktive Anforderung liefert eine eigene Zielposition und einen Diagnosegrund.
- Aus kompatiblen Zielpositionen gewinnt grundsätzlich die kleinste Position.
- Eine Anforderung darf nicht allein deshalb verschwinden, weil eine andere Anforderung gerade stärker ist.
- Unterdrückte Kandidaten bleiben im Decision Trace sichtbar.

Beispiel: Heat fordert 15 %, Glare PC fordert 75 %. Das effektive Ziel ist 15 %, Glare PC bleibt als aktiver Kandidat sichtbar.

### 4.3 Exklusive Modi

Nicht alle Zustände sind normale Kandidaten des Minimum-Modells. Exklusive Modi dürfen fachliche Umweltanforderungen gezielt pausieren.

Insbesondere gilt für `waking`:

- `waking` dient aktiv dem Aufwecken durch verfügbares Tageslicht.
- Beim Eintritt in den kanonischen `waking`-Zustand wird die konfigurierte Waking-Position angefahren; Standardwert ist 100 %.
- Während `waking` werden Heat, Glare, Privacy und Cold Insulation fachlich überstimmt.
- Beim Übergang zu `awake` werden alle normalen Umwelt- und Nutzungskandidaten sofort neu bewertet.
- Blind Control berechnet keine eigene Vorweckzeit. Beginn und Ende von `waking` kommen ausschließlich aus dem kanonischen Core-State-/Wake-Contract.
- Eine alte oder konkurrierende Weckquelle darf das Rollo nicht auslösen.
- Technische Safety, ein nicht fahrbereiter Aktor und eine ausdrücklich deaktivierte Automatik bleiben auch während `waking` übergeordnet.

private_time bleibt kanonischer Core-State-Input einschließlich vorgelagerter Zeitbegrenzung. Blind Control fügt keinen Waking-Sonderfall gegen diesen Zustand hinzu; Waking-Exklusivität betrifft die genannten Umwelt-/Privacy-Anforderungen.

## 5. Eingänge und Ownership

Blind Control konsumiert vorhandene technische und fachliche Wahrheiten. Es darf keine konkurrierenden Wahrheiten zu Anwesenheit, Sleep/Waking, Opening, Lux, Temperatur, Wetter oder Sonnenstand erzeugen.

Erforderliche Eingangskategorien:

- Core State: insbesondere `bio_state`, `activity_state`, `day_state`, Anwesenheit/Away und kanonischer Wake-Zustand
- Core Contracts oder dokumentierter technischer Contract: Opening, Freshness, Quality, Conflict und Availability
- Cover: aktuelle Position, Fahrzustand und Verfügbarkeit
- lokaler Außen-Luxsensor
- Sonnenhöhe und Sonnenazimut
- Innen- und Außentemperatur
- Wetterlage, Wolken, Niederschlag, Wind, Böen und Warnungen, soweit verfügbar
- Zeit- und Kalenderkontext: Werktag, Wochenende, Feiertag und Urlaub

Für jeden verwendeten Eingang müssen Quelle, Aktualität, Qualität und Fehlerverhalten dokumentiert sein. Textuelle Cover-Zustände wie `open` dürfen nicht als Ersatz für die numerische Position verwendet werden.

## 6. Physische Referenz des ersten Rollos

Für das Wohnzimmer gelten als initiale Standortdaten:

- Fensterfront: Ostsüdost
- Standard-Azimut, von Norden im Uhrzeigersinn: ungefähr `123,68°`, konfiguriert als `124°`
- Fensterneigung: `90°`, senkrechte Fläche
- Luxsensor: außen am Rahmen des Wohnzimmerfensters
- Thermorollo: innenliegend
- Der Luxsensor wird durch das Rollo nicht selbst abgeschattet.

Die Standortdaten müssen konfigurierbar sein, damit spätere Fenster oder Installationen abweichende Ausrichtungen verwenden können.

## 7. Fachliche Zustände und Anforderungen

### 7.1 Grundzustände

Mindestens vorzusehen:

- `weekday`
- `weekend`
- `holiday`
- `vacation`

Die Zustände bleiben getrennt, auch wenn sie zunächst dieselben Werte verwenden.

### 7.2 Personen- und Betriebsmodi

Mindestens vorzusehen:

- `sleep`
- `waking`
- `awake`
- `away`
- `private_time`
- `privacy`
- manueller Override
- Automatik deaktiviert

Sleep bleibt ein eigenständiger fachlicher Zustand. Für Consumer-Semantik gilt
`effective_sleep = bio_state in {provisional_sleep, sleep}`: Beide kanonischen
Core-State-Werte aktivieren denselben Sleep-Kandidaten und dasselbe frei
konfigurierbare Sleep-Profil. Blind Control erzeugt daraus keinen zusätzlichen
Bio- oder Activity-State. Waking wird ausschließlich aus dem kanonischen
Zustand übernommen und darf nicht aus einer lokalen Blind-Control-Uhrzeit
abgeleitet werden.

### 7.3 Umwelt- und Nutzungsschutz

Mindestens vorzusehen:

- `heat_protection`
- `glare_general`
- `glare_tv`
- `glare_pc`
- `cold_insulation`
- `storm_approaching`
- `cool_air_available`

PlayStation erhält kein eigenes Glare-Profil. PlayStation, andere Konsolen und TV-/Streaming-Nutzung verwenden `glare_tv`, weil sie denselben Bildschirm nutzen. PC-Nutzung verwendet `glare_pc`.

Cloud Cover wird durchgängig als 0–100 % geführt. Bei Solar-Aggregat unknown bleibt automatische Aktuation blockiert; Unsicherheit erzeugt keine neue Base-Daylight-Öffnung. Positive Opening-Safety bleibt unabhängig.

## 8. Solar Exposure

### 8.1 Zweck

Der bisherige harte Lux-Schalter wird durch eine nachvollziehbare Solar-Exposure-Bewertung ersetzt. Ein einzelner Luxwert darf Heat oder Glare nicht allein ein- oder ausschalten.

Blind Control darf aus vorhandenen Rohdaten eine **blind-spezifische Relevanz für die konfigurierte Fensterfläche** ableiten. Die Quelle für Sonnenstand, Wetter, Lux und Temperatur bleibt außerhalb dieser Ableitung eindeutig dokumentiert.

### 8.2 Eingangssignale

Solar Exposure berücksichtigt mindestens:

- Sonnenhöhe und Sonnenazimut,
- Fensterazimut und Fensterneigung,
- erwartete horizontale beziehungsweise direkte und diffuse Strahlung, soweit verfügbar,
- Wolkenlage und Wettermodell als Erwartung,
- lokalen Außen-Luxwert als Echtzeitbeobachtung,
- Luxverlauf und Verhältnis zwischen erwarteter und beobachteter Helligkeit,
- Freshness, Quality und Source Conflict.

#### 8.2.1 AP2-Modellstrahlungsquelle

Für AP2 darf Blind Control aktuelle direkte und diffuse Modellstrahlung über
einen isolierten internen Open-Meteo-Provider beziehen. Der Provider ist
vollständig über ConfigFlow/OptionsFlow konfigurierbar und benötigt weder YAML,
Package, `secrets.yaml`, API-Key, PV-Anlage noch eine Änderung an Core State oder
eine neue Weather-State-Integration. Ein gemeinsamer read-only Abruf des Modells
`dwd_icon_seamless` liefert ausschließlich
`current.direct_normal_irradiance_instant` und
`current.diffuse_radiation_instant`. Beide Werte bleiben optionale,
ersetzbare Evidence; Außenlux und Sonnengeometrie bleiben tragend. Ein externes
Binding hat je Feld Vorrang. Fehlende, fehlerhafte oder stale Providerdaten
dürfen niemals einen Default-Open- oder Aktuatorpfad erzeugen.

### 8.3 Zustände

Mindestens folgende Zustände werden ausgegeben:

- `direct_sun`: direkte Sonne kann das Fenster treffen
- `cloud_shadow`: Sonne könnte das Fenster treffen, ist momentan jedoch durch eine Wolke abgeschwächt
- `diffuse_bright`: relevantes Streulicht ohne starke direkte Sonne
- `solar_not_on_window`: Sonne ist vorhanden, trifft die Fensterfläche aber geometrisch nicht relevant
- `night`: keine solare Einstrahlung möglich
- `low_light`: gültige Sonnengeometrie und lokale Lux-Evidence, aber keine relevante direkte oder diffuse Solarenergie nach den bestehenden Schwellen
- `unknown`: Daten fehlen, sind stale oder widersprüchlich

v0.6.3 trennt geringe Energie von fehlender Evidence. Alle drei Pflichtwerte
(Sonnenhöhe, Sonnenazimut, Außenlux) müssen fresh und plausibel sein, auch für
`night`. Ohne Sonnenhöhe wird aus niedrigen Lux keine Nacht erfunden.
`low_light` ist kein Quality-Failure und kein eigenständiger Öffnungsbefehl:
Personenmodi, Cold, Umweltstabilisierung und sämtliche Apply-/Safety-Gates gelten
weiter. DNI, Diffus, Cloud und Trend bleiben optional; ihre Abwesenheit allein
macht gültige lokale Pflicht-Evidence nicht unbekannt.

### 8.4 Diagnosewerte

Die Diagnose muss mindestens enthalten:

- geschätzte Einstrahlung auf die Fensterfläche in W/m² oder einen eindeutig bezeichneten relativen Wert,
- geometrischen Einfallsfaktor,
- lokalen Luxwert und Luxtrend,
- erwartete Modellhelligkeit beziehungsweise Modellstrahlung,
- erkannte Abschattung,
- Zustand, Confidence, Quellen und Begründung.

### 8.5 Helios-Learning

Die fachliche Idee orientiert sich an:

- [Helios](https://github.com/ReikanYsora/Helios): Sonnenstand, Clear-Sky-Strahlung, Wolkengewichtung und lokale Sensorübersteuerung
- [Helios Forecast](https://github.com/ReikanYsora/Helios-Forecast): Übertragung der Strahlung auf eine ausgerichtete Fläche

Die Helios-Projekte sind GPL-3.0-lizenziert. Code wird nicht ungeprüft kopiert. Die verwendeten Standardverfahren werden lizenzkonform eigenständig implementiert, dokumentiert und mit Golden-Vector-Tests abgesichert, sofern keine bewusste GPL-kompatible Übernahme beschlossen wird.

Gelände- und Gebäudeschatten sind für die erste Version nicht erforderlich. Sie dürfen später ergänzt werden, wenn die Basisdaten nachweislich nicht ausreichen.

## 9. Heat Protection

Heat Protection darf nicht an einem einzelnen Lux-Hard-Gate hängen.

Die Bewertung berücksichtigt mindestens:

- thermischen Schutzbedarf,
- Innen- und Außentemperatur,
- Solar Exposure auf der Fensterfläche,
- kanonischen Tageskontext; keine eigene Monats-/Saisonmatrix in v1,
- Luxentwicklung; Temperaturtrends in v1 nur optionale diagnostische Evidence,
- Cloud Shadow,
- Cooling Opportunity.

Verbindliches Verhalten:

- Bei hoher thermischer Belastung und weiterhin möglicher Fenstereinstrahlung bleibt Heat während einer vorüberziehenden Wolke aktiv.
- Ein Luxrückgang um ungefähr 1.000 lx darf bei ansonsten unverändert hoher Belastung nicht zu 100 % Öffnung führen.
- Das Ende von Heat wird aus dem Gesamtzustand abgeleitet, nicht aus einer einzelnen Schwellenunterschreitung.
- Exakte Temperatur-, Strahlungs- und Confidence-Bänder sind konfigurierbar beziehungsweise im Shadow-Betrieb datenbasiert zu kalibrieren.

## 10. Glare Protection

Glare wird unabhängig von Heat bewertet und besitzt kein gemeinsames Ein-/Aus-Gate mit Heat.

Verbindliches Verhalten:

- PC- und TV-Glare bleiben eigenständige Kandidaten.
- Konsolen am TV verwenden TV-Glare.
- Wenn Heat endet, muss ein weiterhin aktiver Glare-Kandidat das vollständige Öffnen verhindern.
- Erst wenn weder Heat noch Glare oder eine andere schließende Anforderung aktiv ist, darf ein Öffnungsgrund zu 100 % führen.
- Cloud Shadow kann Glare abschwächen, beendet Glare aber nicht zwangsläufig.

## 11. Cooling Opportunity und Gewitter

Cooling Opportunity wird zweistufig modelliert.

### 11.1 `storm_approaching`

- Ein heranziehender Wetterumschwung muss durch mehrere Signale gestützt werden, beispielsweise Wettercode oder Warnung, Niederschlagstrend, Wind-/Böentrend, Druck- oder Temperaturentwicklung und deutlichen Luxverlauf.
- Ein einzelner niedriger Luxwert genügt nicht.
- `storm_approaching` darf Heat fachlich lockern oder beenden.
- Andere aktive Anforderungen wie Glare oder Privacy bleiben wirksam.

### 11.2 `cool_air_available`

- Tatsächlich nutzbare kühlere Luft wird in v1 aus Innen-/Außentemperaturdifferenz und belegter Luftbewegung abgeleitet. Temperaturtrends sind optionale Diagnose für spätere v2-Arbeit; ohne definierte Einheit/Schwelle wird keine Gewichtung erfunden.
- Ist `cool_air_available` aktiv und besteht keine schließende Anforderung, darf vollständig geöffnet werden.
- Die Diagnose muss unterscheiden, ob Heat wegen Wetterumschwung oder wegen tatsächlich verfügbarer kühler Luft freigegeben wurde.

## 12. Cold Insulation

Cold ist ein eigenständiger Umweltbedarf, getrennt von Heat. Tagsüber soll
natürliches Licht einfallen, bei echter Dunkelheit darf isoliert werden.

Positive Aktivierung benötigt frischen outdoor_lux < cold_lux_enter_threshold
(Default 400 lx) sowie frische Außentemperatur <= cold_outdoor_threshold
(Default 8 °C). Bereits aktives Cold hält bis Lux > cold_lux_exit_threshold
(Default 500 lx); Exit muss größer als Enter sein. Eintritt und Entlastung
müssen zusätzlich gemäß Abschnitt 17 stabil gelten. Die 100-lx-Lücke umfasst
die Review-Schwankungen 390/410/395/420 und ist ein konservativer Kalibrierwert,
kein behaupteter Messfehler des Sensors. Alle Schwellen sind editierbar.
Unknown/stale Lux, solar_not_on_window allein oder ein fallender Temperaturtrend
dürfen Cold nicht aktivieren. Technische Safety bleibt übergeordnet.

## 13. Öffnungsgründe und Fallback

Vollständiges Öffnen darf nur durch einen positiven, diagnostizierbaren Grund entstehen. Mindestens mögliche Gründe:

- `waking`
- regulärer Tageslicht-/Grundzustand
- `cool_air_available`
- bestätigte Wetterentlastung
- manueller Benutzerbefehl
- technische Fenster-/Opening-Sicherheit

Das Fehlen eines aktiven Heat- oder Glare-Profils ist allein kein ausreichender Öffnungsgrund. `unknown`, `stale`, `unavailable` oder widersprüchliche Daten dürfen nicht unbemerkt auf 100 % zurückfallen.

## 14. Achsen-Invertierung und konfigurierbare Positionen

Jeder Modus besitzt genau einen editierbaren **logischen** Wert 0–100 %:
0 geschlossen, 100 offen. Alle Kandidaten, Gewinner und Safety arbeiten auf
dieser Achse. Invertierung verändert weder Gewinner noch Priorität, Modus
oder Suppression.

Erst an der Geräte-/Apply-Grenze gilt:
physical_target = logical_target bei axis_inverted=false,
physical_target = 100 - logical_target bei axis_inverted=true.
Eingehende numerische Geräteposition wird entsprechend normalisiert.
HA opening/closing sind semantische Zustände aus is_opening/is_closing und
werden nicht gespiegelt. Axis Inversion korrigiert ausschließlich Zahlen;
bei einem nicht vertragskonformen Geräteadapter bleibt das Shadow-Gate offen.

| Profil | Logischer Default | Invertiert, nur abgeleitet |
| --- | ---: | ---: |
| Fenster offen / Safety | 100 | 0 |
| Privacy Bett | 40 | 60 |
| Waking | 100 | 0 |
| Sleep | 5 | 95 |
| Privacy | 40 | 60 |
| Heat Protection | 15 | 85 |
| Glare TV | 60 | 40 |
| Glare PC | 75 | 25 |
| Open | 100 | 0 |

Dies sind frei kalibrierbare Defaults. Beispielsweise 60→40, 30→70,
75→25, 85→15, 50→50. Separate invertierte Eingabewerte entfallen.
Bei Migration gewinnt der bisherige Normal-Wert; alte Profilpaare bleiben
gesichert. Config v6 und Versionsrollback sind in MIGRATION.md beschrieben.
Konfigurationsänderung/Recompute/Reload erzeugt keinen Benutzer-Override.

## 15. Opening und technische Safety

Opening-Schutz ist ein technischer Safety-Pfad und kein gewöhnlicher Policy-Kandidat.

Anforderungen:

- Bei open niemals logisch abwärts: Safety verlangt mindestens die tatsächliche Istposition und die konfigurierte Safety-Position (Default 100). open und tilted sind verschieden.
- Istabweichung außerhalb Toleranz erlaubt erneute Safety-Fahrt trotz identischem früherem Command. Laufende oder vorgemerkte Abwärtsentscheidung wird bei open sofort ungültig.
- Der kanonische Opening Owner aggregiert relevante Fenster mit OR; Blind Control baut keine zweite Kontaktfusion.
- Kippstellung darf nur dann normalen Rollo-Betrieb erlauben, wenn der Opening-Contract sie ausdrücklich als sicher bewertet.
- Unbekannte, stale oder widersprüchliche Opening-Daten führen zu einem dokumentierten konservativen Verhalten.
- Fachlich gewünschtes Ziel und technisch tatsächlich freigegebenes Ziel bleiben getrennt sichtbar.
- Safety-Aktionen dürfen nicht durch Cooldown, Override oder Waking blockiert werden.

## 16. Manueller Override

Ein manueller Override entsteht ausschließlich aus einem nachweisbaren Benutzer- oder Fremdeingriff am Cover, nicht durch Blind Controls eigene Befehle, Attribut-Churn oder einen Neustart.

Anforderungen:

- eigener Schreibvorgang ist durch einen Writing Guard erkennbar,
- tatsächliche Zielposition innerhalb Toleranz und stabile Ruhe für position_settle_seconds beendet erst die eigene Fahrt,
- Bewegungstimeout meldet target_not_reached, nicht Benutzer-Override; Zwischenpositionen und Nachlauf bleiben zugeordnet,
- command_error/target_not_reached blockieren normale Automatik bis zu einem
  neuen frischen Ruhefenster (movement_recovery_seconds, Default 30 s,
  mindestens position_settle_seconds). Bewegung, Positionsänderung außerhalb
  Toleranz oder fehlende Evidence unterbrechen dieses Fenster. Danach eigene
  Attribution abbrechen, Istposition als Baseline übernehmen und nur die aktuelle
  Gesamtentscheidung bewerten. Letzter Fehler bleibt mit recovered sichtbar;
  keine alte Zielqueue und keine schnelle Retry-Schleife. Positive Safety bleibt sofort möglich.
- Position in Ruhe dient als Baseline; Restart während Bewegung wartet auf stabile Ruhe,
- `_last_target` allein ist nach einem Neustart kein ausreichender Nachweis,
- Konfigurationsänderungen erzeugen keinen Override,
- Overrides sind sichtbar, löschbar und diagnostizierbar,
- ein Override darf innerhalb derselben Medien-/Nutzungssitzung erhalten bleiben,
- ein klarer Kontextwechsel darf einen nicht mehr passenden Override deterministisch beenden,
- beim Eintritt in `waking` darf ein veralteter Override aus dem vorherigen Schlafkontext das Öffnen nicht verhindern,
- technische Safety bleibt über jedem Override.

## 17. Apply-Verhalten und Flatter-Schutz

Entscheidung und Aktorausführung werden getrennt.

- Jede relevante Eingangsänderung darf die fachliche Entscheidung unmittelbar neu berechnen.
- Ein Apply-Cooldown ist kein Lux-Debounce und darf die Diagnose nicht verzögern.
- Während eines Apply-Cooldowns wird immer das zuletzt berechnete aktuelle Ziel vorgemerkt; veraltete Zwischenziele werden nicht nachträglich gefahren.
- Sicherheitsaktionen und ausdrücklich freigegebene manuelle Aktionen dürfen den normalen automatischen Cooldown umgehen.
- Liegt die aktuelle tatsächliche Position innerhalb Zieltoleranz, entfällt der Write. Ein identischer historischer Command ist kein Dedupe-Beweis; Safety darf wiederholen.
- Nach Neustart wird kein Blindflug gefahren, bevor Inputs und Apply-Readiness ausreichend belegt sind.
- Das System muss wiederholtes Hoch-/Runterfahren durch schwankende Inputs verhindern, ohne relevante Zustandsänderungen zu verschlucken.

### Verbindliche Konkretisierung v0.6.1

Cooldown ist Motorschutz nach erfolgreichem HA-Servicehandler; Hysterese
verwendet getrennte Eintritts-/Halteschwellen; Debounce verlangt zeitlich
stabile Bedingungen. Keiner dieser drei Mechanismen ersetzt die anderen.
Heat, Glare und Cold besitzen je einen kleinen Umwelt-Transition-State ohne
Ziele oder Timerqueue. Default: Eintritt 10 s, Entlastung 120 s
(environment_enter_seconds / environment_exit_seconds, Exit mindestens Enter).
Ein Widerspruch zur laufenden Transition verwirft deren Startzeit; nur die
aktuelle Bedingung zählt. Fehlende Quality unterbricht den Stabilitätsnachweis.

Cold verwendet das Lux-Band aus Abschnitt 12. Für bereits aktives Heat/Glare
gelten Confidence und minimale solare Inzidenz mit environment_hysteresis_ratio
(Default 0.8) als niedrigere Halteschwelle. Defaults: Heat 0.55/0.44,
Glare 0.35/0.28, Inzidenz 0.05/0.04. Das 20-%-Halteband und die Zeiten
sind editierbare Kalibrierwerte, keine zusätzliche Solar-/Heat-v2.
Die rohe Solar-Diagnose bleibt unmittelbar sichtbar. Cloud Shadow bleibt
relevant; unbekannte Solar-Evidence ist weiterhin ein Quality-Blocker.

Während ein schließender Schutz eintritt, wird keine vorübergehende weiter
öffnende Freigabe erzeugt. Andere kompatible Anforderungen bleiben bewertet.
Screen-/TV-/PC-Kontext und Profilziele werden nie verzögert gespeichert.
Waking, Sleep, Privacy, Away, technische Safety, deaktivierte Automatik,
Runtime-/Owner-/Apply-Gates und Failure-Sperren bleiben unmittelbar wirksam.
Umweltzeiten erzeugen keinen eigenen Scheduler: der bestehende Recompute-Timer
prüft spätestens nach min(Freshness-Kadenz, Umwelt-Eintritt, Recovery-Ruhezeit).

HA-Service-Erfolg bedeutet nur: der Handler ist ohne Exception zurückgekehrt
(blocking=True). applied und erfolgreicher Cooldown entstehen erst danach.
Physische Zielerreichung bleibt durch Position, Motion und Settling zu belegen.

## 18. Degraded-, Unknown- und Fallback-Verhalten

Für jeden relevanten Eingang sind mindestens folgende Qualitätszustände zu berücksichtigen:

- `fresh`
- `stale`
- `unavailable`
- `conflict`
- `unknown`

Verbindliches Verhalten:

- Ein unsicherer Zustand wird nicht als normaler offener Zustand behandelt.
- Bei thermischer Gefährdung wird eine konservative Schutzposition beziehungsweise die letzte nachweislich sichere Position bevorzugt.
- Kein versteckter Fallback auf 100 %.
- Degraded-Grund, betroffene Quelle, verwendeter Ersatzwert und resultierende Einschränkung erscheinen in der Diagnose.
- Recovery nach Wiederkehr der Quelle erfolgt deterministisch und ohne künstlichen Manual Override.

## 19. UX und Bedienung

Die UX folgt [ADR 0001](https://github.com/Levtos/control/blob/main/docs/adr/0001-ux-frontend-standard.md) und [control#17](https://github.com/Levtos/control/issues/17).

### 19.1 Übersicht

Mindestens sichtbar:

- aktiver Modus und fachlicher Gewinner
- effektive Zielposition
- tatsächliche Coverposition und Fahrzustand
- Opening- und Haushaltsstatus
- Automatik, Apply und Manual Override
- wesentliche Solar-, Heat-, Glare-, Cold- und Cooling-Zustände
- kompakte manuelle Aktionen

### 19.2 Decision Trace

Der Trace zeigt mindestens:

- alle Kandidaten in fachlicher Reihenfolge,
- active/inactive und Begründung,
- konfigurierte Zielposition,
- unterdrückte Kandidaten,
- exklusiven Modus und pausierte Anforderungen,
- fachliches Ziel,
- Safety-Entscheidung,
- freigegebenes Apply-Ziel,
- tatsächlichen Schreibstatus.

### 19.3 Einstellungen

Mindestens editierbar:

- Profil aktiv/inaktiv
- ein logischer Zielwert je Profil; invertierter Wert nur abgeleitet
- Achseninvertierung
- Fensterazimut und -neigung
- relevante fachliche Schwellen und Bänder
- Apply aktiv/inaktiv
- Override löschen

### 19.4 Technik

Der verbindliche Frontend-Stack bleibt Svelte 5, Vite und TypeScript gemäß ADR 0001. UI-Komponenten greifen auf einen versionierten UX-Contract zu, nicht direkt auf rohe Home-Assistant-Entity-Strukturen.

## 20. Diagnose- und Entity-Anforderungen

Blind Control stellt eine stabile Automations- und Diagnoseoberfläche bereit.

Mindestens erforderlich:

- aktiver fachlicher Modus
- effektive Zielposition
- aktueller Solar-Exposure-Zustand
- Heat-, Glare-, Cold- und Cooling-Status
- Manual-Override-Status und Grund
- Apply-/Writing-Status
- Safety-/Blocker-Status
- Input-Freshness und Quality
- maschinenlesbarer Decision Trace
- kopierbarer Debug-Payload ohne Secrets oder unnötige private Topologie

Kanonische Entity-, Service- und Contract-Namen werden im technischen Entwurf festgelegt. Sie dürfen nicht durch historisch zufällige Slugs vorweggenommen werden.

## 21. Shadow-Modus und Migration

### 21.1 Shadow

Vor jedem produktiven Apply muss Blind Control im Shadow-Modus laufen.

- Die alte Blind Policy bleibt alleiniger Apply-Owner.
- Blind Control berechnet vollständig, sendet aber keine Cover-Befehle.
- Alte und neue Entscheidung werden feldweise verglichen.
- Unterschiede werden als erwartet, verbessert, ungeklärt oder Fehler klassifiziert.
- Das Shadow-Protokoll enthält Inputs, Kandidaten, Gewinner, Zielposition, Blocker und Zeitbezug.

### 21.2 Cutover

- Cutover erfolgt erst nach technischer Abnahme, Shadow-Abnahme und dokumentiertem Rollback-Plan.
- Technisch erfolgreiche Tests sind weder `Live` noch `Live Verified`.
- Benni entscheidet über `Live` und `Live Verified`.
- Die alte Integration bleibt bis zur Live-Verifikation rollback-fähig.
- Erst danach wird `benni_blind_policy` aus Home Assistant entfernt und das alte Repository archiviert, nicht gelöscht.
- Alte Issues werden erst geschlossen, wenn ihre Anforderungen und Evidenz nachweislich übernommen oder bewusst verworfen wurden.

### 21.3 Umbenennung der produktiven Cover-Entität

Die bestehende physische Cover-Entität wird in das kanonische englische Namensschema überführt:

- aktuell: `cover.wohnbereich_thermo_verdunklungsrollo`
- kanonisches Ziel: `cover.living_thermal_blind`
- Schema: englisches semantisches `snake_case` mit Raumpräfix für physische Geräte

Die Umbenennung darf die produktive alte Blind Policy nicht unkontrolliert unterbrechen. Sie wird deshalb als vorbereiteter, atomarer Cutover-Schritt behandelt:

1. Blind Control läuft im Shadow zunächst mit der bestehenden Entity-ID.
2. Bereits der frühe Shadow-Vertical-Slice muss Entity-Wechsel erkennen beziehungsweise nach kontrollierter Neukonfiguration wieder eindeutig dasselbe Gerät auflösen können.
3. Vor der Umbenennung werden alle Consumer und gespeicherten Referenzen inventarisiert und die notwendigen Änderungen vorbereitet.
4. Im gesperrten Cutover-Fenster wird die Legacy vollständig deaktiviert und nach HA-Neustart der Null-Writer bestätigt; erst dann folgen Rename und Consumer-Migration nach AP3_CUTOVER.md.
5. Readiness, Coverposition, Opening-Safety, Shadow-Entscheidung und Schreibschutz werden geprüft.
6. Erst danach übernimmt Blind Control den produktiven Apply-Pfad.
7. Für Rollback sind die alte Entity-ID und die notwendigen Rückänderungen dokumentiert.

Die Umbenennung wird so früh wie technisch sinnvoll durchgeführt, aber nicht als isolierte Vorabänderung, solange die alte Blind Policy alleiniger Apply-Owner ist.

## 22. Verbindliche Abnahmeszenarien

### A1 – Vorüberziehende Wolke bei Hitze

Gegeben: ungefähr 34 °C, Vormittag, passende Sonnengeometrie, Heat aktiv, Lux fällt nur ungefähr von 14.000 auf 13.000 lx.  
Erwartung: `cloud_shadow`; Heat bleibt aktiv; kein Öffnen auf 100 %.

### A2 – Heat endet, PC-Glare bleibt

Gegeben: Heat wird fachlich freigegeben, PC-Nutzung und relevantes Glare bestehen weiter.  
Erwartung: Glare PC gewinnt mit seiner konfigurierten Position; kein Open-Fallback.

### A3 – Kanonisches Waking

Gegeben: kanonischer Wake-Plan 09:30 Uhr, konkurrierende alte Quelle 08:45 Uhr.  
Erwartung: Nur der kanonische `waking`-Zustand darf Blind Control auslösen; keine Fahrt aufgrund der alten Quelle.

### A4 – Waking überschreibt Umwelt

Gegeben: `waking` tritt ein, Heat, Glare, Privacy oder Cold Insulation wären aktiv.  
Erwartung: konfigurierte Waking-Position gewinnt bis zum Übergang zu `awake`. Danach werden alle Kandidaten sofort neu bewertet.

### A5 – Gewitterannäherung mit Glare

Gegeben: Mehrere Signale bestätigen `storm_approaching`, Heat ist aktiv und TV-Glare besteht.  
Erwartung: Heat darf freigegeben werden; TV-Glare bleibt mit seiner konfigurierten Position wirksam.

### A6 – Tatsächlich kühlere Luft

Gegeben: `cool_air_available` ist belegt und keine schließende Anforderung ist aktiv.  
Erwartung: vollständiges Öffnen ist erlaubt und der Grund wird diagnostiziert.

### A7 – Dunkel und kalt

Gegeben: Nacht, außen thermisch ungünstiger als innen, kein Solar Gain, Opening sicher.  
Erwartung: Cold Insulation verwendet ihre konfigurierbare Zielposition.

### A8 – Fenster-Safety

Gegeben: Der Opening-Contract meldet eine für das Rollo unsichere Fensterstellung.  
Erwartung: Safety erzwingt die sichere Position oder blockiert die Fahrt unabhängig vom fachlichen Gewinner.

### A9 – Stale oder widersprüchliche Quelle

Gegeben: relevanter Input ist stale, unavailable oder conflict.  
Erwartung: kein stiller Open-Fallback; konservatives Verhalten mit vollständiger Diagnose.

### A10 – Eigener Schreibvorgang

Gegeben: Blind Control fährt das Cover selbst; Coverattribute ändern sich mehrfach.  
Erwartung: kein manueller Override.

### A11 – Tatsächlicher manueller Eingriff

Gegeben: Die Coverposition ändert sich außerhalb des eigenen Writing Guards.  
Erwartung: manueller Override mit nachvollziehbarer Baseline und Löschmöglichkeit.

### A12 – Neustart

Gegeben: Home Assistant oder Blind Control startet neu und `_last_target` ist noch nicht belastbar.  
Erwartung: kein falscher Override, keine ungesicherte Fahrt, korrekte Ruhepositions-Baseline.

### A13 – Konfigurationsänderung

Gegeben: Eine Zielposition wird in der UI geändert.  
Erwartung: sofortige Neuberechnung ohne falschen manuellen Override.

### A14 – Schnelle Zustandsänderungen

Gegeben: Lux, Wolken oder andere Inputs wechseln schnell.  
Erwartung: Decision Trace aktualisiert sich unmittelbar; der Apply-Pfad fährt nur das aktuelle Ziel und flattert nicht zwischen veralteten Zielen.

### A15 – Achseninvertierung

Gegeben: dieselbe Regel wird mit normaler und invertierter Achse verwendet.  
Erwartung: identischer logischer Gewinner; nur der physische Wert ist bei Invertierung 100 - logical_target.

### A16 – Cover-Entity-Rename

Gegeben: Blind Control lief im Shadow mit `cover.wohnbereich_thermo_verdunklungsrollo`; das physische Gerät wird kontrolliert auf `cover.living_thermal_blind` umbenannt.  
Erwartung: Alle Consumer sind inventarisiert, Blind Control löst nach der vorbereiteten Umstellung weiterhin eindeutig dasselbe Gerät auf, die alte Policy wird nicht unkontrolliert gebrochen und es entsteht weder eine falsche Fahrt noch ein falscher Manual Override.

## 23. Nichtfunktionale Anforderungen

- deterministische und reproduzierbare Entscheidungen
- vollständige Unit- und Integrationstests der Entscheidungsengine
- Golden-Vector-Tests für Sonnengeometrie und Strahlungsmodell
- Tests für Restart, Override, Cooldown, stale/conflict und Shadow
- versionierte Backend-, UX- und Diagnosecontracts
- keine Secrets oder privaten URLs in Logs, Issues oder Repository
- verständliche deutsche und technisch stabile maschinenlesbare Gründe
- sichere Konfigurationsmigration und Validierung
- keine Actuation aus Tests oder Shadow-Modus
- Umsetzung gemäß GitHub-only-Governance und Local-First-Workflow

### 23.1 Risikobasierte Testtiefe und Umsetzungsgeschwindigkeit

Die Tests werden nicht als pauschales Vollständigkeits-Gate vor dem ersten nutzbaren Produkt aufgebaut. Ziel ist ein früher, ausführbarer Vertical Slice und anschließend schnelle fachliche Erweiterung im Shadow-Betrieb.

Verbindliche Mindest-Gates vor jedem Merge bleiben:

- betroffene Unit- und Contract-Tests grün,
- kritische Regressionen für Safety, Waking, Override, Apply und Open-Fallback grün,
- kein produktiver Coverbefehl im Shadow-Modus,
- nachvollziehbarer Decision Trace für den umgesetzten Funktionsumfang,
- kein bekannter Datenverlust oder unkontrollierter Entity-/Config-Bruch.

Nichtkritische Vollständigkeit, seltene Varianten und UI-Polish dürfen nach dem ersten Vertical Slice iterativ folgen. Fehlende Nice-to-have-Tests blockieren nicht automatisch den nächsten Shadow-Schritt. Live-Actuation bleibt dennoch an die ausdrücklich benannten Safety-, Shadow- und Benni-Gates gebunden.

## 24. Nicht Bestandteil der ersten Version

- PV-Ertragsprognose
- selbstlernendes Produktionsmodell
- Gelände- und Gebäudeschatten
- Blackbox-KI für Rolloentscheidungen
- generischer Environment-Owner für andere Integrationen
- frei programmierbare Prioritätszahlen
- sofortige Abschaltung oder Löschung der alten Blind Policy
- produktiver Cutover ohne Shadow, Rollback und Bennis Live-Gates

## 25. Arbeitspakete

Die Umsetzung bleibt auf drei zusammenhängende Arbeitspakete begrenzt.

### AP1 – Lastenheft, Inventar, Contracts und Repository-Gründung

- Lastenheft abnehmen und versionieren
- das bereits angelegte, leere Repository `Levtos/blind_control` unmittelbar lauffähig bootstrappen
- Old→New-Inventar erstellen
- Owner-/Contract-Matrix abschließen
- Architektur- und Migrationsnotiz erstellen
- `control#31` auf kanonischen Namen und neue Entscheidungen aktualisieren
- keine Live-Actuation

AP1 wird bewusst schlank und zeitlich begrenzt. Das Repository besteht bereits; ein minimal lauffähiges Integrationsgerüst darf parallel zum Inventar beginnen. Ein perfektes Inventar ist kein Vorwand, den Produktstart aufzuschieben. Vor dem jeweiligen Consumer-Cutover muss der betroffene Inventarteil jedoch vollständig sein.

### AP2 – Vollständige Shadow-Implementierung

- zuerst einen frühen Vertical Slice aus Konfiguration → Inputs → Entscheidung → Trace → Shadow-Snapshot liefern
- Backend und versionierte Contracts
- Entscheidungsengine und Kompatibilitätsmodell
- Solar Exposure
- Konfiguration und Migration
- Safety, Apply und Override-Lifecycle
- Übersicht, Diagnose und Einstellungen
- automatisierte Tests
- Shadow-Vergleich ohne Coverbefehle

Der Vertical Slice soll so früh wie möglich in Home Assistant installierbar sein. Weitere Fachmodule werden danach inkrementell ergänzt und anhand realer Traces geprüft, statt die vollständige Integration ausschließlich außerhalb von Home Assistant fertigzustellen.

### AP3 – Cutover und kontrollierte Ablösung

- Shadow-Differenzen erklären und abnehmen
- Rollback-Protokoll
- kontrollierter Wechsel des Apply-Owners
- Bennis Live-Test und `Live Verified`
- alte Integration entfernen
- alte Issues mit Nachweis schließen
- Repository `benni_blind_policy` archivieren

## 26. Status der fachlichen Entscheidungen

### Verbindlich entschieden

- Name und Domain `blind_control`
- Repository `Levtos/blind_control` ist angelegt und einsatzbereit
- Neuaufbau statt Rename
- drei Arbeitspakete
- Minimum-Prinzip für kompatible Anforderungen
- `waking` als exklusiver Aufweckmodus bis `awake`
- nur kanonischer Wake-Zustand
- PlayStation/Konsolen verwenden TV-Glare
- ein logischer Profilwert vollständig editierbar, Invertierung als 100 - x
- Achseninvertierung als eigenständige UI- und Laufzeitfunktion
- lokaler Außen-Luxsensor am Fensterrahmen
- Fensterorientierung ungefähr 124° OSO, Neigung 90°
- kanonischer Zielname der Cover-Entität `cover.living_thermal_blind`
- Solar Exposure statt einzelner Lux-Hard-Grenze
- Cloud Shadow beendet Heat nicht automatisch
- Heat und Glare unabhängig
- zweistufige Cooling Opportunity
- Cold Insulation als eigener Bedarf
- positive Öffnungsgründe statt Open-Fallback
- konservatives und diagnostiziertes Unknown-/Stale-Verhalten
- Shadow, Rollback, Live und Live Verified als getrennte Gates

### Im Shadow-Betrieb zu kalibrieren, nicht als neue Grundsatzrunde

- genaue Temperatur-, Lux- und Strahlungsbänder
- Confidence-Grenzen für `cloud_shadow`
- genaue Trendfenster für Wetterumschwung und kühlere Luft
- initialer Zielwert für neue Profile wie Cold Insulation
- Apply-Cooldown und technische Toleranzen

Diese Werte werden als konfigurierbare Defaults implementiert und anhand realer Traces abgestimmt. Ihre Kalibrierung blockiert weder Lastenheft noch Repository-Gründung.

## 27. Abnahme des Lastenhefts

Das Lastenheft v0.1 ist fachlich abnahmefähig, wenn:

- die verbindlichen Entscheidungen vollständig und widerspruchsfrei enthalten sind,
- `control#31` anschließend auf die abweichenden neuen Entscheidungen aktualisiert wird,
- alle noch variablen Zahlen ausdrücklich als Konfiguration oder Shadow-Kalibrierung markiert sind,
- aus den drei Arbeitspaketen klar abgegrenzte Codex-Issues mit Akzeptanzkriterien abgeleitet werden können.

Die fachliche Grundstruktur wurde von Benni am 15. August 2026 grundsätzlich als ordentlich und verwendbar bestätigt. Version 0.2 ergänzt die ausdrücklich gewünschte Achsen-Invertierfunktion, den kontrollierten Cover-Entity-Rename und den beschleunigten, risikobasierten Produktstart.

## 28. Verbindliche AP2-Nachbesserung: Statusmodell und Projektion

Dieser Abschnitt ist für AP2 normativ und präzisiert die Darstellung des
bereits beschlossenen Entscheidungsmodells. Er autorisiert weder Cutover noch
eine produktive Fahrt.

### 28.1 Fachlicher Mastermodus

Der Mastermodus beschreibt ausschließlich den Betriebszustand und hat genau
drei Werte:

- `normal`: reguläre automatische Auswertung;
- `manual`: ein nachgewiesener fremder manueller Override hält;
- `failure`: fehlende Entscheidungsqualität oder ein Contractfehler verhindert
  eine belastbare automatische Entscheidung.

Safety, Apply, Opening, Cover-Readiness und Shadow/Live sind technische
Ebenen. Sie bleiben separat sichtbar und werden nicht als fachlicher
Mastermodus ausgegeben. Ein bekannter neutraler Zustand ohne besonderen
Schutzkandidaten ist weiterhin `normal`, nicht `failure`.

### 28.2 Hierarchische Entscheidung und kompatible Nebenäste

Unter `normal` wird der Gewinner als Kategorie und gegebenenfalls Variante
ausgegeben:

- `waking`, `sleep`, `away`, `privacy` oder `neutral`;
- `glare -> general|tv|pc`;
- `climate -> heat|cold|storm|cool_air`.

`pc` und `tv` sind damit Varianten von `glare`, nicht gleichrangige Kategorien.
Der original Candidate-Key und die Zielposition bleiben maschinenlesbar. Die
Minimum-Komposition kompatibler Zielpositionen bleibt unverändert: Unterlegene,
aber aktive Anforderungen werden nicht entfernt, sondern als aktive Nebenäste
mit Quality, Source, Reason und einer möglichen Unterdrückung ausgewiesen.

Beispiel: Fordert Heat 15 % und PC-Glare 75 %, lautet die Projektion
`normal -> climate -> heat`; `glare -> pc` bleibt als aktiver Nebenast sichtbar
und das fachliche Ziel ist 15 %. Endet Heat, gewinnt `normal -> glare -> pc`.
Waking bleibt exklusiv: nur bereits tatsächlich aktive Heat-, Glare-, Privacy-
und Cold-Äste werden pausiert und bleiben im Trace sichtbar, bis der
kanonische Bio-State `awake` erreicht ist. Fachlich inaktive Kandidaten bleiben
in der flachen Diagnose, gehören aber nicht zu `active_branches`.

Die UX muss mindestens folgende Pfade lesbar darstellen:

- `Normal -> Glare -> PC`;
- `Normal -> Glare -> TV`;
- `Normal -> Climate -> Heat`;
- `Normal -> Waking`;
- `Manual -> Override`;
- `Failure -> Input-/Contract-Grund -> Position halten oder Apply blockiert`.

Die bisherige flache Darstellung `active_mode`/`winner_keys` darf als
Kompatibilitäts- und Diagnoseansicht bestehen bleiben, aber nicht als alleiniger
Entscheidungsbaum.

### 28.3 Failure-Verhalten

Bei `failure` gibt es keine neue automatische Fahrt. Die Auswertung hält die
aktuelle oder zuletzt nachweislich sichere Position; ist dies nicht belastbar
möglich, wird Apply blockiert. Es gibt keinen generischen Fallback auf 100 %.
Vollständig öffnen ist während Failure nur aufgrund einer positiv belegten
Safety-Anforderung zulässig; diese verwendet das konfigurierte
logischen Profilwert der Safety-Position; Geräteumrechnung erst am Adapter. `unknown`, `stale`,
`unavailable` oder `conflict` einer Opening-Evidence erzeugen keine
Öffnungsfahrt. Ein automatischer Öffnungskandidat darf die Quality-Prüfung
nicht überspringen: Innen-/Außentemperatur, Activity/Belegung sowie die
zwingende Solar-Evidence aus Sonnengeometrie und Außenlux müssen die mögliche
schließende Schutzanforderung positiv ausschließen. Lux-Trend, direkte/diffuse
Modellstrahlung und Bewölkung sind ersetzbare Zusatz-Evidence: Sie erhöhen
Confidence, sind aber nicht einzeln verpflichtend. Fehlt die Kombination
insgesamt oder widersprechen sich Day State und Sonnenstand, bleibt die
Entscheidung `failure`. `missing` gehört dabei ebenso
zur Failure-Evidence wie `unknown`, `unavailable`, `stale` und `conflict`.
`failure.quality_blockers` nennt die konkreten nicht belastbaren Felder, ohne
Bindings oder Rohwerte offenzulegen.

### 28.4 Live-Owner-Adapter und Capability-Modell

Blind Control adaptiert Owner-Contracts feldspezifisch und erfindet keine
zweite Fachwahrheit. Presence wird auf `away=true` für `away`, `not_home` und
`abwesend` sowie `away=false` für `home` und `zuhause` normalisiert; ein
gültiges `away_gate`-Attribut hat Vorrang. Activity wird aus dem kanonischen
Core-State-Gewinner plus dokumentierten Attributen in die Glare-Kontexte
`tv`, `pc`, `screen` oder `none` projiziert. Gleichzeitige positive Signale
verwenden deterministisch `tv > pc > screen`; `music` löscht positive PC- oder
Entertainment-Evidence nicht.

Der kanonische Day-State-Vertrag besteht exakt aus `early_night`,
`late_night`, `early_morning`, `forenoon`, `midday`, `afternoon`,
`late_afternoon`, `evening` und `late_evening`. Tageslichtphasen sind
`early_morning` bis `late_afternoon`; `evening` und `late_evening` sind
Übergang, `early_night` und `late_night` Nacht.

Opening-Safety-Signale benötigen eine explizit konfigurierte positive oder
negative Polarität. Aus Entity-Namen wird keine Invertierung abgeleitet.
Standard-Cover-Zustände wie `open` oder `closed` bedeuten verfügbar, sofern HA
den Zustand nicht als `unavailable` markiert. Die Position kommt ausschließlich
aus `current_position`; ein Source-Timestamp hat Vorrang, der normale
HA-Zeitstempel eines Standard-Covers ist als Freshness-Evidence zulässig.
Restore-Evidence bleibt degradiert und kann keinen Override begründen.
v0.6.2 konkretisiert: eine gültige ruhende Standard-Coverposition ohne expliziten
Device-Timestamp verliert ihre Baseline nicht allein durch einen alten
HA-Änderungszeitpunkt. Bewegte Position und explizite Device-Evidence behalten
ihre Altersprüfung; negative, ungültige oder restored Evidence bleibt blockierend.
Motion hat eigene semantische Quality, ersetzt aber niemals die numerische
Position. Timestamp-Precedence und genaue Grenzen: CONTRACTS.md Abschnitt 7.1.

### 28.5 Bindings und stabile Diagnoseprojektion

Owner-Bindings werden ausschließlich in den nativen
Home-Assistant-Entity-Selectoren des OptionsFlow bearbeitet und fachlich
gruppiert: Core State, Opening/Safety/Cover, Solar, Temperatur/Wetter und
Legacy-Vergleich. Leere Slots sind nicht konfiguriert und werden weder als
Entität gespeichert noch im Panel als vorhandene Entität dargestellt. Das
Panel zeigt nur Binding-Status und verweist für die Bearbeitung auf den
OptionsFlow. Entity-IDs gehören weder in Debug-Payloads noch in die öffentliche
UX-Projektion.

Für Automationen und Diagnose ist `blind_control.automation_projection.v3`
eine kleine stabile, redigierte read-only Contractprojektion mit Mastermodus,
aktiver Kategorie/Variante, Failure-Status/-Grund/-Blockern, fachlichem und
effektivem Ziel sowie Safety-/Apply-/Shadow-Status. AP2 veröffentlicht sie über
genau eine diagnostische Statusentität aus der Entity Registry: ihr Zustand ist
der Mastermodus, die genannten Werte sind stabile Attribute. Die
Integrationsinstanz bestimmt die Entity-ID selbst; weder Produktcode noch
Dokumentation tragen eine installationsspezifische ID vor. Es gibt keine
Services, keine Steuerung und keine Entity-Flut. AP3 ergänzt ausschließlich
die technischen Attribute `runtime_mode` und `apply_owner`; die Entity bleibt
read-only.

Historische AP2-Feldzahl (durch Config v6 ersetzt): 89 sichtbare Felder, davon 55 mit Defaults
versehene allgemeine/Positionswerte, eine private interne Open-Meteo-URL, 28
aktuelle Input-Bindings, vier optionale Legacy-Vergleichsbindings und eine
explizite Opening-Safety-Polarität. Von den
28 Inputs sind zwölf fachlich und vier technisch zwingend, ein Safety-Signal
ist bedingt und elf Evidence-Signale sind optional. Fehlende optionale Trends
oder Modellstrahlung sind bewusst leer und allein kein Failure-Grund.

Eine kleine installationslokale Suggestion darf vorhandene Owner über ihre
publizierten Contracts vorfüllen. Sie ist keine zentrale Binding Registry,
enthält keine festen Installations-IDs und überschreibt weder eine gespeicherte
Nutzerwahl noch einen bewusst geleerten Slot. Der Panelstatus unterscheidet
aufgelöste/nicht aufgelöste Pflichtfelder, aufgelöste/nicht anwendbare
Conditional-Felder, gebundene/bewusst leere Optionals und
gebundene/nicht verfügbare Legacy-Vergleiche.

Optionale Modellstrahlung wird durch einen isolierten internen Blind-Control-
Provider mit genau einem gemeinsamen read-only Abruf bereitgestellt: aktuelles
`direct_normal_irradiance_instant` als direkte und aktuelles
`diffuse_radiation_instant` als diffuse Strahlung, Modell
`dwd_icon_seamless`, 15-Minuten-Rhythmus, ohne API-Key. Konfiguration erfolgt
vollständig über ConfigFlow/OptionsFlow; YAML, Package, `secrets.yaml`, PV-
Felder und separate Koordinatenformulare sind ausgeschlossen. Blind Control
stellt beide Werte zusätzlich als normale read-only Sensorentitäten bereit.
Explizite externe Bindings haben Vorrang. Lokaler Außenlux bleibt zwingende
Echtzeitbeobachtung und ein fehlender Lux-Trend wird weiterhin intern aus
frischen Beobachtungen abgeleitet. Core State und Weather State bleiben
unverändert; der Provider ist hinter dem Evidence-Adapter austauschbar.

Config-v6-Fortschreibung: 79 Felder im initialen ConfigFlow, 81 im OptionsFlow; je Profil nur ein logischer Wert, neue Cold-/Motion-/Cloud-Kalibrierung. Sie ersetzt die historischen AP2-Feldzahlen.
