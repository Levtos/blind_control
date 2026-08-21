# Blind Control

`blind_control` is the new native Home Assistant integration target for the
Blind Control rebuild. This AP2 branch contains an installable, configurable
Shadow runtime: owner-bound input contracts flow through a deterministic
decision engine into a versioned trace and Shadow snapshot for Issue
[Levtos/blind_control#2](https://github.com/Levtos/blind_control/issues/2).

The old `benni_blind_policy` integration remains the sole rollbackable
productive Apply owner. AP2 does not install, reload, disable, migrate, rename,
or drive a cover. Shadow configuration/options and read-only observation
listeners are allowed; no cover platform, service-call, or actuator path exists
here.

Read the documents in this order:

1. [Lastenheft](docs/LASTENHEFT.md)
2. [Architecture](docs/ARCHITECTURE.md)
3. [Inventory](docs/INVENTORY.md)
4. [Contracts](docs/CONTRACTS.md)
5. [Migration and gates](docs/MIGRATION.md)
6. [AP2 Shadow implementation](docs/AP2_SHADOW.md)

## Installation through HACS

Add `https://github.com/Levtos/blind_control` as a custom HACS integration
repository and install the latest published release. Restart Home Assistant,
then add **Blind Control** from **Settings → Devices & services**.

The AP2 installation runs exclusively in Shadow mode. It observes configured
inputs and publishes decisions and diagnostics, but it cannot send a cover
command or replace the productive `benni_blind_policy` Apply owner.

## AP2 boundary

**Current status:** `Installed / Shadow / Not Live`. Issue #2 remains open;
this AP2 follow-up is a Draft PR only.

- product/domain name: `Blind Control` / `blind_control`
- configurable normal/inverted profiles, axis inversion, geometry, and
  calibration defaults
- versioned owner-bound input, decision, diagnostic, UX, and Shadow contracts
- deterministic Solar Exposure, compatible minimum composition, exclusive
  Waking, Opening Safety, Override tracking, and latest-target cooldown state
- versioned hierarchy: `normal|manual|failure`, winner category/variant and
  visible compatible active or paused branches; Safety and Apply remain a
  separate technical layer
- Failure holds only a current/last proven safe position or blocks Apply; it
  never invents a 100 % open fallback; a quality gate also blocks an already
  composed daylight target when mandatory Temperature, Activity or
  geometry/Lux evidence is missing, unknown, unavailable, stale or conflicting;
  trend, model radiation and cloud evidence remain capability-aware additions
- native OptionsFlow Entity Selectors grouped for Core State,
  Opening/Safety/Cover, Solar, Temperature/Weather and Legacy comparison;
  contract-based installation-local suggestions preserve user choices and
  intentionally empty optional slots; the panel shows only redacted readiness
  states for the exact 89-field contract (the additional field is the private
  Open-Meteo API URL)
- an isolated internal Open-Meteo coordinator performs one read-only request
  for current DNI and diffuse radiation every 900 seconds; it is configured
  entirely in ConfigFlow/OptionsFlow without YAML, secrets file, API key,
  coordinate form, PV model, Core-State change or new Weather-State integration
- the provider publishes `Blind Control DNI Instant` and `Blind Control Diffuse
  Radiation Instant` as registry-stable irradiance measurement sensors; an
  explicit external radiation binding remains the advanced override
- field-specific Core-State Presence/Activity/Day adapters, explicit Opening
  polarity, and standard-cover availability/current-position handling
- HA 2026.8 `async_reload(entry_id)` lifecycle and Svelte-5-proxy-safe draft
  rebasing are contract-tested without a live reload or browser preview
- setup starts the owner-bound read-only ShadowCoordinator and publishes a
  snapshot through a read-only WebSocket projection, one native diagnostic
  status sensor and two read-only radiation sensors on the same device; URL and
  coordinates are never projected and no actuator service or device command
  path exists
- no entity flood, frontend device-command surface, Apply, cover movement,
  productive migration, Cutover, Rename, or live activation
- no hardcoded productive entity IDs in product Python code

`Live`, `Live Verified`, Cutover, Rename, Release, and Merge are separate
gates. The currently installed AP2 Shadow runtime does not make this Draft
follow-up live and does not change the old productive policy.
