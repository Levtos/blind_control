import assert from 'node:assert/strict';
import test from 'node:test';

import {
  cloneSettings,
  rebaseDraft,
  settleSave,
} from '../src/lib/draft-settings.js';
import { proxy as svelteProxy } from '../node_modules/svelte/src/internal/client/proxy.js';

const settings = () => ({
  axis_inverted: false,
  window_azimuth: 124,
  window_tilt: 90,
  automation_enabled: true,
  apply_enabled: true,
  runtime_mode: 'shadow',
  apply_owner: 'legacy',
  binding_groups: [],
  observation_freshness_seconds: 120,
  binding_freshness: {},
  profiles: { open: { normal: 100, inverted: 0 } },
  calibration_defaults: { heat_outdoor_threshold: 30 },
});

test('poll during editing preserves the local profile draft', () => {
  const initial = rebaseDraft(null, null, settings());
  initial.draftSettings.profiles.open.normal = 73;

  const poll = rebaseDraft(
    initial.draftSettings,
    initial.confirmedRevision,
    structuredClone(settings()),
  );

  assert.equal(poll.adopted, false);
  assert.equal(poll.dirty, true);
  assert.equal(poll.draftSettings.profiles.open.normal, 73);
});

test('real Svelte deep-state proxy is detached before transport cloning', () => {
  const proxied = svelteProxy(settings());
  proxied.profiles.open.normal = 72;
  proxied.binding_groups.push({
    key: 'solar',
    label: 'Solar',
    readiness: 'ready',
    missing_required: [],
    fields: [],
  });

  assert.throws(() => structuredClone(proxied), { name: 'DataCloneError' });
  const detached = cloneSettings(proxied);

  assert.equal(detached.profiles.open.normal, 72);
  assert.equal(detached.binding_groups[0].key, 'solar');
  assert.notEqual(detached, proxied);
  assert.notEqual(detached.profiles, proxied.profiles);
});

test('a clean draft adopts an external server settings change', () => {
  const initial = rebaseDraft(null, null, settings());
  const external = settings();
  external.window_azimuth = 210;

  const poll = rebaseDraft(
    initial.draftSettings,
    initial.confirmedRevision,
    external,
  );

  assert.equal(poll.adopted, true);
  assert.equal(poll.dirty, false);
  assert.equal(poll.draftSettings.window_azimuth, 210);
});

test('a successful save establishes a clean confirmed baseline', () => {
  const initial = rebaseDraft(null, null, settings());
  initial.draftSettings.profiles.open.normal = 61;
  const confirmed = structuredClone(initial.draftSettings);

  const saved = settleSave(
    initial.draftSettings,
    initial.confirmedRevision,
    confirmed,
  );
  const poll = rebaseDraft(saved.draftSettings, saved.confirmedRevision, confirmed);

  assert.equal(saved.saved, true);
  assert.equal(poll.dirty, false);
  assert.equal(poll.draftSettings.profiles.open.normal, 61);
});

test('a failed save deliberately retains the local draft', () => {
  const initial = rebaseDraft(null, null, settings());
  initial.draftSettings.profiles.open.normal = 44;

  const failed = settleSave(
    initial.draftSettings,
    initial.confirmedRevision,
    null,
  );

  assert.equal(failed.saved, false);
  assert.equal(failed.draftSettings.profiles.open.normal, 44);
});
