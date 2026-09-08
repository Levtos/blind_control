<script lang="ts">
  import type { UxSnapshot } from './lib/contracts';
  let { snapshot }: { snapshot: UxSnapshot } = $props();
  const names: Record<string, string> = { normal: 'Regulär', manual: 'Manuell gehalten', failure: 'Entscheidung blockiert', heat: 'Hitzeschutz', cold: 'Kälteschutz', glare: 'Blendschutz', privacy: 'Privacy', waking: 'Aufwachen', sleep: 'Schlaf', away: 'Abwesend', low_light: 'low_light · geringe Solarenergie' };
  const reasons: Record<string, string> = {
    thermal_load_below_configured_band: 'Temperaturschwelle nicht erreicht',
    solar_exposure_not_relevant_for_heat: 'Keine relevante Solarenergie für Hitzeschutz',
    solar_confidence_below_configured_band: 'Solar-Evidence nicht ausreichend sicher',
    thermal_load_with_window_solar_relevance: 'Temperatur und Solarenergie erfordern Schutz',
    heat_temperature_not_fresh: 'Belastbare Temperaturevidence fehlt',
    storm_approaching_relaxes_heat: 'Gewitterregel entlastet Hitzeschutz',
    environment_enter_pending: 'Schutzbedingung wird stabilisiert',
    environment_exit_pending: 'Entlastung wird stabilisiert',
    cold_insulation_conditions_not_met: 'Kälte-/Dunkelheitsbedingungen nicht erfüllt',
    dark_cold_without_solar_gain: 'Dunkel und kalt, ohne relevanten Solargewinn',
    privacy_not_active: 'Kanonischer Privacy-State nicht aktiv',
    privacy_active: 'Kanonischer Privacy-State aktiv',
    private_time_active: 'Private Zeit aktiv',
    private_time_not_active: 'Private Zeit nicht aktiv',
  };
  const label = (value: string | null | undefined) => value ? names[value] ?? value.replaceAll('_', ' ') : '—';
  const position = (value: number | null) => value === null ? 'unbekannt' : `${Math.round(value)} %`;
  const metric = (key: string, unit: string) => snapshot.overview.environment_values[key] === null ? 'nicht belastbar' : `${snapshot.overview.environment_values[key]} ${unit}`;
  function explanation(key: string) {
    const candidate = snapshot.diagnosis.candidates.find(item => item.key === key);
    if (!candidate) return 'Im aktuellen exklusiven Modus nicht bewertet';
    if (candidate.paused) return `Pausiert durch ${label(candidate.suppressed_by)}`;
    if (candidate.quality !== 'fresh') return 'Erforderliche Evidence nicht belastbar';
    return reasons[candidate.reason] ?? (candidate.reason.includes('without_window_solar') ? 'Solar/Lux für Blendschutz nicht ausreichend' : candidate.reason.startsWith('no_') ? 'Keine passende Bildschirmaktivität' : candidate.active ? 'Schutzanforderung aktiv' : 'Bedingungen nicht erfüllt');
  }
</script>

<article class="card hero-card span-2">
  <p class="eyebrow">WARUM DIESE POSITION?</p>
  <h2>Rollo {snapshot.overview.environment_values.cover_motion === 'idle' ? 'steht' : 'ist'} bei</h2>
  <div class="target-row"><strong class="target-value">{position(snapshot.overview.cover_position)}</strong><span class="muted">Istposition · {label(String(snapshot.overview.environment_values.cover_motion ?? 'unknown'))}</span></div>
  <p class="decision-reason">Grund: {label(snapshot.overview.master_mode)}{snapshot.overview.winner ? ` · ${label(snapshot.overview.winner.variant ?? snapshot.overview.winner.category)}` : ''}</p>
  <div class="metric-strip">
    <div><span>Aktivität</span><strong>{label(snapshot.overview.household.activity_state)}</strong></div>
    <div><span>Opening</span><strong>{snapshot.overview.opening_state}</strong></div>
    <div><span>Solar</span><strong>{label(snapshot.diagnosis.solar.state)}</strong></div>
    <div><span>Außenhelligkeit</span><strong>{metric('outdoor_lux', 'lx')}</strong></div>
    <div><span>Außentemperatur</span><strong>{metric('outdoor_temperature', '°C')}</strong></div>
    <div><span>Aktuelles Ziel</span><strong>{position(snapshot.overview.effective_target)}</strong></div>
  </div>
  {#if snapshot.overview.failure.status !== 'none'}
    <p class="callout warning">Automatik blockiert: {snapshot.overview.failure.quality_blockers.map(item => `${label(item.key)} (${label(item.quality)})`).join(', ') || label(snapshot.overview.failure.reason)}. Kein normales Ziel freigegeben.</p>
  {/if}
  {#if snapshot.settings.runtime_mode === 'shadow'}<p class="hint">Shadow berechnet dieses Ziel. Blind Control steuert die reale Position noch nicht.</p>{/if}
</article>
<article class="card span-2">
  <p class="eyebrow">HAUPTREGELN</p><h2>Was greift — und was nicht?</h2>
  <div class="rule-grid">
    {#each [['heat_protection', 'Heat'], ['glare_pc', 'Glare · PC'], ['glare_tv', 'Glare · TV'], ['cold_insulation', 'Cold'], ['privacy', 'Privacy'], ['private_time', 'Private Zeit']] as [key, title]}
      <div class="rule"><strong>{title}</strong><p>{explanation(key)}</p></div>
    {/each}
  </div>
</article>
