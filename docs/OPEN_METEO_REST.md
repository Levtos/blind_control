# Open-Meteo-REST-Zwischenvertrag für AP2

Blind Control enthält keinen Wetter-API-Client. Die installationsseitige
Home-Assistant-Core-REST-Integration führt einen gemeinsamen Abruf aus und
projiziert daraus zwei normale, read-only Sensoren. Die konkrete URL mit
Standortkoordinaten liegt ausschließlich als lokales Home-Assistant-Secret vor.

Normativer Abrufvertrag:

- kostenlose nichtkommerzielle Standard-API ohne API-Key;
- Modell `dwd_icon_seamless`;
- `current`, keine fest eingebaute Prognose und keine rückwärts gemittelten
  `hourly`-Werte;
- `expected_direct_radiation` liest
  `current.direct_normal_irradiance_instant` in `W/m²`;
- `expected_diffuse_radiation` liest
  `current.diffuse_radiation_instant` in `W/m²`;
- ein REST-Abruf mit `scan_interval: 900` erzeugt beide Sensorwerte;
- lokaler Außenlux bleibt Pflicht-Evidence, beide Modellwerte bleiben optional.

Repository-geführte Installationen verwenden eine Package-Konfiguration dieses
Aufbaus; Namen und Entity-IDs sind installationslokal und kein Teil des
öffentlichen Blind-Control-Contracts:

```yaml
blind_control_weather:
  rest:
    - resource: !secret blind_control_open_meteo_url
      method: GET
      scan_interval: 900
      sensor:
        - name: <lokaler DNI-Sensorname>
          value_template: >-
            {{ value_json.current.direct_normal_irradiance_instant | float(none) }}
          json_attributes_path: "$.current"
          json_attributes:
            - direct_normal_irradiance_instant
          unit_of_measurement: "W/m²"
          device_class: irradiance
          state_class: measurement
        - name: <lokaler Diffus-Sensorname>
          value_template: >-
            {{ value_json.current.diffuse_radiation_instant | float(none) }}
          json_attributes_path: "$.current"
          json_attributes:
            - diffuse_radiation_instant
          unit_of_measurement: "W/m²"
          device_class: irradiance
          state_class: measurement
```

Die OptionsFlow-Suggestion erkennt die Sensoren an den publizierten
JSON-Attributen, nicht an einer fest codierten Entity-ID. Ein fehlender Sensor
bleibt als optionale Capability bewusst leer und blockiert den Normalbetrieb
nicht allein. Eine insgesamt unzureichende oder widersprüchliche Solar-Evidence
bleibt weiterhin ein sichtbarer Quality-Blocker und kann keine Öffnung auslösen.
