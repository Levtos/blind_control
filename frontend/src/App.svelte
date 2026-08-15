<script lang="ts">
  import type { Candidate, UxSettings, UxSnapshot } from './lib/contracts';

  type Tab = 'overview' | 'diagnosis' | 'settings';
  type ProfileAxis = 'normal' | 'inverted';

  let {
    snapshot,
    onSaveSettings,
    saving = false,
  }: {
    snapshot: UxSnapshot;
    onSaveSettings?: (settings: UxSettings) => Promise<void>;
    saving?: boolean;
  } = $props();
  let activeTab = $state<Tab>('overview');
  const cloneSettings = (settings: UxSettings): UxSettings => structuredClone(settings);
  let draftSettings = $state<UxSettings | null>(null);
  let editableSettings = $derived(draftSettings ?? snapshot.settings);
  let lastSnapshot = $state<UxSnapshot | undefined>();
  let copyState = $state<'idle' | 'copied' | 'failed'>('idle');
  let activeCandidates = $derived(snapshot.diagnosis.candidates.filter((candidate) => candidate.active));

  $effect(() => {
    if (lastSnapshot !== snapshot) {
      draftSettings = structuredClone(snapshot.settings);
      lastSnapshot = snapshot;
    }
  });

  const modeLabels: Record<string, string> = {
    daylight: 'Tageslicht',
    waking: 'Waking',
    sleep: 'Schlaf',
    away: 'Abwesend',
    privacy: 'Privacy',
    private_time: 'Private Zeit',
    none: 'Kein Modus',
  };

  const labelFor = (value: string): string => modeLabels[value] ?? value.replaceAll('_', ' ');

  const positionLabel = (value: number | null): string =>
    value === null ? '—' : `${Math.round(value)} %`;

  const statusLabel = (value: string): string => value.replaceAll('_', ' ');

  const statusTone = (value: string): string => {
    if (value === 'ready' || value === 'safety_ready' || value === 'shadow_ready') return 'ready';
    if (value === 'blocked') return 'blocked';
    if (value === 'error' || value === 'unavailable') return 'error';
    return 'warning';
  };

  const candidateClass = (candidate: Candidate): string =>
    candidate.paused ? 'candidate paused' : candidate.active ? 'candidate active' : 'candidate';

  function updateProfile(key: string, axis: ProfileAxis, value: number): void {
    if (!draftSettings) return;
    const profile = draftSettings.profiles[key];
    if (!profile || !Number.isFinite(value)) return;
    profile[axis] = Math.max(0, Math.min(100, value));
  }

  function resetDraft(): void {
    draftSettings = structuredClone(snapshot.settings);
  }

  async function saveDraft(): Promise<void> {
    if (onSaveSettings && draftSettings) await onSaveSettings(cloneSettings(draftSettings));
  }

  async function copyDebugPayload(): Promise<void> {
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard API unavailable');
      await navigator.clipboard.writeText(JSON.stringify(snapshot.debug_payload, null, 2));
      copyState = 'copied';
      window.setTimeout(() => (copyState = 'idle'), 1800);
    } catch {
      copyState = 'failed';
    }
  }

  function updateBinding(kind: 'input_bindings' | 'legacy_bindings', key: string, event: Event): void {
    if (!draftSettings) return;
    const value = (event.currentTarget as HTMLInputElement).value.trim();
    draftSettings[kind][key] = value;
  }

  function updateNumber(key: 'window_azimuth' | 'window_tilt', event: Event): void {
    if (!draftSettings) return;
    const value = (event.currentTarget as HTMLInputElement).valueAsNumber;
    if (Number.isFinite(value)) draftSettings[key] = value;
  }

  function updateBoolean(key: 'axis_inverted' | 'automation_enabled' | 'apply_enabled', event: Event): void {
    if (draftSettings) draftSettings[key] = (event.currentTarget as HTMLInputElement).checked;
  }

  function updateCalibration(key: string, event: Event): void {
    if (!draftSettings) return;
    const value = (event.currentTarget as HTMLInputElement).valueAsNumber;
    if (Number.isFinite(value)) draftSettings.calibration_defaults[key] = value;
  }
</script>

<svelte:head>
  <title>Blind Control · Shadow</title>
</svelte:head>

<div class="panel-root">
  <header class="app-header">
    <div>
      <p class="eyebrow">BLIND CONTROL · SHADOW</p>
      <h1>Wohnzimmer-Rollo</h1>
      <p class="subtitle">Deterministischer Entscheidungs- und Diagnosevertrag</p>
    </div>
    <div class="header-status">
      <span class={`status-dot ${statusTone(snapshot.overview.apply_status)}`}></span>
      <span>Shadow · {statusLabel(snapshot.overview.apply_status)}</span>
    </div>
  </header>

  <div class="tabs" aria-label="Blind Control Bereiche" role="tablist">
    {#each [
      ['overview', 'Übersicht'],
      ['diagnosis', 'Diagnose'],
      ['settings', 'Einstellungen'],
    ] as [tab, label]}
      <button
        class:active={activeTab === tab}
        class="tab"
        type="button"
        role="tab"
        aria-selected={activeTab === tab}
        onclick={() => (activeTab = tab as Tab)}
      >
        {label}
      </button>
    {/each}
  </div>

  {#if activeTab === 'overview'}
    <section class="content-grid" aria-label="Übersicht">
      <article class="hero-card card">
        <div class="card-heading">
          <div>
            <p class="eyebrow">AKTIVER MODUS</p>
            <h2>{labelFor(snapshot.overview.active_mode)}</h2>
          </div>
          <span class={`badge ${statusTone(snapshot.overview.safety_status)}`}>{statusLabel(snapshot.overview.safety_status)}</span>
        </div>
        <div class="target-row">
          <span class="target-value">{positionLabel(snapshot.overview.effective_target)}</span>
          <span class="muted">technisch freigegebenes Ziel</span>
        </div>
        <div class="metric-strip">
          <div><span>Fachliches Ziel</span><strong>{positionLabel(snapshot.overview.fachlicher_target)}</strong></div>
          <div><span>Gewinner</span><strong>{snapshot.overview.winner_keys.join(', ') || '—'}</strong></div>
          <div><span>Opening</span><strong>{statusLabel(snapshot.overview.opening_state)}</strong></div>
        </div>
      </article>

      <article class="card status-card">
        <div class="card-heading">
          <div><p class="eyebrow">TECHNISCHE GRENZE</p><h2>Safety & Apply</h2></div>
          <span class={`badge ${statusTone(snapshot.overview.safety_status)}`}>{statusLabel(snapshot.overview.safety_status)}</span>
        </div>
        <dl class="facts">
          <div><dt>Apply</dt><dd class={statusTone(snapshot.overview.apply_status)}>{statusLabel(snapshot.overview.apply_status)}</dd></div>
          <div><dt>Manual Override</dt><dd>{snapshot.overview.override.active ? 'aktiv' : 'inaktiv'}</dd></div>
          <div><dt>Shadow</dt><dd>{snapshot.overview.shadow_only ? 'nur Berechnung' : 'unbekannt'}</dd></div>
        </dl>
        <p class="callout">Keine Geräteaktion ist in diesem Contract erreichbar.</p>
      </article>

      <article class="card span-2">
        <div class="card-heading"><div><p class="eyebrow">ENTSCHEIDUNGSBAUM</p><h2>Aktive Kandidaten</h2></div><span class="muted">{activeCandidates.length} aktiv</span></div>
        <div class="candidate-grid">
          {#each activeCandidates as candidate}
            <div class={candidateClass(candidate)}>
              <div class="candidate-top"><strong>{labelFor(candidate.key)}</strong><span>{positionLabel(candidate.target_position)}</span></div>
              <p>{candidate.reason.replaceAll('_', ' ')}</p>
              <small>{candidate.quality} · {candidate.source}</small>
            </div>
          {:else}
            <p class="empty-state">Keine positive Anforderung liegt vor.</p>
          {/each}
        </div>
      </article>
    </section>
  {:else if activeTab === 'diagnosis'}
    <section class="diagnosis-layout" aria-label="Diagnose">
      <article class="card">
        <div class="card-heading"><div><p class="eyebrow">DECISION TRACE</p><h2>Kandidaten & pausierte Äste</h2></div><span class="badge">{snapshot.version}</span></div>
        <div class="trace-list">
          {#each snapshot.diagnosis.candidates as candidate}
            <div class={candidateClass(candidate)}>
              <div class="candidate-top"><strong>{labelFor(candidate.key)}</strong><span>{candidate.active ? positionLabel(candidate.target_position) : 'inaktiv'}</span></div>
              <p>{candidate.reason.replaceAll('_', ' ')}</p>
              <small>{candidate.paused ? `pausiert durch ${candidate.suppressed_by}` : candidate.quality} · {candidate.source}</small>
            </div>
          {/each}
        </div>
        {#if snapshot.diagnosis.paused_requirements.length}
          <h3>Pausiert</h3>
          <ul class="plain-list">
            {#each snapshot.diagnosis.paused_requirements as item}
              <li><strong>{labelFor(item.key)}</strong><span>{item.reason.replaceAll('_', ' ')}</span></li>
            {/each}
          </ul>
        {/if}
      </article>

      <div class="side-stack">
        <article class="card">
          <div class="card-heading"><div><p class="eyebrow">SOLAR EXPOSURE</p><h2>{statusLabel(snapshot.diagnosis.solar.state)}</h2></div><span class="badge">{Math.round(snapshot.diagnosis.solar.confidence * 100)} %</span></div>
          <dl class="facts">
            <div><dt>Einfallsfaktor</dt><dd>{snapshot.diagnosis.solar.incidence_factor?.toFixed(3) ?? '—'}</dd></div>
            <div><dt>Außen-Lux</dt><dd>{snapshot.diagnosis.solar.observed_lux ?? '—'}</dd></div>
            <div><dt>Trend</dt><dd>{snapshot.diagnosis.solar.lux_trend ?? '—'}</dd></div>
            <div><dt>Grund</dt><dd>{snapshot.diagnosis.solar.reason.replaceAll('_', ' ')}</dd></div>
          </dl>
        </article>
        <article class="card">
          <div class="card-heading"><div><p class="eyebrow">INPUT QUALITY</p><h2>Quellen</h2></div></div>
          <div class="source-list">
            {#each Object.entries(snapshot.diagnosis.inputs) as [key, value]}
              <div><span>{labelFor(key)}</span><code>{typeof value === 'string' ? value : JSON.stringify(value)}</code></div>
            {:else}
              <p class="empty-state">Noch keine owner-bound Inputs gebunden.</p>
            {/each}
          </div>
        </article>
        <article class="card debug-card">
          <div class="card-heading"><div><p class="eyebrow">EXPORT</p><h2>Debug-Payload</h2></div><button class="quiet-button" type="button" onclick={copyDebugPayload}>{copyState === 'copied' ? 'Kopiert' : copyState === 'failed' ? 'Kopieren fehlgeschlagen' : 'Evidence kopieren'}</button></div>
          <details>
            <summary>Kopierbare Shadow-Evidence anzeigen</summary>
            <pre>{JSON.stringify(snapshot.debug_payload, null, 2)}</pre>
          </details>
        </article>
      </div>
    </section>
  {:else}
    <section class="settings-layout" aria-label="Einstellungen">
      <article class="card">
        <div class="card-heading"><div><p class="eyebrow">GEOMETRIE & STATUS</p><h2>Fensterfläche</h2></div><span class={`badge ${statusTone(snapshot.overview.apply_status)}`}>{statusLabel(snapshot.overview.apply_status)}</span></div>
        <div class="form-grid">
          <label>Azimut (°)<input type="number" min="0" max="360" value={editableSettings.window_azimuth} onchange={(event) => updateNumber('window_azimuth', event)} /></label>
          <label>Neigung (°)<input type="number" min="0" max="180" value={editableSettings.window_tilt} onchange={(event) => updateNumber('window_tilt', event)} /></label>
          <label class="toggle"><input type="checkbox" checked={editableSettings.axis_inverted} onchange={(event) => updateBoolean('axis_inverted', event)} /> Achse invertiert</label>
          <label class="toggle"><input type="checkbox" checked={editableSettings.automation_enabled} onchange={(event) => updateBoolean('automation_enabled', event)} /> Automatik aktiv</label>
          <label class="toggle"><input type="checkbox" checked={editableSettings.apply_enabled} onchange={(event) => updateBoolean('apply_enabled', event)} /> Apply-Gate aktiv</label>
        </div>
        <p class="hint">Die Werte stammen aus der laufenden Shadow-Projektion. Speicherung läuft über den ConfigEntry-/OptionsFlow-Transport und erreicht keinen Cover-Service.</p>
      </article>

      <article class="card span-2">
        <div class="card-heading"><div><p class="eyebrow">PROFILE</p><h2>Normal / Invertiert</h2></div><div class="button-row"><button class="quiet-button" type="button" onclick={resetDraft}>Entwurf zurücksetzen</button><button class="primary-button" type="button" disabled={saving || !onSaveSettings} onclick={() => void saveDraft()}>{saving ? 'Speichere …' : 'Über OptionsFlow speichern'}</button></div></div>
        <div class="profile-table" role="table" aria-label="Positionsprofile">
          <div class="profile-row profile-header" role="row"><span>Profil</span><span>Normal</span><span>Invertiert</span></div>
          {#each Object.entries(editableSettings.profiles) as [key, profile]}
            <div class="profile-row" role="row">
              <strong>{labelFor(key)}</strong>
              <input aria-label={`${key} normal`} type="number" min="0" max="100" value={profile.normal} onchange={(event) => updateProfile(key, 'normal', event.currentTarget.valueAsNumber)} />
              <input aria-label={`${key} invertiert`} type="number" min="0" max="100" value={profile.inverted} onchange={(event) => updateProfile(key, 'inverted', event.currentTarget.valueAsNumber)} />
            </div>
          {/each}
        </div>
      </article>

      <article class="card span-2">
        <div class="card-heading"><div><p class="eyebrow">KALIBRIERUNG</p><h2>Shadow-Defaults</h2></div><span class="muted">später trace-basiert kalibrieren</span></div>
        <div class="calibration-grid">
          {#each Object.entries(editableSettings.calibration_defaults) as [key, value]}
            <label>{labelFor(key)}<input type="number" min="0" value={value} onchange={(event) => updateCalibration(key, event)} /></label>
          {/each}
        </div>
      </article>

      <article class="card span-2">
        <div class="card-heading"><div><p class="eyebrow">OWNER-BINDINGS</p><h2>Reale HA-Quellen</h2></div><span class="muted">OptionsFlow</span></div>
        <p class="hint">Entity IDs werden ausschließlich vom Owner konfiguriert; ohne frische Bindung bleibt die entsprechende Entscheidung blockiert.</p>
        <div class="binding-grid">
          {#each Object.entries(editableSettings.input_bindings) as [key, value]}
            <label>{labelFor(key)}<input type="text" value={value} onchange={(event) => updateBinding('input_bindings', key, event)} /></label>
          {/each}
          {#each Object.entries(editableSettings.legacy_bindings) as [key, value]}
            <label>Legacy · {labelFor(key)}<input type="text" value={value} onchange={(event) => updateBinding('legacy_bindings', key, event)} /></label>
          {/each}
        </div>
      </article>
    </section>
  {/if}
</div>
