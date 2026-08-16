# Lastenheft Blind Control

**Dokumentstatus:** v0.2 – fachlich grundsätzlich abgenommen, Ergänzungen für frühen Produktstart  
**Stand:** 15. August 2026  
**Zielprodukt:** Home-Assistant-Integration `blind_control`  
**Übergeordnete Entscheidung:** [Levtos/control#31](https://github.com/Levtos/control/issues/31)

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
- erst nach Bennis `Live Verified` produktiver Apply-Owner werden.

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

Sleep bleibt ein eigenständiger fachlicher Zustand. Waking wird ausschließlich aus dem kanonischen Zustand übernommen und darf nicht aus einer lokalen Blind-Control-Uhrzeit abgeleitet werden.

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

### 8.3 Zustände

Mindestens folgende Zustände werden ausgegeben:

- `direct_sun`: direkte Sonne kann das Fenster treffen
- `cloud_shadow`: Sonne könnte das Fenster treffen, ist momentan jedoch durch eine Wolke abgeschwächt
- `diffuse_bright`: relevantes Streulicht ohne starke direkte Sonne
- `solar_not_on_window`: Sonne ist vorhanden, trifft die Fensterfläche aber geometrisch nicht relevant
- `night`: keine solare Einstrahlung möglich
- `unknown`: Daten fehlen, sind stale oder widersprüchlich

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
- Tages- und Saisonkontext,
- Temperatur- und Luxentwicklung,
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

- Tatsächlich nutzbare kühlere Luft wird aus Innen-/Außentemperatur, Temperaturtrend und Luftbewegung abgeleitet.
- Ist `cool_air_available` aktiv und besteht keine schließende Anforderung, darf vollständig geöffnet werden.
- Die Diagnose muss unterscheiden, ob Heat wegen Wetterumschwung oder wegen tatsächlich verfügbarer kühler Luft freigegeben wurde.

## 12. Cold Insulation

Cold Insulation ist ein eigenständiger Umweltbedarf.

Sie darf aktiv werden, wenn mindestens folgende Sachlage belegt ist:

- draußen ist es dunkel,
- die Außentemperatur ist kalt beziehungsweise thermisch ungünstiger als innen,
- es besteht kein sinnvoll nutzbarer solarer Wärmeeintrag,
- technische Opening-Sicherheit erlaubt das Absenken.

Die Zielposition ist vollständig konfigurierbar. Als initialer Vorschlag darf dieselbe Position wie bei Sleep verwendet werden; sie ist keine fest verdrahtete Geschäftsregel.

Während `waking` wird Cold Insulation überstimmt. Eine spätere Funktion `passive_solar_gain`, die an kalten sonnigen Tagen gezielt öffnet, ist eine mögliche Erweiterung und nicht Teil der ersten Abnahme.

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

Alle fachlichen Zielpositionen bleiben wie in der bisherigen Oberfläche manuell editierbar.

Anforderungen:

- Wertebereich 0–100 %
- getrennte Zielwerte für normale und invertierte Achse
- Achseninvertierung als vollwertige Funktion pro Instanz
- Achseninvertierung ist in den Einstellungen ein- und ausschaltbar und ihr aktueller Zustand ist in Übersicht und Diagnose sichtbar
- bei aktiver Invertierung wird der ausdrücklich konfigurierte invertierte Zielwert verwendet; er wird nicht stillschweigend als mathematisches Komplement des normalen Werts errechnet
- sichere Validierung und verständliche Fehlermeldung
- Änderung eines Zielwerts oder der Achseninvertierung löst eine Neuberechnung aus
- Konfigurationsänderungen dürfen nicht als manueller Cover-Override erkannt werden
- Logik und Position bleiben getrennt: Ein Modus kann fachlich gewinnen, während sein Zielwert frei konfigurierbar bleibt

Initial zu migrierende Live-Werte des Wohnzimmerprofils:

| Profil | Normal | Invertiert |
| --- | ---: | ---: |
| Fenster offen / Safety | 100 % | 0 % |
| Privacy Bett | 40 % | 60 % |
| Waking | 100 % | 0 % |
| Sleep | 5 % | 60 % |
| Privacy | 40 % | 60 % |
| Heat Protection | 15 % | 55 % |
| Glare TV | 60 % | 40 % |
| Glare PC | 75 % | 25 % |
| Open | 100 % | 0 % |

Diese Werte sind Migrationsdefaults, keine unveränderlichen Anforderungen. Neue Profile wie Cold Insulation erhalten dieselbe Konfigurierbarkeit.

## 15. Opening und technische Safety

Opening-Schutz ist ein technischer Safety-Pfad und kein gewöhnlicher Policy-Kandidat.

Anforderungen:

- Vollständig geöffnetes Fenster muss eine für Rollo und Fenster sichere Position erzwingen beziehungsweise eine unsichere Fahrt blockieren.
- Kippstellung darf nur dann normalen Rollo-Betrieb erlauben, wenn der Opening-Contract sie ausdrücklich als sicher bewertet.
- Unbekannte, stale oder widersprüchliche Opening-Daten führen zu einem dokumentierten konservativen Verhalten.
- Fachlich gewünschtes Ziel und technisch tatsächlich freigegebenes Ziel bleiben getrennt sichtbar.
- Safety-Aktionen dürfen nicht durch Cooldown, Override oder Waking blockiert werden.

## 16. Manueller Override

Ein manueller Override entsteht ausschließlich aus einem nachweisbaren Benutzer- oder Fremdeingriff am Cover, nicht durch Blind Controls eigene Befehle, Attribut-Churn oder einen Neustart.

Anforderungen:

- eigener Schreibvorgang ist durch einen Writing Guard erkennbar,
- Position in Ruhe dient als Baseline,
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
- Identische Zielpositionen erzeugen keine wiederholten Service-Aufrufe.
- Nach Neustart wird kein Blindflug gefahren, bevor Inputs und Apply-Readiness ausreichend belegt sind.
- Das System muss wiederholtes Hoch-/Runterfahren durch schwankende Inputs verhindern, ohne relevante Zustandsänderungen zu verschlucken.

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
- Zielposition normal/invertiert
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
4. In einem kurzen Cutover-Fenster wird der alte Apply-Pfad pausiert, die Entity umbenannt und jede betroffene Referenz aktualisiert beziehungsweise verifiziert.
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
Erwartung: jeweils der konfigurierte Zielwert wird korrekt angewandt und diagnostiziert.

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
- Positionen normal/invertiert vollständig editierbar
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
Waking bleibt exklusiv: pausierte Heat-, Glare-, Privacy- und Cold-Äste bleiben
im Trace sichtbar, bis der kanonische Bio-State `awake` erreicht ist.

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
Normal-/Invertiert-Profil der Safety-Position. `unknown`, `stale`,
`unavailable` oder `conflict` einer Opening-Evidence erzeugen keine
Öffnungsfahrt.

### 28.4 Bindings und stabile Diagnoseprojektion

Optionale Owner-Bindings werden ausschließlich in den nativen
Home-Assistant-Entity-Selectoren des OptionsFlow bearbeitet und fachlich
gruppiert: Core State, Opening/Safety/Cover, Solar, Temperatur/Wetter und
Legacy-Vergleich. Leere Slots sind nicht konfiguriert und werden weder als
Entität gespeichert noch im Panel als vorhandene Entität dargestellt. Das
Panel zeigt nur Binding-Status und verweist für die Bearbeitung auf den
OptionsFlow. Entity-IDs gehören weder in Debug-Payloads noch in die öffentliche
UX-Projektion.

Für Automationen und Diagnose ist eine kleine stabile
`blind_control.automation_projection.v1` mit Mastermodus, Gewinnerkategorie,
Gewinnervariante, fachlichem/effektivem Ziel sowie Safety-/Apply-/Shadow-Status
vorgesehen. Sie ist eine read-only Contractprojektion und erzeugt in AP2 keine
zusätzliche Entity-Flut.
