<script lang="ts">
  import type { UxSnapshot } from './lib/contracts';
  let { snapshot, onOperation }: {
    snapshot: UxSnapshot;
    onOperation?: (mode: 'shadow' | 'live', owner: 'legacy' | 'blind_control', apply: boolean, confirmed: boolean) => Promise<void>;
  } = $props();
  let confirmed = $state(false);
  let busy = $state(false);
  let error = $state('');
  let staged = $derived(snapshot.settings.runtime_mode === 'live' && snapshot.settings.apply_owner === 'blind_control' && !snapshot.settings.apply_enabled);
  let blocked = $derived(!onOperation || !snapshot.operation || snapshot.operation.pending || busy);
  async function change(mode: 'shadow' | 'live', owner: 'legacy' | 'blind_control', apply: boolean) {
    if (!onOperation) return;
    busy = true; error = '';
    try { await onOperation(mode, owner, apply, confirmed); confirmed = false; }
    catch (cause) { error = cause instanceof Error ? cause.message : 'Betriebswechsel fehlgeschlagen'; }
    finally { busy = false; }
  }
</script>

<article class="card operation-card" aria-label="Betrieb">
  <div class="card-heading"><div><p class="eyebrow">BETRIEB</p><h2>Writer kontrolliert freigeben</h2></div><span class="badge">Apply {snapshot.settings.apply_enabled ? 'AN' : 'AUS'}</span></div>
  <dl class="facts">
    <div><dt>Aktuelle Generation / Lease</dt><dd>{snapshot.operation?.runtime_generation ?? '—'} / {snapshot.operation?.decision_generation ?? '—'} · {snapshot.operation?.lease_status ?? 'unbekannt'}</dd></div>
    <div><dt>Writer-Gates freigegeben</dt><dd>{snapshot.operation?.armed ? 'ja' : 'nein'}</dd></div>
    <div><dt>Betriebsmodus</dt><dd>{snapshot.settings.runtime_mode === 'shadow' ? 'Shadow' : 'Live'}</dd></div>
    <div><dt>Writer-Zuständigkeit</dt><dd>{snapshot.settings.apply_owner === 'legacy' ? 'Legacy' : 'Blind Control'}</dd></div>
    <div><dt>Readiness / Ruhebaseline</dt><dd>{snapshot.overview.baseline_ready ? 'bestätigt' : 'wartet'}</dd></div>
    <div><dt>Opening Safety</dt><dd>{snapshot.overview.opening_state} · {snapshot.overview.safety_status === 'ready' ? 'freigegeben' : snapshot.overview.safety_status}</dd></div>
    <div><dt>Schreibpfad erreichbar</dt><dd>{snapshot.overview.write_path_reachable ? 'ja' : 'nein'}</dd></div>
    <div><dt>Apply-Grund</dt><dd>{snapshot.overview.technical.apply.reason === 'no_effective_target' ? 'Bereit – aktuell kein Fahrziel' : String(snapshot.overview.technical.apply.reason ?? '—').replaceAll('_', ' ')}</dd></div>
  </dl>
  <div class="button-row">
    <p class="hint">Apply AUS verhindert neue Befehle, stoppt aber keine bereits angenommene physische Fahrt.</p>
    <button class="quiet-button" disabled={blocked} onclick={() => change('shadow', 'legacy', false)}>Shadow + Legacy · Apply AUS</button>
    <button class="quiet-button" disabled={blocked} onclick={() => change('live', 'blind_control', false)}>Live + Blind Control · Apply AUS</button>
  </div>
  {#if snapshot.settings.apply_enabled}
    <button class="quiet-button stop-button" disabled={blocked} onclick={() => change(snapshot.settings.runtime_mode, snapshot.settings.apply_owner, false)}>Apply ausschalten</button>
  {:else if staged}
    <p class="hint">Apply AN kann unmittelbar eine Fahrt der aktuellen Entscheidung auslösen. Legacy zuerst deaktivieren, HA neu starten und Null-Writer bestätigen.</p>
    <label class="toggle"><input type="checkbox" bind:checked={confirmed} disabled={blocked} />Legacy ist deaktiviert, HA neu gestartet und Null-Writer geprüft. Ich gebe die kontrollierte Fahrt frei.</label>
    <button class="primary-button" disabled={blocked || !confirmed || !!snapshot.operation?.legacy_blocker} onclick={() => change('live', 'blind_control', true)}>Apply bewusst einschalten</button>
  {/if}
  {#if snapshot.operation?.legacy_blocker}<p class="hint warning">Freigabe gesperrt: {snapshot.operation.legacy_blocker.replaceAll('_', ' ')}</p>{/if}
  {#if snapshot.operation?.pending}<p class="hint" role="status">Betriebswechsel wird geladen. Auf bestätigten Zustand warten.</p>{/if}
  {#if error}<p class="error" role="alert">{error}</p>{/if}
</article>
