# Lastenheft – Blind Control

**Dokumentversion:** 0.2

**Fachlicher Status:** grundsätzlich abgenommen mit der verbindlichen
Fortschreibung vom 15. August 2026 in [`control#31`](https://github.com/Levtos/control/issues/31).

**Normativer Charakter:** Dieses Dokument beschreibt das vollständige
Produktziel. AP1 implementiert davon nur den nicht-aktiven Bootstrap; die
AP1-Grenze ist keine Kürzung oder Ablösung des Lastenhefts.

## 1. Verbindliche Quellen und Vorrang

Die fachliche Reihenfolge und der Vorrang der Quellen sind:

1. [`blind_control#1`](https://github.com/Levtos/blind_control/issues/1)
   für Repository, Mindestumfang, Defaults und Abschlussformat;
2. [`control#31`](https://github.com/Levtos/control/issues/31) für die
   Architekturentscheidung und die Fortschreibung vom 15. August 2026;
3. [`blind_control#2`](https://github.com/Levtos/blind_control/issues/2) für
   den verbindlichen Shadow-Vertical-Slice, die fachlichen Einzelregeln und
   die Pflichtregressionen;
4. [ADR 0001](https://github.com/Levtos/control/blob/main/docs/adr/0001-ux-frontend-standard.md),
   [ADR 0002](https://github.com/Levtos/control/blob/main/docs/adr/0002-github-only-governance.md)
   und [`control#17`](https://github.com/Levtos/control/issues/17) für UX und
   Governance.

Das reviewed Wohnzimmer-Rollo-Lastenheft im
[`einhornzentrale`-Repository](https://github.com/Levtos/einhornzentrale/tree/main/docs/lastenhefte/reviewed/rollo)
und die alte Integration `benni_blind_policy` sind Ist-/Regressionsevidence.
Widersprechende ältere Regeln (insbesondere altes Lux-Hard-Gate, alte
Waking-Semantik und alte Fallbacks) gelten nicht als Zielentscheidung.

## 2. Produkt, Repository und Migration

- Kanonisches Repository und Domain sind ausschließlich
  `Levtos/blind_control` und `blind_control`.
- Produkt- und UI-Name ist **Blind Control**; das neue Produkt verwendet
  keinen `benni_`-Präfix.
- Die alte Integration `benni_blind_policy` bleibt bis nach Shadow, Cutover,
  Bennis `Live` und `Live Verified` vollständig erhalten, aktiv und
  rollback-fähig.
- Das alte Repository wird später archiviert, nicht gelöscht.
- Das reale Wohnzimmer-Cover heißt aktuell
  `cover.wohnbereich_thermo_verdunklungsrollo`.
- Der kanonische Zielname für den späteren Cutover ist
  `cover.living_thermal_blind`.
- Der Rename ist in AP1 und während der alleinigen Alt-Apply-Phase verboten.

Blind Control übernimmt später fachliche Rollo-Entscheidung, Zielposition,
Trace, Diagnose, Konfiguration, Override-Lifecycle, UX und den freigegebenen
Apply-Pfad. Es ist kein bloßer Rename und kein Umbau der alten Integration.

## 3. Ownership und Contracts

Blind Control konsumiert kanonische Verträge, rekonstruiert aber keine fremden
Wahrheiten.

| Bereich | Owner-/Vertragsentscheidung |
| --- | --- |
| `activity_state`, `bio_state`, `day_state`, Presence, Away, Sleep, Waking | Core State; kein lokales Recompute und keine Legacy-Zweitquelle |
| Opening/Fenster, Freshness, Quality und primitive technische Fakten | Core Contracts oder ein ausdrücklich beschlossener technischer Contract |
| Lux, Außentemperatur, Wetter, Wolken, Wind, Böen, Warnungen, Sonnenstand | jeweilige technische Owner; konkrete Binding-/Freshness-Lücken sind Gates |
| Solar Exposure | Blind-spezifische Ableitung für die konfigurierte Fensterfläche, nicht Rohwahrheit |
| fachliche Kandidaten, Gewinner, effektives Ziel, Reason-/Decision-Trace | Blind Control |
| Override-Lifecycle, Konfiguration und Blind-UX | Blind Control |
| technische Readiness, Safety-Freigabe und Apply-Entscheidung | Blind Control als getrennte technische Grenze |
| eigentliche Cover-Actuation | späterer freigegebener Apply-Pfad; nicht AP1 |

Jeder Eingang benötigt vor Implementierung eine konkrete Quelle, Version,
Consumer, Freshness-/Quality-/Conflict-Regel und ein dokumentiertes Verhalten
für `unknown`, `stale`, `unavailable`, `degraded`, `restore` und Konflikte.
Offene Owner- oder Freshness-Fragen sind Blocker und werden nicht durch
Entity-Aliase, alte YAML oder lokale Heuristik geschlossen.

## 4. Fachlicher Entscheidungsbaum

Die Reihenfolge ist:

```text
Grundzustand -> Modus -> Umwelt -> technische Safety/Apply-Prüfung
```

### 4.1 Grundzustand

Die Kontexte sind:

- `weekday`
- `weekend`
- `holiday`
- `vacation`

`holiday` darf anfangs dieselben Werte wie `weekend` verwenden, bleibt aber
als eigener Kontext erhalten. `vacation` ist ein eigener Kontext für längere
Abwesenheit. Anwesenheit/Away bleibt trotzdem ein Core-State-Eingang.

### 4.2 Modus

Mindestens enthalten sind:

- `sleep`
- `waking`
- `away`
- `private_time`
- `privacy`

Die Gründe bleiben im Trace sichtbar, auch wenn mehrere Regeln auf dieselbe
Position führen. Ein generisches `open` ersetzt keinen fachlichen Grund.

`waking` ist exklusiv: Der kanonische Waking-Zustand gewinnt bis `awake` mit
seiner konfigurierbaren Position, initial 100 %, gegen Heat, Glare, Privacy
und Cold Insulation. Technische Safety, fehlende Readiness und deaktivierte
Automatik bleiben übergeordnet. Nach `awake` wird sofort vollständig neu
berechnet. Es gibt keine eigene Vorweckzeit und keine Legacy-Wake-Quelle.

### 4.3 Umwelt

Die Umweltkategorien sind mindestens:

- `climate`: `heat`, `cold`;
- `glare`: `general`, `tv`, `pc`;
- `storm_approaching`;
- `cool_air_available`;
- `cold_insulation`.

Heat und Glare sind unabhängige Demands. PlayStation, andere Konsolen und
Streaming am TV verwenden `glare_tv`; ein eigenes PlayStation-Profil entfällt.

### 4.4 Kompatible Demands und Minimum-Prinzip

- `0 %` bedeutet geschlossen, `100 %` vollständig geöffnet.
- Jede aktive oder inaktive Regel bleibt mit `active`, Zielposition,
  Bedingung/Quelle und Diagnosegrund nachvollziehbar.
- Kompatible aktive Anforderungen werden in der gewählten Achse mit der
  kleinsten Zielposition zusammengeführt.
- Spätere Ebenen dürfen weiter schließen, aber nicht ohne dokumentierten
  fachlichen Grund wieder öffnen.
- `waking` ist die ausdrücklich dokumentierte exklusive Ausnahme.
- Widersprüchliche oder stale Zustände werden deterministisch mit Diagnose
  behandelt; Prozentwerte lösen keinen unbekannten Konflikt zufällig auf.

Beispiele: Grundzustand 100 %, Sleep 25 %, Heat 40 % ergibt 25 %. Grundzustand
100 %, TV-Glare 60 %, Heat 40 % ergibt 40 %.

## 5. Solar Exposure

Solar Exposure ist eine fensterbezogene Blind-Control-Ableitung aus:

- Sonnenhöhe und Sonnenazimut;
- Fensterazimut und Fensterneigung;
- Modellstrahlung beziehungsweise direkter/diffuser Strahlung, soweit
  verfügbar;
- Wolken-/Wettererwartung;
- lokalem Außen-Lux und Luxtrend;
- Freshness, Quality und Source Conflict aller verwendeten Quellen.

Die verbindliche Initialgeometrie ist:

- Fensterazimut 124° OSO;
- Fensterneigung 90°;
- Außen-Luxsensor am Fensterrahmen;
- innenliegendes Thermorollo beeinflusst den Außen-Luxsensor nicht.

Mindestens auszugeben und im Trace zu unterscheiden sind:

- `direct_sun`;
- `cloud_shadow`;
- `diffuse_bright`;
- `solar_not_on_window`;
- `night`;
- `unknown`.

Die Diagnose umfasst mindestens Einfallsfaktor, erwartete Strahlung oder
relativen Erwartungswert, lokalen Luxwert und Trend, Abschattung, Confidence,
Quellen und Reason. `unknown` darf nicht in einen positiven Öffnungsgrund oder
einen stillen 100-%-Fallback umgedeutet werden.

Helios-/Helios-Forecast-Ideen dürfen als fachliche Referenz dienen. GPL-3.0-
Code wird nicht ungeprüft übernommen; eigene Standardformeln werden separat
dokumentiert und mit Golden Vectors geprüft, falls dieser Pfad umgesetzt wird.

## 6. Heat, Glare, Cooling und Cold

### 6.1 Heat

- Heat verwendet kein einzelnes Lux-Hard-Gate.
- Thermischer Bedarf, Innen-/Außentemperatur, Solar Exposure,
  Tages-/Saisonkontext und Trends werden gemeinsam bewertet.
- `cloud_shadow` beendet Heat bei fortbestehender thermischer Last nicht
  automatisch.
- Exakte Bänder bleiben konfigurierbar und werden anhand von Shadow-Traces
  kalibriert.

### 6.2 Cooling Opportunity

- `storm_approaching` benötigt mehrere Wetter-/Trend-Signale und darf Heat
  lockern; andere schließende Kandidaten bleiben bestehen.
- `cool_air_available` bedeutet tatsächlich nutzbare kühlere Außenluft.
- Vollständiges Öffnen wegen `cool_air_available` ist nur erlaubt, wenn kein
  schließender Kandidat aktiv ist.
- Beide Gründe werden im Trace getrennt diagnostiziert.

### 6.3 Cold Insulation

Cold Insulation ist ein eigener Umweltbedarf bei Dunkelheit, thermisch
ungünstiger Außenluft und ohne sinnvollen Solar Gain. Die Zielposition ist
vollständig konfigurierbar. Während `waking` ist dieser Bedarf pausiert.
`passive_solar_gain` gehört nicht zu diesem Arbeitsstand.

## 7. Opening und technische Safety

Technische Blocker sind kein normaler Ast des fachlichen Minimum-Baums. Zu
prüfen sind mindestens:

- Fenster-/Opening-Schutz;
- Cover `unavailable`;
- blockierter oder fehlerhafter Aktor;
- stale/degraded/source-conflict relevanter Contracts;
- Startup-/Apply-Readiness.

Ein vollständig offenes oder unsicher gemeldetes Fenster erzwingt eine sichere
Position oder blockiert die Fahrt. Kippstellung ist nur zulässig, wenn der
Opening-Contract sie ausdrücklich als sicher bewertet. Fachliches Ziel und
technisch freigegebenes Ziel bleiben getrennt diagnostizierbar.

Ein positives Öffnen braucht einen positiven, belastbaren Grund. Fehlende,
stale, unavailable oder konfliktäre Evidence erzeugt keinen stillen
Open-Fallback und keine erfundene geschlossene oder offene physische Wahrheit.
Safety wird nie durch Cooldown, Override oder Waking blockiert.

## 8. Konfiguration, Positionen und Achseninvertierung

- Alle fachlichen Profile sind von 0 bis 100 % editierbar.
- Normal- und Invertiert-Werte werden getrennt gespeichert.
- Achseninvertierung ist eine eigene UI-/Runtime-Option pro Instanz.
- Der invertierte Wert wird ausdrücklich konfiguriert; er wird nicht
  automatisch mathematisch aus dem Normalwert angenommen.
- Eine Konfigurationsänderung löst Neuberechnung, aber keinen Manual Override,
  aus.

Die verbindlichen Migrationsdefaults sind:

| Demand/Modus | normal | invertiert |
| --- | ---: | ---: |
| Window Safety | 100 | 0 |
| Privacy Bed | 40 | 60 |
| Waking | 100 | 0 |
| Sleep | 5 | 60 |
| Privacy | 40 | 60 |
| Heat | 15 | 55 |
| TV Glare | 60 | 40 |
| PC Glare | 75 | 25 |
| Open | 100 | 0 |

Die Werte sind editierbare Migrationsdefaults, kein AP1-Apply-Befehl und keine
Behauptung über einen aktuell registrierten HA-Wert.

## 9. Override, Writing Guard, Decision und Apply

- Manual Override entsteht nur bei nachweisbarem Fremd-/Benutzereingriff.
- Ein Writing Guard erkennt eigene Befehle und deren Echo.
- Die Ruhepositions-Baseline wird berücksichtigt; `_last_target` allein reicht
  nach einem Neustart nicht als Override-Nachweis.
- Eigener Write, Attribut-Churn, Optionsänderung und Restart erzeugen keinen
  Manual Override.
- Ein Override ist sichtbar, erklärbar und löschbar.
- Ein Kontextwechsel beendet einen nicht mehr passenden Override deterministisch.
- Fachliche Decision und technische Apply-Entscheidung sind getrennt.
- Im Shadow wird das beabsichtigte Apply vollständig berechnet, aber niemals
  ausgeführt.
- Rate Limiter/Cooldown behalten nur das jüngste Ziel; veraltete Nachfahrten
  sind unzulässig.

## 10. Diagnose und UX

Die UX folgt ADR 0001 und `control#17` ohne abweichenden Stack:

- Svelte 5, Vite und TypeScript;
- statische SPA mit Bits UI, kontrolliertem shadcn-svelte, Tailwind,
  CSS Custom Properties und Lucide;
- Svelte-5-Runes, typisierte Stores und versionierte Contracts;
- `Graphite Dark – semantic accent system`, 4-Pixel-Raster, Radien 8/12;
- mindestens 44-Pixel-Touchziele, Fokusbedienung und Reduced Motion;
- keine freien Kategorienfarben; Status wird über semantische Tokens, Text,
  Icons, Kontrast und Hierarchie vermittelt.

### Übersicht

Die Übersicht zeigt aktiven Entscheidungsbaum, gewonnenen Pfad, effektive
Zielposition, Cover-/Opening-/Haushaltsstatus und kompakte manuelle Aktionen.

### Diagnose

Die Diagnose zeigt alle Kandidaten und unterdrückten Äste, Input-States,
Roh-/Effektivwerte, Freshness, Quality, degraded/stale/unavailable/blocked,
den vollständigen Decision Trace und einen kopierbaren Debug-Payload ohne
Secrets oder private Topologie.

### Einstellungen

Die Einstellungen zeigen Kontext, Kategorie, Variante, Aktivstatus,
Zielposition, Normal-/Invertiert-Werte, Achseninvertierung, Apply-Gate,
Migration und Defaults mit sicherer Validierung und deterministischem
Fallback.

Frontend-Komponenten binden an einen versionierten UX-Contract, nicht an rohe
HA-Entity-Strukturen. REST liefert Snapshots, WebSocket liefert Live-
Änderungen; Commands und Events bleiben getrennt.

## 11. Verbindliche Szenarien A1–A16

Die Szenarien konkretisieren die in `blind_control#1`, `control#31` und
`blind_control#2` festgelegten Entscheidungen. Sie sind vor einem
produktiven Apply mindestens als risikobasierte Regressionen zu prüfen.

| Szenario | Verbindliche Erwartung |
| --- | --- |
| A1 Grundzustand | `weekday`, `weekend`, `holiday` und `vacation` bleiben getrennte, tracebare Kontexte; kein lokales Recompute von Core State. |
| A2 kompatible Demands | Bei 100 % Grundzustand, Sleep 25 % und Heat 40 % gewinnt nach dem Minimum-Prinzip 25 %. |
| A3 exklusives Waking | Bei Heat, Glare, Privacy und Cold Insulation gewinnt `waking` bis `awake` mit dem konfigurierten Wert, initial 100 %. |
| A4 falsche Wake-Quelle | Nur der kanonische Core-State-Waking-Zustand löst Waking aus; eine Legacy-/zweite Quelle wird ignoriert. |
| A5 direkte Sonne | Die festgelegte Fenstergeometrie und belastbare Sonnen-/Quell-Evidence ergeben den diagnostizierten Zustand `direct_sun`; Rohwahrheiten bleiben extern. |
| A6 Wolke bei Heat | Bei thermischer Last und sinkendem Lux wird `cloud_shadow` sichtbar; Heat bleibt aktiv und es gibt keinen 100-%-Fallback. |
| A7 übrige Solar-Zustände | `diffuse_bright`, `solar_not_on_window`, `night` und `unknown` bleiben unterscheidbar; Diagnosewerte und Source Quality bleiben erhalten. |
| A8 PC nach Heat | Wenn Heat endet, bleibt PC-Glare aktiv und das PC-Ziel gewinnt; es wird nicht unbegründet geöffnet. |
| A9 TV und Konsolen | PlayStation, andere Konsolen und Streaming verwenden `glare_tv`; ein eigenes PlayStation-Profil wird nicht erzeugt. |
| A10 Gewitter mit TV-Glare | `storm_approaching` kann Heat lockern, aber aktives TV-Glare bleibt erhalten und wird separat diagnostiziert. |
| A11 nutzbare Kühlluft | `cool_air_available` öffnet vollständig nur ohne schließenden Kandidaten; der Grund bleibt vom Storm-Grund getrennt. |
| A12 Dunkelheit und Kälte | Cold Insulation verwendet das konfigurierte Ziel bei ungünstiger Außenluft ohne sinnvollen Solar Gain und ist während Waking pausiert. |
| A13 unsicheres Opening | Opening-Safety gewinnt unabhängig vom fachlichen Ziel; unsichere oder stale Evidence führt nicht zum stillen Open-Fallback. |
| A14 eigener Write | Eigener Write, Echo, Attribut-Churn oder Writing-Guard-Fenster erzeugt keinen Manual Override. |
| A15 echter Override | Ein nachweisbarer manueller Eingriff erzeugt einen sichtbaren, löschbaren Override; ein unpassender Kontext beendet ihn deterministisch. |
| A16 Restart, Konfiguration und Apply | Restart/Optionsänderung erzeugen keinen falschen Override; explizite Normal-/Invertiert-Werte werden genutzt, und im Shadow wird nur das jüngste Apply-Ziel vorgemerkt, niemals gefahren. |

## 12. Früher Vertical Slice und risikobasierte Tests

Der erste Meilenstein lautet:

```text
Konfiguration -> Inputs -> Entscheidung -> Trace -> Shadow-Snapshot
```

Er muss früh in Home Assistant installierbar sein, darf aber keinen
Coverbefehl ausführen. Vor einem Merge eines fachlichen Shadow-Slices sind
mindestens betroffene Unit-/Contract-Tests, die A1–A16-Risikofälle,
Safety/Waking/Override/Apply/Open-Fallback, Install/Unload/Restart,
Normal-/Invertiert-Konfiguration und Solar-Golden-Vectors abzudecken.

Nichtkritische seltene Varianten und UI-Polish dürfen iterativ folgen.
Bekannte Lücken bleiben im PR sichtbar und werden nicht durch pauschale
Testbreite verdeckt.

## 13. Harte Stop-Bedingungen und getrennte Gates

Die Arbeit stoppt, wenn:

- ein Shadow-Codepfad einen Cover-Service ausführen könnte;
- der Owner eines sicherheitsrelevanten Inputs unbekannt ist;
- Waking mehr als eine Quelle verwendet;
- Opening-Safety nicht eindeutig ist;
- Config-/Entity-Migration Daten verlieren könnte;
- eine Lizenzfrage eine ungeprüfte Helios-Codeübernahme berührt.

Die Gates bleiben getrennt:

```text
Local checks -> Draft PR -> Review/Merge -> Shadow -> Cutover -> Live -> Live Verified
```

Ein technischer Test, ein Merge, ein Release oder ein Shadow-Ergebnis ist nicht
automatisch `Live`. `Live` und `Live Verified` bleiben Bennis Gates.

## 14. AP1-Stand und Nicht-Ziele

AP1 darf dieses vollständige Lastenheft dokumentieren und prüfen, implementiert
aber ausschließlich den nicht-aktiven nativen ConfigEntry-Bootstrap. AP1
enthält keine Decision Engine, Solar-Exposure-Berechnung, Heat-/Glare-/Cold-
Fusion, Cover-/Entity-Plattform, Services, WebSocket-Mutationen, Frontend,
Storage-/Optionsmigration, Apply/Actuation, Live-Installation, Reload,
Restart, Cutover oder Entity-Umbenennung.

Die alte Blind Policy bleibt unangetastet und alleiniger produktiver
Apply-Owner, bis die späteren Shadow-, Cutover-, Live- und Live-Verified-Gates
nachweislich erfüllt sind.
