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
