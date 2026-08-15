# Migration, Shadow und Cutover – Blind Control AP1

**Dokumentversion:** 0.1.0

AP1 ist eine vorbereitende, nicht-aktive Stufe. Es wird weder eine alte
ConfigEntry importiert noch eine Coverfahrt ausgelöst. Die alte
`benni_blind_policy` bleibt die rollbackbare produktive Instanz.

## 1. Ist → Soll

| Ist | Soll | AP1-Entscheidung |
| --- | --- | --- |
| `benni_blind_policy` mit bestehendem ConfigEntry, Runtime-State, Panel und Apply | `blind_control` als neue native Integration mit versionierten Contracts und späterer interner Policy/Apply-Struktur | Alt bleibt unverändert; neuer Rahmen ist leer/non-actuating |
| aktuelle Cover-Entity `cover.wohnbereich_thermo_verdunklungsrollo` | späterer freigegebener technischer Actuator-/Position-Contract | dokumentiert, nicht gebunden/umbenannt |
| historische/konkurrierende ID `cover.living_blackout_blind` | später vorbereiteter Zielname `cover.living_thermal_blind` | nur dokumentiert; keine Registry- oder YAML-Änderung |
| alte Opening-/Core-Master-Projektionen | Core-State/Core-Contracts owner-bound contracts | keine Alias-/Recompute-Schicht in AP1 |
| alte Flat-Rule-/Apply-Lifecycle | neue Entscheidung mit Winner/Trace, Demand-/Safety-Gates und separatem Apply | fachliche/technische Neubewertung später |

## 2. Gate-Reihenfolge

```text
AP1 local bootstrap
  -> Draft PR / review
  -> merge (technical)
  -> Shadow: observe + parity, no productive writes
  -> Cutover preparation: explicit consumer and rollback plan
  -> Cutover: separate approved change
  -> Benni Live
  -> Live Verified
```

`Tests Pass`, Draft PR, Merge und ein eventueller HACS-Release sind keine Live-
oder Live-Verified-Aussage. Benni entscheidet und führt Live-Reload, Restart,
Installation und Cutover separat aus.

## 3. Shadow- und Rollback-Regeln

- Shadow darf Quellen beobachten/diagnostizieren, aber keine Cover-, Service-,
  Registry- oder Policy-Writes ausführen.
- Die alte Integration bleibt installiert/rollbackbar, bis Shadow-Parität,
  Safety, `waking`, Override-Lifecycle, Consumer-Inventar und ein Cutover-
  Beschluss dokumentiert sind.
- Rollback bedeutet Rückkehr zur alten, unveränderten Policy und deren
  ConfigEntry; kein AP1-Schritt löscht oder deaktiviert sie.
- Ein alter Storage-State darf nicht ohne versionierte Migrationsentscheidung
  als neuer Runtime-State interpretiert werden.
- Ein Cover-Rename ist eine spätere Registry-/Consumer-Migration. AP1 legt
  keine neue Entity an und ändert keine bestehende ID.

## 4. Stop-Bedingungen vor Shadow/Cutover

Stoppen und als Blocker dokumentieren, wenn:

- ein Owner für Opening, Sun, Lux, Weather, Temperature, Cover-Position oder
  Availability fehlt;
- Freshness nur aus Initial-/Restore-/Retained-Snapshot abgeleitet würde;
- eine alte YAML-/README-ID als aktueller Contract verwendet werden müsste;
- ein Consumer des aktuellen Covers oder des alten Master-Sensors ungeklärt ist;
- eine Fallbackregel eine physische Öffnung/Schließung ohne positive Evidence
  behaupten würde;
- `waking` nicht exklusiv und kanonisch aus Core State bezogen würde;
- Apply-, Override-, Cooldown- oder Writing-Guard-Parität nicht getestet wäre.

## 5. Benötigte spätere Nachweise

Vor einem technischen Shadow-Slice müssen mindestens vorliegen:

1. vollständige, owner-bestätigte Input-/Consumer-Matrix;
2. aktuelle Contract-/Mapping-Versionen inklusive Feldqualität und Freshness;
3. Opening-Safety- und Cover-Position-Gates;
4. Regressionstests für Privacy/Sleep, Waking, Window Safety, Heat/Glare,
   Override, Cooldown und Apply-Readiness;
5. expliziter Consumer-/Rollback-Plan ohne parallele Policy-Owner;
6. getrennte UX-/Frontend-Entscheidung nach ADR 0001.

Bis dahin bleibt der AP1-Stand **Not Live**.

## 6. AP2-Shadow-Vertical-Slice

AP2 erweitert den Rahmen um eine installierbare, weiterhin nicht-aktive
Shadow-Fachschicht. Der Pfad ist:

```text
ConfigEntry / OptionsFlow
  -> owner-bound InputObservation
  -> Solar Exposure / DecisionEngine
  -> DecisionTrace / Safety / Apply-Intent
  -> ShadowSnapshot / optionaler Legacy-Diff
```

Der Snapshot markiert `shadow_only=true`, `actuation_executed=false` und
`write_path_reachable=false`. ConfigEntry-/OptionsFlow-Speicherung ist nur
Konfigurationsspeicherung; es existiert kein Geräte-Schreibpfad.

AP2 übernimmt die Migrationsdefaults für Normal-/Invertiert-Positionen und
macht die kalibrierbaren Temperatur-, Lux-, Strahlungs-, Confidence-, Trend-,
Cooldown- und Toleranzwerte explizit konfigurierbar. Die fachliche
Interpretation, Owner-/Freshness-Grenzen und bekannte offene Bindings sind in
[AP2_SHADOW.md](AP2_SHADOW.md) festgehalten.
