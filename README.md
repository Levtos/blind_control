# Blind Control

`blind_control` is the new native Home Assistant integration target for the
Blind Control rebuild. This AP1 branch contains only a reproducible,
non-actuating ConfigEntry bootstrap and the normative inventory/contract
documentation for Issue [Levtos/blind_control#1](https://github.com/Levtos/blind_control/issues/1).

The old `benni_blind_policy` integration remains the rollbackable productive
implementation. AP1 does not install, reload, disable, migrate, rename, or
drive a cover. The current physical cover is documented as an external
contract only; no cover platform or apply path exists here.

Read the documents in this order:

1. [Lastenheft](docs/LASTENHEFT.md)
2. [Architecture](docs/ARCHITECTURE.md)
3. [Inventory](docs/INVENTORY.md)
4. [Contracts](docs/CONTRACTS.md)
5. [Migration and gates](docs/MIGRATION.md)

## AP1 boundary

- product/domain name: `Blind Control` / `blind_control`
- one minimal ConfigEntry flow with no source fields
- setup/unload stores and removes only bootstrap runtime state
- no entities, services, WebSocket commands, frontend, apply, cover movement,
  migration, or live installation
- no hardcoded productive entity IDs in product Python code

The work remains technical/testing until the Draft PR is reviewed and merged.
`Live` and `Live Verified` are separate Benni gates.
