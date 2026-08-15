export type UiStatus =
  | 'loading'
  | 'ready'
  | 'empty'
  | 'stale'
  | 'degraded'
  | 'unavailable'
  | 'reconnecting'
  | 'offline'
  | 'error'
  | 'blocked';

export type Candidate = {
  key: string;
  category: string;
  active: boolean;
  target_position: number | null;
  source: string;
  reason: string;
  quality: string;
  paused: boolean;
  suppressed_by: string | null;
};

export type UxSnapshot = {
  version: 'blind_control.ux.v1';
  overview: {
    active_mode: string;
    winner_keys: string[];
    fachlicher_target: number | null;
    effective_target: number | null;
    opening_state: string;
    safety_status: string;
    apply_status: string;
    override: {
      active: boolean;
      baseline: number | null;
      observed_position: number | null;
      source: string;
      reason: string;
      started_at: string | null;
    };
    shadow_only: boolean;
  };
  diagnosis: {
    candidates: Candidate[];
    paused_requirements: { key: string; reason: string; source: string }[];
    solar: {
      state: string;
      confidence: number;
      incidence_factor: number | null;
      expected_radiation_w_m2: number | null;
      observed_lux: number | null;
      lux_trend: number | null;
      cloud_shadow: boolean;
      sources: string[];
      reason: string;
    };
    reasons: string[];
    inputs: Record<string, unknown>;
    diffs: { field: string; legacy_value: unknown; shadow_value: unknown; classification: string; reason: string }[];
  };
  debug_payload: Record<string, unknown>;
  settings: {
    axis_inverted: boolean;
    window_azimuth: number;
    window_tilt: number;
    automation_enabled: boolean;
    apply_enabled: boolean;
    profiles: Record<string, { normal: number; inverted: number }>;
    calibration_defaults: Record<string, number>;
  };
};

export const sampleSnapshot: UxSnapshot = {
  version: 'blind_control.ux.v1',
  overview: {
    active_mode: 'daylight',
    winner_keys: ['base_daylight'],
    fachlicher_target: 100,
    effective_target: null,
    opening_state: 'unknown',
    safety_status: 'blocked',
    apply_status: 'blocked',
    override: {
      active: false,
      baseline: null,
      observed_position: null,
      source: 'none',
      reason: 'unbound_input_contract',
      started_at: null,
    },
    shadow_only: true,
  },
  diagnosis: {
    candidates: [
      {
        key: 'base_daylight',
        category: 'base_state',
        active: true,
        target_position: 100,
        source: 'core_state.day',
        reason: 'canonical_day_state_is_daylight',
        quality: 'fresh',
        paused: false,
        suppressed_by: null,
      },
      {
        key: 'heat_protection',
        category: 'environment',
        active: false,
        target_position: null,
        source: 'weather_temperature',
        reason: 'heat_temperature_not_fresh',
        quality: 'unknown',
        paused: false,
        suppressed_by: null,
      },
    ],
    paused_requirements: [],
    solar: {
      state: 'unknown',
      confidence: 0,
      incidence_factor: null,
      expected_radiation_w_m2: null,
      observed_lux: null,
      lux_trend: null,
      cloud_shadow: false,
      sources: [],
      reason: 'unbound_input_contract',
    },
    reasons: ['opening_contract_not_fresh_positive_evidence_required', 'shadow_intent_only_no_write_path'],
    inputs: {},
    diffs: [],
  },
  settings: {
    axis_inverted: false,
    window_azimuth: 124,
    window_tilt: 90,
    automation_enabled: true,
    apply_enabled: true,
    profiles: {
      waking: { normal: 100, inverted: 0 },
      sleep: { normal: 5, inverted: 60 },
      privacy: { normal: 40, inverted: 60 },
      heat_protection: { normal: 15, inverted: 55 },
      glare_tv: { normal: 60, inverted: 40 },
      glare_pc: { normal: 75, inverted: 25 },
      cold_insulation: { normal: 5, inverted: 60 },
    },
    calibration_defaults: {
      heat_outdoor_threshold: 30,
      heat_indoor_threshold: 26,
      heat_radiation_threshold: 250,
      heat_confidence_threshold: 0.55,
      cloud_shadow_lux_drop: 1000,
      cloud_shadow_ratio: 0.75,
      cool_air_delta: 2,
      storm_required_signals: 2,
      diffuse_lux_threshold: 2500,
      night_lux_threshold: 50,
      cold_outdoor_threshold: 8,
      storm_precipitation_trend_threshold: 0,
      storm_wind_trend_threshold: 0,
      storm_pressure_drop_threshold: 0,
      apply_cooldown_seconds: 60,
      position_tolerance: 3,
    },
  },
  debug_payload: {
    version: 'blind_control.shadow.v1',
    shadow_only: true,
    actuation_executed: false,
    write_path_reachable: false,
  },
};
