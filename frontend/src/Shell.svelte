<script lang="ts">
  import App from './App.svelte';
  import type { UxSettings, UxSnapshot } from './lib/contracts';
  import { fetchSnapshot, updateOptions } from './lib/transport';
  import type { HassContext } from './lib/transport';

  let { hass }: { hass: HassContext } = $props();

  let snapshot = $state<UxSnapshot | null>(null);
  let error = $state<string | null>(null);
  let loading = $state(true);
  let saving = $state(false);

  async function refresh(): Promise<void> {
    try {
      const next = await fetchSnapshot(hass);
      snapshot = next;
      error = null;
    } catch (cause) {
      error = cause instanceof Error ? cause.message : 'Shadow snapshot unavailable';
    } finally {
      loading = false;
    }
  }

  async function saveSettings(settings: UxSettings): Promise<void> {
    saving = true;
    try {
      await updateOptions(hass, settings);
      await refresh();
    } finally {
      saving = false;
    }
  }

  $effect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 5000);
    return () => window.clearInterval(timer);
  });
</script>

{#if snapshot}
  <App {snapshot} onSaveSettings={saveSettings} {saving} />
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
