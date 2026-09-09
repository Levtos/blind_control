# AP3 Operator- und Consumer-Vertrag v0.7.0

## Aktueller Betreibervertrag ab v0.7.3

[Issue #3, aktueller Vertrag](https://github.com/Levtos/blind_control/issues/3#issuecomment-5609119991)
ersetzt widersprechende historische Status-/Failure-Aussagen weiter unten.
Der Betreiber hat v0.7.2 bereits produktiv; das neue Release erhält dadurch
keinen automatischen Live-Nachweis. Status des Patches: Testing / Released /
Not Live, nach technischer Veröffentlichung. Keine zusätzliche Shadow-Instanz.

Diagnose getrennt lesen: Context/Basisziel, Glare-Variante und sämtliche
Protections, Modifier, Safety-Minimum/Richtungssperre, Intervall/finales Ziel,
aktive/pausierte/unterdrückte Beiträge, feature-lokale Quality mit Owner/Zeitbasis/
Fallback, Solar-Lifecycle/Exposure und kanonische Activity-Evidence. Generation,
Config-Revision, Snapshot und Lease beschreiben die aktuelle Writer-Prüfung.

Automation AUS und Apply AUS widerrufen alte Freigaben vor dem Speichern bzw.
Reload; das gilt für Panel und native Optionen. **Apply AUS verhindert neue
Commands, stoppt aber keine bereits angenommene physische Fahrt.** Optionsänderung
ist keine Bestätigung der realen Position. Null-Writer, Safety, Ruhebaseline,
Owner und aktuelle Decision bleiben vor jeder Freigabe erforderlich.

Die vollständige manuelle Verifikation und Rollback-Schritte stehen im
[Cutover-Runbook](AP3_CUTOVER.md) und in [Migration](MIGRATION.md). Codex führt
keinen dieser HA-Schritte aus.

Entscheidung: [Issue #3, aktueller Vertrag](https://github.com/Levtos/blind_control/issues/3#issuecomment-5581296547).
Diese Entscheidung ersetzt die frühere vollständige Verschiebung der
Core-Contracts-Anbindung und den ausschließlich nativen Betriebswechsel.
Status bleibt **Testing / Not Live**. Installation und Cutover führt Benni aus.

## Gemeinsame Inputs: Consumer API zuerst

`core_inputs.py` verwendet die öffentliche interne Consumer API von
`benni_core_contracts`, keine Registry-Payloads, Datenbankzugriffe oder Graph-Interna.
Consumer-Deklarationen, feste Schema-Version 1, Feldanforderungen, gefilterte
Subscriptions und Cleanup gehören zu dieser Grenze. Eine neue API-Instanz nach
Upstream-Reload wird neu abonniert. Ohne API ist eine gewählte Bindung unbrauchbar.
Die CI prüft gegen den unveränderten Upstream-Commit
`def02cdf6db4daf24bb97ee36678eac090b9f863`.

| Vorhandenes Schema | Konsumierte Felder | Blind-Control-Eingang |
| --- | --- | --- |
| opening v1 | opening_state, available | Opening-State; kein neuer Öffnungsowner |
| room_climate v1 | temperature, available | Innentemperatur |
| weather_environment v1 | outdoor_temperature, illuminance, available | Außentemperatur und Außen-Lux |

Unter Einstellungen werden Profil (`benni` / `eltern`) und die drei bestehenden
Contract-IDs aus der Registry gewählt. IDs werden nicht erfunden und kein
beliebiges Opening-Pilotprofil automatisch übernommen: der Scope muss zur
betroffenen Fenster-/Raumgruppe passen. Dies ist Consumer-Konfiguration, keine
zweite Registry. Die Auswahl ersetzt für diese Felder die lokalen Bindings.
Ein ausgewählter Contract muss verfügbar, schema-kompatibel und feldweise
`valid / good / fresh / healthy` sein; `available` muss positiv sein.
Stale, restored, conflict, unknown, fehlende Felder, inkompatible Version,
Upstream-Ausfall und gelöschte ausgewählte Contracts fallen **nicht** auf lokale
Werte zurück. Core Contracts besitzt die Freshness; Blind Control erhöht keine TTL
und erklärt keinen abgelehnten Wert nachträglich für frisch.

Eine leere Auswahl ist explizit `compatibility_fallback_unselected`. Bestehende
v0.6.3-Installationen behalten so ihre Bedeutung. Die Diagnose unterscheidet diese
Lücke von einer gesunden oder blockierten Consumer-Verbindung. Änderungen der
Contract-Auswahl/des Profils erfordern Apply AUS.

**Offene Plattform-Gaps:** Der geprüfte Schema-Katalog besitzt keine passenden
Bio-/Activity-/Day-/Away-/Private-Time-/Privacy-Schemas sowie keine vollständigen
Sun-/Cloud-/DNI-/Diffus-/Wettertrendrollen. Diese Eingänge behalten bis zu einer
belegten produktiven Rolle den vorhandenen kanonischen Owner-Adapter bzw. den
internen optionalen Strahlungsprovider. Die vollständige produktive Registry-
Belegung ist nicht belegt. Es wird kein Device-Owner, Core-State-Ersatz oder
neuer Solarprovider gebaut. Diese Gaps blockieren die Behauptung einer vollständigen
Core-Contracts-Migration, nicht den dokumentierten Cutover mit belastbaren
bestehenden Owner-Bindings. Ein fehlerhafter ausgewählter Pflichtcontract blockiert
hingegen die Fahrt.

Cover/Actuator, numerische Achse, Geometrie, Positionsprofile und Kalibrierwerte
bleiben lokal. `low_light`, echte UNKNOWN-Quality, stationäre Coverbaseline und
semantische HA-Motion bleiben unverändert. Safety OPEN verhindert Abwärtsfahrt.

## Operator-Oberfläche

Die zentrierte Graphite-Oberfläche mit maximal 1240 px Gesamtbreite zeigt zuerst
Istposition, aktuelle Entscheidung, Ziel, Aktivität, Opening, Solar, Lux und
Temperatur. Die Regelübersicht übersetzt vorhandene Candidate-Reasons und
kennzeichnet fehlende Evidence bzw. exklusive Pausen; sie berechnet keine zweite
Policy. Shadow beschreibt Absicht, keine angeblich ausgeführte Fahrt.
Technische Bewegung/Recovery/Override, Context und Rohdiagnose stehen getrennt.
Tablet-Breakpoints und ShadowRoot-eigene Styles bleiben Bestandteil des Bundles.

## Betriebswechsel ohne versteckte OptionsFlow-Pflicht

Übersicht → Betrieb bietet Shadow/Legacy mit Apply AUS, Live/Blind Control mit
Apply AUS und danach bewusstes Apply AN. `blind_control/set_operation` ist nur
für HA-Administratoren verfügbar. Er ist ein ConfigEntry-Staging-Endpunkt,
kein Cover-Service und kein `apply_now`.

- Modus-/Owner-Staging speichert Apply AUS.
- Apply AN setzt einen bereits geladenen aktiven Live/Blind-Control/OFF-Stand,
  aktuelle Konfigurationsrevision und ausdrückliche Null-Writer-Bestätigung voraus.
- Alte Runtime-Freigaben werden synchron vor Persistierung entzogen. Der normale
  Update-Listener lädt die neue Runtime; bis dahin bleibt Bedienung gesperrt.
- Eine nicht deaktivierte oder noch geladene Legacy-ConfigEntry sowie ein noch
  registriertes Legacy-Apply-Service blockieren die Freigabe. Derselbe Interlock
  wird zusätzlich vor jedem tatsächlichen Cover-Dispatch geprüft, auch bei
  Konfiguration über native Optionen.
- Fehlende Registry-Einsicht blockiert. Kein automatisches Legacy-Disable,
  kein Prozessrestart und keine Änderung fremder Integration findet statt.
- Ein Legacy-Interlock ersetzt nicht Bennis Prozessrestart/Null-Writer-Prüfung:
  beliebige fremde Automationen und schon gestartete physische Fahrten sind kein
  atomar sperrbarer HA-Writer-Lock. Während des Fensters sind fremde Befehle verboten.
- Apply OFF widerruft künftige Freigaben; es stoppt keine laufende physische Fahrt.
  Safety-, Baseline-, Quality-, Override-, Recovery- und Cooldown-Gates gelten weiter.

Transportfehler sperren Bedienung und markieren die Anzeige als möglicherweise
veraltet. Settings-Transport darf weiterhin keine Runtime-/Owner-/Apply-Werte
einschleusen. Keine private URL oder Entity-ID gelangt in kopierbare Debug-Evidence.

## Nächstes reales Gate

Benni installiert v0.7.0, deaktiviert Legacy (installiert lassen), startet HA neu,
bestätigt Null-Writer und kontrolliert Live/Blind Control mit Apply AUS. Danach
bewusst Apply AN, aktuelle Ziele und reale Fahrt/Opening-Safety prüfen. Benni
entscheidet Live und später Live Verified. Keine automatische weitere
Shadow-Hardening-Runde; nur ein echter neuer Safety-/Funktionsfehler rechtfertigt
einen weiteren Patch. Exakter Ablauf und Rückweg: [AP3_CUTOVER.md](AP3_CUTOVER.md).
