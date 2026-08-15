# Blind Control

`blind_control` is the new native Home Assistant integration target for the
Blind Control rebuild. This AP2 branch contains an installable, configurable
Shadow runtime: owner-bound input contracts flow through a deterministic
decision engine into a versioned trace and Shadow snapshot for Issue
[Levtos/blind_control#2](https://github.com/Levtos/blind_control/issues/2).

The old `benni_blind_policy` integration remains the sole rollbackable
productive Apply owner. AP2 does not install, reload, disable, migrate, rename,
or drive a cover. Shadow configuration/options are allowed; no cover platform,
service, listener, or actuator path exists here.

Read the documents in this order:

1. [Lastenheft](docs/LASTENHEFT.md)
2. [Architecture](docs/ARCHITECTURE.md)
3. [Inventory](docs/INVENTORY.md)
4. [Contracts](docs/CONTRACTS.md)
5. [Migration and gates](docs/MIGRATION.md)
6. [AP2 Shadow implementation](docs/AP2_SHADOW.md)

## AP2 boundary

- product/domain name: `Blind Control` / `blind_control`
- configurable normal/inverted profiles, axis inversion, geometry, and
  calibration defaults
- versioned owner-bound input, decision, diagnostic, UX, and Shadow contracts
- deterministic Solar Exposure, compatible minimum composition, exclusive
  Waking, Opening Safety, Override tracking, and latest-target cooldown state
- setup creates an initial read-only Shadow snapshot and no input/observation
  listeners, services, or actuator path
- no entities, WebSocket commands, frontend command surface, Apply, cover
  movement, productive migration, or live installation
- no hardcoded productive entity IDs in product Python code

The work remains technical/testing until the Draft PR is reviewed and merged.
`Live`, `Live Verified`, Cutover, Rename, Release, and Merge are separate gates.
