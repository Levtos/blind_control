<script lang="ts">
  import App from './App.svelte';
  import type { UxSettings, UxSnapshot } from './lib/contracts';
  import { fetchSnapshot, updateOptions, setOperation } from './lib/transport';
  import type { HassContext } from './lib/transport';

  let { hass }: { hass: HassContext } = $props();

  let snapshot = $state<UxSnapshot | null>(null);
  let error = $state<string | null>(null);
  let loading = $state(true);
  let saving = $state(false);

  async function refresh(): Promise<UxSnapshot | null> {
    try {
      const next = await fetchSnapshot(hass);
      snapshot = next;
      error = null;
      return next;
    } catch (cause) {
      error = cause instanceof Error ? cause.message : 'Shadow snapshot unavailable';
      return null;
    } finally {
      loading = false;
    }
  }

  async function saveSettings(settings: UxSettings): Promise<UxSettings> {
    saving = true;
    try {
      await updateOptions(hass, settings);
      const confirmed = await refresh();
      if (!confirmed) throw new Error('Confirmed Shadow snapshot unavailable');
      return confirmed.settings;
    } finally {
      saving = false;
    }
  }

  async function changeOperation(mode: 'shadow' | 'live', owner: 'legacy' | 'blind_control', apply: boolean, confirmed: boolean): Promise<void> {
    if (!snapshot?.operation || error) throw new Error('Aktuelle Betriebsdaten fehlen');
    await setOperation(hass, snapshot.operation.revision, mode, owner, apply, confirmed);
    await refresh();
  }

  $effect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 5000);
    return () => window.clearInterval(timer);
  });
</script>

{#if snapshot}
  {#if error}<p class="callout error" role="alert">Verbindung unterbrochen — Anzeige möglicherweise veraltet. Bedienung gesperrt.</p>{/if}
  <App {snapshot} onSaveSettings={error ? undefined : saveSettings} onOperation={error ? undefined : changeOperation} {saving} />
{:else if loading}
  <main class="transport-state">
    <p class="eyebrow">BLIND CONTROL · SHADOW</p>
    <h1>Shadow-Daten werden geladen</h1>
    <p>Die Anzeige wartet auf die laufende Home-Assistant-Projektion.</p>
  </main>
{:else}
  <main class="transport-state error-state">
    <p class="eyebrow">BLIND CONTROL · SHADOW</p>
    <h1>Shadow-Projektion nicht verfügbar</h1>
    <p>{error ?? 'Unbekannter Transportfehler'}</p>
    <button class="quiet-button" type="button" onclick={() => void refresh()}>Erneut verbinden</button>
  </main>
{/if}
