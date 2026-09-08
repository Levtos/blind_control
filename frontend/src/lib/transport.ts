import type { UxSettings, UxSnapshot } from './contracts';

export type HassConnection = {
  sendMessagePromise<T>(message: Record<string, unknown>): Promise<T>;
};

/** The context is supplied by Home Assistant through the custom panel element. */
export type HassContext = { connection: HassConnection };

export async function fetchSnapshot(hass: HassContext): Promise<UxSnapshot> {
  return hass.connection.sendMessagePromise<UxSnapshot>({
    type: 'blind_control/get_snapshot',
  });
}

export async function updateOptions(hass: HassContext, settings: UxSettings): Promise<void> {
  const options = {
    ...settings,
    ...settings.calibration_defaults,
  } as Record<string, unknown>;
  delete options.calibration_defaults;
  delete options.binding_groups;
  delete options.binding_freshness;
  delete options.runtime_mode;
  delete options.apply_owner;
  delete options.apply_enabled;

  await hass.connection.sendMessagePromise({
    type: 'blind_control/update_options',
    options,
  });
}

export async function setOperation(hass: HassContext, revision: string, mode: 'shadow' | 'live', owner: 'legacy' | 'blind_control', apply: boolean, confirmed: boolean): Promise<void> {
  await hass.connection.sendMessagePromise({
    type: 'blind_control/set_operation', expected_revision: revision,
    operation: { runtime_mode: mode, apply_owner: owner, apply_enabled: apply },
    confirm_null_writer: confirmed,
  });
}
