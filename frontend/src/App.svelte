<script lang="ts">
  import type {
    Candidate,
    DecisionBranch,
    UxSettings,
    UxSnapshot,
  } from './lib/contracts';
  import {
    cloneSettings,
    rebaseDraft,
    settingsRevision,
    settleSave,
  } from './lib/draft-settings.js';

  type Tab = 'overview' | 'diagnosis' | 'settings';
  type ProfileAxis = 'normal' | 'inverted';

  let {
    snapshot,
    onSaveSettings,
    saving = false,
  }: {
    snapshot: UxSnapshot;
    onSaveSettings?: (settings: UxSettings) => Promise<UxSettings>;
    saving?: boolean;
  } = $props();

  let activeTab = $state<Tab>('overview');
  let draftSettings = $state<UxSettings | null>(null);
  let confirmedSettingsRevision = $state<string | null>(null);
  let saveError = $state<string | null>(null);
  let copyState = $state<'idle' | 'copied' | 'failed'>('idle');
  let editableSettings = $derived(draftSettings ?? snapshot.settings);
  let draftDirty = $derived(
    draftSettings !== null
      && confirmedSettingsRevision !== null
      && settingsRevision(draftSettings) !== confirmedSettingsRevision,
  );
  let activeBranches = $derived(snapshot.overview.active_branches);
  let supportingBranches = $derived(activeBranches.filter((branch) => !branch.winner && !branch.paused));
  let pausedBranches = $derived(activeBranches.filter((branch) => branch.paused));

  $effect(() => {
    const next = rebaseDraft(
      draftSettings,
      confirmedSettingsRevision,
      snapshot.settings,
    );
    if (
      next.draftSettings !== draftSettings
      || next.confirmedRevision !== confirmedSettingsRevision
    ) {
      draftSettings = next.draftSettings;
      confirmedSettingsRevision = next.confirmedRevision;
    }
  });

  const labels: Record<string, string> = {
    normal: 'Regulär',
    manual: 'Manuell',
    failure: 'Fehler',
    neutral: 'Neutral',
    waking: 'Waking',
    sleep: 'Schlaf',
    away: 'Abwesend',
    privacy: 'Privacy',
    private_time: 'Private Zeit',
    glare: 'Blendung',
    general: 'Allgemein',
    tv: 'TV',
    pc: 'PC',
    climate: 'Klima',
    heat: 'Hitze',
    cold: 'Kälte',
    storm: 'Gewitter',
    cool_air: 'Kühle Luft',
    override: 'Override',
    manual_override: 'Manueller Override',
    bio_state: 'Bio',
    activity_state: 'Aktivität',
    day_state: 'Tag',
    day_context: 'Tageskontext',
    daylight: 'Tageslicht',
    ready: 'bereit',
    blocked: 'blockiert',
    safe_position: 'Safety-Position',
    safety_ready: 'Safety bereit',
    shadow_ready: 'Shadow bereit',
  };

  const labelFor = (value: string | null | undefined): string => {
    if (!value) return '—';
    return labels[value] ?? value.replaceAll('_', ' ');
  };

  const branchLabel = (
    branch: { category: string; variant: string | null } | null,
  ): string => {
    if (!branch) return '—';
    return branch.variant
      ? `${labelFor(branch.category)} → ${labelFor(branch.variant)}`
      : labelFor(branch.category);
  };

  const positionLabel = (value: number | null): string =>
    value === null ? '—' : `${Math.round(value)} %`;

  const statusLabel = (value: string | null | undefined): string => labelFor(value);

  const failureBlockersLabel = (
    blockers: { key: string; quality: string; reason: string }[],
  ): string => blockers
    .map((blocker) => `${labelFor(blocker.key)} (${labelFor(blocker.quality)})`)
    .join(', ');

  const statusTone = (value: string | null | undefined): string => {
    if (value === 'ready' || value === 'safe_position' || value === 'safety_ready' || value === 'shadow_ready') return 'ready';
    if (value === 'failure' || value === 'error' || value === 'unavailable') return 'error';
    if (value === 'blocked' || value === 'manual' || value === 'holding_safe_position') return 'warning';
    return 'warning';
  };

  const householdLabel = (value: boolean | null): string =>
    value === null ? '—' : value ? 'ja' : 'nein';

  const contextValue = (value: string | boolean | null): string =>
    typeof value === 'boolean' ? householdLabel(value) : statusLabel(value);

  const candidateClass = (candidate: Candidate | DecisionBranch): string =>
    candidate.paused ? 'candidate paused' : candidate.active ? 'candidate active' : 'candidate';

  const recordValue = (record: Record<string, unknown>, key: string): string =>
    statusLabel(typeof record[key] === 'string' ? record[key] : null);

  function updateProfile(key: string, axis: ProfileAxis, value: number): void {
    if (!draftSettings) return;
    const profile = draftSettings.profiles[key];
    if (!profile || !Number.isFinite(value)) return;
    profile[axis] = Math.max(0, Math.min(100, value));
  }

  function resetDraft(): void {
    draftSettings = cloneSettings(snapshot.settings);
    confirmedSettingsRevision = settingsRevision(snapshot.settings);
    saveError = null;
  }

  async function saveDraft(): Promise<void> {
    if (!onSaveSettings || !draftSettings) return;
    const submittedDraft = cloneSettings(draftSettings);
    const submittedRevision = settingsRevision(submittedDraft);
    saveError = null;
    try {
      const confirmedSettings = await onSaveSettings(submittedDraft);
      if (draftSettings && settingsRevision(draftSettings) === submittedRevision) {
        const settled = settleSave(
          draftSettings,
          confirmedSettingsRevision,
          confirmedSettings,
        );
        draftSettings = settled.draftSettings;
        confirmedSettingsRevision = settled.confirmedRevision;
      } else {
        confirmedSettingsRevision = settingsRevision(confirmedSettings);
      }
    } catch {
      const preserved = settleSave(draftSettings, confirmedSettingsRevision, null);
      draftSettings = preserved.draftSettings;
      confirmedSettingsRevision = preserved.confirmedRevision;
      saveError = 'Speichern fehlgeschlagen. Der lokale Entwurf bleibt erhalten.';
    }
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

  function updateNumber(key: 'window_azimuth' | 'window_tilt', event: Event): void {
    if (!draftSettings) return;
    const value = (event.currentTarget as HTMLInputElement).valueAsNumber;
    if (Number.isFinite(value)) draftSettings[key] = value;
  }

  function updateBoolean(
    key: 'axis_inverted' | 'automation_enabled' | 'apply_enabled',
    event: Event,
  ): void {
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
      <p class="eyebrow">BLIND CONTROL · SHADOW · NOT LIVE</p>
      <h1>Wohnzimmer-Rollo</h1>
      <p class="subtitle">Versionierter Entscheidungs-, Safety- und Shadow-Vertrag</p>
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
            <p class="eyebrow">MASTERMODUS</p>
            <h2>{labelFor(snapshot.overview.master_mode)}</h2>
          </div>
          <span class={`badge ${statusTone(snapshot.overview.master_mode)}`}>{statusLabel(snapshot.overview.master_mode)}</span>
        </div>
        <div class="target-row">
          <span class="target-value">{positionLabel(snapshot.overview.effective_target)}</span>
          <span class="muted">effektives beziehungsweise gehaltenes Ziel</span>
        </div>
        <div class="metric-strip">
          <div><span>Gewinner</span><strong>{branchLabel(snapshot.overview.winner)}</strong></div>
          <div><span>Fachliches Ziel</span><strong>{positionLabel(snapshot.overview.fachlicher_target)}</strong></div>
          <div><span>Safety</span><strong>{statusLabel(snapshot.overview.safety_status)}</strong></div>
        </div>
        {#if snapshot.overview.failure.status !== 'none'}
          <p class="callout failure-callout">
            Failure · {snapshot.overview.failure.reason?.replaceAll('_', ' ') ?? 'unbekannter Grund'} ·
            {snapshot.overview.failure.hold_target === null
              ? 'Apply blockiert'
              : `Position halten: ${positionLabel(snapshot.overview.failure.hold_target)}`}
            {#if snapshot.overview.failure.quality_blockers.length}
              · Fehlende belastbare Evidence: {failureBlockersLabel(snapshot.overview.failure.quality_blockers)}
            {/if}
          </p>
        {/if}
      </article>

      <article class="card status-card">
        <div class="card-heading">
          <div><p class="eyebrow">TECHNISCHE EBENE</p><h2>Safety & Apply</h2></div>
          <span class={`badge ${statusTone(snapshot.overview.apply_status)}`}>{statusLabel(snapshot.overview.apply_status)}</span>
        </div>
        <dl class="facts">
          <div><dt>Opening</dt><dd>{statusLabel(snapshot.overview.technical.opening_state)}</dd></div>
          <div><dt>Safety</dt><dd class={statusTone(recordValue(snapshot.overview.technical.safety, 'status'))}>{recordValue(snapshot.overview.technical.safety, 'status')}</dd></div>
          <div><dt>Apply</dt><dd class={statusTone(recordValue(snapshot.overview.technical.apply, 'status'))}>{recordValue(snapshot.overview.technical.apply, 'status')}</dd></div>
          <div><dt>Coverposition</dt><dd>{positionLabel(snapshot.overview.cover_position)}</dd></div>
          <div><dt>Cover bereit</dt><dd>{householdLabel(snapshot.overview.technical.cover_ready)}</dd></div>
          <div><dt>Manual Override</dt><dd>{snapshot.overview.override.active ? 'aktiv' : 'inaktiv'}</dd></div>
        </dl>
        <p class="eyebrow">HAUSHALT & KONTEXT</p>
        <dl class="facts">
          {#each Object.entries(snapshot.overview.household) as [key, value]}
            <div><dt>{labelFor(key)}</dt><dd>{contextValue(value)}</dd></div>
          {/each}
        </dl>
        <p class="callout">Safety und Apply sind technisch getrennt; der Mastermodus bleibt fachlich lesbar.</p>
      </article>

      <article class="card span-2">
        <div class="card-heading">
          <div><p class="eyebrow">FACHLICHER ENTSCHEIDUNGSBAUM</p><h2>Kategorie → Variante → Nebenäste</h2></div>
          <span class="muted">{activeBranches.length} aktiv oder pausiert</span>
        </div>
        {#if snapshot.overview.winner}
          <div class="winner-tree">
            <span>Gewinner</span>
            <strong>{labelFor(snapshot.overview.master_mode)} → {branchLabel(snapshot.overview.winner)}</strong>
            <span>{positionLabel(snapshot.overview.winner.target_position)}</span>
          </div>
        {:else}
          <p class="empty-state">Keine fachlich belastbare Gewinneranforderung vorhanden.</p>
        {/if}
        <div class="candidate-grid">
          {#each supportingBranches as branch}
            <div class={candidateClass(branch)}>
              <div class="candidate-top"><strong>{branchLabel(branch)}</strong><span>{positionLabel(branch.target_position)}</span></div>
              <p>Aktiver Nebenast · {branch.reason.replaceAll('_', ' ')}</p>
              <small>{branch.quality} · {branch.source}</small>
            </div>
          {/each}
          {#each pausedBranches as branch}
            <div class={candidateClass(branch)}>
              <div class="candidate-top"><strong>{branchLabel(branch)}</strong><span>pausiert</span></div>
              <p>{branch.suppressed_by ? `unterdrückt durch ${labelFor(branch.suppressed_by)}` : branch.reason.replaceAll('_', ' ')}</p>
              <small>{branch.quality} · {branch.source}</small>
            </div>
          {/each}
        </div>
      </article>
    </section>
  {:else if activeTab === 'diagnosis'}
    <section class="diagnosis-layout" aria-label="Diagnose">
      <article class="card">
        <div class="card-heading"><div><p class="eyebrow">DECISION TRACE</p><h2>Hierarchie und flache Diagnose</h2></div><span class="badge">{snapshot.version}</span></div>
        <div class="winner-tree">
          <span>Master</span>
          <strong>{labelFor(snapshot.diagnosis.hierarchy.master_mode)} → {branchLabel(snapshot.diagnosis.hierarchy.winner)}</strong>
          <span>{snapshot.diagnosis.hierarchy.failure.status === 'none' ? 'belastbar' : snapshot.diagnosis.hierarchy.failure.status}</span>
        </div>
        <h3>Flache Kandidatenliste (Diagnose)</h3>
        <div class="trace-list">
          {#each snapshot.diagnosis.candidates as candidate}
            <div class={candidateClass(candidate)}>
              <div class="candidate-top"><strong>{branchLabel(candidate)}</strong><span>{candidate.active ? positionLabel(candidate.target_position) : 'inaktiv'}</span></div>
              <p>{candidate.reason.replaceAll('_', ' ')}</p>
              <small>{candidate.paused ? `pausiert durch ${candidate.suppressed_by}` : candidate.quality} · {candidate.source}</small>
            </div>
          {/each}
        </div>
        {#if snapshot.diagnosis.paused_requirements.length}
          <h3>Pausiert / unterdrückt</h3>
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
          <div class="card-heading"><div><p class="eyebrow">INPUT QUALITY</p><h2>Owner-gebundene Inputs</h2></div></div>
          <div class="source-list">
            {#each Object.entries(snapshot.diagnosis.inputs) as [key, value]}
              <div><span>{labelFor(key)}</span><code>{typeof value === 'string' ? value : JSON.stringify(value)}</code></div>
            {:else}
              <p class="empty-state">Noch keine owner-bound Inputs gebunden.</p>
            {/each}
          </div>
        </article>
        <article class="card debug-card">
          <div class="card-heading"><div><p class="eyebrow">EXPORT</p><h2>Redigierte Debug-Evidence</h2></div><button class="quiet-button" type="button" onclick={copyDebugPayload}>{copyState === 'copied' ? 'Kopiert' : copyState === 'failed' ? 'Kopieren fehlgeschlagen' : 'Evidence kopieren'}</button></div>
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
        <p class="hint">Die Werte stammen aus der laufenden Shadow-Projektion. Speicherung erreicht niemals einen Cover-Service.</p>
      </article>

      <article class="card span-2">
        <div class="card-heading"><div><p class="eyebrow">PROFILE</p><h2>Normal / Invertiert</h2></div><div class="button-row"><span class="muted">{draftDirty ? 'Ungespeicherter Entwurf' : 'Serverstand bestätigt'}</span><button class="quiet-button" type="button" onclick={resetDraft}>Entwurf zurücksetzen</button><button class="primary-button" type="button" disabled={saving || !onSaveSettings} onclick={() => void saveDraft()}>{saving ? 'Speichere …' : 'Shadow-Konfiguration speichern'}</button></div></div>
        {#if saveError}
          <p class="callout failure-callout">{saveError}</p>
        {/if}
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
        <div class="card-heading"><div><p class="eyebrow">OWNER-BINDINGS</p><h2>Native Entity-Selectoren</h2></div><span class="muted">OptionsFlow</span></div>
        <p class="hint">Bearbeitung erfolgt ausschließlich über Blind Control → Konfigurieren im nativen Home-Assistant-OptionsFlow. Entity-IDs werden im Panel nicht angezeigt oder entgegengenommen.</p>
        <div class="binding-grid">
          {#each editableSettings.binding_groups as group}
            <section class="binding-group">
              <h3>{group.label}</h3>
              {#each group.fields as field}
                <div class="binding-row">
                  <strong>{labelFor(field.key)}</strong>
                  <span class={field.configured ? 'ready' : 'warning'}>{field.configured ? 'konfiguriert' : 'nicht konfiguriert'}</span>
                  <small>{field.owner} · {field.max_age_seconds === null ? 'stateful' : `${field.max_age_seconds} s`} · {field.require_timestamp ? 'Zeitbeleg erforderlich' : 'kein Zeitbeleg erforderlich'}</small>
                </div>
              {/each}
            </section>
          {/each}
        </div>
      </article>
    </section>
  {/if}
</div>
