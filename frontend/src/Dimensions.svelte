<script lang="ts">
  import type { DimensionalDecision } from './lib/contracts';
  let { decision, lifecycle, exposure }: { decision: DimensionalDecision; lifecycle: string; exposure: string } = $props();
  const position = (value: number | null) => value === null ? 'Halten / kein Ziel' : `${value} %`;
  let activity = $derived(decision.evidence.find(item => item.key === 'activity_state'));
</script>

<section class="surface-card">
  <h2>Entscheidung nach Dimensionen</h2>
  <p>Context: {decision.context.mode} {decision.context.variant ?? ''} · Basisziel: {position(decision.context.base_target)}</p>
  <p>Solar-Lifecycle: {lifecycle} · Exposure: {exposure}</p>
  <p>Gewählte Screen-Klasse: {String(activity?.value ?? 'unbekannt')}</p>
  {#each activity?.details ?? [] as [key, value]}<p>Owner-Evidence {key}: {String(value)}</p>{/each}
  <p>Safety: {decision.safety.status} · min_open: {decision.safety.min_open} % · Richtungssperre: {decision.safety.block_direction ?? 'keine'}</p>
  <p>Zulässiges Intervall: {decision.feasible_interval[0]}–{decision.feasible_interval[1]} % · Finales Ziel: {position(decision.target_position)}</p>
  <h3>Protection und Modifier</h3>
  {#each decision.contributions as item}
    <p>{item.feature} {item.variant ?? ''}: {item.status} · {item.effect} {position(item.value)} · {item.reason}</p>
  {/each}
  <h3>Feature-lokale Quality</h3>
  {#each decision.issues as issue}
    <p>{issue.feature}: {issue.quality} · {issue.evidence} · Owner: {issue.owner} · Zeitbasis: {issue.timestamp_basis} · Fallback: {issue.fallback} · {issue.reason}</p>
  {:else}
    <p>Keine feature-lokalen Quality-Issues.</p>
  {/each}
  <details>
    <summary>Generationen und Writer-Freigabe</summary>
    <p>Runtime {decision.runtime_generation}: {decision.runtime_status} · Decision {decision.decision_generation} · Lease: {decision.lease_status} · Apply: {decision.apply_status}</p>
    <p>Snapshot: {decision.snapshot_identity}</p>
    <p>Config-Revision: <code>{decision.config_revision}</code></p>
  </details>
  <p class="hint">Apply AUS verhindert neue Befehle. Eine bereits angenommene physische Fahrt wird dadurch nicht gestoppt.</p>
</section>
