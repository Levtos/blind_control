import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile, writeFile, mkdtemp, rm } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
import { compile } from 'svelte/compiler';
import { render } from 'svelte/server';
import ts from 'typescript';

async function component(name, props) {
  const source = await readFile(`src/${name}.svelte`, 'utf8');
  const directory = await mkdtemp(resolve('node_modules/.operator-test-'));
  try {
    const file = resolve(directory, 'component.mjs');
    await writeFile(file, compile(source, { generate: 'server', filename: `${name}.svelte` }).js.code);
    const loaded = await import(pathToFileURL(file).href);
    return render(loaded.default, { props }).body;
  } finally { await rm(directory, { recursive: true }); }
}

function snapshot() {
  return {
    settings: { runtime_mode: 'shadow', apply_owner: 'legacy', apply_enabled: false },
    overview: { cover_position: 100, effective_target: 80, master_mode: 'normal',
      environment_values: { cover_motion: 'idle', outdoor_lux: 299, outdoor_temperature: 12 },
      household: { activity_state: 'pc' }, opening_state: 'tilted', winner: null,
      failure: { status: 'none' }, baseline_ready: true, apply_status: 'blocked', safety_status: 'ready',
      write_path_reachable: false, technical: { apply: { reason: 'apply_disabled' } } },
    diagnosis: { solar: { state: 'low_light' }, candidates: [
      { key: 'heat_protection', quality: 'fresh', reason: 'thermal_load_below_configured_band' },
    ] },
    operation: { revision: 'revision', pending: false, legacy_blocker: null },
  };
}

test('no target is idle, not a baseline or safety failure', async () => {
  const data = snapshot();
  data.overview.apply_status = 'idle';
  data.overview.technical.apply.reason = 'no_effective_target';
  const html = await component('Operation', { snapshot: data });
  assert.ok(html.includes('Bereit – aktuell kein Fahrziel'));
  assert.ok(html.includes('freigegeben'));
  assert.ok(!html.includes('bestätigt · idle'));
});

test('privacy explains the backend phase decision', async () => {
  const data = snapshot();
  data.diagnosis.candidates.push({ key: 'privacy', quality: 'fresh', active: true, reason: 'privacy_active' });
  const html = await component('Overview', { snapshot: data });
  assert.ok(html.includes('Sichtschutz aus Core-State-Abend-/Nachtphase'));
});

test('overview renders actual position separately from intent and explains inactive heat', async () => {
  const html = await component('Overview', { snapshot: snapshot() });
  for (const text of ['100 %', '80 %', 'Istposition', 'low_light', '299 lx', '12 °C', 'Temperaturschwelle nicht erreicht', 'Blind Control steuert die reale Position noch nicht']) assert.ok(html.includes(text), text);
});

test('missing measurements are not shown as valid values and exclusive rules are not invented', async () => {
  const data = snapshot(); data.overview.environment_values.outdoor_lux = null;
  data.overview.master_mode = 'manual';
  const html = await component('Overview', { snapshot: data });
  assert.ok(html.includes('nicht belastbar'));
  assert.ok(html.includes('Im aktuellen exklusiven Modus nicht bewertet'));
});

test('operation needs staging and explicit confirmation; stale transport cannot enable controls', async () => {
  const data = snapshot();
  let html = await component('Operation', { snapshot: data });
  assert.ok(!html.includes('Apply bewusst einschalten'));
  assert.match(html, /disabled[^>]*>Shadow \+ Legacy/);
  data.settings.runtime_mode = 'live'; data.settings.apply_owner = 'blind_control';
  html = await component('Operation', { snapshot: data, onOperation: async () => {} });
  assert.match(html, /disabled[^>]*>Apply bewusst einschalten/);
  assert.ok(html.includes('Null-Writer geprüft'));
  data.operation.pending = true;
  html = await component('Operation', { snapshot: data, onOperation: async () => {} });
  assert.ok(html.includes('Betriebswechsel wird geladen'));
});

test('transport sends only the explicit staged operation and concurrency token', async () => {
  const source = await readFile('src/lib/transport.ts', 'utf8');
  const js = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext } }).outputText;
  const transport = await import(`data:text/javascript;base64,${Buffer.from(js).toString('base64')}`);
  const calls = [];
  await transport.setOperation({ connection: { sendMessagePromise: async msg => calls.push(msg) } }, 'fresh-revision', 'live', 'blind_control', false, false);
  assert.deepEqual(calls, [{ type: 'blind_control/set_operation', expected_revision: 'fresh-revision', operation: { runtime_mode: 'live', apply_owner: 'blind_control', apply_enabled: false }, confirm_null_writer: false }]);
});

test('dimensions renders backend target, scoped quality and gates without another arbitration', async () => {
  const html = await component('Dimensions', {
    lifecycle: 'INACTIVE', exposure: 'night',
    decision: {
      context: { mode: 'sleep', variant: 'provisional_sleep', base_target: 5 },
      evidence: [{ key: 'activity_state', value: 'pc', details: [['media_device', 'pc'], ['activity_state', 'gaming']] }],
      contributions: [
        { feature: 'glare', variant: 'pc', effect: 'max_open', value: 75, status: 'paused', reason: 'fixture_pause' },
        { feature: 'private_time', variant: null, effect: 'max_open', value: 20, status: 'suppressed', reason: 'hard_safety_min_open' },
      ],
      issues: [{ feature: 'cold', quality: 'stale', evidence: 'outdoor_lux', owner: 'core_contracts', timestamp_basis: 'owner_field_quality_no_consumer_reaging', fallback: 'block_opening_direction', reason: 'fixture_loss' }],
      safety: { min_open: 30, block_direction: null, status: 'safe_position' },
      feasible_interval: [30, 100], target_position: 37,
      runtime_generation: 4, decision_generation: 12, runtime_status: 'active',
      lease_status: 'latest', apply_status: 'blocked', snapshot_identity: '4:12', config_revision: 'fixture-hash',
    },
  });
  for (const text of ['provisional_sleep', '37 %', 'private_time', 'suppressed', 'paused', 'cold', 'owner_field_quality_no_consumer_reaging', '4:12', 'INACTIVE', 'night', 'nicht gestoppt']) assert.ok(html.includes(text), text);
});
