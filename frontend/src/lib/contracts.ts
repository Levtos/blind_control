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

export type PositionProfile = { normal: number; inverted: number };

export type BindingFreshness = {
  max_age_seconds: number | null;
  require_timestamp: boolean;
  owner: string;
};

export type BindingStatus = {
  input_bindings: Record<string, boolean>;
  legacy_bindings: Record<string, boolean>;
};

export type UxSettings = {
  axis_inverted: boolean;
  window_azimuth: number;
  window_tilt: number;
  automation_enabled: boolean;
  apply_enabled: boolean;
  input_bindings: Record<string, string>;
  legacy_bindings: Record<string, string>;
  binding_status: BindingStatus;
  observation_freshness_seconds: number;
  binding_freshness: Record<string, BindingFreshness>;
  profiles: Record<string, PositionProfile>;
  calibration_defaults: Record<string, number>;
};

export type UxSnapshot = {
  version: 'blind_control.ux.v1';
  evaluated_at: string;
  overview: {
    active_mode: string;
    winner_keys: string[];
    fachlicher_target: number | null;
    effective_target: number | null;
    opening_state: string;
    cover_position: number | null;
    household: {
      bio_state: string | null;
      activity_state: string | null;
      day_state: string | null;
      day_context: string | null;
      away: boolean | null;
      private_time: boolean | null;
      privacy: boolean | null;
    };
    safety_status: string;
    apply_status: string;
    override: {
      active: boolean;
      baseline: number | null;
      observed_position: number | null;
      source: string;
      reason: string;
      started_at: string | null;
      context_key: Record<string, string> | null;
    };
    shadow_only: boolean;
    actuation_executed: boolean;
    write_path_reachable: boolean;
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
    diffs: {
      field: string;
      legacy_value: unknown;
      shadow_value: unknown;
      classification: string;
      reason: string;
      legacy_quality: string;
      legacy_source: string;
    }[];
    legacy_evidence: Record<string, unknown>;
  };
  settings: UxSettings;
  debug_payload: Record<string, unknown>;
};
