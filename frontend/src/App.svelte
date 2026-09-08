<script lang="ts">
  import Operation from './Operation.svelte';
  import Overview from './Overview.svelte';
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
  type ProfileAxis = 'logical';

  let {
    snapshot,
    onSaveSettings,
    onOperation,
    saving = false,
  }: {
    snapshot: UxSnapshot;
    onSaveSettings?: (settings: UxSettings) => Promise<UxSettings>;
    onOperation?: (mode: 'shadow' | 'live', owner: 'legacy' | 'blind_control', apply: boolean, confirmed: boolean) => Promise<void>;
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
    const incomingSettings = $state.snapshot(snapshot.settings);
    const next = rebaseDraft(
      draftSettings,
      confirmedSettingsRevision,
      incomingSettings,
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
    core_contract_selected: 'Consumer API gewählt · Quality in Diagnose',
    compatibility_fallback_unselected: 'Keine zentrale Auswahl · kompatibler Owner-Fallback',
    opening: 'Opening / Fenster',
    room_climate: 'Raumklima',
    weather_environment: 'Wetter / Außenumgebung',
    low_light: 'Geringe Solarenergie',
    cold_lux_enter_threshold: 'Cold: Eintritt unter (lx)',
    cold_lux_exit_threshold: 'Cold: Austritt über (lx)',
    environment_hysteresis_ratio: 'Solar/Confidence: Haltefaktor (0–1)',
    environment_enter_seconds: 'Umweltschutz: Eintritt stabil (s)',
    environment_exit_seconds: 'Umweltschutz: Entlastung stabil (s)',
    movement_recovery_seconds: 'Bewegungsfehler: stabile Ruhe zur Erholung (s)',
    cold_outdoor_threshold: 'Cold: Außentemperatur bis (°C)',
    heat_indoor_threshold: 'Heat: Innentemperatur ab (°C)',
    heat_outdoor_threshold: 'Heat: Außentemperatur ab (°C)',
    cloud_cover_threshold: 'Wolkenschatten: Bewölkung ab (%)',
    model_lux_ratio: 'Beobachtete / erwartete Helligkeit (0–1)',
    minimum_incidence_factor: 'Min. Einfallsfaktor (0–1)',
    model_lux_per_watt: 'Modellhelligkeit (lx pro W/m²)',
    position_settle_seconds: 'Ruheposition bestätigen (s)',
    movement_timeout_seconds: 'Zielerreichung: Fehlerfrist (s)',
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
    live_ready: 'Live-Ziel bereit',
    applied: 'Ziel übergeben',
    stable: 'Ziel stabil',
    cooldown: 'Cooldown aktiv',
    manual_hold: 'Manuell gehalten',
    error: 'Fehler',
    required_resolved: 'Pflicht aufgelöst',
    required_unresolved: 'Pflicht nicht aufgelöst',
    conditional_resolved: 'Bedingt aufgelöst',
    conditional_unresolved: 'Bedingt nicht aufgelöst',
    conditional_not_applicable: 'Nicht erforderlich',
    optional_bound: 'Optional gebunden',
    optional_intentionally_empty: 'Bewusst leer',
    internal_provider_active: 'Interner Provider aktiv',
    internal_provider_degraded: 'Interner Provider mit letztem frischen Wert',
    external_override_active: 'Externes Override aktiv',
    provider_unavailable: 'Provider nicht verfügbar',
    provider_stale: 'Providerwert veraltet',
    legacy_bound: 'Legacy gebunden',
    legacy_not_available: 'Legacy nicht verfügbar',
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
    if (value === 'ready' || value === 'safe_position' || value === 'safety_ready' || value === 'shadow_ready' || value === 'live_ready' || value === 'applied' || value === 'stable') return 'ready';
    if (value === 'failure' || value === 'error' || value === 'unavailable') return 'error';
    if (value === 'blocked' || value === 'manual' || value === 'manual_hold' || value === 'cooldown' || value === 'holding_safe_position') return 'warning';
    return 'warning';
  };

  const bindingStatusTone = (value: string): string => {
    if (value === 'required_unresolved' || value === 'conditional_unresolved') return 'warning';
    if (value === 'required_resolved' || value === 'conditional_resolved' || value === 'optional_bound' || value === 'legacy_bound' || value === 'internal_provider_active' || value === 'external_override_active') return 'ready';
    if (value === 'provider_unavailable' || value === 'provider_stale') return 'warning';
    return 'muted';
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
    const serverSettings = $state.snapshot(snapshot.settings);
    draftSettings = cloneSettings(serverSettings);
    confirmedSettingsRevision = settingsRevision(serverSettings);
    saveError = null;
  }

  async function saveDraft(): Promise<void> {
    if (!onSaveSettings || !draftSettings) return;
    const submittedDraft = cloneSettings($state.snapshot(draftSettings));
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
    key: 'axis_inverted' | 'automation_enabled',
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
  <title>Blind Control · {snapshot.settings.runtime_mode === 'shadow' ? 'Shadow' : 'Live vorbereitet'}</title>
</svelte:head>

<div class="panel-root">
  <header class="app-header">
    <div>
      <p class="eyebrow">BLIND CONTROL · {snapshot.settings.runtime_mode.toUpperCase()} · {snapshot.settings.apply_owner === 'blind_control' ? 'BLIND CONTROL' : 'LEGACY'}</p>
      <h1>Wohnzimmer-Rollo</h1>
      <p class="subtitle">Aktuelle Entscheidung und kontrollierter Betrieb</p>
    </div>
    <div class="header-status">
      <span class={`status-dot ${statusTone(snapshot.overview.apply_status)}`}></span>
      <span>{snapshot.settings.runtime_mode === 'shadow' ? 'Shadow' : 'Live vorbereitet'} · {statusLabel(snapshot.overview.apply_status)}</span>
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
      <Overview {snapshot} />
      <div class="span-2"><Operation {snapshot} {onOperation} /></div>
    </section>
  {:else if activeTab === 'diagnosis'}
    <section class="diagnosis-layout" aria-label="Diagnose">
      <article class="card span-2">
        <p class="eyebrow">TECHNISCHE EBENE</p><h2>Baseline, Bewegung und Kontext</h2>
        <dl class="facts">
          <div><dt>Bewegung</dt><dd>{snapshot.overview.movement_status}</dd></div>
          <div><dt>Recovery</dt><dd>{snapshot.overview.recovery_status ?? '—'} · {snapshot.overview.movement_error ?? 'kein Fehler'}</dd></div>
          <div><dt>Ruhebaseline</dt><dd>{positionLabel(snapshot.overview.baseline_position)}</dd></div>
          <div><dt>Manual Override</dt><dd>{snapshot.overview.override.active ? 'aktiv' : 'inaktiv'}</dd></div>
          <div><dt>Core Contracts</dt><dd>{JSON.stringify(snapshot.diagnosis.core_contracts ?? {})}</dd></div>
        </dl>
        <h3>HAUSHALT & KONTEXT</h3>
        <dl class="facts">{#each Object.entries(snapshot.overview.household) as [key, value]}<div><dt>{labelFor(key)}</dt><dd>{contextValue(value)}</dd></div>{/each}</dl>
      </article>
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
            <div><dt>Capabilities</dt><dd>{snapshot.diagnosis.solar.capabilities.map(labelFor).join(', ') || '—'}</dd></div>
            <div><dt>Optionale Capabilities fehlen</dt><dd>{snapshot.diagnosis.solar.missing_optional_capabilities.map(labelFor).join(', ') || 'keine'}</dd></div>
            <div><dt>Verwendete Evidence</dt><dd>{snapshot.diagnosis.solar.used_evidence.map(labelFor).join(', ') || '—'}</dd></div>
            <div><dt>Abgeleitet</dt><dd>{snapshot.diagnosis.solar.derived_evidence.map(labelFor).join(', ') || 'keine'}</dd></div>
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
        </div>
<p class="hint">Betriebsmodus, Writer und Apply stehen unter Übersicht → Betrieb zur Verfügung.</p>
      </article>

      <article class="card">
        <p class="eyebrow">GEMEINSAME INPUTS</p><h2>Core Contracts · primärer Pfad</h2>
        <p class="hint">Vorhandene Contract-ID aus der Registry auswählen. Leer bedeutet expliziter kompatibler Owner-Fallback. Ein ausgewählter defekter Contract blockiert; er fällt nicht lokal zurück. Änderungen nur mit Apply AUS.</p>
        <label>Profil<select value={editableSettings.core_contract_profile} disabled={snapshot.settings.apply_enabled} onchange={(event) => { if (draftSettings) draftSettings.core_contract_profile = event.currentTarget.value as 'benni' | 'eltern'; }}><option value="benni">Benni</option><option value="eltern">Eltern</option></select></label>
        {#each ['opening', 'room_climate', 'weather_environment'] as schema}
          <label>{labelFor(schema)} · Contract-ID<input type="text" disabled={snapshot.settings.apply_enabled} value={editableSettings.core_contracts[schema] ?? ''} onchange={(event) => { if (draftSettings) { const value = event.currentTarget.value.trim(); if (value) draftSettings.core_contracts[schema] = value; else delete draftSettings.core_contracts[schema]; } }} /></label>
          <p class="hint">{labelFor(snapshot.diagnosis.core_contracts?.[schema] ?? 'compatibility_fallback_unselected')}</p>
        {/each}
        <p class="hint">Plattform-Gaps: Bio, Activity, Day/Context und weitere Solar-/Wetterfelder. Bis zu passenden zentralen Rollen bleiben ihre bisherigen Owner-Bindings erhalten.</p>
      </article>

      <article class="card span-2">
        <div class="card-heading"><div><p class="eyebrow">PROFILE</p><h2>Logische Zielposition</h2></div><div class="button-row"><span class="muted">{draftDirty ? 'Ungespeicherter Entwurf' : 'Serverstand bestätigt'}</span><button class="quiet-button" type="button" onclick={resetDraft}>Entwurf zurücksetzen</button><button class="primary-button" type="button" disabled={saving || !onSaveSettings} onclick={() => void saveDraft()}>{saving ? 'Speichere …' : 'Konfiguration speichern'}</button></div></div>
        {#if saveError}
          <p class="callout failure-callout">{saveError}</p>
        {/if}
        <div class="profile-table" role="table" aria-label="Positionsprofile">
          <div class="profile-row profile-header" role="row"><span>Profil</span><span>Logisch</span><span>Invertiert (abgeleitet)</span></div>
          {#each Object.entries(editableSettings.profiles) as [key, profile]}
            <div class="profile-row" role="row">
              <strong>{labelFor(key)}</strong>
              <input aria-label={`${key} logisch`} type="number" min="0" max="100" value={profile.logical} onchange={(event) => updateProfile(key, 'logical', event.currentTarget.valueAsNumber)} />
              <output>{100 - profile.logical} %</output>
            </div>
          {/each}
        </div>
      </article>

      <article class="card span-2">
        <div class="card-heading"><div><p class="eyebrow">KALIBRIERUNG</p><h2>Shadow-Defaults</h2></div><span class="muted">später trace-basiert kalibrieren</span></div>
        <p class="hint">Cold endet erst oberhalb der höheren Austrittsschwelle. Der Solar-Haltefaktor senkt die Austrittsschwellen für bestehenden Schutz. Eintritt und Entlastung müssen jeweils stabil bleiben; Safety reagiert sofort. Der Apply-Cooldown schützt den Motor unabhängig davon.</p>
        <div class="calibration-grid">
          {#each Object.entries(editableSettings.calibration_defaults) as [key, value]}
            <label>{labelFor(key)}<input type="number" min={key.endsWith("_temperature_threshold") || ["heat_indoor_threshold", "heat_outdoor_threshold", "cold_outdoor_threshold"].includes(key) ? -100 : 0} step="any" value={value} onchange={(event) => updateCalibration(key, event)} /></label>
          {/each}
        </div>
      </article>

      <article class="card span-2">
        <div class="card-heading"><div><p class="eyebrow">DOMÄNE & ÜBERGANG</p><h2>Lokales Cover und kompatible Fallbacks</h2></div><span class="muted">OptionsFlow</span></div>
        <p class="hint">Bearbeitung erfolgt ausschließlich über Blind Control → Konfigurieren im nativen Home-Assistant-OptionsFlow. Entity-IDs werden im Panel nicht angezeigt oder entgegengenommen.</p>
        <div class="binding-grid">
          {#each editableSettings.binding_groups as group}
            <section class="binding-group">
              <h3>{group.label} · {group.readiness === 'ready' ? 'bereit' : 'Pflicht-Evidence fehlt'}</h3>
              {#each group.fields as field}
                <div class="binding-row">
                  <strong>{labelFor(field.key)}</strong>
                  <span class={bindingStatusTone(field.status)}>{labelFor(field.status)}</span>
                  <small>{field.requirement === 'required' ? 'Pflicht' : field.requirement === 'conditional' ? 'bedingt erforderlich' : 'optional'} · {field.owner} · {field.max_age_seconds === null ? 'stateful' : `${field.max_age_seconds} s`} · {field.require_timestamp ? 'Zeitbeleg erforderlich' : 'kein Zeitbeleg erforderlich'}</small>
                </div>
              {/each}
              {#if group.key === 'opening_safety_cover_bindings'}
                <p class="hint">Opening-Safety-Polarität: {labelFor(editableSettings.opening_safety_polarity)}. Ohne explizite Polarität bleibt eine Kippfreigabe blockiert.</p>
              {/if}
            </section>
          {/each}
        </div>
      </article>
    </section>
  {/if}
</div>
