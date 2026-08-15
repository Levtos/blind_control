# Lastenheft – Blind Control AP1

**Dokumentversion:** 0.1.0

**Status:** AP1 normativer Scope- und Entscheidungsrahmen, keine Policy-
oder Apply-Implementierung.

**Verbindliche Reihenfolge:** Issue
[`blind_control#1`](https://github.com/Levtos/blind_control/issues/1),
[`control#31`](https://github.com/Levtos/control/issues/31), ADR 0001 und
ADR 0002. Das reviewed Wohnzimmer-Rollo-Lastenheft im
[`einhornzentrale`-Repository](https://github.com/Levtos/einhornzentrale/tree/main/docs/lastenhefte/reviewed/rollo)
ist historische Fachbasis. Wo es mit der aktuellen Issue-/Control-Entscheidung
kollidiert, gilt die aktuelle Entscheidung; die alte Integration wird nicht
umgeschrieben.

## 1. Produkt und Ziel

- Neue Integration und neuer Produktname: `blind_control` / **Blind Control**.
- Kein `benni_`-Prefix im neuen Produktnamen.
- Die alte Integration `benni_blind_policy` bleibt bis Shadow, Cutover, Benni
  Live und Live Verified unverändert rollbackbar.
- AP1 baut den nativen ConfigEntry-Rahmen und die prüfbare Dokumentationsbasis.
  Es gibt noch keinen vollständigen Entscheidungsbaum, keine Entität, kein
  Frontend und keinen Apply-Aufruf.

## 2. Normativer Entscheidungsrahmen für spätere APs

Die spätere Entscheidung ist in dieser Reihenfolge zu modellieren:

```text
Grundzustand -> Modus -> Umwelt -> technische Safety -> Apply
```

### Grundzustand

Wochentag/Wochenende/Feiertag/Ferien und der kanonische Tageskontext kommen
aus einem Owner-Vertrag. Blind Control berechnet diese Zustände nicht erneut.

### Modus

Die dokumentierten Modi umfassen mindestens `sleep`, `waking`, `away`,
`private_time` und `privacy`. Der kanonische `waking`-Zustand ist exklusiv:
Während `waking` gilt der konfigurierbare Standardwert, initial 100 %, bis der
Zustand `awake` erreicht ist. Dieser Pfad überschreibt Heat, Glare, Privacy
und Cold Insulation.

Es gibt keine eigene Prewake-Zeit und keinen zweiten Legacy-Wake-Source. Blind
Control konsumiert ausschließlich den kanonischen Wake-/Bio-State-Vertrag.

### Umwelt

- Heat und Glare sind unabhängige Demands.
- Glare unterscheidet allgemeines Glare, `glare_tv` und `glare_pc`.
- PS/Console konsumieren den TV-Glare-Pfad; es gibt kein eigenes PS-Profil.
- Solar Exposure ersetzt einen einzelnen Lux-Hard-Gate. Blind darf dafür eine
  blind-spezifische Ableitung besitzen, aber rohe Lux-, Sonnen-, Wetter- und
  Temperaturwahrheiten gehören zu ihren jeweiligen Ownern.
- `storm_approaching` und `cool_air_available` sind getrennte Signale.
- Cold Insulation ist ein eigener Demand und kein Alias von Heat, Privacy oder
  Storm.

### Compatible Demands und Safety

Für gleichzeitig kompatible Demands gilt das Minimum-Prinzip in der gewählten
Achse: Das Ergebnis bleibt beim stärker schließenden Ziel. `waking` ist die
ausdrücklich dokumentierte exklusive Ausnahme und gewinnt bis `awake`.

Opening Safety arbeitet mit positiven Öffnungsgründen. Ein unbekannter,
staler, nicht verfügbarer oder konfliktärer Opening-Vertrag darf nicht
stillschweigend als geschlossen oder offen umgedeutet werden; ein Safety-
Blocker bleibt sichtbar und blockiert die sichere Verwendung. Fallbacks müssen
begründet und diagnostizierbar sein; ein positives Öffnen ohne positive Quelle
ist unzulässig.

### Positionen und Achsen

Alle Prozentwerte für normale und invertierte Achse sind editierbar. Die
Normal-/Invertiert-Profile sind von der technischen Achseninversion getrennt.
Eine Achseninversion ist eine eigene UI-/Runtime-Option und darf nicht durch
vertauschte Fachwerte simuliert werden.

Die dokumentierten Migrations-Defaults sind:

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

Diese Werte sind eine editierbare Migrationsbasis aus Issue #1, kein AP1-
Apply-Befehl und keine Behauptung über einen aktuellen HA-Registry-Wert.

## 3. AP1-Implementierungsgrenze

AP1 enthält ausschließlich:

- `custom_components/blind_control` mit Manifest, Config Flow und
  reproduzierbarem Setup/Unload ohne Plattform-Weiterleitung;
- versionierte Lastenheft-, Architektur-, Inventar-, Contract- und
  Migrationsdokumente;
- lokale Boundary-, Translation- und Dokumenttests sowie CI für diese Checks.

AP1 enthält ausdrücklich nicht:

- Decision Engine, Solar Exposure, Heat/Glare-Berechnung oder Demand-Fusion;
- Cover-/Entity-Plattform, Service, WebSocket-Mutation oder Apply/Actuation;
- produktive UI oder Frontend-Bundle;
- Storage-/Optionsmigration aus `benni_blind_policy`;
- Coverfahrt, HA-Installation, Reload, Restart, Cutover oder Entity-
  Umbenennung.

## 4. Test- und Gate-Prinzip

Die erste vertikale Implementierung späterer APs wird risikobasiert um
Opening Safety, `waking`, Override-/Apply-Grenzen und Regressionen gebaut.
Technische Tests, ein Draft-/Merge-Stand, ein Release und die Benni-Live-
Prüfung sind getrennte Gates:

```text
Local checks -> Draft PR -> Review/Merge -> Shadow -> Cutover -> Live -> Live Verified
```

AP1 endet vor Shadow und bleibt `Not Live`.
