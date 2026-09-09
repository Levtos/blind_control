# Input audit for v0.7.4

Read-only evidence on 2026-09-10; no installation, options or service changes.
Core State source reviewed at c9408fa33f2914b1c5f7316738cb38b43add33b5.
This inventory separates connected inputs from semantic suitability and real
movement verification. It does not certify every scenario as Live Verified.

| Scenario / input | Observed binding role | Finding |
|---|---|---|
| Sleep / Waking | Core State Bio | Direct canonical state, currently awake; both sleep variants share profile 5, Waking 100 |
| Glare | Core State Activity | Direct canonical media_device=pc; PC/TV specificity retained |
| Day / Privacy | Core State Day / Day Context | Direct nine-phase day_state, currently late_evening; v0.7.4 maps approved evening/night phases to Privacy 40 |
| Private Time | Core State Activity private attribute | Separate canonical false, no extra Waking filter |
| Away | Media State presence away_gate | Canonical gate exists and is false; this is not a direct Core-State presence binding |
| Former Privacy | Core Devices Combined presence candidate | false from household_empty_privacy; retired and ignored by v0.7.4 |
| Opening / Safety | Core Devices Master and Combined | closed, unsafe=false; still legacy data dependencies, not migrated in this release |
| Cover position / availability | Standard HA cover | Existing direct actuator/position binding retained |
| Readiness | Existing readiness binary sensor | on; weather-only degradation remains scoped by existing technical adapter |
| Solar / Heat / Cold lux | Core Devices garden lux | 2 lx, owner reports not degraded; remains a data dependency |
| Solar geometry | HA Sun | Existing horizon-first path retained |
| Heat indoor temperature | Core Devices bathroom climate | Numeric usable evidence, but intended room suitability for the living-room blind is not established; operator clarification required before claiming correct Heat behavior |
| Outdoor temperature | Existing weather entity | Existing numeric adapter retained |
| Storm / Cool Air | Optional weather/trend/air-movement roles | Missing optional signals cannot prove relief/opening; no automatic substitute invented |

Core State does not currently publish an evening privacy Boolean. Its display
privacy_level redacts personal details and must not become a blind input. The
user-approved solution maps its existing day_state to the blind profile without
recalculating time, activity, presence or sleep. Core State and Core Contracts
repositories are unchanged. No new Core-Contracts connection was created.

Deployment requires operator installation/restart and inspection with Apply OFF.
The existing Day-State selection is sufficient for the Privacy correction.
Correcting other room/device selections or retiring Core Devices entirely is a
separate verified migration; removing it now would still break retained inputs.
Do not interpret release tests as proof of physical Sleep/Privacy/Safety motion.
