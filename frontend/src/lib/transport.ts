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
  delete options.binding_status;

  for (const key of ['input_bindings', 'legacy_bindings'] as const) {
    const configured = Object.fromEntries(
      Object.entries(settings[key]).filter(([, value]) => value.trim().length > 0),
    );
    delete options[key];
    if (Object.keys(configured).length > 0) options[key] = configured;
  }

  await hass.connection.sendMessagePromise({
    type: 'blind_control/update_options',
    options,
  });
}
