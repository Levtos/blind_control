// @ts-check

/** @typedef {import('./contracts').UxSettings} UxSettings */

/**
 * Clone settings at the transport boundary so a local draft never aliases a
 * server snapshot object.
 *
 * @template T
 * @param {T} value
 * @returns {T}
 */
export function cloneSettings(value) {
  return structuredClone(value);
}

/**
 * Build a deterministic content revision without relying on object identity.
 *
 * @param {object} settings
 * @returns {string}
 */
export function settingsRevision(settings) {
  return JSON.stringify(canonicalize(settings));
}

/**
 * Keep a dirty local draft while accepting external server changes only when
 * the draft still represents the last confirmed server revision.
 *
 * @param {UxSettings | null} draftSettings
 * @param {string | null} confirmedRevision
 * @param {UxSettings} incomingSettings
 */
export function rebaseDraft(draftSettings, confirmedRevision, incomingSettings) {
  const incomingRevision = settingsRevision(incomingSettings);
  if (incomingRevision === confirmedRevision) {
    return {
      draftSettings,
      confirmedRevision,
      dirty: isDraftDirty(draftSettings, confirmedRevision),
      adopted: false,
    };
  }

  if (draftSettings && isDraftDirty(draftSettings, confirmedRevision)) {
    return {
      draftSettings,
      confirmedRevision: incomingRevision,
      dirty: isDraftDirty(draftSettings, incomingRevision),
      adopted: false,
    };
  }

  return {
    draftSettings: cloneSettings(incomingSettings),
    confirmedRevision: incomingRevision,
    dirty: false,
    adopted: true,
  };
}

/**
 * Settle a save attempt. A missing confirmation deliberately preserves the
 * draft, while a confirmed server result becomes the new clean baseline.
 *
 * @param {UxSettings | null} draftSettings
 * @param {string | null} confirmedRevision
 * @param {UxSettings | null} confirmedSettings
 */
export function settleSave(draftSettings, confirmedRevision, confirmedSettings) {
  if (!confirmedSettings) {
    return { draftSettings, confirmedRevision, saved: false };
  }
  return {
    draftSettings: cloneSettings(confirmedSettings),
    confirmedRevision: settingsRevision(confirmedSettings),
    saved: true,
  };
}

/**
 * @param {UxSettings | null} draftSettings
 * @param {string | null} confirmedRevision
 */
function isDraftDirty(draftSettings, confirmedRevision) {
  return Boolean(
    draftSettings
      && confirmedRevision
      && settingsRevision(draftSettings) !== confirmedRevision,
  );
}

/**
 * @param {unknown} value
 * @returns {unknown}
 */
function canonicalize(value) {
  if (Array.isArray(value)) {
    return value.map(canonicalize);
  }
  if (value && typeof value === 'object') {
    const record = /** @type {Record<string, unknown>} */ (value);
    return Object.fromEntries(
      Object.keys(record)
        .sort()
        .map((key) => [key, canonicalize(record[key])]),
    );
  }
  return value;
}
