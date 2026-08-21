# Interner Open-Meteo-Strahlungsprovider für AP2

Blind Control enthält einen kleinen, isolierten und vollständig read-only
Open-Meteo-Provider. Er wird ausschließlich über ConfigFlow/OptionsFlow
konfiguriert. Es gibt weder YAML noch Package-, `secrets.yaml`-, API-Key-,
Koordinatenformular-, PV- oder Weather-State-Konfiguration. Core State bleibt
unverändert.

## Abrufvertrag

- HTTPS-Host `api.open-meteo.com`, Endpunkt `/v1/forecast`;
- Modell `dwd_icon_seamless`;
- `current`, keine fest eingebaute Prognose und keine rückwärts gemittelten
  `hourly`-Werte;
- `current.direct_normal_irradiance_instant` wird zu
  `expected_direct_radiation` in `W/m²`;
- `current.diffuse_radiation_instant` wird zu
  `expected_diffuse_radiation` in `W/m²`;
- genau ein gemeinsamer HTTP-Abruf liefert beide Werte;
- Standardintervall 900 Sekunden, Freshness-Grenze 1200 Sekunden;
- kein API-Key, keine PV-Anlage, keine PV-Leistung und keine Ertragsprognose.

Beim ersten ConfigFlow erzeugt Blind Control aus den Home-Assistant-
Standortdaten ausschließlich im privaten Formular eine URL-Suggestion. Benni
kann im Freitextfeld **Open-Meteo API-URL** eine vollständige URL einsetzen.
Gespeichert wird sie in der Blind-Control-ConfigEntry. OptionsFlow validiert
Schema, Host, Endpunkt, Modell und beide Current-Felder, entfernt
Tracking-Parameter und lehnt Benutzerinformationen, API-Key-/PV-Parameter und
fremde Hosts ab. Eine ungültige Änderung ersetzt die letzte gültige Option
nicht. Erfolgreiches Speichern lädt nur diese ConfigEntry neu; ein vollständiger
Home-Assistant-Neustart ist nicht erforderlich.

## Native Sensoren

Ein Request speist zwei normale read-only Sensoren am Blind-Control-Gerät:

| Name | stabile `unique_id` | Wert | HA-Metadaten |
| --- | --- | --- | --- |
| Blind Control DNI Instant | `blind_control_dni_instant` | DNI Instant | `irradiance`, `measurement`, `W/m²` |
| Blind Control Diffuse Radiation Instant | `blind_control_diffuse_radiation_instant` | Diffusstrahlung Instant | `irradiance`, `measurement`, `W/m²` |

Die erwarteten Entity-IDs sind `sensor.blind_control_dni_instant` und
`sensor.blind_control_diffuse_radiation_instant`; bei Kollisionen darf Home
Assistant die Entity-ID anpassen. Die `unique_id` bleibt maßgeblich. Attribute
enthalten nur Provider, Modell, letzten erfolgreichen Abruf, Datenzeitstempel,
Intervall und Providerstatus. URL und Koordinaten werden niemals projiziert.

## Evidence, Freshness und Fehler

Die Precedence lautet:

1. ausdrücklich gespeichertes externes Entity-Binding;
2. interner Open-Meteo-Provider;
3. `missing` beziehungsweise `unavailable`.

Ein erfolgreicher Wert ist `fresh`. Nach einem späteren Abruffehler bleibt der
letzte Erfolg nur innerhalb der Freshness-Grenze nutzbar und der Providerstatus
wird `degraded`; danach ist die Evidence `stale`. Ein fehlgeschlagener
Erstabruf ist `unavailable`, unvollständige oder nicht numerische Antworten
werden nicht geraten. Ein tatsächlich gelieferter Nachtwert `0 W/m²` bleibt
ein gültiger Wert und unterscheidet sich von fehlender Evidence.

Lokaler Außenlux und Sonnengeometrie bleiben die tragende Solar-Evidence.
Modellstrahlung ist zusätzliche, ersetzbare Confidence-Evidence. Providerfehler
erzeugen weder Default-Open noch Cover-, Service-, Apply- oder Command-Pfade.
Der Provider ist hinter dem internen Evidence-Adapter austauschbar, sodass eine
spätere Übernahme durch Core Contracts die Solar-Engine nicht neu entwerfen
muss.

**Status:** `Installed / Shadow / Not Live`.
