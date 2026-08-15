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
