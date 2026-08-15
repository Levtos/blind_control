import type { UxSettings, UxSnapshot } from './contracts';

type HassConnection = {
  sendMessagePromise<T>(message: Record<string, unknown>): Promise<T>;
};

type HassHost = {
  connection?: HassConnection;
};

function resolveConnection(): HassConnection {
  const windows = [window, window.parent];
  for (const candidate of windows) {
    const host = candidate as Window & { hass?: HassHost; hassConnection?: HassConnection };
    if (host.hassConnection) return host.hassConnection;
    if (host.hass?.connection) return host.hass.connection;
  }
  const homeAssistant = window.parent.document.querySelector('home-assistant') as {
    hass?: HassHost;
  } | null;
  if (homeAssistant?.hass?.connection) return homeAssistant.hass.connection;
  throw new Error('Home Assistant WebSocket connection unavailable');
}

export async function fetchSnapshot(): Promise<UxSnapshot> {
  return resolveConnection().sendMessagePromise<UxSnapshot>({
    type: 'blind_control/get_snapshot',
  });
}

export async function updateOptions(settings: UxSettings): Promise<void> {
  const options = {
    ...settings,
    ...settings.calibration_defaults,
  } as Record<string, unknown>;
  delete options.calibration_defaults;
  await resolveConnection().sendMessagePromise({
    type: 'blind_control/update_options',
    options,
  });
}
