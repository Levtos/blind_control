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

export type MasterMode = 'normal' | 'manual' | 'failure';

export type Candidate = {
  key: string;
  category: string;
  variant: string | null;
  active: boolean;
  target_position: number | null;
  source: string;
  reason: string;
  quality: string;
  paused: boolean;
  suppressed_by: string | null;
};

export type DecisionWinner = {
  category: string;
  variant: string | null;
  candidate_key: string;
  target_position: number | null;
};

export type DecisionBranch = {
  category: string;
  variant: string | null;
  candidate_key: string;
  active: boolean;
  paused: boolean;
  winner: boolean;
  target_position: number | null;
  quality: string;
  source: string;
  reason: string;
  suppressed_by: string | null;
};

export type FailureDecision = {
  status: string;
  reason: string | null;
  hold_target: number | null;
  quality_blockers: { key: string; quality: string; reason: string }[];
};

export type PositionProfile = { normal: number; inverted: number };

export type BindingFreshness = {
  max_age_seconds: number | null;
  require_timestamp: boolean;
  owner: string;
};

export type BindingField = BindingFreshness & {
  key: string;
  configured: boolean;
  requirement: 'required' | 'conditional' | 'optional';
  status:
    | 'required_resolved'
    | 'required_unresolved'
    | 'conditional_resolved'
    | 'conditional_unresolved'
    | 'conditional_not_applicable'
    | 'optional_bound'
    | 'optional_intentionally_empty'
    | 'legacy_bound'
    | 'legacy_not_available';
};

export type BindingGroup = {
  key: string;
  label: string;
  readiness: 'ready' | 'missing_required';
  missing_required: string[];
  fields: BindingField[];
};

export type UxSettings = {
  axis_inverted: boolean;
  window_azimuth: number;
  window_tilt: number;
  automation_enabled: boolean;
  apply_enabled: boolean;
  runtime_mode: 'shadow' | 'live';
  apply_owner: 'legacy' | 'blind_control';
  opening_safety_polarity: 'unspecified' | 'positive_safe' | 'negative_unsafe';
  binding_groups: BindingGroup[];
  observation_freshness_seconds: number;
  binding_freshness: Record<string, BindingFreshness>;
  profiles: Record<string, PositionProfile>;
  calibration_defaults: Record<string, number>;
};

export type UxSnapshot = {
  version: 'blind_control.ux.v3';
  evaluated_at: string;
  overview: {
    master_mode: MasterMode;
    winner: DecisionWinner | null;
    active_branches: DecisionBranch[];
    failure: FailureDecision;
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
    technical: {
      opening_state: string;
      safety: Record<string, unknown>;
      apply: Record<string, unknown>;
      cover_available: boolean | null;
      cover_ready: boolean | null;
      shadow_only: boolean;
      actuation_executed: boolean;
      write_path_reachable: boolean;
      runtime_mode: 'shadow' | 'live';
      apply_owner: 'legacy' | 'blind_control';
    };
    shadow_only: boolean;
    actuation_executed: boolean;
    write_path_reachable: boolean;
  };
  diagnosis: {
    hierarchy: {
      master_mode: MasterMode;
      winner: DecisionWinner | null;
      active_branches: DecisionBranch[];
      failure: FailureDecision;
      legacy_flat: { active_mode: string; winner_keys: string[] };
    };
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
      capabilities: string[];
      missing_optional_capabilities: string[];
      used_evidence: string[];
      derived_evidence: string[];
      quality_blockers: { key: string; quality: string; reason: string }[];
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
  automation_projection: {
    version: 'blind_control.automation_projection.v2';
    master_mode: MasterMode;
    winner_category: string | null;
    winner_variant: string | null;
    active_category: string | null;
    active_variant: string | null;
    fachlicher_target: number | null;
    effective_target: number | null;
    failure_status: string;
    failure_reason: string | null;
    failure_quality_blockers: { key: string; quality: string; reason: string }[];
    safety_status: string;
    apply_status: string;
    safety_blocked: boolean;
    apply_blocked: boolean;
    shadow_only: boolean;
    actuation_executed: boolean;
    write_path_reachable: boolean;
    runtime_mode: 'shadow' | 'live';
    apply_owner: 'legacy' | 'blind_control';
  };
  debug_payload: Record<string, unknown>;
};
