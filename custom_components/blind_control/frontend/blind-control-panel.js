var __defProp = Object.defineProperty;
var __typeError = (msg) => {
  throw TypeError(msg);
};
var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __publicField = (obj, key, value) => __defNormalProp(obj, typeof key !== "symbol" ? key + "" : key, value);
var __accessCheck = (obj, member, msg) => member.has(obj) || __typeError("Cannot " + msg);
var __privateGet = (obj, member, getter) => (__accessCheck(obj, member, "read from private field"), getter ? getter.call(obj) : member.get(obj));
var __privateAdd = (obj, member, value) => member.has(obj) ? __typeError("Cannot add the same private member more than once") : member instanceof WeakSet ? member.add(obj) : member.set(obj, value);
var __privateSet = (obj, member, value, setter) => (__accessCheck(obj, member, "write to private field"), setter ? setter.call(obj, value) : member.set(obj, value), value);
var __privateMethod = (obj, member, method) => (__accessCheck(obj, member, "access private method"), method);
var _a, _anchor, _hydrate_open, _props, _children, _effect, _main_effect, _pending_effect, _failed_effect, _offscreen_fragment, _local_pending_count, _pending_count, _pending_count_update_queued, _dirty_effects, _maybe_dirty_effects, _effect_pending, _effect_pending_subscriber, _Boundary_instances, hydrate_resolved_content_fn, hydrate_failed_content_fn, create_reset_fn, hydrate_pending_content_fn, render_fn, resolve_fn, run_fn, update_pending_count_fn, handle_error_fn, _started, _prev, _next, _commit_callbacks, _discard_callbacks, _pending, _blocking_pending, _deferred, _roots, _new_effects, _dirty_effects2, _maybe_dirty_effects2, _skipped_branches, _unskipped_branches, _decrement_queued, _Batch_instances, is_deferred_fn, process_fn, traverse_fn, find_earlier_batch_fn, merge_fn, defer_effects_fn, commit_fn, unlink_fn, _b, _batches, _onscreen, _offscreen, _outroing, _transition, _commit, _discard, _c;
const DEV = false;
var is_array = Array.isArray;
var index_of = Array.prototype.indexOf;
var includes = Array.prototype.includes;
var array_from = Array.from;
var define_property = Object.defineProperty;
var get_descriptor = Object.getOwnPropertyDescriptor;
var get_descriptors = Object.getOwnPropertyDescriptors;
var object_prototype = Object.prototype;
var array_prototype = Array.prototype;
var get_prototype_of = Object.getPrototypeOf;
var is_extensible = Object.isExtensible;
const noop = () => {
};
function run_all(arr) {
  for (var i = 0; i < arr.length; i++) {
    arr[i]();
  }
}
function deferred() {
  var resolve;
  var reject;
  var promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}
function to_array(value, n) {
  if (Array.isArray(value)) {
    return value;
  }
  if (!(Symbol.iterator in value)) {
    return Array.from(value);
  }
  const array = [];
  for (const element of value) {
    array.push(element);
    if (array.length === n) break;
  }
  return array;
}
const DERIVED = 1 << 1;
const EFFECT = 1 << 2;
const RENDER_EFFECT = 1 << 3;
const MANAGED_EFFECT = 1 << 24;
const BLOCK_EFFECT = 1 << 4;
const BRANCH_EFFECT = 1 << 5;
const ROOT_EFFECT = 1 << 6;
const BOUNDARY_EFFECT = 1 << 7;
const CONNECTED = 1 << 9;
const CLEAN = 1 << 10;
const DIRTY = 1 << 11;
const MAYBE_DIRTY = 1 << 12;
const INERT = 1 << 13;
const DESTROYED = 1 << 14;
const REACTION_RAN = 1 << 15;
const DESTROYING = 1 << 25;
const EFFECT_TRANSPARENT = 1 << 16;
const EAGER_EFFECT = 1 << 17;
const HEAD_EFFECT = 1 << 18;
const EFFECT_PRESERVED = 1 << 19;
const USER_EFFECT = 1 << 20;
const EFFECT_OFFSCREEN = 1 << 25;
const WAS_MARKED = 1 << 16;
const REACTION_IS_UPDATING = 1 << 21;
const ASYNC = 1 << 22;
const ERROR_VALUE = 1 << 23;
const STATE_SYMBOL = Symbol("$state");
const LOADING_ATTR_SYMBOL = Symbol("");
const ATTRIBUTES_CACHE = Symbol("attributes");
const CLASS_CACHE = Symbol("class");
const STYLE_CACHE = Symbol("style");
const TEXT_CACHE = Symbol("text");
const FORM_RESET_HANDLER = Symbol("form reset");
const STALE_REACTION = new class StaleReactionError extends Error {
  constructor() {
    super(...arguments);
    __publicField(this, "name", "StaleReactionError");
    __publicField(this, "message", "The reaction that called `getAbortSignal()` was re-run or destroyed");
  }
}();
const IS_XHTML = (
  // We gotta write it like this because after downleveling the pure comment may end up in the wrong location
  !!((_a = globalThis.document) == null ? void 0 : _a.contentType) && /* @__PURE__ */ globalThis.document.contentType.includes("xml")
);
function async_derived_orphan() {
  {
    throw new Error(`https://svelte.dev/e/async_derived_orphan`);
  }
}
function each_key_duplicate(a, b, value) {
  {
    throw new Error(`https://svelte.dev/e/each_key_duplicate`);
  }
}
function effect_in_teardown(rune) {
  {
    throw new Error(`https://svelte.dev/e/effect_in_teardown`);
  }
}
function effect_in_unowned_derived() {
  {
    throw new Error(`https://svelte.dev/e/effect_in_unowned_derived`);
  }
}
function effect_orphan(rune) {
  {
    throw new Error(`https://svelte.dev/e/effect_orphan`);
  }
}
function effect_update_depth_exceeded() {
  {
    throw new Error(`https://svelte.dev/e/effect_update_depth_exceeded`);
  }
}
function state_descriptors_fixed() {
  {
    throw new Error(`https://svelte.dev/e/state_descriptors_fixed`);
  }
}
function state_prototype_fixed() {
  {
    throw new Error(`https://svelte.dev/e/state_prototype_fixed`);
  }
}
function state_unsafe_mutation() {
  {
    throw new Error(`https://svelte.dev/e/state_unsafe_mutation`);
  }
}
function svelte_boundary_reset_onerror() {
  {
    throw new Error(`https://svelte.dev/e/svelte_boundary_reset_onerror`);
  }
}
const EACH_ITEM_REACTIVE = 1;
const EACH_INDEX_REACTIVE = 1 << 1;
const EACH_IS_CONTROLLED = 1 << 2;
const EACH_IS_ANIMATED = 1 << 3;
const EACH_ITEM_IMMUTABLE = 1 << 4;
const TEMPLATE_FRAGMENT = 1;
const TEMPLATE_USE_IMPORT_NODE = 1 << 1;
const UNINITIALIZED = Symbol("uninitialized");
const NAMESPACE_HTML = "http://www.w3.org/1999/xhtml";
function derived_inert() {
  {
    console.warn(`https://svelte.dev/e/derived_inert`);
  }
}
function select_multiple_invalid_value() {
  {
    console.warn(`https://svelte.dev/e/select_multiple_invalid_value`);
  }
}
function svelte_boundary_reset_noop() {
  {
    console.warn(`https://svelte.dev/e/svelte_boundary_reset_noop`);
  }
}
function equals(value) {
  return value === this.v;
}
function safe_not_equal(a, b) {
  return a != a ? b == b : a !== b || a !== null && typeof a === "object" || typeof a === "function";
}
function safe_equals(value) {
  return !safe_not_equal(value, this.v);
}
let tracing_mode_flag = false;
const empty = [];
function snapshot(value, skip_warning = false, no_tojson = false) {
  return clone(value, /* @__PURE__ */ new Map(), "", empty, null, no_tojson);
}
function clone(value, cloned, path, paths, original = null, no_tojson = false) {
  if (typeof value === "object" && value !== null) {
    var unwrapped = cloned.get(value);
    if (unwrapped !== void 0) return unwrapped;
    if (value instanceof Map) return (
      /** @type {Snapshot<T>} */
      new Map(value)
    );
    if (value instanceof Set) return (
      /** @type {Snapshot<T>} */
      new Set(value)
    );
    if (is_array(value)) {
      var copy = (
        /** @type {Snapshot<any>} */
        Array(value.length)
      );
      cloned.set(value, copy);
      if (original !== null) {
        cloned.set(original, copy);
      }
      for (var i = 0; i < value.length; i += 1) {
        var element = value[i];
        if (i in value) {
          copy[i] = clone(element, cloned, path, paths, null, no_tojson);
        }
      }
      return copy;
    }
    if (get_prototype_of(value) === object_prototype) {
      copy = {};
      cloned.set(value, copy);
      if (original !== null) {
        cloned.set(original, copy);
      }
      for (var key of Object.keys(value)) {
        copy[key] = clone(
          // @ts-expect-error
          value[key],
          cloned,
          path,
          paths,
          null,
          no_tojson
        );
      }
      return copy;
    }
    if (value instanceof Date) {
      return (
        /** @type {Snapshot<T>} */
        structuredClone(value)
      );
    }
    if (typeof /** @type {T & { toJSON?: any } } */
    value.toJSON === "function" && !no_tojson) {
      return clone(
        /** @type {T & { toJSON(): any } } */
        value.toJSON(),
        cloned,
        path,
        paths,
        // Associate the instance with the toJSON clone
        value
      );
    }
  }
  if (value instanceof EventTarget) {
    return (
      /** @type {Snapshot<T>} */
      value
    );
  }
  try {
    return (
      /** @type {Snapshot<T>} */
      structuredClone(value)
    );
  } catch (e) {
    return (
      /** @type {Snapshot<T>} */
      value
    );
  }
}
let component_context = null;
function set_component_context(context) {
  component_context = context;
}
function push(props, runes = false, fn) {
  component_context = {
    p: component_context,
    i: false,
    c: null,
    e: null,
    s: props,
    x: null,
    r: (
      /** @type {Effect} */
      active_effect
    ),
    l: null
  };
}
function pop(component) {
  var context = (
    /** @type {ComponentContext} */
    component_context
  );
  var effects = context.e;
  if (effects !== null) {
    context.e = null;
    for (var fn of effects) {
      create_user_effect(fn);
    }
  }
  context.i = true;
  component_context = context.p;
  return (
    /** @type {T} */
    {}
  );
}
function is_runes() {
  return true;
}
let micro_tasks = [];
function run_micro_tasks() {
  var tasks = micro_tasks;
  micro_tasks = [];
  run_all(tasks);
}
function queue_micro_task(fn) {
  if (micro_tasks.length === 0 && true) {
    var tasks = micro_tasks;
    queueMicrotask(() => {
      if (tasks === micro_tasks) run_micro_tasks();
    });
  }
  micro_tasks.push(fn);
}
function handle_error(error) {
  var effect = active_effect;
  if (effect === null) {
    active_reaction.f |= ERROR_VALUE;
    return error;
  }
  if ((effect.f & REACTION_RAN) === 0 && (effect.f & EFFECT) === 0) {
    throw error;
  }
  invoke_error_boundary(error, effect);
}
function invoke_error_boundary(error, effect) {
  if (effect !== null && (effect.f & DESTROYED) !== 0) {
    return;
  }
  while (effect !== null) {
    if ((effect.f & BOUNDARY_EFFECT) !== 0) {
      if ((effect.f & REACTION_RAN) === 0) {
        throw error;
      }
      try {
        effect.b.error(error);
        return;
      } catch (e) {
        error = e;
      }
    }
    effect = effect.parent;
  }
  throw error;
}
const STATUS_MASK = -7169;
function set_signal_status(signal, status) {
  signal.f = signal.f & STATUS_MASK | status;
}
function update_derived_status(derived2) {
  if ((derived2.f & CONNECTED) !== 0 || derived2.deps === null) {
    set_signal_status(derived2, CLEAN);
  } else {
    set_signal_status(derived2, MAYBE_DIRTY);
  }
}
function clear_marked(deps) {
  if (deps === null) return;
  for (const dep of deps) {
    if ((dep.f & DERIVED) === 0 || (dep.f & WAS_MARKED) === 0) {
      continue;
    }
    dep.f ^= WAS_MARKED;
    clear_marked(
      /** @type {Derived} */
      dep.deps
    );
  }
}
function defer_effect(effect, dirty_effects, maybe_dirty_effects) {
  if ((effect.f & DIRTY) !== 0) {
    dirty_effects.add(effect);
  } else if ((effect.f & MAYBE_DIRTY) !== 0) {
    maybe_dirty_effects.add(effect);
  }
  clear_marked(effect.deps);
  set_signal_status(effect, CLEAN);
}
let listening_to_form_reset = false;
function add_form_reset_listener() {
  if (!listening_to_form_reset) {
    listening_to_form_reset = true;
    document.addEventListener(
      "reset",
      (evt) => {
        Promise.resolve().then(() => {
          var _a2;
          if (!evt.defaultPrevented) {
            for (
              const e of
              /**@type {HTMLFormElement} */
              evt.target.elements
            ) {
              (_a2 = e[FORM_RESET_HANDLER]) == null ? void 0 : _a2.call(e);
            }
          }
        });
      },
      // In the capture phase to guarantee we get noticed of it (no possibility of stopPropagation)
      { capture: true }
    );
  }
}
function without_reactive_context(fn) {
  var previous_reaction = active_reaction;
  var previous_effect = active_effect;
  set_active_reaction(null);
  set_active_effect(null);
  try {
    return fn();
  } finally {
    set_active_reaction(previous_reaction);
    set_active_effect(previous_effect);
  }
}
function listen_to_event_and_reset_event(element, event, handler, on_reset = handler) {
  element.addEventListener(event, () => without_reactive_context(handler));
  const prev = (
    /** @type {any} */
    element[FORM_RESET_HANDLER]
  );
  if (prev) {
    element[FORM_RESET_HANDLER] = () => {
      prev();
      on_reset(true);
    };
  } else {
    element[FORM_RESET_HANDLER] = () => on_reset(true);
  }
  add_form_reset_listener();
}
function createSubscriber(start) {
  let subscribers = 0;
  let version = source(0);
  let stop;
  return () => {
    if (effect_tracking()) {
      get(version);
      render_effect(() => {
        if (subscribers === 0) {
          stop = untrack(() => start(() => increment(version)));
        }
        subscribers += 1;
        return () => {
          queue_micro_task(() => {
            subscribers -= 1;
            if (subscribers === 0) {
              stop == null ? void 0 : stop();
              stop = void 0;
              increment(version);
            }
          });
        };
      });
    }
  };
}
var flags = EFFECT_TRANSPARENT | EFFECT_PRESERVED;
function boundary(node, props, children, transform_error) {
  new Boundary(node, props, children, transform_error);
}
class Boundary {
  /**
   * @param {TemplateNode} node
   * @param {BoundaryProps} props
   * @param {((anchor: Node) => void)} children
   * @param {((error: unknown) => unknown) | undefined} [transform_error]
   */
  constructor(node, props, children, transform_error) {
    __privateAdd(this, _Boundary_instances);
    /** @type {Boundary | null} */
    __publicField(this, "parent");
    __publicField(this, "is_pending", false);
    /**
     * API-level transformError transform function. Transforms errors before they reach the `failed` snippet.
     * Inherited from parent boundary, or defaults to identity.
     * @type {(error: unknown) => unknown}
     */
    __publicField(this, "transform_error");
    /** @type {TemplateNode} */
    __privateAdd(this, _anchor);
    /** @type {TemplateNode | null} */
    __privateAdd(this, _hydrate_open, null);
    /** @type {BoundaryProps} */
    __privateAdd(this, _props);
    /** @type {((anchor: Node) => void)} */
    __privateAdd(this, _children);
    /** @type {Effect} */
    __privateAdd(this, _effect);
    /** @type {Effect | null} */
    __privateAdd(this, _main_effect, null);
    /** @type {Effect | null} */
    __privateAdd(this, _pending_effect, null);
    /** @type {Effect | null} */
    __privateAdd(this, _failed_effect, null);
    /** @type {DocumentFragment | null} */
    __privateAdd(this, _offscreen_fragment, null);
    __privateAdd(this, _local_pending_count, 0);
    __privateAdd(this, _pending_count, 0);
    __privateAdd(this, _pending_count_update_queued, false);
    /** @type {Set<Effect>} */
    __privateAdd(this, _dirty_effects, /* @__PURE__ */ new Set());
    /** @type {Set<Effect>} */
    __privateAdd(this, _maybe_dirty_effects, /* @__PURE__ */ new Set());
    /**
     * A source containing the number of pending async deriveds/expressions.
     * Only created if `$effect.pending()` is used inside the boundary,
     * otherwise updating the source results in needless `Batch.ensure()`
     * calls followed by no-op flushes
     * @type {Source<number> | null}
     */
    __privateAdd(this, _effect_pending, null);
    __privateAdd(this, _effect_pending_subscriber, createSubscriber(() => {
      __privateSet(this, _effect_pending, source(__privateGet(this, _local_pending_count)));
      return () => {
        __privateSet(this, _effect_pending, null);
      };
    }));
    var _a2;
    __privateSet(this, _anchor, node);
    __privateSet(this, _props, props);
    __privateSet(this, _children, (anchor) => {
      var effect = (
        /** @type {Effect} */
        active_effect
      );
      effect.b = this;
      effect.f |= BOUNDARY_EFFECT;
      children(anchor);
    });
    this.parent = /** @type {Effect} */
    active_effect.b;
    this.transform_error = transform_error ?? ((_a2 = this.parent) == null ? void 0 : _a2.transform_error) ?? ((e) => e);
    __privateSet(this, _effect, block(() => {
      {
        __privateMethod(this, _Boundary_instances, render_fn).call(this);
      }
    }, flags));
  }
  /**
   * Defer an effect inside a pending boundary until the boundary resolves
   * @param {Effect} effect
   */
  defer_effect(effect) {
    defer_effect(effect, __privateGet(this, _dirty_effects), __privateGet(this, _maybe_dirty_effects));
  }
  /**
   * Returns `false` if the effect exists inside a boundary whose pending snippet is shown
   * @returns {boolean}
   */
  is_rendered() {
    return !this.is_pending && (!this.parent || this.parent.is_rendered());
  }
  has_pending_snippet() {
    return !!__privateGet(this, _props).pending;
  }
  /**
   * Update the source that powers `$effect.pending()` inside this boundary,
   * and controls when the current `pending` snippet (if any) is removed.
   * Do not call from inside the class
   * @param {1 | -1} d
   * @param {Batch} batch
   */
  update_pending_count(d, batch) {
    __privateMethod(this, _Boundary_instances, update_pending_count_fn).call(this, d, batch);
    __privateSet(this, _local_pending_count, __privateGet(this, _local_pending_count) + d);
    if (!__privateGet(this, _effect_pending) || __privateGet(this, _pending_count_update_queued)) return;
    __privateSet(this, _pending_count_update_queued, true);
    queue_micro_task(() => {
      __privateSet(this, _pending_count_update_queued, false);
      if (__privateGet(this, _effect_pending)) {
        internal_set(__privateGet(this, _effect_pending), __privateGet(this, _local_pending_count));
      }
    });
  }
  get_effect_pending() {
    __privateGet(this, _effect_pending_subscriber).call(this);
    return get(
      /** @type {Source<number>} */
      __privateGet(this, _effect_pending)
    );
  }
  /** @param {unknown} error */
  error(error) {
    if (!__privateGet(this, _props).onerror && !__privateGet(this, _props).failed) {
      throw error;
    }
    if (current_batch == null ? void 0 : current_batch.is_fork) {
      if (__privateGet(this, _main_effect)) current_batch.skip_effect(__privateGet(this, _main_effect));
      if (__privateGet(this, _pending_effect)) current_batch.skip_effect(__privateGet(this, _pending_effect));
      if (__privateGet(this, _failed_effect)) current_batch.skip_effect(__privateGet(this, _failed_effect));
      current_batch.oncommit(() => {
        __privateMethod(this, _Boundary_instances, handle_error_fn).call(this, error);
      });
    } else {
      __privateMethod(this, _Boundary_instances, handle_error_fn).call(this, error);
    }
  }
}
_anchor = new WeakMap();
_hydrate_open = new WeakMap();
_props = new WeakMap();
_children = new WeakMap();
_effect = new WeakMap();
_main_effect = new WeakMap();
_pending_effect = new WeakMap();
_failed_effect = new WeakMap();
_offscreen_fragment = new WeakMap();
_local_pending_count = new WeakMap();
_pending_count = new WeakMap();
_pending_count_update_queued = new WeakMap();
_dirty_effects = new WeakMap();
_maybe_dirty_effects = new WeakMap();
_effect_pending = new WeakMap();
_effect_pending_subscriber = new WeakMap();
_Boundary_instances = new WeakSet();
hydrate_resolved_content_fn = function() {
  try {
    __privateSet(this, _main_effect, branch(() => __privateGet(this, _children).call(this, __privateGet(this, _anchor))));
  } catch (error) {
    this.error(error);
  }
};
/**
 * @param {unknown} error The deserialized error from the server's hydration comment
 */
hydrate_failed_content_fn = function(error) {
  const failed = __privateGet(this, _props).failed;
  const { reset, invoke_onerror } = __privateMethod(this, _Boundary_instances, create_reset_fn).call(this, error);
  queue_micro_task(invoke_onerror);
  if (!failed) return;
  __privateSet(this, _failed_effect, branch(() => {
    failed(
      __privateGet(this, _anchor),
      () => error,
      () => reset
    );
  }));
};
/**
 * Creates the `reset` function for a failed boundary, along with a function
 * that invokes `onerror` with it (if provided)
 * @param {unknown} error
 * @returns {{ reset: () => void, invoke_onerror: () => void }}
 */
create_reset_fn = function(error) {
  var did_reset = false;
  var calling_on_error = false;
  const reset = () => {
    if (did_reset) {
      svelte_boundary_reset_noop();
      return;
    }
    did_reset = true;
    if (calling_on_error) {
      svelte_boundary_reset_onerror();
    }
    if (__privateGet(this, _failed_effect) !== null) {
      pause_effect(__privateGet(this, _failed_effect), () => {
        __privateSet(this, _failed_effect, null);
      });
    }
    __privateMethod(this, _Boundary_instances, run_fn).call(this, () => {
      __privateMethod(this, _Boundary_instances, render_fn).call(this);
    });
  };
  const invoke_onerror = () => {
    var _a2, _b2;
    try {
      calling_on_error = true;
      (_b2 = (_a2 = __privateGet(this, _props)).onerror) == null ? void 0 : _b2.call(_a2, error, reset);
      calling_on_error = false;
    } catch (err) {
      invoke_error_boundary(err, __privateGet(this, _effect) && __privateGet(this, _effect).parent);
    }
  };
  return { reset, invoke_onerror };
};
hydrate_pending_content_fn = function() {
  const pending = __privateGet(this, _props).pending;
  if (!pending) return;
  this.is_pending = true;
  __privateSet(this, _pending_effect, branch(() => pending(__privateGet(this, _anchor))));
  queue_micro_task(() => {
    var fragment = __privateSet(this, _offscreen_fragment, document.createDocumentFragment());
    var anchor = create_text();
    fragment.append(anchor);
    __privateSet(this, _main_effect, __privateMethod(this, _Boundary_instances, run_fn).call(this, () => {
      return branch(() => __privateGet(this, _children).call(this, anchor));
    }));
    if (__privateGet(this, _pending_count) === 0) {
      __privateGet(this, _anchor).before(fragment);
      __privateSet(this, _offscreen_fragment, null);
      pause_effect(
        /** @type {Effect} */
        __privateGet(this, _pending_effect),
        () => {
          __privateSet(this, _pending_effect, null);
        }
      );
      __privateMethod(this, _Boundary_instances, resolve_fn).call(
        this,
        /** @type {Batch} */
        current_batch
      );
    }
  });
};
render_fn = function() {
  try {
    this.is_pending = this.has_pending_snippet();
    __privateSet(this, _pending_count, 0);
    __privateSet(this, _local_pending_count, 0);
    __privateSet(this, _main_effect, branch(() => {
      __privateGet(this, _children).call(this, __privateGet(this, _anchor));
    }));
    if (__privateGet(this, _pending_count) > 0) {
      var fragment = __privateSet(this, _offscreen_fragment, document.createDocumentFragment());
      move_effect(__privateGet(this, _main_effect), fragment);
      const pending = (
        /** @type {(anchor: Node) => void} */
        __privateGet(this, _props).pending
      );
      __privateSet(this, _pending_effect, branch(() => pending(__privateGet(this, _anchor))));
    } else {
      __privateMethod(this, _Boundary_instances, resolve_fn).call(
        this,
        /** @type {Batch} */
        current_batch
      );
    }
  } catch (error) {
    this.error(error);
  }
};
/**
 * @param {Batch} batch
 */
resolve_fn = function(batch) {
  this.is_pending = false;
  batch.transfer_effects(__privateGet(this, _dirty_effects), __privateGet(this, _maybe_dirty_effects));
};
/**
 * @template T
 * @param {() => T} fn
 */
run_fn = function(fn) {
  var previous_effect = active_effect;
  var previous_reaction = active_reaction;
  var previous_ctx = component_context;
  set_active_effect(__privateGet(this, _effect));
  set_active_reaction(__privateGet(this, _effect));
  set_component_context(__privateGet(this, _effect).ctx);
  try {
    Batch.ensure();
    return fn();
  } catch (e) {
    handle_error(e);
    return null;
  } finally {
    set_active_effect(previous_effect);
    set_active_reaction(previous_reaction);
    set_component_context(previous_ctx);
  }
};
/**
 * Updates the pending count associated with the currently visible pending snippet,
 * if any, such that we can replace the snippet with content once work is done
 * @param {1 | -1} d
 * @param {Batch} batch
 */
update_pending_count_fn = function(d, batch) {
  var _a2;
  if (!this.has_pending_snippet()) {
    if (this.parent) {
      __privateMethod(_a2 = this.parent, _Boundary_instances, update_pending_count_fn).call(_a2, d, batch);
    }
    return;
  }
  __privateSet(this, _pending_count, __privateGet(this, _pending_count) + d);
  if (__privateGet(this, _pending_count) === 0) {
    __privateMethod(this, _Boundary_instances, resolve_fn).call(this, batch);
    if (__privateGet(this, _pending_effect)) {
      pause_effect(__privateGet(this, _pending_effect), () => {
        __privateSet(this, _pending_effect, null);
      });
    }
    if (__privateGet(this, _offscreen_fragment)) {
      __privateGet(this, _anchor).before(__privateGet(this, _offscreen_fragment));
      __privateSet(this, _offscreen_fragment, null);
    }
  }
};
/**
 * @param {unknown} error
 */
handle_error_fn = function(error) {
  if (__privateGet(this, _main_effect)) {
    destroy_effect(__privateGet(this, _main_effect));
    __privateSet(this, _main_effect, null);
  }
  if (__privateGet(this, _pending_effect)) {
    destroy_effect(__privateGet(this, _pending_effect));
    __privateSet(this, _pending_effect, null);
  }
  if (__privateGet(this, _failed_effect)) {
    destroy_effect(__privateGet(this, _failed_effect));
    __privateSet(this, _failed_effect, null);
  }
  let failed = __privateGet(this, _props).failed;
  const handle_error_result = (transformed_error) => {
    const { reset, invoke_onerror } = __privateMethod(this, _Boundary_instances, create_reset_fn).call(this, transformed_error);
    invoke_onerror();
    if (failed) {
      __privateSet(this, _failed_effect, __privateMethod(this, _Boundary_instances, run_fn).call(this, () => {
        try {
          return branch(() => {
            var effect = (
              /** @type {Effect} */
              active_effect
            );
            effect.b = this;
            effect.f |= BOUNDARY_EFFECT;
            failed(
              __privateGet(this, _anchor),
              () => transformed_error,
              () => reset
            );
          });
        } catch (error2) {
          invoke_error_boundary(
            error2,
            /** @type {Effect} */
            __privateGet(this, _effect).parent
          );
          return null;
        }
      }));
    }
  };
  queue_micro_task(() => {
    var result;
    try {
      result = this.transform_error(error);
    } catch (e) {
      invoke_error_boundary(e, __privateGet(this, _effect) && __privateGet(this, _effect).parent);
      return;
    }
    if (result !== null && typeof result === "object" && typeof /** @type {any} */
    result.then === "function") {
      result.then(
        handle_error_result,
        /** @param {unknown} e */
        (e) => invoke_error_boundary(e, __privateGet(this, _effect) && __privateGet(this, _effect).parent)
      );
    } else {
      handle_error_result(result);
    }
  });
};
function flatten(blockers, sync, async, fn) {
  const d = derived;
  var pending = blockers.filter((b) => !b.settled);
  var deriveds = sync.map(d);
  if (async.length === 0 && pending.length === 0) {
    fn(deriveds);
    return;
  }
  var parent = (
    /** @type {Effect} */
    active_effect
  );
  var restore = capture();
  var blocker_promise = pending.length === 1 ? pending[0].promise : pending.length > 1 ? Promise.all(pending.map((b) => b.promise)) : null;
  function finish(async2) {
    if ((parent.f & DESTROYED) !== 0) {
      return;
    }
    restore();
    try {
      fn([...deriveds, ...async2]);
    } catch (error) {
      invoke_error_boundary(error, parent);
    }
    unset_context();
  }
  var decrement_pending = increment_pending();
  if (async.length === 0) {
    blocker_promise.then(() => finish([])).finally(decrement_pending);
    return;
  }
  function run() {
    Promise.all(async.map((expression) => /* @__PURE__ */ async_derived(expression))).then(finish).catch((error) => invoke_error_boundary(error, parent)).finally(decrement_pending);
  }
  if (blocker_promise) {
    blocker_promise.then(() => {
      restore();
      run();
      unset_context();
    });
  } else {
    run();
  }
}
function capture() {
  var previous_effect = (
    /** @type {Effect} */
    active_effect
  );
  var previous_reaction = active_reaction;
  var previous_component_context = component_context;
  var previous_batch2 = (
    /** @type {Batch} */
    current_batch
  );
  return function restore(activate_batch = true) {
    set_active_effect(previous_effect);
    set_active_reaction(previous_reaction);
    set_component_context(previous_component_context);
    if (activate_batch && (previous_effect.f & DESTROYED) === 0) {
      previous_batch2 == null ? void 0 : previous_batch2.activate();
      previous_batch2 == null ? void 0 : previous_batch2.apply();
    }
  };
}
function unset_context(deactivate_batch = true) {
  set_active_effect(null);
  set_active_reaction(null);
  set_component_context(null);
  if (deactivate_batch) current_batch == null ? void 0 : current_batch.deactivate();
}
function increment_pending() {
  var effect = (
    /** @type {Effect} */
    active_effect
  );
  var boundary2 = effect.b;
  var batch = (
    /** @type {Batch} */
    current_batch
  );
  var blocking = !!(boundary2 == null ? void 0 : boundary2.is_rendered());
  boundary2 == null ? void 0 : boundary2.update_pending_count(1, batch);
  batch.increment(blocking, effect);
  return () => {
    boundary2 == null ? void 0 : boundary2.update_pending_count(-1, batch);
    batch.decrement(blocking, effect);
  };
}
// @__NO_SIDE_EFFECTS__
function derived(fn) {
  var flags2 = DERIVED | DIRTY;
  if (active_effect !== null) {
    active_effect.f |= EFFECT_PRESERVED;
  }
  const signal = {
    ctx: component_context,
    deps: null,
    effects: null,
    equals,
    f: flags2,
    fn,
    reactions: null,
    rv: 0,
    v: (
      /** @type {V} */
      UNINITIALIZED
    ),
    wv: 0,
    parent: active_effect,
    ac: null
  };
  return signal;
}
const OBSOLETE = Symbol("obsolete");
// @__NO_SIDE_EFFECTS__
function async_derived(fn, label, location) {
  let parent = (
    /** @type {Effect | null} */
    active_effect
  );
  if (parent === null) {
    async_derived_orphan();
  }
  var promise = (
    /** @type {Promise<V>} */
    /** @type {unknown} */
    void 0
  );
  var signal = source(
    /** @type {V} */
    UNINITIALIZED
  );
  var should_suspend = !active_reaction;
  var deferreds = /* @__PURE__ */ new Set();
  async_effect(() => {
    var _a2, _b2;
    var effect = (
      /** @type {Effect} */
      active_effect
    );
    var d = deferred();
    promise = d.promise;
    try {
      Promise.resolve(fn()).then(d.resolve, (e) => {
        if (e !== STALE_REACTION) d.reject(e);
      }).finally(unset_context);
    } catch (error) {
      d.reject(error);
      unset_context();
    }
    var batch = (
      /** @type {Batch} */
      current_batch
    );
    if (should_suspend) {
      if ((effect.f & REACTION_RAN) !== 0) {
        var decrement_pending = increment_pending();
      }
      if (
        // boundary can be null if the async derived is inside an $effect.root not connected to the component render tree
        (_a2 = parent.b) == null ? void 0 : _a2.is_rendered()
      ) {
        (_b2 = batch.async_deriveds.get(effect)) == null ? void 0 : _b2.reject(OBSOLETE);
      } else {
        for (const d2 of deferreds.values()) {
          d2.reject(OBSOLETE);
        }
      }
      deferreds.add(d);
      batch.async_deriveds.set(effect, d);
    }
    const handler = (value, error = void 0) => {
      decrement_pending == null ? void 0 : decrement_pending();
      deferreds.delete(d);
      if (error === OBSOLETE) return;
      batch.activate();
      if (error) {
        signal.f |= ERROR_VALUE;
        internal_set(signal, error);
      } else {
        if ((signal.f & ERROR_VALUE) !== 0) {
          signal.f ^= ERROR_VALUE;
        }
        internal_set(signal, value);
      }
      batch.deactivate();
    };
    d.promise.then(handler, (e) => handler(null, e || "unknown"));
  });
  teardown(() => {
    for (const d of deferreds) {
      d.reject(OBSOLETE);
    }
  });
  return new Promise((fulfil) => {
    function next(p) {
      function go() {
        if (p === promise) {
          fulfil(signal);
        } else {
          next(promise);
        }
      }
      p.then(go, go);
    }
    next(promise);
  });
}
// @__NO_SIDE_EFFECTS__
function user_derived(fn) {
  const d = /* @__PURE__ */ derived(fn);
  push_reaction_value(d);
  return d;
}
// @__NO_SIDE_EFFECTS__
function derived_safe_equal(fn) {
  const signal = /* @__PURE__ */ derived(fn);
  signal.equals = safe_equals;
  return signal;
}
function destroy_derived_effects(derived2) {
  var effects = derived2.effects;
  if (effects !== null) {
    derived2.effects = null;
    for (var i = 0; i < effects.length; i += 1) {
      destroy_effect(
        /** @type {Effect} */
        effects[i]
      );
    }
  }
}
function execute_derived(derived2) {
  var value;
  var prev_active_effect = active_effect;
  var parent = derived2.parent;
  if (!is_destroying_effect && parent !== null && derived2.v !== UNINITIALIZED && // if it was never evaluated before, it's guaranteed to fail downstream, so we try to execute instead
  (parent.f & (DESTROYED | INERT)) !== 0) {
    derived_inert();
    return derived2.v;
  }
  set_active_effect(parent);
  {
    try {
      derived2.f &= ~WAS_MARKED;
      destroy_derived_effects(derived2);
      value = update_reaction(derived2);
    } finally {
      set_active_effect(prev_active_effect);
    }
  }
  return value;
}
function update_derived(derived2) {
  var value = execute_derived(derived2);
  if (!derived2.equals(value)) {
    derived2.wv = increment_write_version();
    if (!(current_batch == null ? void 0 : current_batch.is_fork) || derived2.deps === null) {
      if (current_batch !== null) {
        current_batch.capture(derived2, value, true);
        previous_batch == null ? void 0 : previous_batch.capture(derived2, value, true);
      } else {
        derived2.v = value;
      }
      if (derived2.deps === null) {
        set_signal_status(derived2, CLEAN);
        return;
      }
    }
  }
  if (is_destroying_effect) {
    return;
  }
  if (batch_values !== null) {
    if (effect_tracking() || (current_batch == null ? void 0 : current_batch.is_fork)) {
      batch_values.set(derived2, value);
    }
  } else {
    update_derived_status(derived2);
  }
}
function freeze_derived_effects(derived2) {
  var _a2;
  if (derived2.effects === null) return;
  for (const e of derived2.effects) {
    if (e.teardown || e.ac) {
      (_a2 = e.teardown) == null ? void 0 : _a2.call(e);
      if (e.ac !== null) {
        without_reactive_context(() => {
          e.ac.abort(STALE_REACTION);
          e.ac = null;
        });
      }
      if (e.fn !== null) e.teardown = noop;
      remove_reactions(e, 0);
      destroy_effect_children(e);
    }
  }
}
function unfreeze_derived_effects(derived2) {
  if (derived2.effects === null) return;
  for (const e of derived2.effects) {
    if (e.teardown && e.fn !== null) {
      update_effect(e);
    }
  }
}
let first_batch = null;
let last_batch = null;
let current_batch = null;
let previous_batch = null;
let batch_values = null;
let last_scheduled_effect = null;
let is_processing = false;
let collected_effects = null;
let legacy_updates = null;
var flush_count = 0;
var source_stacks = /* @__PURE__ */ new Set();
let uid = 1;
const _Batch = class _Batch {
  constructor() {
    __privateAdd(this, _Batch_instances);
    __publicField(this, "id", uid++);
    /** True as soon as `#process` was called */
    __privateAdd(this, _started, false);
    __publicField(this, "linked", true);
    /** @type {Batch | null} */
    __privateAdd(this, _prev, null);
    /** @type {Batch | null} */
    __privateAdd(this, _next, null);
    /** @type {Map<Effect, ReturnType<typeof deferred<any>>>} */
    __publicField(this, "async_deriveds", /* @__PURE__ */ new Map());
    /**
     * The current values of any signals that are updated in this batch.
     * Tuple format: [value, is_derived] (note: is_derived is false for deriveds, too, if they were overridden via assignment)
     * They keys of this map are identical to `this.#previous`
     * @type {Map<Value, [any, boolean]>}
     */
    __publicField(this, "current", /* @__PURE__ */ new Map());
    /**
     * The values of any signals (sources and deriveds) that are updated in this batch _before_ those updates took place.
     * They keys of this map are identical to `this.#current`
     * @type {Map<Value, any>}
     */
    __publicField(this, "previous", /* @__PURE__ */ new Map());
    /**
     * When the batch is committed (and the DOM is updated), we need to remove old branches
     * and append new ones by calling the functions added inside (if/each/key/etc) blocks
     * @type {Set<(batch: Batch) => void>}
     */
    __privateAdd(this, _commit_callbacks, /* @__PURE__ */ new Set());
    /**
     * If a fork is discarded, we need to destroy any effects that are no longer needed
     * @type {Set<(batch: Batch) => void>}
     */
    __privateAdd(this, _discard_callbacks, /* @__PURE__ */ new Set());
    /**
     * The number of async effects that are currently in flight
     */
    __privateAdd(this, _pending, 0);
    /**
     * Async effects that are currently in flight, _not_ inside a pending boundary
     * @type {Map<Effect, number>}
     */
    __privateAdd(this, _blocking_pending, /* @__PURE__ */ new Map());
    /**
     * A deferred that resolves when the batch is committed, used with `settled()`
     * TODO replace with Promise.withResolvers once supported widely enough
     * @type {{ promise: Promise<void>, resolve: (value?: any) => void, reject: (reason: unknown) => void } | null}
     */
    __privateAdd(this, _deferred, null);
    /**
     * The root effects that need to be flushed
     * @type {Effect[]}
     */
    __privateAdd(this, _roots, []);
    /**
     * Effects created while this batch was active.
     * @type {Effect[]}
     */
    __privateAdd(this, _new_effects, []);
    /**
     * Deferred effects (which run after async work has completed) that are DIRTY
     * @type {Set<Effect>}
     */
    __privateAdd(this, _dirty_effects2, /* @__PURE__ */ new Set());
    /**
     * Deferred effects that are MAYBE_DIRTY
     * @type {Set<Effect>}
     */
    __privateAdd(this, _maybe_dirty_effects2, /* @__PURE__ */ new Set());
    /**
     * A map of branches that still exist, but will be destroyed when this batch
     * is committed — we skip over these during `process`.
     * The value contains child effects that were dirty/maybe_dirty before being reset,
     * so they can be rescheduled if the branch survives.
     * @type {Map<Effect, { d: Effect[], m: Effect[] }>}
     */
    __privateAdd(this, _skipped_branches, /* @__PURE__ */ new Map());
    /**
     * Inverse of #skipped_branches which we need to tell prior batches to unskip them when committing
     * @type {Set<Effect>}
     */
    __privateAdd(this, _unskipped_branches, /* @__PURE__ */ new Set());
    __publicField(this, "is_fork", false);
    __privateAdd(this, _decrement_queued, false);
    if (last_batch === null) {
      first_batch = last_batch = this;
    } else {
      __privateSet(last_batch, _next, this);
      __privateSet(this, _prev, last_batch);
    }
    last_batch = this;
  }
  /**
   * Add an effect to the #skipped_branches map and reset its children
   * @param {Effect} effect
   */
  skip_effect(effect) {
    if (!__privateGet(this, _skipped_branches).has(effect)) {
      __privateGet(this, _skipped_branches).set(effect, { d: [], m: [] });
    }
    __privateGet(this, _unskipped_branches).delete(effect);
  }
  /**
   * Remove an effect from the #skipped_branches map and reschedule
   * any tracked dirty/maybe_dirty child effects
   * @param {Effect} effect
   * @param {(e: Effect) => void} callback
   */
  unskip_effect(effect, callback = (e) => this.schedule(e)) {
    var tracked = __privateGet(this, _skipped_branches).get(effect);
    if (tracked) {
      __privateGet(this, _skipped_branches).delete(effect);
      for (var e of tracked.d) {
        set_signal_status(e, DIRTY);
        callback(e);
      }
      for (e of tracked.m) {
        set_signal_status(e, MAYBE_DIRTY);
        callback(e);
      }
    }
    __privateGet(this, _unskipped_branches).add(effect);
  }
  /**
   * Associate a change to a given source with the current
   * batch, noting its previous and current values
   * @param {Value} source
   * @param {any} value
   * @param {boolean} [is_derived]
   */
  capture(source2, value, is_derived = false) {
    if (source2.v !== UNINITIALIZED && !this.previous.has(source2)) {
      this.previous.set(source2, source2.v);
    }
    if ((source2.f & ERROR_VALUE) === 0) {
      this.current.set(source2, [value, is_derived]);
      batch_values == null ? void 0 : batch_values.set(source2, value);
    }
    if (!this.is_fork) {
      source2.v = value;
    }
  }
  activate() {
    current_batch = this;
  }
  deactivate() {
    current_batch = null;
    batch_values = null;
  }
  flush() {
    try {
      if (DEV) ;
      is_processing = true;
      current_batch = this;
      __privateMethod(this, _Batch_instances, process_fn).call(this);
    } finally {
      flush_count = 0;
      last_scheduled_effect = null;
      collected_effects = null;
      legacy_updates = null;
      is_processing = false;
      current_batch = null;
      batch_values = null;
      old_values.clear();
    }
  }
  discard() {
    var _a2;
    for (const fn of __privateGet(this, _discard_callbacks)) fn(this);
    __privateGet(this, _discard_callbacks).clear();
    for (const deferred2 of this.async_deriveds.values()) {
      deferred2.reject(OBSOLETE);
    }
    __privateMethod(this, _Batch_instances, unlink_fn).call(this);
    (_a2 = __privateGet(this, _deferred)) == null ? void 0 : _a2.resolve();
  }
  /**
   * @param {Effect} effect
   */
  register_created_effect(effect) {
    __privateGet(this, _new_effects).push(effect);
  }
  /**
   * @param {boolean} blocking
   * @param {Effect} effect
   */
  increment(blocking, effect) {
    __privateSet(this, _pending, __privateGet(this, _pending) + 1);
    if (blocking) {
      let blocking_pending_count = __privateGet(this, _blocking_pending).get(effect) ?? 0;
      __privateGet(this, _blocking_pending).set(effect, blocking_pending_count + 1);
    }
  }
  /**
   * @param {boolean} blocking
   * @param {Effect} effect
   */
  decrement(blocking, effect) {
    __privateSet(this, _pending, __privateGet(this, _pending) - 1);
    if (blocking) {
      let blocking_pending_count = __privateGet(this, _blocking_pending).get(effect) ?? 0;
      if (blocking_pending_count === 1) {
        __privateGet(this, _blocking_pending).delete(effect);
      } else {
        __privateGet(this, _blocking_pending).set(effect, blocking_pending_count - 1);
      }
    }
    if (__privateGet(this, _decrement_queued)) return;
    __privateSet(this, _decrement_queued, true);
    queue_micro_task(() => {
      __privateSet(this, _decrement_queued, false);
      if (this.linked) {
        this.flush();
      }
    });
  }
  /**
   * @param {Set<Effect>} dirty_effects
   * @param {Set<Effect>} maybe_dirty_effects
   */
  transfer_effects(dirty_effects, maybe_dirty_effects) {
    for (const e of dirty_effects) {
      __privateGet(this, _dirty_effects2).add(e);
    }
    for (const e of maybe_dirty_effects) {
      __privateGet(this, _maybe_dirty_effects2).add(e);
    }
    dirty_effects.clear();
    maybe_dirty_effects.clear();
  }
  /** @param {(batch: Batch) => void} fn */
  oncommit(fn) {
    __privateGet(this, _commit_callbacks).add(fn);
  }
  /** @param {(batch: Batch) => void} fn */
  ondiscard(fn) {
    __privateGet(this, _discard_callbacks).add(fn);
  }
  settled() {
    return (__privateGet(this, _deferred) ?? __privateSet(this, _deferred, deferred())).promise;
  }
  static ensure() {
    if (current_batch === null) {
      const batch = current_batch = new _Batch();
      if (!is_processing && true) {
        queue_micro_task(() => {
          if (!__privateGet(batch, _started)) {
            batch.flush();
          }
        });
      }
    }
    return current_batch;
  }
  apply() {
    {
      batch_values = null;
      return;
    }
  }
  /**
   *
   * @param {Effect} effect
   */
  schedule(effect) {
    var _a2;
    last_scheduled_effect = effect;
    if (((_a2 = effect.b) == null ? void 0 : _a2.is_pending) && (effect.f & (EFFECT | RENDER_EFFECT | MANAGED_EFFECT)) !== 0 && (effect.f & REACTION_RAN) === 0) {
      effect.b.defer_effect(effect);
      return;
    }
    var e = effect;
    while (e.parent !== null) {
      e = e.parent;
      var flags2 = e.f;
      if (collected_effects !== null && e === active_effect) {
        if ((active_reaction === null || (active_reaction.f & DERIVED) === 0) && true) {
          return;
        }
      }
      if ((flags2 & (ROOT_EFFECT | BRANCH_EFFECT)) !== 0) {
        if ((flags2 & CLEAN) === 0) {
          return;
        }
        e.f ^= CLEAN;
      }
    }
    __privateGet(this, _roots).push(e);
  }
};
_started = new WeakMap();
_prev = new WeakMap();
_next = new WeakMap();
_commit_callbacks = new WeakMap();
_discard_callbacks = new WeakMap();
_pending = new WeakMap();
_blocking_pending = new WeakMap();
_deferred = new WeakMap();
_roots = new WeakMap();
_new_effects = new WeakMap();
_dirty_effects2 = new WeakMap();
_maybe_dirty_effects2 = new WeakMap();
_skipped_branches = new WeakMap();
_unskipped_branches = new WeakMap();
_decrement_queued = new WeakMap();
_Batch_instances = new WeakSet();
is_deferred_fn = function() {
  if (this.is_fork) return true;
  for (const effect of __privateGet(this, _blocking_pending).keys()) {
    var e = effect;
    var skipped = false;
    while (e.parent !== null) {
      if (__privateGet(this, _skipped_branches).has(e)) {
        skipped = true;
        break;
      }
      e = e.parent;
    }
    if (!skipped) {
      return true;
    }
  }
  return false;
};
process_fn = function() {
  var _a2, _b2, _c2, _d;
  __privateSet(this, _started, true);
  if (flush_count++ > 1e3) {
    __privateMethod(this, _Batch_instances, unlink_fn).call(this);
    infinite_loop_guard();
  }
  for (const e of __privateGet(this, _dirty_effects2)) {
    __privateGet(this, _maybe_dirty_effects2).delete(e);
    set_signal_status(e, DIRTY);
    this.schedule(e);
  }
  for (const e of __privateGet(this, _maybe_dirty_effects2)) {
    set_signal_status(e, MAYBE_DIRTY);
    this.schedule(e);
  }
  const roots = __privateGet(this, _roots);
  __privateSet(this, _roots, []);
  this.apply();
  var effects = collected_effects = [];
  var render_effects = [];
  var updates = legacy_updates = [];
  for (const root2 of roots) {
    try {
      __privateMethod(this, _Batch_instances, traverse_fn).call(this, root2, effects, render_effects);
    } catch (e) {
      reset_all(root2);
      if (!__privateMethod(this, _Batch_instances, is_deferred_fn).call(this)) this.discard();
      throw e;
    }
  }
  current_batch = null;
  if (updates.length > 0) {
    var batch = _Batch.ensure();
    for (const e of updates) {
      batch.schedule(e);
    }
  }
  collected_effects = null;
  legacy_updates = null;
  if (__privateMethod(this, _Batch_instances, is_deferred_fn).call(this)) {
    __privateMethod(this, _Batch_instances, defer_effects_fn).call(this, render_effects);
    __privateMethod(this, _Batch_instances, defer_effects_fn).call(this, effects);
    for (const [e, t] of __privateGet(this, _skipped_branches)) {
      reset_branch(e, t);
    }
    if (updates.length > 0) {
      /** @type {unknown} */
      __privateMethod(_a2 = current_batch, _Batch_instances, process_fn).call(_a2);
    }
    return;
  }
  const earlier_batch = __privateMethod(this, _Batch_instances, find_earlier_batch_fn).call(this);
  if (earlier_batch) {
    __privateMethod(this, _Batch_instances, defer_effects_fn).call(this, render_effects);
    __privateMethod(this, _Batch_instances, defer_effects_fn).call(this, effects);
    __privateMethod(_b2 = earlier_batch, _Batch_instances, merge_fn).call(_b2, this);
    return;
  }
  __privateGet(this, _dirty_effects2).clear();
  __privateGet(this, _maybe_dirty_effects2).clear();
  for (const fn of __privateGet(this, _commit_callbacks)) fn(this);
  __privateGet(this, _commit_callbacks).clear();
  previous_batch = this;
  flush_queued_effects(render_effects);
  flush_queued_effects(effects);
  previous_batch = null;
  (_c2 = __privateGet(this, _deferred)) == null ? void 0 : _c2.resolve();
  var next_batch = (
    /** @type {Batch | null} */
    /** @type {unknown} */
    current_batch
  );
  if (__privateGet(this, _pending) === 0 && (__privateGet(this, _roots).length === 0 || next_batch !== null)) {
    __privateMethod(this, _Batch_instances, unlink_fn).call(this);
  }
  if (__privateGet(this, _roots).length > 0) {
    if (next_batch !== null) {
      const batch2 = next_batch;
      __privateGet(batch2, _roots).push(...__privateGet(this, _roots).filter((r2) => !__privateGet(batch2, _roots).includes(r2)));
    } else {
      next_batch = this;
    }
  }
  if (next_batch !== null) {
    __privateMethod(_d = next_batch, _Batch_instances, process_fn).call(_d);
  }
};
/**
 * Traverse the effect tree, executing effects or stashing
 * them for later execution as appropriate
 * @param {Effect} root
 * @param {Effect[]} effects
 * @param {Effect[]} render_effects
 */
traverse_fn = function(root2, effects, render_effects) {
  root2.f ^= CLEAN;
  var effect = root2.first;
  while (effect !== null) {
    var flags2 = effect.f;
    var is_branch = (flags2 & (BRANCH_EFFECT | ROOT_EFFECT)) !== 0;
    var is_skippable_branch = is_branch && (flags2 & CLEAN) !== 0;
    var skip = is_skippable_branch || (flags2 & INERT) !== 0 || __privateGet(this, _skipped_branches).has(effect);
    if (!skip && effect.fn !== null) {
      if (is_branch) {
        effect.f ^= CLEAN;
      } else if ((flags2 & EFFECT) !== 0) {
        effects.push(effect);
      } else if (is_dirty(effect)) {
        if ((flags2 & BLOCK_EFFECT) !== 0) __privateGet(this, _maybe_dirty_effects2).add(effect);
        update_effect(effect);
      }
      var child2 = effect.first;
      if (child2 !== null) {
        effect = child2;
        continue;
      }
    }
    while (effect !== null) {
      var next = effect.next;
      if (next !== null) {
        effect = next;
        break;
      }
      effect = effect.parent;
    }
  }
};
find_earlier_batch_fn = function() {
  var batch = __privateGet(this, _prev);
  while (batch !== null) {
    if (!batch.is_fork) {
      for (const [value, [, is_derived]] of this.current) {
        if (batch.current.has(value) && !is_derived) {
          return batch;
        }
      }
    }
    batch = __privateGet(batch, _prev);
  }
  return null;
};
/**
 * @param {Batch} batch
 */
merge_fn = function(batch) {
  var _a2;
  for (const [source2, value] of batch.current) {
    if (!this.previous.has(source2) && batch.previous.has(source2)) {
      this.previous.set(source2, batch.previous.get(source2));
    }
    this.current.set(source2, value);
  }
  for (const [effect, deferred2] of batch.async_deriveds) {
    const d = this.async_deriveds.get(effect);
    if (d) deferred2.promise.then(d.resolve).catch(d.reject);
  }
  batch.async_deriveds.clear();
  this.transfer_effects(__privateGet(batch, _dirty_effects2), __privateGet(batch, _maybe_dirty_effects2));
  const mark = (value) => {
    var reactions = value.reactions;
    if (reactions === null) return;
    if ((value.f & DERIVED) !== 0 && (value.f & (DIRTY | MAYBE_DIRTY)) === 0) {
      return;
    }
    for (const reaction of reactions) {
      var flags2 = reaction.f;
      if ((flags2 & DERIVED) !== 0) {
        mark(
          /** @type {Derived} */
          reaction
        );
      } else {
        var effect = (
          /** @type {Effect} */
          reaction
        );
        if (flags2 & (ASYNC | BLOCK_EFFECT) && !this.async_deriveds.has(effect)) {
          __privateGet(this, _maybe_dirty_effects2).delete(effect);
          set_signal_status(effect, DIRTY);
          this.schedule(effect);
        }
      }
    }
  };
  for (const source2 of this.current.keys()) {
    mark(source2);
  }
  this.oncommit(() => batch.discard());
  __privateMethod(_a2 = batch, _Batch_instances, unlink_fn).call(_a2);
  current_batch = this;
  __privateMethod(this, _Batch_instances, process_fn).call(this);
};
/**
 * @param {Effect[]} effects
 */
defer_effects_fn = function(effects) {
  for (var i = 0; i < effects.length; i += 1) {
    defer_effect(effects[i], __privateGet(this, _dirty_effects2), __privateGet(this, _maybe_dirty_effects2));
  }
};
commit_fn = function() {
  var _a2;
  for (let batch = first_batch; batch !== null; batch = __privateGet(batch, _next)) {
    var is_earlier = batch.id < this.id;
    var sources = [];
    for (const [source3, [value, is_derived]] of this.current) {
      if (batch.current.has(source3)) {
        var batch_value = (
          /** @type {[any, boolean]} */
          batch.current.get(source3)[0]
        );
        if (is_earlier && value !== batch_value) {
          batch.current.set(source3, [value, is_derived]);
        } else {
          continue;
        }
      }
      sources.push(source3);
    }
    if (is_earlier) {
      for (const [effect, deferred2] of this.async_deriveds) {
        const d = batch.async_deriveds.get(effect);
        if (d) deferred2.promise.then(d.resolve).catch(d.reject);
      }
    }
    var current = [...batch.current.keys()].filter(
      (source3) => !/** @type {[any, boolean]} */
      batch.current.get(source3)[1]
    );
    if (!__privateGet(batch, _started) || current.length === 0) continue;
    var others = current.filter((source3) => !this.current.has(source3));
    if (others.length === 0) {
      if (is_earlier) {
        batch.discard();
      }
    } else if (sources.length > 0) {
      if (is_earlier) {
        for (const unskipped of __privateGet(this, _unskipped_branches)) {
          batch.unskip_effect(unskipped, (e) => {
            var _a3;
            if ((e.f & (BLOCK_EFFECT | ASYNC)) !== 0) {
              batch.schedule(e);
            } else {
              __privateMethod(_a3 = batch, _Batch_instances, defer_effects_fn).call(_a3, [e]);
            }
          });
        }
      }
      batch.activate();
      var marked = /* @__PURE__ */ new Set();
      var checked = /* @__PURE__ */ new Map();
      for (var source2 of sources) {
        mark_effects(source2, others, marked, checked);
      }
      checked = /* @__PURE__ */ new Map();
      var current_unequal = [...batch.current].filter(([c, v1]) => {
        const v2 = this.current.get(c);
        if (!v2) return true;
        return v2[0] !== v1[0] || v2[1] !== v1[1];
      }).map(([c]) => c);
      if (current_unequal.length > 0) {
        for (const effect of __privateGet(this, _new_effects)) {
          if ((effect.f & (DESTROYED | INERT | EAGER_EFFECT)) === 0 && depends_on(effect, current_unequal, checked)) {
            if ((effect.f & (ASYNC | BLOCK_EFFECT)) !== 0) {
              set_signal_status(effect, DIRTY);
              batch.schedule(effect);
            } else {
              __privateGet(batch, _dirty_effects2).add(effect);
            }
          }
        }
      }
      if (__privateGet(batch, _roots).length > 0 && !__privateGet(batch, _decrement_queued)) {
        batch.apply();
        for (var root2 of __privateGet(batch, _roots)) {
          __privateMethod(_a2 = batch, _Batch_instances, traverse_fn).call(_a2, root2, [], []);
        }
        __privateSet(batch, _roots, []);
      }
      batch.deactivate();
    }
  }
};
unlink_fn = function() {
  if (!this.linked) return;
  var prev = __privateGet(this, _prev);
  var next = __privateGet(this, _next);
  if (prev === null) {
    first_batch = next;
  } else {
    __privateSet(prev, _next, next);
  }
  if (next === null) {
    last_batch = prev;
  } else {
    __privateSet(next, _prev, prev);
  }
  this.linked = false;
};
let Batch = _Batch;
function infinite_loop_guard() {
  try {
    effect_update_depth_exceeded();
  } catch (error) {
    invoke_error_boundary(error, last_scheduled_effect);
  }
}
let eager_block_effects = null;
function flush_queued_effects(effects) {
  var length = effects.length;
  if (length === 0) return;
  var i = 0;
  while (i < length) {
    var effect = effects[i++];
    if ((effect.f & (DESTROYED | INERT)) === 0 && is_dirty(effect)) {
      eager_block_effects = /* @__PURE__ */ new Set();
      update_effect(effect);
      if (effect.deps === null && effect.first === null && effect.nodes === null && effect.teardown === null && effect.ac === null) {
        unlink_effect(effect);
      }
      if ((eager_block_effects == null ? void 0 : eager_block_effects.size) > 0) {
        old_values.clear();
        for (const e of eager_block_effects) {
          if ((e.f & (DESTROYED | INERT)) !== 0) continue;
          const ordered_effects = [e];
          let ancestor = e.parent;
          while (ancestor !== null) {
            if (eager_block_effects.has(ancestor)) {
              eager_block_effects.delete(ancestor);
              ordered_effects.push(ancestor);
            }
            ancestor = ancestor.parent;
          }
          for (let j = ordered_effects.length - 1; j >= 0; j--) {
            const e2 = ordered_effects[j];
            if ((e2.f & (DESTROYED | INERT)) !== 0) continue;
            update_effect(e2);
          }
        }
        eager_block_effects.clear();
      }
    }
  }
  eager_block_effects = null;
}
function mark_effects(value, sources, marked, checked) {
  if (marked.has(value)) return;
  marked.add(value);
  if (value.reactions !== null) {
    for (const reaction of value.reactions) {
      const flags2 = reaction.f;
      if ((flags2 & DERIVED) !== 0) {
        mark_effects(
          /** @type {Derived} */
          reaction,
          sources,
          marked,
          checked
        );
      } else if ((flags2 & (ASYNC | BLOCK_EFFECT)) !== 0 && (flags2 & DIRTY) === 0 && depends_on(reaction, sources, checked)) {
        set_signal_status(reaction, DIRTY);
        schedule_effect(
          /** @type {Effect} */
          reaction
        );
      }
    }
  }
}
function depends_on(reaction, sources, checked) {
  const depends = checked.get(reaction);
  if (depends !== void 0) return depends;
  if (reaction.deps !== null) {
    for (const dep of reaction.deps) {
      if (includes.call(sources, dep)) {
        return true;
      }
      if ((dep.f & DERIVED) !== 0 && depends_on(
        /** @type {Derived} */
        dep,
        sources,
        checked
      )) {
        checked.set(
          /** @type {Derived} */
          dep,
          true
        );
        return true;
      }
    }
  }
  checked.set(reaction, false);
  return false;
}
function schedule_effect(effect) {
  current_batch.schedule(effect);
}
function reset_branch(effect, tracked) {
  if ((effect.f & BRANCH_EFFECT) !== 0 && (effect.f & CLEAN) !== 0) {
    return;
  }
  if ((effect.f & DIRTY) !== 0) {
    tracked.d.push(effect);
  } else if ((effect.f & MAYBE_DIRTY) !== 0) {
    tracked.m.push(effect);
  }
  set_signal_status(effect, CLEAN);
  var e = effect.first;
  while (e !== null) {
    reset_branch(e, tracked);
    e = e.next;
  }
}
function reset_all(effect) {
  set_signal_status(effect, CLEAN);
  var e = effect.first;
  while (e !== null) {
    reset_all(e);
    e = e.next;
  }
}
let eager_effects = /* @__PURE__ */ new Set();
const old_values = /* @__PURE__ */ new Map();
let eager_effects_deferred = false;
function source(v, stack) {
  var signal = {
    f: 0,
    // TODO ideally we could skip this altogether, but it causes type errors
    v,
    reactions: null,
    equals,
    rv: 0,
    wv: 0
  };
  return signal;
}
// @__NO_SIDE_EFFECTS__
function state(v, stack) {
  const s = source(v);
  push_reaction_value(s);
  return s;
}
// @__NO_SIDE_EFFECTS__
function mutable_source(initial_value, immutable = false, trackable = true) {
  const s = source(initial_value);
  if (!immutable) {
    s.equals = safe_equals;
  }
  return s;
}
function set(source2, value, should_proxy = false) {
  if (active_reaction !== null && // since we are untracking the function inside `$inspect.with` we need to add this check
  // to ensure we error if state is set inside an inspect effect
  (!untracking || (active_reaction.f & EAGER_EFFECT) !== 0) && is_runes() && (active_reaction.f & (DERIVED | BLOCK_EFFECT | ASYNC | EAGER_EFFECT)) !== 0 && (current_sources === null || !current_sources.has(source2))) {
    state_unsafe_mutation();
  }
  let new_value = should_proxy ? proxy(value) : value;
  return internal_set(source2, new_value, legacy_updates);
}
function internal_set(source2, value, updated_during_traversal = null) {
  if (!source2.equals(value)) {
    old_values.set(source2, is_destroying_effect ? value : source2.v);
    var batch = Batch.ensure();
    batch.capture(source2, value);
    if ((source2.f & DERIVED) !== 0) {
      const derived2 = (
        /** @type {Derived} */
        source2
      );
      if ((source2.f & DIRTY) !== 0) {
        execute_derived(derived2);
      }
      if (batch_values === null) {
        update_derived_status(derived2);
      }
    }
    source2.wv = increment_write_version();
    mark_reactions(source2, DIRTY, updated_during_traversal);
    if (active_effect !== null && (active_effect.f & CLEAN) !== 0 && (active_effect.f & (BRANCH_EFFECT | ROOT_EFFECT)) === 0) {
      if (untracked_writes === null) {
        set_untracked_writes([source2]);
      } else {
        untracked_writes.push(source2);
      }
    }
    if (!batch.is_fork && eager_effects.size > 0 && !eager_effects_deferred) {
      flush_eager_effects();
    }
  }
  return value;
}
function flush_eager_effects() {
  eager_effects_deferred = false;
  for (const effect of eager_effects) {
    if ((effect.f & CLEAN) !== 0) {
      set_signal_status(effect, MAYBE_DIRTY);
    }
    let dirty;
    try {
      dirty = is_dirty(effect);
    } catch {
      dirty = true;
    }
    if (dirty) {
      update_effect(effect);
    }
  }
  eager_effects.clear();
}
function increment(source2) {
  set(source2, source2.v + 1);
}
function mark_reactions(signal, status, updated_during_traversal) {
  var reactions = signal.reactions;
  if (reactions === null) return;
  var length = reactions.length;
  for (var i = 0; i < length; i++) {
    var reaction = reactions[i];
    var flags2 = reaction.f;
    var not_dirty = (flags2 & DIRTY) === 0;
    if (not_dirty) {
      set_signal_status(reaction, status);
    }
    if ((flags2 & EAGER_EFFECT) !== 0) {
      eager_effects.add(
        /** @type {Effect} */
        reaction
      );
    } else if ((flags2 & DERIVED) !== 0) {
      var derived2 = (
        /** @type {Derived} */
        reaction
      );
      batch_values == null ? void 0 : batch_values.delete(derived2);
      if ((flags2 & WAS_MARKED) === 0) {
        if (flags2 & CONNECTED && (active_effect === null || (active_effect.f & REACTION_IS_UPDATING) === 0)) {
          reaction.f |= WAS_MARKED;
        }
        mark_reactions(derived2, MAYBE_DIRTY, updated_during_traversal);
      }
    } else if (not_dirty) {
      var effect = (
        /** @type {Effect} */
        reaction
      );
      if ((flags2 & BLOCK_EFFECT) !== 0 && eager_block_effects !== null) {
        eager_block_effects.add(effect);
      }
      if (updated_during_traversal !== null) {
        updated_during_traversal.push(effect);
      } else {
        schedule_effect(effect);
      }
    }
  }
}
function proxy(value) {
  if (typeof value !== "object" || value === null || STATE_SYMBOL in value) {
    return value;
  }
  const prototype = get_prototype_of(value);
  if (prototype !== object_prototype && prototype !== array_prototype) {
    return value;
  }
  var sources = /* @__PURE__ */ new Map();
  var is_proxied_array = is_array(value);
  var version = /* @__PURE__ */ state(0);
  var parent_version = update_version;
  var with_parent = (fn) => {
    if (update_version === parent_version) {
      return fn();
    }
    var reaction = active_reaction;
    var version2 = update_version;
    set_active_reaction(null);
    set_update_version(parent_version);
    var result = fn();
    set_active_reaction(reaction);
    set_update_version(version2);
    return result;
  };
  if (is_proxied_array) {
    sources.set("length", /* @__PURE__ */ state(
      /** @type {any[]} */
      value.length
    ));
  }
  return new Proxy(
    /** @type {any} */
    value,
    {
      defineProperty(_, prop2, descriptor) {
        if (!("value" in descriptor) || descriptor.configurable === false || descriptor.enumerable === false || descriptor.writable === false) {
          state_descriptors_fixed();
        }
        var s = sources.get(prop2);
        if (s === void 0) {
          with_parent(() => {
            var s2 = /* @__PURE__ */ state(descriptor.value);
            sources.set(prop2, s2);
            return s2;
          });
        } else {
          set(s, descriptor.value, true);
        }
        return true;
      },
      deleteProperty(target, prop2) {
        var s = sources.get(prop2);
        if (s === void 0) {
          if (prop2 in target) {
            const s2 = with_parent(() => /* @__PURE__ */ state(UNINITIALIZED));
            sources.set(prop2, s2);
            increment(version);
          }
        } else {
          set(s, UNINITIALIZED);
          increment(version);
        }
        return true;
      },
      get(target, prop2, receiver) {
        var _a2;
        if (prop2 === STATE_SYMBOL) {
          return value;
        }
        var s = sources.get(prop2);
        var exists = prop2 in target;
        if (s === void 0 && (!exists || ((_a2 = get_descriptor(target, prop2)) == null ? void 0 : _a2.writable))) {
          s = with_parent(() => {
            var p = proxy(exists ? target[prop2] : UNINITIALIZED);
            var s2 = /* @__PURE__ */ state(p);
            return s2;
          });
          sources.set(prop2, s);
        }
        if (s !== void 0) {
          var v = get(s);
          return v === UNINITIALIZED ? void 0 : v;
        }
        return Reflect.get(target, prop2, receiver);
      },
      getOwnPropertyDescriptor(target, prop2) {
        var descriptor = Reflect.getOwnPropertyDescriptor(target, prop2);
        if (descriptor && "value" in descriptor) {
          var s = sources.get(prop2);
          if (s) descriptor.value = get(s);
        } else if (descriptor === void 0) {
          var source2 = sources.get(prop2);
          var value2 = source2 == null ? void 0 : source2.v;
          if (source2 !== void 0 && value2 !== UNINITIALIZED) {
            return {
              enumerable: true,
              configurable: true,
              value: value2,
              writable: true
            };
          }
        }
        return descriptor;
      },
      has(target, prop2) {
        var _a2;
        if (prop2 === STATE_SYMBOL) {
          return true;
        }
        var s = sources.get(prop2);
        var has = s !== void 0 && s.v !== UNINITIALIZED || Reflect.has(target, prop2);
        if (s !== void 0 || active_effect !== null && (!has || ((_a2 = get_descriptor(target, prop2)) == null ? void 0 : _a2.writable))) {
          if (s === void 0) {
            s = with_parent(() => {
              var p = has ? proxy(target[prop2]) : UNINITIALIZED;
              var s2 = /* @__PURE__ */ state(p);
              return s2;
            });
            sources.set(prop2, s);
          }
          var value2 = get(s);
          if (value2 === UNINITIALIZED) {
            return false;
          }
        }
        return has;
      },
      set(target, prop2, value2, receiver) {
        var _a2;
        var s = sources.get(prop2);
        var has = prop2 in target;
        if (is_proxied_array && prop2 === "length") {
          for (var i = value2; i < /** @type {Source<number>} */
          s.v; i += 1) {
            var other_s = sources.get(i + "");
            if (other_s !== void 0) {
              set(other_s, UNINITIALIZED);
            } else if (i in target) {
              other_s = with_parent(() => /* @__PURE__ */ state(UNINITIALIZED));
              sources.set(i + "", other_s);
            }
          }
        }
        if (s === void 0) {
          if (!has || ((_a2 = get_descriptor(target, prop2)) == null ? void 0 : _a2.writable)) {
            s = with_parent(() => /* @__PURE__ */ state(void 0));
            set(s, proxy(value2));
            sources.set(prop2, s);
          }
        } else {
          has = s.v !== UNINITIALIZED;
          var p = with_parent(() => proxy(value2));
          set(s, p);
        }
        var descriptor = Reflect.getOwnPropertyDescriptor(target, prop2);
        if (descriptor == null ? void 0 : descriptor.set) {
          descriptor.set.call(receiver, value2);
        }
        if (!has) {
          if (is_proxied_array && typeof prop2 === "string") {
            var ls = (
              /** @type {Source<number>} */
              sources.get("length")
            );
            var n = Number(prop2);
            if (Number.isInteger(n) && n >= ls.v) {
              set(ls, n + 1);
            }
          }
          increment(version);
        }
        return true;
      },
      ownKeys(target) {
        get(version);
        var own_keys = Reflect.ownKeys(target).filter((key2) => {
          var source3 = sources.get(key2);
          return source3 === void 0 || source3.v !== UNINITIALIZED;
        });
        for (var [key, source2] of sources) {
          if (source2.v !== UNINITIALIZED && !(key in target)) {
            own_keys.push(key);
          }
        }
        return own_keys;
      },
      setPrototypeOf() {
        state_prototype_fixed();
      }
    }
  );
}
function get_proxied_value(value) {
  try {
    if (value !== null && typeof value === "object" && STATE_SYMBOL in value) {
      return value[STATE_SYMBOL];
    }
  } catch {
  }
  return value;
}
function is(a, b) {
  return Object.is(get_proxied_value(a), get_proxied_value(b));
}
var $window;
var $document;
var is_firefox;
var first_child_getter;
var next_sibling_getter;
function init_operations() {
  if ($window !== void 0) {
    return;
  }
  $window = window;
  $document = document;
  is_firefox = /Firefox/.test(navigator.userAgent);
  var element_prototype = Element.prototype;
  var node_prototype = Node.prototype;
  var text_prototype = Text.prototype;
  first_child_getter = get_descriptor(node_prototype, "firstChild").get;
  next_sibling_getter = get_descriptor(node_prototype, "nextSibling").get;
  if (is_extensible(element_prototype)) {
    element_prototype[CLASS_CACHE] = void 0;
    element_prototype[ATTRIBUTES_CACHE] = null;
    element_prototype[STYLE_CACHE] = void 0;
    element_prototype.__e = void 0;
  }
  if (is_extensible(text_prototype)) {
    text_prototype[TEXT_CACHE] = void 0;
  }
}
function create_text(value = "") {
  return document.createTextNode(value);
}
// @__NO_SIDE_EFFECTS__
function get_first_child(node) {
  return (
    /** @type {TemplateNode | null} */
    first_child_getter.call(node)
  );
}
// @__NO_SIDE_EFFECTS__
function get_next_sibling(node) {
  return (
    /** @type {TemplateNode | null} */
    next_sibling_getter.call(node)
  );
}
function child(node, is_text) {
  {
    return /* @__PURE__ */ get_first_child(node);
  }
}
function first_child(node, is_text = false) {
  {
    var first = /* @__PURE__ */ get_first_child(node);
    if (first instanceof Comment && first.data === "") return /* @__PURE__ */ get_next_sibling(first);
    return first;
  }
}
function sibling(node, count = 1, is_text = false) {
  let next_sibling = node;
  while (count--) {
    next_sibling = /** @type {TemplateNode} */
    /* @__PURE__ */ get_next_sibling(next_sibling);
  }
  {
    return next_sibling;
  }
}
function clear_text_content(node) {
  node.textContent = "";
}
function should_defer_append() {
  return false;
}
function create_element(tag, namespace, is2) {
  {
    return (
      /** @type {T extends keyof HTMLElementTagNameMap ? HTMLElementTagNameMap[T] : Element} */
      is2 ? document.createElement(tag, { is: is2 }) : document.createElement(tag)
    );
  }
}
function validate_effect(rune) {
  if (active_effect === null) {
    if (active_reaction === null) {
      effect_orphan();
    }
    effect_in_unowned_derived();
  }
  if (is_destroying_effect) {
    effect_in_teardown();
  }
}
function push_effect(effect, parent_effect) {
  var parent_last = parent_effect.last;
  if (parent_last === null) {
    parent_effect.last = parent_effect.first = effect;
  } else {
    parent_last.next = effect;
    effect.prev = parent_last;
    parent_effect.last = effect;
  }
}
function create_effect(type, fn) {
  var parent = active_effect;
  if (parent !== null && (parent.f & INERT) !== 0) {
    type |= INERT;
  }
  var effect = {
    ctx: component_context,
    deps: null,
    nodes: null,
    f: type | DIRTY | CONNECTED,
    first: null,
    fn,
    last: null,
    next: null,
    parent,
    b: parent && parent.b,
    prev: null,
    teardown: null,
    wv: 0,
    ac: null
  };
  current_batch == null ? void 0 : current_batch.register_created_effect(effect);
  var e = effect;
  if ((type & EFFECT) !== 0) {
    if (collected_effects !== null) {
      collected_effects.push(effect);
    } else {
      Batch.ensure().schedule(effect);
    }
  } else if (fn !== null) {
    try {
      update_effect(effect);
    } catch (e2) {
      destroy_effect(effect);
      throw e2;
    }
    if (e.deps === null && e.teardown === null && e.nodes === null && e.first === e.last && // either `null`, or a singular child
    (e.f & EFFECT_PRESERVED) === 0) {
      e = e.first;
      if ((type & BLOCK_EFFECT) !== 0 && (type & EFFECT_TRANSPARENT) !== 0 && e !== null) {
        e.f |= EFFECT_TRANSPARENT;
      }
    }
  }
  if (e !== null) {
    e.parent = parent;
    if (parent !== null) {
      push_effect(e, parent);
    }
    if (active_reaction !== null && (active_reaction.f & DERIVED) !== 0 && (type & ROOT_EFFECT) === 0) {
      var derived2 = (
        /** @type {Derived} */
        active_reaction
      );
      (derived2.effects ?? (derived2.effects = [])).push(e);
    }
  }
  return effect;
}
function effect_tracking() {
  return active_reaction !== null && !untracking;
}
function teardown(fn) {
  const effect = create_effect(RENDER_EFFECT, null);
  set_signal_status(effect, CLEAN);
  effect.teardown = fn;
  return effect;
}
function user_effect(fn) {
  validate_effect();
  var flags2 = (
    /** @type {Effect} */
    active_effect.f
  );
  var defer = !active_reaction && (flags2 & BRANCH_EFFECT) !== 0 && component_context !== null && !component_context.i;
  if (defer) {
    var context = (
      /** @type {ComponentContext} */
      component_context
    );
    (context.e ?? (context.e = [])).push(fn);
  } else {
    return create_user_effect(fn);
  }
}
function create_user_effect(fn) {
  return create_effect(EFFECT | USER_EFFECT, fn);
}
function component_root(fn) {
  Batch.ensure();
  const effect = create_effect(ROOT_EFFECT | EFFECT_PRESERVED, fn);
  return (options = {}) => {
    return new Promise((fulfil) => {
      if (options.outro) {
        pause_effect(effect, () => {
          destroy_effect(effect);
          fulfil(void 0);
        });
      } else {
        destroy_effect(effect);
        fulfil(void 0);
      }
    });
  };
}
function async_effect(fn) {
  return create_effect(ASYNC | EFFECT_PRESERVED, fn);
}
function render_effect(fn, flags2 = 0) {
  return create_effect(RENDER_EFFECT | flags2, fn);
}
function template_effect(fn, sync = [], async = [], blockers = []) {
  flatten(blockers, sync, async, (values) => {
    create_effect(RENDER_EFFECT, () => {
      fn(...values.map(get));
    });
  });
}
function deferred_template_effect(fn, sync = [], async = [], blockers = []) {
  flatten(blockers, sync, async, (values) => {
    create_effect(EFFECT, () => fn(...values.map(get)));
  });
}
function block(fn, flags2 = 0) {
  var effect = create_effect(BLOCK_EFFECT | flags2, fn);
  return effect;
}
function branch(fn) {
  return create_effect(BRANCH_EFFECT | EFFECT_PRESERVED, fn);
}
function execute_effect_teardown(effect) {
  var teardown2 = effect.teardown;
  if (teardown2 !== null) {
    const previously_destroying_effect = is_destroying_effect;
    const previous_reaction = active_reaction;
    set_is_destroying_effect(true);
    set_active_reaction(null);
    try {
      teardown2.call(null);
    } finally {
      set_is_destroying_effect(previously_destroying_effect);
      set_active_reaction(previous_reaction);
    }
  }
}
function destroy_effect_children(signal, remove_dom = false) {
  var effect = signal.first;
  signal.first = signal.last = null;
  while (effect !== null) {
    const controller = effect.ac;
    if (controller !== null) {
      without_reactive_context(() => {
        controller.abort(STALE_REACTION);
      });
    }
    var next = effect.next;
    if ((effect.f & ROOT_EFFECT) !== 0) {
      effect.parent = null;
    } else {
      destroy_effect(effect, remove_dom);
    }
    effect = next;
  }
}
function destroy_block_effect_children(signal) {
  var effect = signal.first;
  while (effect !== null) {
    var next = effect.next;
    if ((effect.f & BRANCH_EFFECT) === 0) {
      destroy_effect(effect);
    }
    effect = next;
  }
}
function destroy_effect(effect, remove_dom = true) {
  var removed = false;
  if ((remove_dom || (effect.f & HEAD_EFFECT) !== 0) && effect.nodes !== null && effect.nodes.end !== null) {
    remove_effect_dom(
      effect.nodes.start,
      /** @type {TemplateNode} */
      effect.nodes.end
    );
    removed = true;
  }
  effect.f |= DESTROYING;
  destroy_effect_children(effect, remove_dom && !removed);
  remove_reactions(effect, 0);
  var transitions = effect.nodes && effect.nodes.t;
  if (transitions !== null) {
    for (const transition of transitions) {
      transition.stop();
    }
  }
  execute_effect_teardown(effect);
  effect.f ^= DESTROYING;
  effect.f |= DESTROYED;
  var parent = effect.parent;
  if (parent !== null && parent.first !== null) {
    unlink_effect(effect);
  }
  effect.next = effect.prev = effect.teardown = effect.ctx = effect.deps = effect.fn = effect.nodes = effect.ac = effect.b = null;
}
function remove_effect_dom(node, end) {
  while (node !== null) {
    var next = node === end ? null : /* @__PURE__ */ get_next_sibling(node);
    node.remove();
    node = next;
  }
}
function unlink_effect(effect) {
  var parent = effect.parent;
  var prev = effect.prev;
  var next = effect.next;
  if (prev !== null) prev.next = next;
  if (next !== null) next.prev = prev;
  if (parent !== null) {
    if (parent.first === effect) parent.first = next;
    if (parent.last === effect) parent.last = prev;
  }
}
function pause_effect(effect, callback, destroy = true) {
  var transitions = [];
  pause_children(effect, transitions, true);
  var fn = () => {
    if (destroy) destroy_effect(effect);
    if (callback) callback();
  };
  var remaining = transitions.length;
  if (remaining > 0) {
    var check = () => --remaining || fn();
    for (var transition of transitions) {
      transition.out(check);
    }
  } else {
    fn();
  }
}
function pause_children(effect, transitions, local) {
  if ((effect.f & INERT) !== 0) return;
  effect.f ^= INERT;
  var t = effect.nodes && effect.nodes.t;
  if (t !== null) {
    for (const transition of t) {
      if (transition.is_global || local) {
        transitions.push(transition);
      }
    }
  }
  var child2 = effect.first;
  while (child2 !== null) {
    var sibling2 = child2.next;
    if ((child2.f & ROOT_EFFECT) === 0) {
      var transparent = (child2.f & EFFECT_TRANSPARENT) !== 0 || // If this is a branch effect without a block effect parent,
      // it means the parent block effect was pruned. In that case,
      // transparency information was transferred to the branch effect.
      (child2.f & BRANCH_EFFECT) !== 0 && (effect.f & BLOCK_EFFECT) !== 0;
      pause_children(child2, transitions, transparent ? local : false);
    }
    child2 = sibling2;
  }
}
function resume_effect(effect) {
  resume_children(effect, true);
}
function resume_children(effect, local) {
  if ((effect.f & INERT) === 0) return;
  effect.f ^= INERT;
  if ((effect.f & CLEAN) === 0) {
    set_signal_status(effect, DIRTY);
    Batch.ensure().schedule(effect);
  }
  var child2 = effect.first;
  while (child2 !== null) {
    var sibling2 = child2.next;
    var transparent = (child2.f & EFFECT_TRANSPARENT) !== 0 || (child2.f & BRANCH_EFFECT) !== 0;
    resume_children(child2, transparent ? local : false);
    child2 = sibling2;
  }
  var t = effect.nodes && effect.nodes.t;
  if (t !== null) {
    for (const transition of t) {
      if (transition.is_global || local) {
        transition.in();
      }
    }
  }
}
function move_effect(effect, fragment) {
  if (!effect.nodes) return;
  var node = effect.nodes.start;
  var end = effect.nodes.end;
  while (node !== null) {
    var next = node === end ? null : /* @__PURE__ */ get_next_sibling(node);
    fragment.append(node);
    node = next;
  }
}
let is_updating_effect = false;
let is_destroying_effect = false;
function set_is_destroying_effect(value) {
  is_destroying_effect = value;
}
let active_reaction = null;
let untracking = false;
function set_active_reaction(reaction) {
  active_reaction = reaction;
}
let active_effect = null;
function set_active_effect(effect) {
  active_effect = effect;
}
let current_sources = null;
function push_reaction_value(value) {
  if (active_reaction !== null && true) {
    (current_sources ?? (current_sources = /* @__PURE__ */ new Set())).add(value);
  }
}
let new_deps = null;
let skipped_deps = 0;
let untracked_writes = null;
function set_untracked_writes(value) {
  untracked_writes = value;
}
let write_version = 1;
let read_version = 0;
let update_version = read_version;
function set_update_version(value) {
  update_version = value;
}
function increment_write_version() {
  return ++write_version;
}
function is_dirty(reaction) {
  var flags2 = reaction.f;
  if ((flags2 & DIRTY) !== 0) {
    return true;
  }
  if (flags2 & DERIVED) {
    reaction.f &= ~WAS_MARKED;
  }
  if ((flags2 & MAYBE_DIRTY) !== 0) {
    var dependencies = (
      /** @type {Value[]} */
      reaction.deps
    );
    var length = dependencies.length;
    for (var i = 0; i < length; i++) {
      var dependency = dependencies[i];
      if (is_dirty(
        /** @type {Derived} */
        dependency
      )) {
        update_derived(
          /** @type {Derived} */
          dependency
        );
      }
      if (dependency.wv > reaction.wv) {
        return true;
      }
    }
    if ((flags2 & CONNECTED) !== 0 && // During time traveling we don't want to reset the status so that
    // traversal of the graph in the other batches still happens
    batch_values === null) {
      set_signal_status(reaction, CLEAN);
    }
  }
  return false;
}
function schedule_possible_effect_self_invalidation(signal, effect, root2 = true) {
  var reactions = signal.reactions;
  if (reactions === null) return;
  if (current_sources !== null && current_sources.has(signal)) {
    return;
  }
  for (var i = 0; i < reactions.length; i++) {
    var reaction = reactions[i];
    if ((reaction.f & DERIVED) !== 0) {
      schedule_possible_effect_self_invalidation(
        /** @type {Derived} */
        reaction,
        effect,
        false
      );
    } else if (effect === reaction) {
      if (root2) {
        set_signal_status(reaction, DIRTY);
      } else if ((reaction.f & CLEAN) !== 0) {
        set_signal_status(reaction, MAYBE_DIRTY);
      }
      schedule_effect(
        /** @type {Effect} */
        reaction
      );
    }
  }
}
function update_reaction(reaction) {
  var _a2;
  var previous_deps = new_deps;
  var previous_skipped_deps = skipped_deps;
  var previous_untracked_writes = untracked_writes;
  var previous_reaction = active_reaction;
  var previous_sources = current_sources;
  var previous_component_context = component_context;
  var previous_untracking = untracking;
  var previous_update_version = update_version;
  var flags2 = reaction.f;
  new_deps = /** @type {null | Value[]} */
  null;
  skipped_deps = 0;
  untracked_writes = null;
  active_reaction = (flags2 & (BRANCH_EFFECT | ROOT_EFFECT)) === 0 ? reaction : null;
  current_sources = null;
  set_component_context(reaction.ctx);
  untracking = false;
  update_version = ++read_version;
  if (reaction.ac !== null) {
    without_reactive_context(() => {
      reaction.ac.abort(STALE_REACTION);
    });
    reaction.ac = null;
  }
  try {
    reaction.f |= REACTION_IS_UPDATING;
    var fn = (
      /** @type {Function} */
      reaction.fn
    );
    var result = fn();
    reaction.f |= REACTION_RAN;
    var deps = reaction.deps;
    var is_fork = current_batch == null ? void 0 : current_batch.is_fork;
    if (new_deps !== null) {
      var i;
      if (!is_fork) {
        remove_reactions(reaction, skipped_deps);
      }
      if (deps !== null && skipped_deps > 0) {
        deps.length = skipped_deps + new_deps.length;
        for (i = 0; i < new_deps.length; i++) {
          deps[skipped_deps + i] = new_deps[i];
        }
      } else {
        reaction.deps = deps = new_deps;
      }
      if (effect_tracking() && (reaction.f & CONNECTED) !== 0) {
        for (i = skipped_deps; i < deps.length; i++) {
          ((_a2 = deps[i]).reactions ?? (_a2.reactions = [])).push(reaction);
        }
      }
    } else if (!is_fork && deps !== null && skipped_deps < deps.length) {
      remove_reactions(reaction, skipped_deps);
      deps.length = skipped_deps;
    }
    if (is_runes() && untracked_writes !== null && !untracking && deps !== null && (reaction.f & (DERIVED | MAYBE_DIRTY | DIRTY)) === 0) {
      for (i = 0; i < /** @type {Source[]} */
      untracked_writes.length; i++) {
        schedule_possible_effect_self_invalidation(
          untracked_writes[i],
          /** @type {Effect} */
          reaction
        );
      }
    }
    if (previous_reaction !== null && previous_reaction !== reaction) {
      read_version++;
      if (previous_reaction.deps !== null) {
        for (let i2 = 0; i2 < previous_skipped_deps; i2 += 1) {
          previous_reaction.deps[i2].rv = read_version;
        }
      }
      if (previous_deps !== null) {
        for (const dep of previous_deps) {
          dep.rv = read_version;
        }
      }
      if (untracked_writes !== null) {
        if (previous_untracked_writes === null) {
          previous_untracked_writes = untracked_writes;
        } else {
          previous_untracked_writes.push(.../** @type {Source[]} */
          untracked_writes);
        }
      }
    }
    if ((reaction.f & ERROR_VALUE) !== 0) {
      reaction.f ^= ERROR_VALUE;
    }
    return result;
  } catch (error) {
    return handle_error(error);
  } finally {
    reaction.f ^= REACTION_IS_UPDATING;
    new_deps = previous_deps;
    skipped_deps = previous_skipped_deps;
    untracked_writes = previous_untracked_writes;
    active_reaction = previous_reaction;
    current_sources = previous_sources;
    set_component_context(previous_component_context);
    untracking = previous_untracking;
    update_version = previous_update_version;
  }
}
function remove_reaction(signal, dependency) {
  let reactions = dependency.reactions;
  if (reactions !== null) {
    var index2 = index_of.call(reactions, signal);
    if (index2 !== -1) {
      var new_length = reactions.length - 1;
      if (new_length === 0) {
        reactions = dependency.reactions = null;
      } else {
        reactions[index2] = reactions[new_length];
        reactions.pop();
      }
    }
  }
  if (reactions === null && (dependency.f & DERIVED) !== 0 && // Destroying a child effect while updating a parent effect can cause a dependency to appear
  // to be unused, when in fact it is used by the currently-updating parent. Checking `new_deps`
  // allows us to skip the expensive work of disconnecting and immediately reconnecting it
  (new_deps === null || !includes.call(new_deps, dependency))) {
    var derived2 = (
      /** @type {Derived} */
      dependency
    );
    if ((derived2.f & CONNECTED) !== 0) {
      derived2.f ^= CONNECTED;
      derived2.f &= ~WAS_MARKED;
    }
    if (derived2.v !== UNINITIALIZED) {
      update_derived_status(derived2);
    }
    if (derived2.ac !== null) {
      without_reactive_context(() => {
        derived2.ac.abort(STALE_REACTION);
        derived2.ac = null;
        set_signal_status(derived2, DIRTY);
      });
    }
    freeze_derived_effects(derived2);
    remove_reactions(derived2, 0);
  }
}
function remove_reactions(signal, start_index) {
  var dependencies = signal.deps;
  if (dependencies === null) return;
  for (var i = start_index; i < dependencies.length; i++) {
    remove_reaction(signal, dependencies[i]);
  }
}
function update_effect(effect) {
  var flags2 = effect.f;
  if ((flags2 & DESTROYED) !== 0) {
    return;
  }
  set_signal_status(effect, CLEAN);
  var previous_effect = active_effect;
  var was_updating_effect = is_updating_effect;
  active_effect = effect;
  is_updating_effect = (flags2 & (BRANCH_EFFECT | ROOT_EFFECT)) === 0;
  try {
    if ((flags2 & (BLOCK_EFFECT | MANAGED_EFFECT)) !== 0) {
      destroy_block_effect_children(effect);
    } else {
      destroy_effect_children(effect);
    }
    execute_effect_teardown(effect);
    var teardown2 = update_reaction(effect);
    effect.teardown = typeof teardown2 === "function" ? teardown2 : null;
    effect.wv = write_version;
    var dep;
    if (DEV && tracing_mode_flag && (effect.f & DIRTY) !== 0 && effect.deps !== null) ;
  } finally {
    is_updating_effect = was_updating_effect;
    active_effect = previous_effect;
  }
}
function get(signal) {
  var flags2 = signal.f;
  var is_derived = (flags2 & DERIVED) !== 0;
  if (active_reaction !== null && !untracking) {
    var destroyed = active_effect !== null && (active_effect.f & DESTROYED) !== 0;
    if (!destroyed && (current_sources === null || !current_sources.has(signal))) {
      var deps = active_reaction.deps;
      if ((active_reaction.f & REACTION_IS_UPDATING) !== 0) {
        if (signal.rv < read_version) {
          signal.rv = read_version;
          if (new_deps === null && deps !== null && deps[skipped_deps] === signal) {
            skipped_deps++;
          } else if (new_deps === null) {
            new_deps = [signal];
          } else {
            new_deps.push(signal);
          }
        }
      } else {
        active_reaction.deps ?? (active_reaction.deps = []);
        if (!includes.call(active_reaction.deps, signal)) {
          active_reaction.deps.push(signal);
        }
        var reactions = signal.reactions;
        if (reactions === null) {
          signal.reactions = [active_reaction];
        } else if (!includes.call(reactions, active_reaction)) {
          reactions.push(active_reaction);
        }
      }
    }
  }
  if (is_destroying_effect && old_values.has(signal)) {
    return old_values.get(signal);
  }
  if (is_derived) {
    var derived2 = (
      /** @type {Derived} */
      signal
    );
    if (is_destroying_effect) {
      var value = derived2.v;
      if ((derived2.f & CLEAN) === 0 && derived2.reactions !== null || depends_on_old_values(derived2)) {
        value = execute_derived(derived2);
      }
      old_values.set(derived2, value);
      return value;
    }
    var should_connect = (derived2.f & CONNECTED) === 0 && !untracking && active_reaction !== null && (is_updating_effect || (active_reaction.f & CONNECTED) !== 0);
    var is_new = (derived2.f & REACTION_RAN) === 0;
    if (is_dirty(derived2)) {
      if (should_connect) {
        derived2.f |= CONNECTED;
      }
      update_derived(derived2);
    }
    if (should_connect && !is_new) {
      unfreeze_derived_effects(derived2);
      reconnect(derived2);
    }
  }
  if (batch_values == null ? void 0 : batch_values.has(signal)) {
    return batch_values.get(signal);
  }
  if ((signal.f & ERROR_VALUE) !== 0) {
    throw signal.v;
  }
  return signal.v;
}
function reconnect(derived2) {
  derived2.f |= CONNECTED;
  if (derived2.deps === null) return;
  for (const dep of derived2.deps) {
    (dep.reactions ?? (dep.reactions = [])).push(derived2);
    if ((dep.f & DERIVED) !== 0 && (dep.f & CONNECTED) === 0) {
      unfreeze_derived_effects(
        /** @type {Derived} */
        dep
      );
      reconnect(
        /** @type {Derived} */
        dep
      );
    }
  }
}
function depends_on_old_values(derived2) {
  if (derived2.v === UNINITIALIZED) return true;
  if (derived2.deps === null) return false;
  for (const dep of derived2.deps) {
    if (old_values.has(dep)) {
      return true;
    }
    if ((dep.f & DERIVED) !== 0 && depends_on_old_values(
      /** @type {Derived} */
      dep
    )) {
      return true;
    }
  }
  return false;
}
function untrack(fn) {
  var previous_untracking = untracking;
  try {
    untracking = true;
    return fn();
  } finally {
    untracking = previous_untracking;
  }
}
const PASSIVE_EVENTS = ["touchstart", "touchmove"];
function is_passive_event(name) {
  return PASSIVE_EVENTS.includes(name);
}
const event_symbol = Symbol("events");
const all_registered_events = /* @__PURE__ */ new Set();
const root_event_handles = /* @__PURE__ */ new Set();
function delegated(event_name, element, handler) {
  (element[event_symbol] ?? (element[event_symbol] = {}))[event_name] = handler;
}
function delegate(events) {
  for (var i = 0; i < events.length; i++) {
    all_registered_events.add(events[i]);
  }
  for (var fn of root_event_handles) {
    fn(events);
  }
}
let last_propagated_event = null;
function handle_event_propagation(event) {
  var _a2, _b2;
  var handler_element = this;
  var owner_document = (
    /** @type {Node} */
    handler_element.ownerDocument
  );
  var event_name = event.type;
  var path = ((_a2 = event.composedPath) == null ? void 0 : _a2.call(event)) || [];
  var current_target = (
    /** @type {null | Element} */
    path[0] || event.target
  );
  last_propagated_event = event;
  var path_idx = 0;
  var handled_at = last_propagated_event === event && event[event_symbol];
  if (handled_at) {
    var at_idx = path.indexOf(handled_at);
    if (at_idx !== -1 && (handler_element === document || handler_element === /** @type {any} */
    window)) {
      event[event_symbol] = handler_element;
      return;
    }
    var handler_idx = path.indexOf(handler_element);
    if (handler_idx === -1) {
      return;
    }
    if (at_idx <= handler_idx) {
      path_idx = at_idx;
    }
  }
  current_target = /** @type {Element} */
  path[path_idx] || event.target;
  if (current_target === handler_element) return;
  define_property(event, "currentTarget", {
    configurable: true,
    get() {
      return current_target || owner_document;
    }
  });
  var previous_reaction = active_reaction;
  var previous_effect = active_effect;
  set_active_reaction(null);
  set_active_effect(null);
  try {
    var throw_error;
    var other_errors = [];
    while (current_target !== null) {
      if (current_target === handler_element) break;
      try {
        var delegated2 = (_b2 = current_target[event_symbol]) == null ? void 0 : _b2[event_name];
        if (delegated2 != null && (!/** @type {any} */
        current_target.disabled || // DOM could've been updated already by the time this is reached, so we check this as well
        // -> the target could not have been disabled because it emits the event in the first place
        event.target === current_target)) {
          delegated2.call(current_target, event);
        }
      } catch (error) {
        if (throw_error) {
          other_errors.push(error);
        } else {
          throw_error = error;
        }
      }
      if (event.cancelBubble) break;
      path_idx++;
      current_target = path_idx < path.length ? (
        /** @type {Element} */
        path[path_idx]
      ) : null;
    }
    if (throw_error) {
      for (let error of other_errors) {
        queueMicrotask(() => {
          throw error;
        });
      }
      throw throw_error;
    }
  } finally {
    event[event_symbol] = handler_element;
    delete event.currentTarget;
    set_active_reaction(previous_reaction);
    set_active_effect(previous_effect);
  }
}
const policy = (
  // We gotta write it like this because after downleveling the pure comment may end up in the wrong location
  ((_b = globalThis == null ? void 0 : globalThis.window) == null ? void 0 : _b.trustedTypes) && /* @__PURE__ */ globalThis.window.trustedTypes.createPolicy("svelte-trusted-html", {
    /** @param {string} html */
    createHTML: (html) => {
      return html;
    }
  })
);
function create_trusted_html(html) {
  return (
    /** @type {string} */
    (policy == null ? void 0 : policy.createHTML(html)) ?? html
  );
}
function create_fragment_from_html(html) {
  var elem = create_element("template");
  elem.innerHTML = create_trusted_html(html.replaceAll("<!>", "<!---->"));
  return elem.content;
}
function assign_nodes(start, end) {
  var effect = (
    /** @type {Effect} */
    active_effect
  );
  if (effect.nodes === null) {
    effect.nodes = { start, end, a: null, t: null };
  }
}
// @__NO_SIDE_EFFECTS__
function from_html(content, flags2) {
  var is_fragment = (flags2 & TEMPLATE_FRAGMENT) !== 0;
  var use_import_node = (flags2 & TEMPLATE_USE_IMPORT_NODE) !== 0;
  var node;
  var has_start = !content.startsWith("<!>");
  return () => {
    if (node === void 0) {
      node = create_fragment_from_html(has_start ? content : "<!>" + content);
      if (!is_fragment) node = /** @type {TemplateNode} */
      /* @__PURE__ */ get_first_child(node);
    }
    var clone2 = (
      /** @type {TemplateNode} */
      use_import_node || is_firefox ? document.importNode(node, true) : node.cloneNode(true)
    );
    if (is_fragment) {
      var start = (
        /** @type {TemplateNode} */
        /* @__PURE__ */ get_first_child(clone2)
      );
      var end = (
        /** @type {TemplateNode} */
        clone2.lastChild
      );
      assign_nodes(start, end);
    } else {
      assign_nodes(clone2, clone2);
    }
    return clone2;
  };
}
function comment() {
  var frag = document.createDocumentFragment();
  var start = document.createComment("");
  var anchor = create_text();
  frag.append(start, anchor);
  assign_nodes(start, anchor);
  return frag;
}
function append(anchor, dom) {
  if (anchor === null) {
    return;
  }
  anchor.before(
    /** @type {Node} */
    dom
  );
}
function set_text(text, value) {
  var str = value == null ? "" : typeof value === "object" ? `${value}` : value;
  if (str !== /** @type {any} */
  (text[TEXT_CACHE] ?? (text[TEXT_CACHE] = text.nodeValue))) {
    text[TEXT_CACHE] = str;
    text.nodeValue = `${str}`;
  }
}
function mount(component, options) {
  return _mount(component, options);
}
const listeners = /* @__PURE__ */ new Map();
function _mount(Component, { target, anchor, props = {}, events, context, intro = true, transformError }) {
  init_operations();
  var component = void 0;
  var unmount2 = component_root(() => {
    var anchor_node = anchor ?? target.appendChild(create_text());
    boundary(
      /** @type {TemplateNode} */
      anchor_node,
      {
        pending: () => {
        }
      },
      (anchor_node2) => {
        push({});
        var ctx = (
          /** @type {ComponentContext} */
          component_context
        );
        if (context) ctx.c = context;
        if (events) {
          props.$$events = events;
        }
        component = Component(anchor_node2, props) || {};
        pop();
      },
      transformError
    );
    var registered_events = /* @__PURE__ */ new Set();
    var event_handle = (events2) => {
      for (var i = 0; i < events2.length; i++) {
        var event_name = events2[i];
        if (registered_events.has(event_name)) continue;
        registered_events.add(event_name);
        var passive = is_passive_event(event_name);
        for (const node of [target, document]) {
          var counts = listeners.get(node);
          if (counts === void 0) {
            counts = /* @__PURE__ */ new Map();
            listeners.set(node, counts);
          }
          var count = counts.get(event_name);
          if (count === void 0) {
            node.addEventListener(event_name, handle_event_propagation, { passive });
            counts.set(event_name, 1);
          } else {
            counts.set(event_name, count + 1);
          }
        }
      }
    };
    event_handle(array_from(all_registered_events));
    root_event_handles.add(event_handle);
    return () => {
      var _a2;
      for (var event_name of registered_events) {
        for (const node of [target, document]) {
          var counts = (
            /** @type {Map<string, number>} */
            listeners.get(node)
          );
          var count = (
            /** @type {number} */
            counts.get(event_name)
          );
          if (--count == 0) {
            node.removeEventListener(event_name, handle_event_propagation);
            counts.delete(event_name);
            if (counts.size === 0) {
              listeners.delete(node);
            }
          } else {
            counts.set(event_name, count);
          }
        }
      }
      root_event_handles.delete(event_handle);
      if (anchor_node !== anchor) {
        (_a2 = anchor_node.parentNode) == null ? void 0 : _a2.removeChild(anchor_node);
      }
    };
  });
  mounted_components.set(component, unmount2);
  return component;
}
let mounted_components = /* @__PURE__ */ new WeakMap();
function unmount(component, options) {
  const fn = mounted_components.get(component);
  if (fn) {
    mounted_components.delete(component);
    return fn(options);
  }
  return Promise.resolve();
}
class BranchManager {
  /**
   * @param {TemplateNode} anchor
   * @param {boolean} transition
   */
  constructor(anchor, transition = true) {
    /** @type {TemplateNode} */
    __publicField(this, "anchor");
    /** @type {Map<Batch, Key>} */
    __privateAdd(this, _batches, /* @__PURE__ */ new Map());
    /**
     * Map of keys to effects that are currently rendered in the DOM.
     * These effects are visible and actively part of the document tree.
     * Example:
     * ```
     * {#if condition}
     * 	foo
     * {:else}
     * 	bar
     * {/if}
     * ```
     * Can result in the entries `true->Effect` and `false->Effect`
     * @type {Map<Key, Effect>}
     */
    __privateAdd(this, _onscreen, /* @__PURE__ */ new Map());
    /**
     * Similar to #onscreen with respect to the keys, but contains branches that are not yet
     * in the DOM, because their insertion is deferred.
     * @type {Map<Key, Branch>}
     */
    __privateAdd(this, _offscreen, /* @__PURE__ */ new Map());
    /**
     * Keys of effects that are currently outroing
     * @type {Set<Key>}
     */
    __privateAdd(this, _outroing, /* @__PURE__ */ new Set());
    /**
     * Whether to pause (i.e. outro) on change, or destroy immediately.
     * This is necessary for `<svelte:element>`
     */
    __privateAdd(this, _transition, true);
    /**
     * @param {Batch} batch
     */
    __privateAdd(this, _commit, (batch) => {
      if (!__privateGet(this, _batches).has(batch)) return;
      var key = (
        /** @type {Key} */
        __privateGet(this, _batches).get(batch)
      );
      var onscreen = __privateGet(this, _onscreen).get(key);
      if (onscreen) {
        resume_effect(onscreen);
        __privateGet(this, _outroing).delete(key);
      } else {
        var offscreen = __privateGet(this, _offscreen).get(key);
        if (offscreen) {
          resume_effect(offscreen.effect);
          __privateGet(this, _onscreen).set(key, offscreen.effect);
          __privateGet(this, _offscreen).delete(key);
          offscreen.fragment.lastChild.remove();
          this.anchor.before(offscreen.fragment);
          onscreen = offscreen.effect;
        }
      }
      for (const [b, k] of __privateGet(this, _batches)) {
        __privateGet(this, _batches).delete(b);
        if (b === batch) {
          break;
        }
        const offscreen2 = __privateGet(this, _offscreen).get(k);
        if (offscreen2) {
          destroy_effect(offscreen2.effect);
          __privateGet(this, _offscreen).delete(k);
        }
      }
      for (const [k, effect] of __privateGet(this, _onscreen)) {
        if (k === key || __privateGet(this, _outroing).has(k)) continue;
        const on_destroy = () => {
          const keys = Array.from(__privateGet(this, _batches).values());
          if (keys.includes(k)) {
            var fragment = document.createDocumentFragment();
            move_effect(effect, fragment);
            fragment.append(create_text());
            __privateGet(this, _offscreen).set(k, { effect, fragment });
          } else {
            destroy_effect(effect);
          }
          __privateGet(this, _outroing).delete(k);
          __privateGet(this, _onscreen).delete(k);
        };
        if (__privateGet(this, _transition) || !onscreen) {
          __privateGet(this, _outroing).add(k);
          pause_effect(effect, on_destroy, false);
        } else {
          on_destroy();
        }
      }
    });
    /**
     * @param {Batch} batch
     */
    __privateAdd(this, _discard, (batch) => {
      __privateGet(this, _batches).delete(batch);
      const keys = Array.from(__privateGet(this, _batches).values());
      for (const [k, branch2] of __privateGet(this, _offscreen)) {
        if (!keys.includes(k)) {
          destroy_effect(branch2.effect);
          __privateGet(this, _offscreen).delete(k);
        }
      }
    });
    this.anchor = anchor;
    __privateSet(this, _transition, transition);
  }
  /**
   *
   * @param {any} key
   * @param {null | ((target: TemplateNode) => void)} fn
   */
  ensure(key, fn) {
    var batch = (
      /** @type {Batch} */
      current_batch
    );
    var defer = should_defer_append();
    if (fn && !__privateGet(this, _onscreen).has(key) && !__privateGet(this, _offscreen).has(key)) {
      if (defer) {
        var fragment = document.createDocumentFragment();
        var target = create_text();
        fragment.append(target);
        __privateGet(this, _offscreen).set(key, {
          effect: branch(() => fn(target)),
          fragment
        });
      } else {
        __privateGet(this, _onscreen).set(
          key,
          branch(() => fn(this.anchor))
        );
      }
    }
    __privateGet(this, _batches).set(batch, key);
    if (defer) {
      for (const [k, effect] of __privateGet(this, _onscreen)) {
        if (k === key) {
          batch.unskip_effect(effect);
        } else {
          batch.skip_effect(effect);
        }
      }
      for (const [k, branch2] of __privateGet(this, _offscreen)) {
        if (k === key) {
          batch.unskip_effect(branch2.effect);
        } else {
          batch.skip_effect(branch2.effect);
        }
      }
      batch.oncommit(__privateGet(this, _commit));
      batch.ondiscard(__privateGet(this, _discard));
    } else {
      __privateGet(this, _commit).call(this, batch);
    }
  }
}
_batches = new WeakMap();
_onscreen = new WeakMap();
_offscreen = new WeakMap();
_outroing = new WeakMap();
_transition = new WeakMap();
_commit = new WeakMap();
_discard = new WeakMap();
function if_block(node, fn, elseif = false) {
  var branches = new BranchManager(node);
  var flags2 = elseif ? EFFECT_TRANSPARENT : 0;
  function update_branch(key, fn2) {
    branches.ensure(key, fn2);
  }
  block(() => {
    var has_branch = false;
    fn((fn2, key = 0) => {
      has_branch = true;
      update_branch(key, fn2);
    });
    if (!has_branch) {
      update_branch(-1, null);
    }
  }, flags2);
}
function index(_, i) {
  return i;
}
function pause_effects(state2, to_destroy, controlled_anchor) {
  var transitions = [];
  var length = to_destroy.length;
  var group;
  var remaining = to_destroy.length;
  for (var i = 0; i < length; i++) {
    let effect = to_destroy[i];
    pause_effect(
      effect,
      () => {
        if (group) {
          group.pending.delete(effect);
          group.done.add(effect);
          if (group.pending.size === 0) {
            var groups = (
              /** @type {Set<EachOutroGroup>} */
              state2.outrogroups
            );
            destroy_effects(state2, array_from(group.done));
            groups.delete(group);
            if (groups.size === 0) {
              state2.outrogroups = null;
            }
          }
        } else {
          remaining -= 1;
        }
      },
      false
    );
  }
  if (remaining === 0) {
    var fast_path = transitions.length === 0 && controlled_anchor !== null && state2.pending.size === 0;
    if (fast_path) {
      var anchor = (
        /** @type {Element} */
        controlled_anchor
      );
      var parent_node = (
        /** @type {Element} */
        anchor.parentNode
      );
      clear_text_content(parent_node);
      parent_node.append(anchor);
      state2.items.clear();
    }
    destroy_effects(state2, to_destroy, !fast_path);
  } else {
    group = {
      pending: new Set(to_destroy),
      done: /* @__PURE__ */ new Set()
    };
    (state2.outrogroups ?? (state2.outrogroups = /* @__PURE__ */ new Set())).add(group);
  }
}
function destroy_effects(state2, to_destroy, remove_dom = true) {
  var preserved_effects;
  if (state2.pending.size > 0) {
    preserved_effects = /* @__PURE__ */ new Set();
    for (const keys of state2.pending.values()) {
      for (const key of keys) {
        preserved_effects.add(
          /** @type {EachItem} */
          state2.items.get(key).e
        );
      }
    }
  }
  for (var i = 0; i < to_destroy.length; i++) {
    var e = to_destroy[i];
    if (preserved_effects == null ? void 0 : preserved_effects.has(e)) {
      e.f |= EFFECT_OFFSCREEN;
      const fragment = document.createDocumentFragment();
      move_effect(e, fragment);
    } else {
      destroy_effect(to_destroy[i], remove_dom);
    }
  }
}
var offscreen_anchor;
function each(node, flags2, get_collection, get_key, render_fn2, fallback_fn = null) {
  var anchor = node;
  var items = /* @__PURE__ */ new Map();
  var is_controlled = (flags2 & EACH_IS_CONTROLLED) !== 0;
  if (is_controlled) {
    var parent_node = (
      /** @type {Element} */
      node
    );
    anchor = parent_node.appendChild(create_text());
  }
  var fallback = null;
  var each_array = /* @__PURE__ */ derived_safe_equal(() => {
    var collection = get_collection();
    return (
      /** @type {V[]} */
      is_array(collection) ? collection : collection == null ? [] : array_from(collection)
    );
  });
  var array;
  var pending = /* @__PURE__ */ new Map();
  var first_run = true;
  function commit(batch) {
    if ((state2.effect.f & DESTROYED) !== 0) {
      return;
    }
    state2.pending.delete(batch);
    state2.fallback = fallback;
    reconcile(state2, array, anchor, flags2, get_key);
    if (fallback !== null) {
      if (array.length === 0) {
        if ((fallback.f & EFFECT_OFFSCREEN) === 0) {
          resume_effect(fallback);
        } else {
          fallback.f ^= EFFECT_OFFSCREEN;
          move(fallback, null, anchor);
        }
      } else {
        pause_effect(fallback, () => {
          fallback = null;
        });
      }
    }
  }
  function discard(batch) {
    state2.pending.delete(batch);
  }
  var effect = block(() => {
    array = /** @type {V[]} */
    get(each_array);
    var length = array.length;
    var keys = /* @__PURE__ */ new Set();
    var batch = (
      /** @type {Batch} */
      current_batch
    );
    var defer = should_defer_append();
    for (var index2 = 0; index2 < length; index2 += 1) {
      var value = array[index2];
      var key = get_key(value, index2);
      var item = first_run ? null : items.get(key);
      if (item) {
        if (item.v) internal_set(item.v, value);
        if (item.i) internal_set(item.i, index2);
        if (defer) {
          batch.unskip_effect(item.e);
        }
      } else {
        item = create_item(
          items,
          first_run ? anchor : offscreen_anchor ?? (offscreen_anchor = create_text()),
          value,
          key,
          index2,
          render_fn2,
          flags2,
          get_collection
        );
        if (!first_run) {
          item.e.f |= EFFECT_OFFSCREEN;
        }
        items.set(key, item);
      }
      keys.add(key);
    }
    if (length === 0 && fallback_fn && !fallback) {
      if (first_run) {
        fallback = branch(() => fallback_fn(anchor));
      } else {
        fallback = branch(() => fallback_fn(offscreen_anchor ?? (offscreen_anchor = create_text())));
        fallback.f |= EFFECT_OFFSCREEN;
      }
    }
    if (length > keys.size) {
      {
        each_key_duplicate();
      }
    }
    if (!first_run) {
      pending.set(batch, keys);
      if (defer) {
        for (const [key2, item2] of items) {
          if (!keys.has(key2)) {
            batch.skip_effect(item2.e);
          }
        }
        batch.oncommit(commit);
        batch.ondiscard(discard);
      } else {
        commit(batch);
      }
    }
    get(each_array);
  });
  var state2 = { effect, items, pending, outrogroups: null, fallback };
  first_run = false;
}
function skip_to_branch(effect) {
  while (effect !== null && (effect.f & BRANCH_EFFECT) === 0) {
    effect = effect.next;
  }
  return effect;
}
function reconcile(state2, array, anchor, flags2, get_key) {
  var _a2, _b2, _c2, _d, _e, _f, _g, _h, _i;
  var is_animated = (flags2 & EACH_IS_ANIMATED) !== 0;
  var length = array.length;
  var items = state2.items;
  var current = skip_to_branch(state2.effect.first);
  var seen;
  var prev = null;
  var to_animate;
  var matched = [];
  var stashed = [];
  var value;
  var key;
  var effect;
  var i;
  if (is_animated) {
    for (i = 0; i < length; i += 1) {
      value = array[i];
      key = get_key(value, i);
      effect = /** @type {EachItem} */
      items.get(key).e;
      if ((effect.f & EFFECT_OFFSCREEN) === 0) {
        (_b2 = (_a2 = effect.nodes) == null ? void 0 : _a2.a) == null ? void 0 : _b2.measure();
        (to_animate ?? (to_animate = /* @__PURE__ */ new Set())).add(effect);
      }
    }
  }
  for (i = 0; i < length; i += 1) {
    value = array[i];
    key = get_key(value, i);
    effect = /** @type {EachItem} */
    items.get(key).e;
    if (state2.outrogroups !== null) {
      for (const group of state2.outrogroups) {
        group.pending.delete(effect);
        group.done.delete(effect);
      }
    }
    if ((effect.f & INERT) !== 0) {
      resume_effect(effect);
      if (is_animated) {
        (_d = (_c2 = effect.nodes) == null ? void 0 : _c2.a) == null ? void 0 : _d.unfix();
        (to_animate ?? (to_animate = /* @__PURE__ */ new Set())).delete(effect);
      }
    }
    if ((effect.f & EFFECT_OFFSCREEN) !== 0) {
      effect.f ^= EFFECT_OFFSCREEN;
      if (effect === current) {
        move(effect, null, anchor);
      } else {
        var next = prev ? prev.next : current;
        if (effect === state2.effect.last) {
          state2.effect.last = effect.prev;
        }
        if (effect.prev) effect.prev.next = effect.next;
        if (effect.next) effect.next.prev = effect.prev;
        link(state2, prev, effect);
        link(state2, effect, next);
        move(effect, next, anchor);
        prev = effect;
        matched = [];
        stashed = [];
        current = skip_to_branch(prev.next);
        continue;
      }
    }
    if (effect !== current) {
      if (seen !== void 0 && seen.has(effect)) {
        if (matched.length < stashed.length) {
          var start = stashed[0];
          var j;
          prev = start.prev;
          var a = matched[0];
          var b = matched[matched.length - 1];
          for (j = 0; j < matched.length; j += 1) {
            move(matched[j], start, anchor);
          }
          for (j = 0; j < stashed.length; j += 1) {
            seen.delete(stashed[j]);
          }
          link(state2, a.prev, b.next);
          link(state2, prev, a);
          link(state2, b, start);
          current = start;
          prev = b;
          i -= 1;
          matched = [];
          stashed = [];
        } else {
          seen.delete(effect);
          move(effect, current, anchor);
          link(state2, effect.prev, effect.next);
          link(state2, effect, prev === null ? state2.effect.first : prev.next);
          link(state2, prev, effect);
          prev = effect;
        }
        continue;
      }
      matched = [];
      stashed = [];
      while (current !== null && current !== effect) {
        (seen ?? (seen = /* @__PURE__ */ new Set())).add(current);
        stashed.push(current);
        current = skip_to_branch(current.next);
      }
      if (current === null) {
        continue;
      }
    }
    if ((effect.f & EFFECT_OFFSCREEN) === 0) {
      matched.push(effect);
    }
    prev = effect;
    current = skip_to_branch(effect.next);
  }
  if (state2.outrogroups !== null) {
    for (const group of state2.outrogroups) {
      if (group.pending.size === 0) {
        destroy_effects(state2, array_from(group.done));
        (_e = state2.outrogroups) == null ? void 0 : _e.delete(group);
      }
    }
    if (state2.outrogroups.size === 0) {
      state2.outrogroups = null;
    }
  }
  if (current !== null || seen !== void 0) {
    var to_destroy = [];
    if (seen !== void 0) {
      for (effect of seen) {
        if ((effect.f & INERT) === 0) {
          to_destroy.push(effect);
        }
      }
    }
    while (current !== null) {
      if ((current.f & INERT) === 0 && current !== state2.fallback) {
        to_destroy.push(current);
      }
      current = skip_to_branch(current.next);
    }
    var destroy_length = to_destroy.length;
    if (destroy_length > 0) {
      var controlled_anchor = (flags2 & EACH_IS_CONTROLLED) !== 0 && length === 0 ? anchor : null;
      if (is_animated) {
        for (i = 0; i < destroy_length; i += 1) {
          (_g = (_f = to_destroy[i].nodes) == null ? void 0 : _f.a) == null ? void 0 : _g.measure();
        }
        for (i = 0; i < destroy_length; i += 1) {
          (_i = (_h = to_destroy[i].nodes) == null ? void 0 : _h.a) == null ? void 0 : _i.fix();
        }
      }
      pause_effects(state2, to_destroy, controlled_anchor);
    }
  }
  if (is_animated) {
    queue_micro_task(() => {
      var _a3, _b3;
      if (to_animate === void 0) return;
      for (effect of to_animate) {
        (_b3 = (_a3 = effect.nodes) == null ? void 0 : _a3.a) == null ? void 0 : _b3.apply();
      }
    });
  }
}
function create_item(items, anchor, value, key, index2, render_fn2, flags2, get_collection) {
  var v = (flags2 & EACH_ITEM_REACTIVE) !== 0 ? (flags2 & EACH_ITEM_IMMUTABLE) === 0 ? /* @__PURE__ */ mutable_source(value, false, false) : source(value) : null;
  var i = (flags2 & EACH_INDEX_REACTIVE) !== 0 ? source(index2) : null;
  return {
    v,
    i,
    e: branch(() => {
      render_fn2(anchor, v ?? value, i ?? index2, get_collection);
      return () => {
        items.delete(key);
      };
    })
  };
}
function move(effect, next, anchor) {
  if (!effect.nodes) return;
  var node = effect.nodes.start;
  var end = effect.nodes.end;
  var dest = next && (next.f & EFFECT_OFFSCREEN) === 0 ? (
    /** @type {EffectNodes} */
    next.nodes.start
  ) : anchor;
  while (node !== null) {
    var next_node = (
      /** @type {TemplateNode} */
      /* @__PURE__ */ get_next_sibling(node)
    );
    dest.before(node);
    if (node === end) {
      return;
    }
    node = next_node;
  }
}
function link(state2, prev, next) {
  if (prev === null) {
    state2.effect.first = next;
  } else {
    prev.next = next;
  }
  if (next === null) {
    state2.effect.last = prev;
  } else {
    next.prev = prev;
  }
}
function head(hash, render_fn2) {
  var anchor;
  {
    anchor = document.head.appendChild(create_text());
  }
  try {
    block(() => {
      var e = branch(() => render_fn2(anchor));
      e.f |= HEAD_EFFECT;
    });
  } finally {
  }
}
function r(e) {
  var t, f, n = "";
  if ("string" == typeof e || "number" == typeof e) n += e;
  else if ("object" == typeof e) if (Array.isArray(e)) {
    var o = e.length;
    for (t = 0; t < o; t++) e[t] && (f = r(e[t])) && (n && (n += " "), n += f);
  } else for (f in e) e[f] && (n && (n += " "), n += f);
  return n;
}
function clsx$1() {
  for (var e, t, f = 0, n = "", o = arguments.length; f < o; f++) (e = arguments[f]) && (t = r(e)) && (n && (n += " "), n += t);
  return n;
}
function clsx(value) {
  if (typeof value === "object") {
    return clsx$1(value);
  } else {
    return value ?? "";
  }
}
const whitespace = [..." 	\n\r\f \v\uFEFF"];
function to_class(value, hash, directives) {
  var classname = value == null ? "" : "" + value;
  if (hash) {
    classname = classname ? classname + " " + hash : hash;
  }
  if (directives) {
    for (var key of Object.keys(directives)) {
      if (directives[key]) {
        classname = classname ? classname + " " + key : key;
      } else if (classname.length) {
        var len = key.length;
        var a = 0;
        while ((a = classname.indexOf(key, a)) >= 0) {
          var b = a + len;
          if ((a === 0 || whitespace.includes(classname[a - 1])) && (b === classname.length || whitespace.includes(classname[b]))) {
            classname = (a === 0 ? "" : classname.substring(0, a)) + classname.substring(b + 1);
          } else {
            a = b;
          }
        }
      }
    }
  }
  return classname === "" ? null : classname;
}
function set_class(dom, is_html, value, hash, prev_classes, next_classes) {
  var prev = (
    /** @type {any} */
    dom[CLASS_CACHE]
  );
  if (prev !== value || prev === void 0) {
    var next_class_name = to_class(value, hash, next_classes);
    {
      if (next_class_name == null) {
        dom.removeAttribute("class");
      } else {
        dom.className = next_class_name;
      }
    }
    dom[CLASS_CACHE] = value;
  } else if (next_classes && prev_classes !== next_classes) {
    for (var key in next_classes) {
      var is_present = !!next_classes[key];
      if (prev_classes == null || is_present !== !!prev_classes[key]) {
        dom.classList.toggle(key, is_present);
      }
    }
  }
  return next_classes;
}
function select_option(select, value, mounting = false) {
  if (select.multiple) {
    if (value == void 0) {
      return;
    }
    if (!is_array(value)) {
      return select_multiple_invalid_value();
    }
    for (var option of select.options) {
      option.selected = value.includes(get_option_value(option));
    }
    return;
  }
  for (option of select.options) {
    var option_value = get_option_value(option);
    if (is(option_value, value)) {
      option.selected = true;
      return;
    }
  }
  if (!mounting || value !== void 0) {
    select.selectedIndex = -1;
  }
}
function init_select(select) {
  var observer = new MutationObserver(() => {
    if ("__value" in select) {
      select_option(select, select.__value);
    }
  });
  observer.observe(select, {
    // Listen to option element changes
    childList: true,
    subtree: true,
    // because of <optgroup>
    // Listen to option element value attribute changes
    // (doesn't get notified of select value changes,
    // because that property is not reflected as an attribute)
    attributes: true,
    attributeFilter: ["value"]
  });
  teardown(() => {
    observer.disconnect();
  });
}
function get_option_value(option) {
  if ("__value" in option) {
    return option.__value;
  } else {
    return option.value;
  }
}
const IS_CUSTOM_ELEMENT = Symbol("is custom element");
const IS_HTML = Symbol("is html");
const PROGRESS_TAG = IS_XHTML ? "progress" : "PROGRESS";
function set_value(element, value) {
  var attributes = get_attributes(element);
  if (attributes.value === (attributes.value = // treat null and undefined the same for the initial value
  value ?? void 0) || // @ts-expect-error
  // `progress` elements always need their value set when it's `0`
  element.value === value && (value !== 0 || element.nodeName !== PROGRESS_TAG)) {
    return;
  }
  element.value = value ?? "";
}
function set_checked(element, checked) {
  var attributes = get_attributes(element);
  if (attributes.checked === (attributes.checked = // treat null and undefined the same for the initial value
  checked ?? void 0)) {
    return;
  }
  element.checked = checked;
}
function set_attribute(element, attribute, value, skip_warning) {
  var attributes = get_attributes(element);
  if (attributes[attribute] === (attributes[attribute] = value)) return;
  if (attribute === "loading") {
    element[LOADING_ATTR_SYMBOL] = value;
  }
  if (value == null) {
    element.removeAttribute(attribute);
  } else if (typeof value !== "string" && get_setters(element).includes(attribute)) {
    element[attribute] = value;
  } else {
    element.setAttribute(attribute, value);
  }
}
function get_attributes(element) {
  return (
    /** @type {Record<string | symbol, unknown>} **/
    /** @type {any} */
    element[ATTRIBUTES_CACHE] ?? (element[ATTRIBUTES_CACHE] = {
      [IS_CUSTOM_ELEMENT]: element.nodeName.includes("-"),
      [IS_HTML]: element.namespaceURI === NAMESPACE_HTML
    })
  );
}
var setters_cache = /* @__PURE__ */ new Map();
function get_setters(element) {
  var cache_key = element.getAttribute("is") || element.nodeName;
  var setters = setters_cache.get(cache_key);
  if (setters) return setters;
  setters_cache.set(cache_key, setters = []);
  var descriptors;
  var proto = element;
  var element_proto = Element.prototype;
  while (element_proto !== proto) {
    descriptors = get_descriptors(proto);
    for (var key in descriptors) {
      if (descriptors[key].set && // better safe than sorry, we don't want spread attributes to mess with HTML content
      key !== "innerHTML" && key !== "textContent" && key !== "innerText") {
        setters.push(key);
      }
    }
    proto = get_prototype_of(proto);
  }
  return setters;
}
function bind_checked(input, get2, set2 = get2) {
  listen_to_event_and_reset_event(input, "change", (is_reset) => {
    var value = is_reset ? input.defaultChecked : input.checked;
    set2(value);
  });
  if (
    // If we are hydrating and the value has since changed,
    // then use the update value from the input instead.
    // If defaultChecked is set, then checked == defaultChecked
    untrack(get2) == null
  ) {
    set2(input.checked);
  }
  render_effect(() => {
    var value = get2();
    input.checked = Boolean(value);
  });
}
function prop(props, key, flags2, fallback) {
  var fallback_value = (
    /** @type {V} */
    fallback
  );
  var fallback_dirty = true;
  var get_fallback = () => {
    if (fallback_dirty) {
      fallback_dirty = false;
      fallback_value = /** @type {V} */
      fallback;
    }
    return fallback_value;
  };
  var initial_value;
  {
    initial_value = /** @type {V} */
    props[key];
  }
  if (initial_value === void 0 && fallback !== void 0) {
    initial_value = get_fallback();
  }
  var getter;
  {
    getter = () => {
      var value = (
        /** @type {V} */
        props[key]
      );
      if (value === void 0) return get_fallback();
      fallback_dirty = true;
      return value;
    };
  }
  {
    return getter;
  }
}
const PUBLIC_VERSION = "5";
if (typeof window !== "undefined") {
  ((_c = window.__svelte ?? (window.__svelte = {})).v ?? (_c.v = /* @__PURE__ */ new Set())).add(PUBLIC_VERSION);
}
var root$3 = /* @__PURE__ */ from_html(`<button class="quiet-button stop-button">Apply ausschalten</button>`);
var root_1$3 = /* @__PURE__ */ from_html(`<p class="hint">Apply AN kann unmittelbar eine Fahrt der aktuellen Entscheidung auslösen. Legacy zuerst deaktivieren, HA neu starten und Null-Writer bestätigen.</p> <label class="toggle"><input type="checkbox"/>Legacy ist deaktiviert, HA neu gestartet und Null-Writer geprüft. Ich gebe die kontrollierte Fahrt frei.</label> <button class="primary-button">Apply bewusst einschalten</button>`, 1);
var root_2$3 = /* @__PURE__ */ from_html(`<p class="hint warning"> </p>`);
var root_3$3 = /* @__PURE__ */ from_html(`<p class="hint" role="status">Betriebswechsel wird geladen. Auf bestätigten Zustand warten.</p>`);
var root_4$1 = /* @__PURE__ */ from_html(`<p class="error" role="alert"> </p>`);
var root_5$1 = /* @__PURE__ */ from_html(`<article class="card operation-card" aria-label="Betrieb"><div class="card-heading"><div><p class="eyebrow">BETRIEB</p><h2>Writer kontrolliert freigeben</h2></div><span class="badge"> </span></div> <dl class="facts"><div><dt>Betriebsmodus</dt><dd> </dd></div> <div><dt>Writer-Zuständigkeit</dt><dd> </dd></div> <div><dt>Readiness / Ruhebaseline</dt><dd> </dd></div> <div><dt>Opening Safety</dt><dd> </dd></div> <div><dt>Schreibpfad erreichbar</dt><dd> </dd></div> <div><dt>Apply-Grund</dt><dd> </dd></div></dl> <div class="button-row"><button class="quiet-button">Shadow + Legacy · Apply AUS</button> <button class="quiet-button">Live + Blind Control · Apply AUS</button></div> <!> <!> <!> <!></article>`);
function Operation($$anchor, $$props) {
  push($$props, true);
  let confirmed = /* @__PURE__ */ state(false);
  let busy = /* @__PURE__ */ state(false);
  let error = /* @__PURE__ */ state("");
  let staged = /* @__PURE__ */ user_derived(() => $$props.snapshot.settings.runtime_mode === "live" && $$props.snapshot.settings.apply_owner === "blind_control" && !$$props.snapshot.settings.apply_enabled);
  let blocked = /* @__PURE__ */ user_derived(() => !$$props.onOperation || !$$props.snapshot.operation || $$props.snapshot.operation.pending || get(busy));
  async function change(mode, owner, apply) {
    if (!$$props.onOperation) return;
    set(busy, true);
    set(error, "");
    try {
      await $$props.onOperation(mode, owner, apply, get(confirmed));
      set(confirmed, false);
    } catch (cause) {
      set(error, cause instanceof Error ? cause.message : "Betriebswechsel fehlgeschlagen", true);
    } finally {
      set(busy, false);
    }
  }
  var article = root_5$1();
  var div = child(article);
  var span = sibling(child(div));
  var text = child(span);
  var dl = sibling(div, 2);
  var div_1 = child(dl);
  var dd = sibling(child(div_1));
  var text_1 = child(dd);
  var div_2 = sibling(div_1, 2);
  var dd_1 = sibling(child(div_2));
  var text_2 = child(dd_1);
  var div_3 = sibling(div_2, 2);
  var dd_2 = sibling(child(div_3));
  var text_3 = child(dd_2);
  var div_4 = sibling(div_3, 2);
  var dd_3 = sibling(child(div_4));
  var text_4 = child(dd_3);
  var div_5 = sibling(div_4, 2);
  var dd_4 = sibling(child(div_5));
  var text_5 = child(dd_4);
  var div_6 = sibling(div_5, 2);
  var dd_5 = sibling(child(div_6));
  var text_6 = child(dd_5);
  var div_7 = sibling(dl, 2);
  var button = child(div_7);
  var button_1 = sibling(button, 2);
  var node = sibling(div_7, 2);
  {
    var consequent = ($$anchor2) => {
      var button_2 = root$3();
      template_effect(() => button_2.disabled = get(blocked));
      delegated("click", button_2, () => change($$props.snapshot.settings.runtime_mode, $$props.snapshot.settings.apply_owner, false));
      append($$anchor2, button_2);
    };
    var consequent_1 = ($$anchor2) => {
      var fragment = root_1$3();
      var label = sibling(first_child(fragment), 2);
      var input = child(label);
      var button_3 = sibling(label, 2);
      template_effect(() => {
        var _a2;
        input.disabled = get(blocked);
        button_3.disabled = get(blocked) || !get(confirmed) || !!((_a2 = $$props.snapshot.operation) == null ? void 0 : _a2.legacy_blocker);
      });
      bind_checked(input, () => get(confirmed), ($$value) => set(confirmed, $$value));
      delegated("click", button_3, () => change("live", "blind_control", true));
      append($$anchor2, fragment);
    };
    if_block(node, ($$render) => {
      if ($$props.snapshot.settings.apply_enabled) $$render(consequent);
      else if (get(staged)) $$render(consequent_1, 1);
    });
  }
  var node_1 = sibling(node, 2);
  {
    var consequent_2 = ($$anchor2) => {
      var p = root_2$3();
      var text_7 = child(p);
      template_effect(($0) => set_text(text_7, `Freigabe gesperrt: ${$0 ?? ""}`), [
        () => $$props.snapshot.operation.legacy_blocker.replaceAll("_", " ")
      ]);
      append($$anchor2, p);
    };
    if_block(node_1, ($$render) => {
      var _a2;
      if ((_a2 = $$props.snapshot.operation) == null ? void 0 : _a2.legacy_blocker) $$render(consequent_2);
    });
  }
  var node_2 = sibling(node_1, 2);
  {
    var consequent_3 = ($$anchor2) => {
      var p_1 = root_3$3();
      append($$anchor2, p_1);
    };
    if_block(node_2, ($$render) => {
      var _a2;
      if ((_a2 = $$props.snapshot.operation) == null ? void 0 : _a2.pending) $$render(consequent_3);
    });
  }
  var node_3 = sibling(node_2, 2);
  {
    var consequent_4 = ($$anchor2) => {
      var p_2 = root_4$1();
      var text_8 = child(p_2);
      template_effect(() => set_text(text_8, get(error)));
      append($$anchor2, p_2);
    };
    if_block(node_3, ($$render) => {
      if (get(error)) $$render(consequent_4);
    });
  }
  template_effect(
    ($0) => {
      set_text(text, `Apply ${$$props.snapshot.settings.apply_enabled ? "AN" : "AUS"}`);
      set_text(text_1, $$props.snapshot.settings.runtime_mode === "shadow" ? "Shadow" : "Live");
      set_text(text_2, $$props.snapshot.settings.apply_owner === "legacy" ? "Legacy" : "Blind Control");
      set_text(text_3, `${$$props.snapshot.overview.baseline_ready ? "bestätigt" : "wartet"} · ${$$props.snapshot.overview.apply_status ?? ""}`);
      set_text(text_4, `${$$props.snapshot.overview.opening_state ?? ""} · ${$$props.snapshot.overview.safety_status ?? ""}`);
      set_text(text_5, $$props.snapshot.overview.write_path_reachable ? "ja" : "nein");
      set_text(text_6, $0);
      button.disabled = get(blocked);
      button_1.disabled = get(blocked);
    },
    [
      () => String($$props.snapshot.overview.technical.apply.reason ?? "—").replaceAll("_", " ")
    ]
  );
  delegated("click", button, () => change("shadow", "legacy", false));
  delegated("click", button_1, () => change("live", "blind_control", false));
  append($$anchor, article);
  pop();
}
delegate(["click"]);
var root$2 = /* @__PURE__ */ from_html(`<p class="callout warning"> </p>`);
var root_1$2 = /* @__PURE__ */ from_html(`<p class="hint">Shadow berechnet dieses Ziel. Blind Control steuert die reale Position noch nicht.</p>`);
var root_2$2 = /* @__PURE__ */ from_html(`<div class="rule"><strong> </strong><p> </p></div>`);
var root_3$2 = /* @__PURE__ */ from_html(`<article class="card hero-card span-2"><p class="eyebrow">WARUM DIESE POSITION?</p> <h2> </h2> <div class="target-row"><strong class="target-value"> </strong><span class="muted"> </span></div> <p class="decision-reason"> </p> <div class="metric-strip"><div><span>Aktivität</span><strong> </strong></div> <div><span>Opening</span><strong> </strong></div> <div><span>Solar</span><strong> </strong></div> <div><span>Außenhelligkeit</span><strong> </strong></div> <div><span>Außentemperatur</span><strong> </strong></div> <div><span>Aktuelles Ziel</span><strong> </strong></div></div> <!> <!></article> <article class="card span-2"><p class="eyebrow">HAUPTREGELN</p><h2>Was greift — und was nicht?</h2> <div class="rule-grid"></div></article>`, 1);
function Overview($$anchor, $$props) {
  push($$props, true);
  const names = {
    normal: "Regulär",
    manual: "Manuell gehalten",
    failure: "Entscheidung blockiert",
    heat: "Hitzeschutz",
    cold: "Kälteschutz",
    glare: "Blendschutz",
    privacy: "Privacy",
    waking: "Aufwachen",
    sleep: "Schlaf",
    away: "Abwesend",
    low_light: "low_light · geringe Solarenergie"
  };
  const reasons = {
    thermal_load_below_configured_band: "Temperaturschwelle nicht erreicht",
    solar_exposure_not_relevant_for_heat: "Keine relevante Solarenergie für Hitzeschutz",
    solar_confidence_below_configured_band: "Solar-Evidence nicht ausreichend sicher",
    thermal_load_with_window_solar_relevance: "Temperatur und Solarenergie erfordern Schutz",
    heat_temperature_not_fresh: "Belastbare Temperaturevidence fehlt",
    storm_approaching_relaxes_heat: "Gewitterregel entlastet Hitzeschutz",
    environment_enter_pending: "Schutzbedingung wird stabilisiert",
    environment_exit_pending: "Entlastung wird stabilisiert",
    cold_insulation_conditions_not_met: "Kälte-/Dunkelheitsbedingungen nicht erfüllt",
    dark_cold_without_solar_gain: "Dunkel und kalt, ohne relevanten Solargewinn",
    privacy_not_active: "Kanonischer Privacy-State nicht aktiv",
    privacy_active: "Kanonischer Privacy-State aktiv",
    private_time_active: "Private Zeit aktiv",
    private_time_not_active: "Private Zeit nicht aktiv"
  };
  const label = (value) => value ? names[value] ?? value.replaceAll("_", " ") : "—";
  const position = (value) => value === null ? "unbekannt" : `${Math.round(value)} %`;
  const metric = (key, unit) => $$props.snapshot.overview.environment_values[key] === null ? "nicht belastbar" : `${$$props.snapshot.overview.environment_values[key]} ${unit}`;
  function explanation(key) {
    const candidate = $$props.snapshot.diagnosis.candidates.find((item) => item.key === key);
    if (!candidate) return "Im aktuellen exklusiven Modus nicht bewertet";
    if (candidate.paused) return `Pausiert durch ${label(candidate.suppressed_by)}`;
    if (candidate.quality !== "fresh") return "Erforderliche Evidence nicht belastbar";
    return reasons[candidate.reason] ?? (candidate.reason.includes("without_window_solar") ? "Solar/Lux für Blendschutz nicht ausreichend" : candidate.reason.startsWith("no_") ? "Keine passende Bildschirmaktivität" : candidate.active ? "Schutzanforderung aktiv" : "Bedingungen nicht erfüllt");
  }
  var fragment = root_3$2();
  var article = first_child(fragment);
  var h2 = sibling(child(article), 2);
  var text = child(h2);
  var div = sibling(h2, 2);
  var strong = child(div);
  var text_1 = child(strong);
  var span = sibling(strong);
  var text_2 = child(span);
  var p = sibling(div, 2);
  var text_3 = child(p);
  var div_1 = sibling(p, 2);
  var div_2 = child(div_1);
  var strong_1 = sibling(child(div_2));
  var text_4 = child(strong_1);
  var div_3 = sibling(div_2, 2);
  var strong_2 = sibling(child(div_3));
  var text_5 = child(strong_2);
  var div_4 = sibling(div_3, 2);
  var strong_3 = sibling(child(div_4));
  var text_6 = child(strong_3);
  var div_5 = sibling(div_4, 2);
  var strong_4 = sibling(child(div_5));
  var text_7 = child(strong_4);
  var div_6 = sibling(div_5, 2);
  var strong_5 = sibling(child(div_6));
  var text_8 = child(strong_5);
  var div_7 = sibling(div_6, 2);
  var strong_6 = sibling(child(div_7));
  var text_9 = child(strong_6);
  var node = sibling(div_1, 2);
  {
    var consequent = ($$anchor2) => {
      var p_1 = root$2();
      var text_10 = child(p_1);
      template_effect(($0) => set_text(text_10, `Automatik blockiert: ${$0 ?? ""}. Kein normales Ziel freigegeben.`), [
        () => $$props.snapshot.overview.failure.quality_blockers.map((item) => `${label(item.key)} (${label(item.quality)})`).join(", ") || label($$props.snapshot.overview.failure.reason)
      ]);
      append($$anchor2, p_1);
    };
    if_block(node, ($$render) => {
      if ($$props.snapshot.overview.failure.status !== "none") $$render(consequent);
    });
  }
  var node_1 = sibling(node, 2);
  {
    var consequent_1 = ($$anchor2) => {
      var p_2 = root_1$2();
      append($$anchor2, p_2);
    };
    if_block(node_1, ($$render) => {
      if ($$props.snapshot.settings.runtime_mode === "shadow") $$render(consequent_1);
    });
  }
  var article_1 = sibling(article, 2);
  var div_8 = sibling(child(article_1), 3);
  each(
    div_8,
    20,
    () => [
      ["heat_protection", "Heat"],
      ["glare_pc", "Glare · PC"],
      ["glare_tv", "Glare · TV"],
      ["cold_insulation", "Cold"],
      ["privacy", "Privacy"],
      ["private_time", "Private Zeit"]
    ],
    index,
    ($$anchor2, $$item) => {
      var $$array = /* @__PURE__ */ user_derived(() => to_array($$item, 2));
      let key = () => get($$array)[0];
      let title = () => get($$array)[1];
      var div_9 = root_2$2();
      var strong_7 = child(div_9);
      var text_11 = child(strong_7);
      var p_3 = sibling(strong_7);
      var text_12 = child(p_3);
      template_effect(
        ($0) => {
          set_text(text_11, title());
          set_text(text_12, $0);
        },
        [() => explanation(key())]
      );
      append($$anchor2, div_9);
    }
  );
  template_effect(
    ($0, $1, $2, $3, $4, $5, $6, $7, $8) => {
      set_text(text, `Rollo ${$$props.snapshot.overview.environment_values.cover_motion === "idle" ? "steht" : "ist"} bei`);
      set_text(text_1, $0);
      set_text(text_2, `Istposition · ${$1 ?? ""}`);
      set_text(text_3, `Grund: ${$2 ?? ""}${$3 ?? ""}`);
      set_text(text_4, $4);
      set_text(text_5, $$props.snapshot.overview.opening_state);
      set_text(text_6, $5);
      set_text(text_7, $6);
      set_text(text_8, $7);
      set_text(text_9, $8);
    },
    [
      () => position($$props.snapshot.overview.cover_position),
      () => label(String($$props.snapshot.overview.environment_values.cover_motion ?? "unknown")),
      () => label($$props.snapshot.overview.master_mode),
      () => $$props.snapshot.overview.winner ? ` · ${label($$props.snapshot.overview.winner.variant ?? $$props.snapshot.overview.winner.category)}` : "",
      () => label($$props.snapshot.overview.household.activity_state),
      () => label($$props.snapshot.diagnosis.solar.state),
      () => metric("outdoor_lux", "lx"),
      () => metric("outdoor_temperature", "°C"),
      () => position($$props.snapshot.overview.effective_target)
    ]
  );
  append($$anchor, fragment);
  pop();
}
function cloneSettings(value) {
  return (
    /** @type {T} */
    detachJsonValue(value)
  );
}
function settingsRevision(settings) {
  return JSON.stringify(canonicalize(settings));
}
function rebaseDraft(draftSettings, confirmedRevision, incomingSettings) {
  const incomingRevision = settingsRevision(incomingSettings);
  if (incomingRevision === confirmedRevision) {
    return {
      draftSettings,
      confirmedRevision,
      dirty: isDraftDirty(draftSettings, confirmedRevision),
      adopted: false
    };
  }
  if (draftSettings && isDraftDirty(draftSettings, confirmedRevision)) {
    return {
      draftSettings,
      confirmedRevision: incomingRevision,
      dirty: isDraftDirty(draftSettings, incomingRevision),
      adopted: false
    };
  }
  return {
    draftSettings: cloneSettings(incomingSettings),
    confirmedRevision: incomingRevision,
    dirty: false,
    adopted: true
  };
}
function settleSave(draftSettings, confirmedRevision, confirmedSettings) {
  if (!confirmedSettings) {
    return { draftSettings, confirmedRevision, saved: false };
  }
  return {
    draftSettings: cloneSettings(confirmedSettings),
    confirmedRevision: settingsRevision(confirmedSettings),
    saved: true
  };
}
function isDraftDirty(draftSettings, confirmedRevision) {
  return Boolean(
    draftSettings && confirmedRevision && settingsRevision(draftSettings) !== confirmedRevision
  );
}
function canonicalize(value) {
  if (Array.isArray(value)) {
    return value.map(canonicalize);
  }
  if (value && typeof value === "object") {
    const record = (
      /** @type {Record<string, unknown>} */
      value
    );
    return Object.fromEntries(
      Object.keys(record).sort().map((key) => [key, canonicalize(record[key])])
    );
  }
  return value;
}
function detachJsonValue(value) {
  if (Array.isArray(value)) {
    return value.map(detachJsonValue);
  }
  if (value && typeof value === "object") {
    const record = (
      /** @type {Record<string, unknown>} */
      value
    );
    return Object.fromEntries(
      Object.entries(record).map(([key, item]) => [key, detachJsonValue(item)])
    );
  }
  return value;
}
var root$1 = /* @__PURE__ */ from_html(`<button type="button" role="tab"> </button>`);
var root_1$1 = /* @__PURE__ */ from_html(`<section class="content-grid" aria-label="Übersicht"><!> <div class="span-2"><!></div></section>`);
var root_2$1 = /* @__PURE__ */ from_html(`<div><dt> </dt><dd> </dd></div>`);
var root_3$1 = /* @__PURE__ */ from_html(`<div><div class="candidate-top"><strong> </strong><span> </span></div> <p> </p> <small> </small></div>`);
var root_4 = /* @__PURE__ */ from_html(`<li><strong> </strong><span> </span></li>`);
var root_5 = /* @__PURE__ */ from_html(`<h3>Pausiert / unterdrückt</h3> <ul class="plain-list"></ul>`, 1);
var root_6 = /* @__PURE__ */ from_html(`<div><span> </span><code> </code></div>`);
var root_7 = /* @__PURE__ */ from_html(`<p class="empty-state">Noch keine owner-bound Inputs gebunden.</p>`);
var root_8 = /* @__PURE__ */ from_html(`<section class="diagnosis-layout" aria-label="Diagnose"><article class="card span-2"><p class="eyebrow">TECHNISCHE EBENE</p><h2>Baseline, Bewegung und Kontext</h2> <dl class="facts"><div><dt>Bewegung</dt><dd> </dd></div> <div><dt>Recovery</dt><dd> </dd></div> <div><dt>Ruhebaseline</dt><dd> </dd></div> <div><dt>Manual Override</dt><dd> </dd></div> <div><dt>Core Contracts</dt><dd> </dd></div></dl> <h3>HAUSHALT & KONTEXT</h3> <dl class="facts"></dl></article> <article class="card"><div class="card-heading"><div><p class="eyebrow">DECISION TRACE</p><h2>Hierarchie und flache Diagnose</h2></div><span class="badge"> </span></div> <div class="winner-tree"><span>Master</span> <strong> </strong> <span> </span></div> <h3>Flache Kandidatenliste (Diagnose)</h3> <div class="trace-list"></div> <!></article> <div class="side-stack"><article class="card"><div class="card-heading"><div><p class="eyebrow">SOLAR EXPOSURE</p><h2> </h2></div><span class="badge"> </span></div> <dl class="facts"><div><dt>Einfallsfaktor</dt><dd> </dd></div> <div><dt>Außen-Lux</dt><dd> </dd></div> <div><dt>Trend</dt><dd> </dd></div> <div><dt>Capabilities</dt><dd> </dd></div> <div><dt>Optionale Capabilities fehlen</dt><dd> </dd></div> <div><dt>Verwendete Evidence</dt><dd> </dd></div> <div><dt>Abgeleitet</dt><dd> </dd></div> <div><dt>Grund</dt><dd> </dd></div></dl></article> <article class="card"><div class="card-heading"><div><p class="eyebrow">INPUT QUALITY</p><h2>Owner-gebundene Inputs</h2></div></div> <div class="source-list"></div></article> <article class="card debug-card"><div class="card-heading"><div><p class="eyebrow">EXPORT</p><h2>Redigierte Debug-Evidence</h2></div><button class="quiet-button" type="button"> </button></div> <details><summary>Kopierbare Shadow-Evidence anzeigen</summary> <pre> </pre></details></article></div></section>`);
var root_9 = /* @__PURE__ */ from_html(`<label> <input type="text"/></label> <p class="hint"> </p>`, 1);
var root_10 = /* @__PURE__ */ from_html(`<p class="callout failure-callout"> </p>`);
var root_11 = /* @__PURE__ */ from_html(`<div class="profile-row" role="row"><strong> </strong> <input type="number" min="0" max="100"/> <output> </output></div>`);
var root_12 = /* @__PURE__ */ from_html(`<label> <input type="number" step="any"/></label>`);
var root_13 = /* @__PURE__ */ from_html(`<div class="binding-row"><strong> </strong> <span> </span> <small> </small></div>`);
var root_14 = /* @__PURE__ */ from_html(`<p class="hint"> </p>`);
var root_15 = /* @__PURE__ */ from_html(`<section class="binding-group"><h3> </h3> <!> <!></section>`);
var root_16 = /* @__PURE__ */ from_html(`<section class="settings-layout" aria-label="Einstellungen"><article class="card"><div class="card-heading"><div><p class="eyebrow">GEOMETRIE & STATUS</p><h2>Fensterfläche</h2></div><span> </span></div> <div class="form-grid"><label>Azimut (°)<input type="number" min="0" max="360"/></label> <label>Neigung (°)<input type="number" min="0" max="180"/></label> <label class="toggle"><input type="checkbox"/> Achse invertiert</label> <label class="toggle"><input type="checkbox"/> Automatik aktiv</label></div> <p class="hint">Betriebsmodus, Writer und Apply stehen unter Übersicht → Betrieb zur Verfügung.</p></article> <article class="card"><p class="eyebrow">GEMEINSAME INPUTS</p><h2>Core Contracts · primärer Pfad</h2> <p class="hint">Vorhandene Contract-ID aus der Registry auswählen. Leer bedeutet expliziter kompatibler Owner-Fallback. Ein ausgewählter defekter Contract blockiert; er fällt nicht lokal zurück. Änderungen nur mit Apply AUS.</p> <label>Profil<select><option>Benni</option><option>Eltern</option></select></label> <!> <p class="hint">Plattform-Gaps: Bio, Activity, Day/Context und weitere Solar-/Wetterfelder. Bis zu passenden zentralen Rollen bleiben ihre bisherigen Owner-Bindings erhalten.</p></article> <article class="card span-2"><div class="card-heading"><div><p class="eyebrow">PROFILE</p><h2>Logische Zielposition</h2></div><div class="button-row"><span class="muted"> </span><button class="quiet-button" type="button">Entwurf zurücksetzen</button><button class="primary-button" type="button"> </button></div></div> <!> <div class="profile-table" role="table" aria-label="Positionsprofile"><div class="profile-row profile-header" role="row"><span>Profil</span><span>Logisch</span><span>Invertiert (abgeleitet)</span></div> <!></div></article> <article class="card span-2"><div class="card-heading"><div><p class="eyebrow">KALIBRIERUNG</p><h2>Shadow-Defaults</h2></div><span class="muted">später trace-basiert kalibrieren</span></div> <p class="hint">Cold endet erst oberhalb der höheren Austrittsschwelle. Der Solar-Haltefaktor senkt die Austrittsschwellen für bestehenden Schutz. Eintritt und Entlastung müssen jeweils stabil bleiben; Safety reagiert sofort. Der Apply-Cooldown schützt den Motor unabhängig davon.</p> <div class="calibration-grid"></div></article> <article class="card span-2"><div class="card-heading"><div><p class="eyebrow">DOMÄNE & ÜBERGANG</p><h2>Lokales Cover und kompatible Fallbacks</h2></div><span class="muted">OptionsFlow</span></div> <p class="hint">Bearbeitung erfolgt ausschließlich über Blind Control → Konfigurieren im nativen Home-Assistant-OptionsFlow. Entity-IDs werden im Panel nicht angezeigt oder entgegengenommen.</p> <div class="binding-grid"></div></article></section>`);
var root_17 = /* @__PURE__ */ from_html(`<div class="panel-root"><header class="app-header"><div><p class="eyebrow"> </p> <h1>Wohnzimmer-Rollo</h1> <p class="subtitle">Aktuelle Entscheidung und kontrollierter Betrieb</p></div> <div class="header-status"><span></span> <span> </span></div></header> <div class="tabs" aria-label="Blind Control Bereiche" role="tablist"></div> <!></div>`);
function App($$anchor, $$props) {
  push($$props, true);
  let saving = prop($$props, "saving", 3, false);
  let activeTab = /* @__PURE__ */ state("overview");
  let draftSettings = /* @__PURE__ */ state(null);
  let confirmedSettingsRevision = /* @__PURE__ */ state(null);
  let saveError = /* @__PURE__ */ state(null);
  let copyState = /* @__PURE__ */ state("idle");
  let editableSettings = /* @__PURE__ */ user_derived(() => get(draftSettings) ?? $$props.snapshot.settings);
  let draftDirty = /* @__PURE__ */ user_derived(() => get(draftSettings) !== null && get(confirmedSettingsRevision) !== null && settingsRevision(get(draftSettings)) !== get(confirmedSettingsRevision));
  user_effect(() => {
    const incomingSettings = snapshot($$props.snapshot.settings);
    const next = rebaseDraft(get(draftSettings), get(confirmedSettingsRevision), incomingSettings);
    if (next.draftSettings !== get(draftSettings) || next.confirmedRevision !== get(confirmedSettingsRevision)) {
      set(draftSettings, next.draftSettings, true);
      set(confirmedSettingsRevision, next.confirmedRevision, true);
    }
  });
  const labels = {
    normal: "Regulär",
    core_contract_selected: "Consumer API gewählt · Quality in Diagnose",
    compatibility_fallback_unselected: "Keine zentrale Auswahl · kompatibler Owner-Fallback",
    opening: "Opening / Fenster",
    room_climate: "Raumklima",
    weather_environment: "Wetter / Außenumgebung",
    low_light: "Geringe Solarenergie",
    cold_lux_enter_threshold: "Cold: Eintritt unter (lx)",
    cold_lux_exit_threshold: "Cold: Austritt über (lx)",
    environment_hysteresis_ratio: "Solar/Confidence: Haltefaktor (0–1)",
    environment_enter_seconds: "Umweltschutz: Eintritt stabil (s)",
    environment_exit_seconds: "Umweltschutz: Entlastung stabil (s)",
    movement_recovery_seconds: "Bewegungsfehler: stabile Ruhe zur Erholung (s)",
    cold_outdoor_threshold: "Cold: Außentemperatur bis (°C)",
    heat_indoor_threshold: "Heat: Innentemperatur ab (°C)",
    heat_outdoor_threshold: "Heat: Außentemperatur ab (°C)",
    cloud_cover_threshold: "Wolkenschatten: Bewölkung ab (%)",
    model_lux_ratio: "Beobachtete / erwartete Helligkeit (0–1)",
    minimum_incidence_factor: "Min. Einfallsfaktor (0–1)",
    model_lux_per_watt: "Modellhelligkeit (lx pro W/m²)",
    position_settle_seconds: "Ruheposition bestätigen (s)",
    movement_timeout_seconds: "Zielerreichung: Fehlerfrist (s)",
    manual: "Manuell",
    failure: "Fehler",
    neutral: "Neutral",
    waking: "Waking",
    sleep: "Schlaf",
    away: "Abwesend",
    privacy: "Privacy",
    private_time: "Private Zeit",
    glare: "Blendung",
    general: "Allgemein",
    tv: "TV",
    pc: "PC",
    climate: "Klima",
    heat: "Hitze",
    cold: "Kälte",
    storm: "Gewitter",
    cool_air: "Kühle Luft",
    override: "Override",
    manual_override: "Manueller Override",
    bio_state: "Bio",
    activity_state: "Aktivität",
    day_state: "Tag",
    day_context: "Tageskontext",
    daylight: "Tageslicht",
    ready: "bereit",
    blocked: "blockiert",
    safe_position: "Safety-Position",
    safety_ready: "Safety bereit",
    shadow_ready: "Shadow bereit",
    live_ready: "Live-Ziel bereit",
    applied: "Ziel übergeben",
    stable: "Ziel stabil",
    cooldown: "Cooldown aktiv",
    manual_hold: "Manuell gehalten",
    error: "Fehler",
    required_resolved: "Pflicht aufgelöst",
    required_unresolved: "Pflicht nicht aufgelöst",
    conditional_resolved: "Bedingt aufgelöst",
    conditional_unresolved: "Bedingt nicht aufgelöst",
    conditional_not_applicable: "Nicht erforderlich",
    optional_bound: "Optional gebunden",
    optional_intentionally_empty: "Bewusst leer",
    internal_provider_active: "Interner Provider aktiv",
    internal_provider_degraded: "Interner Provider mit letztem frischen Wert",
    external_override_active: "Externes Override aktiv",
    provider_unavailable: "Provider nicht verfügbar",
    provider_stale: "Providerwert veraltet",
    legacy_bound: "Legacy gebunden",
    legacy_not_available: "Legacy nicht verfügbar"
  };
  const labelFor = (value) => {
    if (!value) return "—";
    return labels[value] ?? value.replaceAll("_", " ");
  };
  const branchLabel = (branch2) => {
    if (!branch2) return "—";
    return branch2.variant ? `${labelFor(branch2.category)} → ${labelFor(branch2.variant)}` : labelFor(branch2.category);
  };
  const positionLabel = (value) => value === null ? "—" : `${Math.round(value)} %`;
  const statusLabel = (value) => labelFor(value);
  const statusTone = (value) => {
    if (value === "ready" || value === "safe_position" || value === "safety_ready" || value === "shadow_ready" || value === "live_ready" || value === "applied" || value === "stable") return "ready";
    if (value === "failure" || value === "error" || value === "unavailable") return "error";
    if (value === "blocked" || value === "manual" || value === "manual_hold" || value === "cooldown" || value === "holding_safe_position") return "warning";
    return "warning";
  };
  const bindingStatusTone = (value) => {
    if (value === "required_unresolved" || value === "conditional_unresolved") return "warning";
    if (value === "required_resolved" || value === "conditional_resolved" || value === "optional_bound" || value === "legacy_bound" || value === "internal_provider_active" || value === "external_override_active") return "ready";
    if (value === "provider_unavailable" || value === "provider_stale") return "warning";
    return "muted";
  };
  const householdLabel = (value) => value === null ? "—" : value ? "ja" : "nein";
  const contextValue = (value) => typeof value === "boolean" ? householdLabel(value) : statusLabel(value);
  const candidateClass = (candidate) => candidate.paused ? "candidate paused" : candidate.active ? "candidate active" : "candidate";
  function updateProfile(key, axis, value) {
    if (!get(draftSettings)) return;
    const profile = get(draftSettings).profiles[key];
    if (!profile || !Number.isFinite(value)) return;
    profile[axis] = Math.max(0, Math.min(100, value));
  }
  function resetDraft() {
    const serverSettings = snapshot($$props.snapshot.settings);
    set(draftSettings, cloneSettings(serverSettings), true);
    set(confirmedSettingsRevision, settingsRevision(serverSettings), true);
    set(saveError, null);
  }
  async function saveDraft() {
    if (!$$props.onSaveSettings || !get(draftSettings)) return;
    const submittedDraft = cloneSettings(snapshot(get(draftSettings)));
    const submittedRevision = settingsRevision(submittedDraft);
    set(saveError, null);
    try {
      const confirmedSettings = await $$props.onSaveSettings(submittedDraft);
      if (get(draftSettings) && settingsRevision(get(draftSettings)) === submittedRevision) {
        const settled = settleSave(get(draftSettings), get(confirmedSettingsRevision), confirmedSettings);
        set(draftSettings, settled.draftSettings, true);
        set(confirmedSettingsRevision, settled.confirmedRevision, true);
      } else {
        set(confirmedSettingsRevision, settingsRevision(confirmedSettings), true);
      }
    } catch {
      const preserved = settleSave(get(draftSettings), get(confirmedSettingsRevision), null);
      set(draftSettings, preserved.draftSettings, true);
      set(confirmedSettingsRevision, preserved.confirmedRevision, true);
      set(saveError, "Speichern fehlgeschlagen. Der lokale Entwurf bleibt erhalten.");
    }
  }
  async function copyDebugPayload() {
    var _a2;
    try {
      if (!((_a2 = navigator.clipboard) == null ? void 0 : _a2.writeText)) throw new Error("Clipboard API unavailable");
      await navigator.clipboard.writeText(JSON.stringify($$props.snapshot.debug_payload, null, 2));
      set(copyState, "copied");
      window.setTimeout(() => set(copyState, "idle"), 1800);
    } catch {
      set(copyState, "failed");
    }
  }
  function updateNumber(key, event) {
    if (!get(draftSettings)) return;
    const value = event.currentTarget.valueAsNumber;
    if (Number.isFinite(value)) get(draftSettings)[key] = value;
  }
  function updateBoolean(key, event) {
    if (get(draftSettings)) get(draftSettings)[key] = event.currentTarget.checked;
  }
  function updateCalibration(key, event) {
    if (!get(draftSettings)) return;
    const value = event.currentTarget.valueAsNumber;
    if (Number.isFinite(value)) get(draftSettings).calibration_defaults[key] = value;
  }
  var div = root_17();
  head("1n46o8q", ($$anchor2) => {
    deferred_template_effect(() => {
      $document.title = `Blind Control · ${$$props.snapshot.settings.runtime_mode === "shadow" ? "Shadow" : "Live vorbereitet"}`;
    });
  });
  var header = child(div);
  var div_1 = child(header);
  var p = child(div_1);
  var text = child(p);
  var div_2 = sibling(div_1, 2);
  var span = child(div_2);
  var span_1 = sibling(span, 2);
  var text_1 = child(span_1);
  var div_3 = sibling(header, 2);
  each(
    div_3,
    20,
    () => [
      ["overview", "Übersicht"],
      ["diagnosis", "Diagnose"],
      ["settings", "Einstellungen"]
    ],
    index,
    ($$anchor2, $$item) => {
      var $$array = /* @__PURE__ */ user_derived(() => to_array($$item, 2));
      let tab = () => get($$array)[0];
      let label = () => get($$array)[1];
      var button = root$1();
      let classes;
      var text_2 = child(button);
      template_effect(() => {
        classes = set_class(button, 1, "tab", null, classes, { active: get(activeTab) === tab() });
        set_attribute(button, "aria-selected", get(activeTab) === tab());
        set_text(text_2, label());
      });
      delegated("click", button, () => set(activeTab, tab(), true));
      append($$anchor2, button);
    }
  );
  var node = sibling(div_3, 2);
  {
    var consequent = ($$anchor2) => {
      var section = root_1$1();
      var node_1 = child(section);
      Overview(node_1, {
        get snapshot() {
          return $$props.snapshot;
        }
      });
      var div_4 = sibling(node_1, 2);
      var node_2 = child(div_4);
      Operation(node_2, {
        get snapshot() {
          return $$props.snapshot;
        },
        get onOperation() {
          return $$props.onOperation;
        }
      });
      append($$anchor2, section);
    };
    var consequent_2 = ($$anchor2) => {
      var section_1 = root_8();
      var article = child(section_1);
      var dl = sibling(child(article), 3);
      var div_5 = child(dl);
      var dd = sibling(child(div_5));
      var text_3 = child(dd);
      var div_6 = sibling(div_5, 2);
      var dd_1 = sibling(child(div_6));
      var text_4 = child(dd_1);
      var div_7 = sibling(div_6, 2);
      var dd_2 = sibling(child(div_7));
      var text_5 = child(dd_2);
      var div_8 = sibling(div_7, 2);
      var dd_3 = sibling(child(div_8));
      var text_6 = child(dd_3);
      var div_9 = sibling(div_8, 2);
      var dd_4 = sibling(child(div_9));
      var text_7 = child(dd_4);
      var dl_1 = sibling(dl, 4);
      each(dl_1, 21, () => Object.entries($$props.snapshot.overview.household), index, ($$anchor3, $$item) => {
        var $$array_1 = /* @__PURE__ */ user_derived(() => to_array(get($$item), 2));
        let key = () => get($$array_1)[0];
        let value = () => get($$array_1)[1];
        var div_10 = root_2$1();
        var dt = child(div_10);
        var text_8 = child(dt);
        var dd_5 = sibling(dt);
        var text_9 = child(dd_5);
        template_effect(
          ($0, $1) => {
            set_text(text_8, $0);
            set_text(text_9, $1);
          },
          [() => labelFor(key()), () => contextValue(value())]
        );
        append($$anchor3, div_10);
      });
      var article_1 = sibling(article, 2);
      var div_11 = child(article_1);
      var span_2 = sibling(child(div_11));
      var text_10 = child(span_2);
      var div_12 = sibling(div_11, 2);
      var strong = sibling(child(div_12), 2);
      var text_11 = child(strong);
      var span_3 = sibling(strong, 2);
      var text_12 = child(span_3);
      var div_13 = sibling(div_12, 4);
      each(div_13, 21, () => $$props.snapshot.diagnosis.candidates, index, ($$anchor3, candidate) => {
        var div_14 = root_3$1();
        var div_15 = child(div_14);
        var strong_1 = child(div_15);
        var text_13 = child(strong_1);
        var span_4 = sibling(strong_1);
        var text_14 = child(span_4);
        var p_1 = sibling(div_15, 2);
        var text_15 = child(p_1);
        var small = sibling(p_1, 2);
        var text_16 = child(small);
        template_effect(
          ($0, $1, $2, $3) => {
            set_class(div_14, 1, $0);
            set_text(text_13, $1);
            set_text(text_14, $2);
            set_text(text_15, $3);
            set_text(text_16, `${(get(candidate).paused ? `pausiert durch ${get(candidate).suppressed_by}` : get(candidate).quality) ?? ""} · ${get(candidate).source ?? ""}`);
          },
          [
            () => clsx(candidateClass(get(candidate))),
            () => branchLabel(get(candidate)),
            () => get(candidate).active ? positionLabel(get(candidate).target_position) : "inaktiv",
            () => get(candidate).reason.replaceAll("_", " ")
          ]
        );
        append($$anchor3, div_14);
      });
      var node_3 = sibling(div_13, 2);
      {
        var consequent_1 = ($$anchor3) => {
          var fragment = root_5();
          var ul = sibling(first_child(fragment), 2);
          each(ul, 21, () => $$props.snapshot.diagnosis.paused_requirements, index, ($$anchor4, item) => {
            var li = root_4();
            var strong_2 = child(li);
            var text_17 = child(strong_2);
            var span_5 = sibling(strong_2);
            var text_18 = child(span_5);
            template_effect(
              ($0, $1) => {
                set_text(text_17, $0);
                set_text(text_18, $1);
              },
              [
                () => labelFor(get(item).key),
                () => get(item).reason.replaceAll("_", " ")
              ]
            );
            append($$anchor4, li);
          });
          append($$anchor3, fragment);
        };
        if_block(node_3, ($$render) => {
          if ($$props.snapshot.diagnosis.paused_requirements.length) $$render(consequent_1);
        });
      }
      var div_16 = sibling(article_1, 2);
      var article_2 = child(div_16);
      var div_17 = child(article_2);
      var div_18 = child(div_17);
      var h2 = sibling(child(div_18));
      var text_19 = child(h2);
      var span_6 = sibling(div_18);
      var text_20 = child(span_6);
      var dl_2 = sibling(div_17, 2);
      var div_19 = child(dl_2);
      var dd_6 = sibling(child(div_19));
      var text_21 = child(dd_6);
      var div_20 = sibling(div_19, 2);
      var dd_7 = sibling(child(div_20));
      var text_22 = child(dd_7);
      var div_21 = sibling(div_20, 2);
      var dd_8 = sibling(child(div_21));
      var text_23 = child(dd_8);
      var div_22 = sibling(div_21, 2);
      var dd_9 = sibling(child(div_22));
      var text_24 = child(dd_9);
      var div_23 = sibling(div_22, 2);
      var dd_10 = sibling(child(div_23));
      var text_25 = child(dd_10);
      var div_24 = sibling(div_23, 2);
      var dd_11 = sibling(child(div_24));
      var text_26 = child(dd_11);
      var div_25 = sibling(div_24, 2);
      var dd_12 = sibling(child(div_25));
      var text_27 = child(dd_12);
      var div_26 = sibling(div_25, 2);
      var dd_13 = sibling(child(div_26));
      var text_28 = child(dd_13);
      var article_3 = sibling(article_2, 2);
      var div_27 = sibling(child(article_3), 2);
      each(
        div_27,
        21,
        () => Object.entries($$props.snapshot.diagnosis.inputs),
        index,
        ($$anchor3, $$item) => {
          var $$array_2 = /* @__PURE__ */ user_derived(() => to_array(get($$item), 2));
          let key = () => get($$array_2)[0];
          let value = () => get($$array_2)[1];
          var div_28 = root_6();
          var span_7 = child(div_28);
          var text_29 = child(span_7);
          var code = sibling(span_7);
          var text_30 = child(code);
          template_effect(
            ($0, $1) => {
              set_text(text_29, $0);
              set_text(text_30, $1);
            },
            [
              () => labelFor(key()),
              () => typeof value() === "string" ? value() : JSON.stringify(value())
            ]
          );
          append($$anchor3, div_28);
        },
        ($$anchor3) => {
          var p_2 = root_7();
          append($$anchor3, p_2);
        }
      );
      var article_4 = sibling(article_3, 2);
      var div_29 = child(article_4);
      var button_1 = sibling(child(div_29));
      var text_31 = child(button_1);
      var details = sibling(div_29, 2);
      var pre = sibling(child(details), 2);
      var text_32 = child(pre);
      template_effect(
        ($0, $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12) => {
          set_text(text_3, $$props.snapshot.overview.movement_status);
          set_text(text_4, `${$$props.snapshot.overview.recovery_status ?? "—" ?? ""} · ${$$props.snapshot.overview.movement_error ?? "kein Fehler" ?? ""}`);
          set_text(text_5, $0);
          set_text(text_6, $$props.snapshot.overview.override.active ? "aktiv" : "inaktiv");
          set_text(text_7, $1);
          set_text(text_10, $$props.snapshot.version);
          set_text(text_11, `${$2 ?? ""} → ${$3 ?? ""}`);
          set_text(text_12, $$props.snapshot.diagnosis.hierarchy.failure.status === "none" ? "belastbar" : $$props.snapshot.diagnosis.hierarchy.failure.status);
          set_text(text_19, $4);
          set_text(text_20, `${$5 ?? ""} %`);
          set_text(text_21, $6);
          set_text(text_22, $$props.snapshot.diagnosis.solar.observed_lux ?? "—");
          set_text(text_23, $$props.snapshot.diagnosis.solar.lux_trend ?? "—");
          set_text(text_24, $7);
          set_text(text_25, $8);
          set_text(text_26, $9);
          set_text(text_27, $10);
          set_text(text_28, $11);
          set_text(text_31, get(copyState) === "copied" ? "Kopiert" : get(copyState) === "failed" ? "Kopieren fehlgeschlagen" : "Evidence kopieren");
          set_text(text_32, $12);
        },
        [
          () => positionLabel($$props.snapshot.overview.baseline_position),
          () => JSON.stringify($$props.snapshot.diagnosis.core_contracts ?? {}),
          () => labelFor($$props.snapshot.diagnosis.hierarchy.master_mode),
          () => branchLabel($$props.snapshot.diagnosis.hierarchy.winner),
          () => statusLabel($$props.snapshot.diagnosis.solar.state),
          () => Math.round($$props.snapshot.diagnosis.solar.confidence * 100),
          () => {
            var _a2;
            return ((_a2 = $$props.snapshot.diagnosis.solar.incidence_factor) == null ? void 0 : _a2.toFixed(3)) ?? "—";
          },
          () => $$props.snapshot.diagnosis.solar.capabilities.map(labelFor).join(", ") || "—",
          () => $$props.snapshot.diagnosis.solar.missing_optional_capabilities.map(labelFor).join(", ") || "keine",
          () => $$props.snapshot.diagnosis.solar.used_evidence.map(labelFor).join(", ") || "—",
          () => $$props.snapshot.diagnosis.solar.derived_evidence.map(labelFor).join(", ") || "keine",
          () => $$props.snapshot.diagnosis.solar.reason.replaceAll("_", " "),
          () => JSON.stringify($$props.snapshot.debug_payload, null, 2)
        ]
      );
      delegated("click", button_1, copyDebugPayload);
      append($$anchor2, section_1);
    };
    var alternate = ($$anchor2) => {
      var section_2 = root_16();
      var article_5 = child(section_2);
      var div_30 = child(article_5);
      var span_8 = sibling(child(div_30));
      var text_33 = child(span_8);
      var div_31 = sibling(div_30, 2);
      var label_1 = child(div_31);
      var input = sibling(child(label_1));
      var label_2 = sibling(label_1, 2);
      var input_1 = sibling(child(label_2));
      var label_3 = sibling(label_2, 2);
      var input_2 = child(label_3);
      var label_4 = sibling(label_3, 2);
      var input_3 = child(label_4);
      var article_6 = sibling(article_5, 2);
      var label_5 = sibling(child(article_6), 5);
      var select = sibling(child(label_5));
      var option = child(select);
      option.value = option.__value = "benni";
      var option_1 = sibling(option);
      option_1.value = option_1.__value = "eltern";
      var select_value;
      init_select(select);
      var node_4 = sibling(label_5, 2);
      each(node_4, 16, () => ["opening", "room_climate", "weather_environment"], index, ($$anchor3, schema) => {
        var fragment_1 = root_9();
        var label_6 = first_child(fragment_1);
        var text_34 = child(label_6);
        var input_4 = sibling(text_34);
        var p_3 = sibling(label_6, 2);
        var text_35 = child(p_3);
        template_effect(
          ($0, $1) => {
            set_text(text_34, `${$0 ?? ""} · Contract-ID`);
            input_4.disabled = $$props.snapshot.settings.apply_enabled;
            set_value(input_4, get(editableSettings).core_contracts[schema] ?? "");
            set_text(text_35, $1);
          },
          [
            () => labelFor(schema),
            () => {
              var _a2;
              return labelFor(((_a2 = $$props.snapshot.diagnosis.core_contracts) == null ? void 0 : _a2[schema]) ?? "compatibility_fallback_unselected");
            }
          ]
        );
        delegated("change", input_4, (event) => {
          if (get(draftSettings)) {
            const value = event.currentTarget.value.trim();
            if (value) get(draftSettings).core_contracts[schema] = value;
            else delete get(draftSettings).core_contracts[schema];
          }
        });
        append($$anchor3, fragment_1);
      });
      var article_7 = sibling(article_6, 2);
      var div_32 = child(article_7);
      var div_33 = sibling(child(div_32));
      var span_9 = child(div_33);
      var text_36 = child(span_9);
      var button_2 = sibling(span_9);
      var button_3 = sibling(button_2);
      var text_37 = child(button_3);
      var node_5 = sibling(div_32, 2);
      {
        var consequent_3 = ($$anchor3) => {
          var p_4 = root_10();
          var text_38 = child(p_4);
          template_effect(() => set_text(text_38, get(saveError)));
          append($$anchor3, p_4);
        };
        if_block(node_5, ($$render) => {
          if (get(saveError)) $$render(consequent_3);
        });
      }
      var div_34 = sibling(node_5, 2);
      var node_6 = sibling(child(div_34), 2);
      each(node_6, 17, () => Object.entries(get(editableSettings).profiles), index, ($$anchor3, $$item) => {
        var $$array_3 = /* @__PURE__ */ user_derived(() => to_array(get($$item), 2));
        let key = () => get($$array_3)[0];
        let profile = () => get($$array_3)[1];
        var div_35 = root_11();
        var strong_3 = child(div_35);
        var text_39 = child(strong_3);
        var input_5 = sibling(strong_3, 2);
        var output = sibling(input_5, 2);
        var text_40 = child(output);
        template_effect(
          ($0) => {
            set_text(text_39, $0);
            set_attribute(input_5, "aria-label", `${key()} logisch`);
            set_value(input_5, profile().logical);
            set_text(text_40, `${100 - profile().logical} %`);
          },
          [() => labelFor(key())]
        );
        delegated("change", input_5, (event) => updateProfile(key(), "logical", event.currentTarget.valueAsNumber));
        append($$anchor3, div_35);
      });
      var article_8 = sibling(article_7, 2);
      var div_36 = sibling(child(article_8), 4);
      each(div_36, 21, () => Object.entries(get(editableSettings).calibration_defaults), index, ($$anchor3, $$item) => {
        var $$array_4 = /* @__PURE__ */ user_derived(() => to_array(get($$item), 2));
        let key = () => get($$array_4)[0];
        let value = () => get($$array_4)[1];
        var label_7 = root_12();
        var text_41 = child(label_7);
        var input_6 = sibling(text_41);
        template_effect(
          ($0, $1) => {
            set_text(text_41, $0);
            set_attribute(input_6, "min", $1);
            set_value(input_6, value());
          },
          [
            () => labelFor(key()),
            () => key().endsWith("_temperature_threshold") || [
              "heat_indoor_threshold",
              "heat_outdoor_threshold",
              "cold_outdoor_threshold"
            ].includes(key()) ? -100 : 0
          ]
        );
        delegated("change", input_6, (event) => updateCalibration(key(), event));
        append($$anchor3, label_7);
      });
      var article_9 = sibling(article_8, 2);
      var div_37 = sibling(child(article_9), 4);
      each(div_37, 21, () => get(editableSettings).binding_groups, index, ($$anchor3, group) => {
        var section_3 = root_15();
        var h3 = child(section_3);
        var text_42 = child(h3);
        var node_7 = sibling(h3, 2);
        each(node_7, 17, () => get(group).fields, index, ($$anchor4, field) => {
          var div_38 = root_13();
          var strong_4 = child(div_38);
          var text_43 = child(strong_4);
          var span_10 = sibling(strong_4, 2);
          var text_44 = child(span_10);
          var small_1 = sibling(span_10, 2);
          var text_45 = child(small_1);
          template_effect(
            ($0, $1, $2) => {
              set_text(text_43, $0);
              set_class(span_10, 1, $1);
              set_text(text_44, $2);
              set_text(text_45, `${get(field).requirement === "required" ? "Pflicht" : get(field).requirement === "conditional" ? "bedingt erforderlich" : "optional"} · ${get(field).owner ?? ""} · ${get(field).max_age_seconds === null ? "stateful" : `${get(field).max_age_seconds} s`} · ${get(field).require_timestamp ? "Zeitbeleg erforderlich" : "kein Zeitbeleg erforderlich"}`);
            },
            [
              () => labelFor(get(field).key),
              () => clsx(bindingStatusTone(get(field).status)),
              () => labelFor(get(field).status)
            ]
          );
          append($$anchor4, div_38);
        });
        var node_8 = sibling(node_7, 2);
        {
          var consequent_4 = ($$anchor4) => {
            var p_5 = root_14();
            var text_46 = child(p_5);
            template_effect(($0) => set_text(text_46, `Opening-Safety-Polarität: ${$0 ?? ""}. Ohne explizite Polarität bleibt eine Kippfreigabe blockiert.`), [
              () => labelFor(get(editableSettings).opening_safety_polarity)
            ]);
            append($$anchor4, p_5);
          };
          if_block(node_8, ($$render) => {
            if (get(group).key === "opening_safety_cover_bindings") $$render(consequent_4);
          });
        }
        template_effect(() => set_text(text_42, `${get(group).label ?? ""} · ${get(group).readiness === "ready" ? "bereit" : "Pflicht-Evidence fehlt"}`));
        append($$anchor3, section_3);
      });
      template_effect(
        ($0, $1) => {
          set_class(span_8, 1, $0);
          set_text(text_33, $1);
          set_value(input, get(editableSettings).window_azimuth);
          set_value(input_1, get(editableSettings).window_tilt);
          set_checked(input_2, get(editableSettings).axis_inverted);
          set_checked(input_3, get(editableSettings).automation_enabled);
          select.disabled = $$props.snapshot.settings.apply_enabled;
          if (select_value !== (select_value = get(editableSettings).core_contract_profile)) {
            select.value = (select.__value = get(editableSettings).core_contract_profile) ?? "", select_option(select, get(editableSettings).core_contract_profile);
          }
          set_text(text_36, get(draftDirty) ? "Ungespeicherter Entwurf" : "Serverstand bestätigt");
          button_3.disabled = saving() || !$$props.onSaveSettings;
          set_text(text_37, saving() ? "Speichere …" : "Konfiguration speichern");
        },
        [
          () => `badge ${statusTone($$props.snapshot.overview.apply_status)}`,
          () => statusLabel($$props.snapshot.overview.apply_status)
        ]
      );
      delegated("change", input, (event) => updateNumber("window_azimuth", event));
      delegated("change", input_1, (event) => updateNumber("window_tilt", event));
      delegated("change", input_2, (event) => updateBoolean("axis_inverted", event));
      delegated("change", input_3, (event) => updateBoolean("automation_enabled", event));
      delegated("change", select, (event) => {
        if (get(draftSettings)) get(draftSettings).core_contract_profile = event.currentTarget.value;
      });
      delegated("click", button_2, resetDraft);
      delegated("click", button_3, () => void saveDraft());
      append($$anchor2, section_2);
    };
    if_block(node, ($$render) => {
      if (get(activeTab) === "overview") $$render(consequent);
      else if (get(activeTab) === "diagnosis") $$render(consequent_2, 1);
      else $$render(alternate, -1);
    });
  }
  template_effect(
    ($0, $1, $2) => {
      set_text(text, `BLIND CONTROL · ${$0 ?? ""} · ${$$props.snapshot.settings.apply_owner === "blind_control" ? "BLIND CONTROL" : "LEGACY"}`);
      set_class(span, 1, $1);
      set_text(text_1, `${$$props.snapshot.settings.runtime_mode === "shadow" ? "Shadow" : "Live vorbereitet"} · ${$2 ?? ""}`);
    },
    [
      () => $$props.snapshot.settings.runtime_mode.toUpperCase(),
      () => `status-dot ${statusTone($$props.snapshot.overview.apply_status)}`,
      () => statusLabel($$props.snapshot.overview.apply_status)
    ]
  );
  append($$anchor, div);
  pop();
}
delegate(["click", "change"]);
async function fetchSnapshot(hass) {
  return hass.connection.sendMessagePromise({
    type: "blind_control/get_snapshot"
  });
}
async function updateOptions(hass, settings) {
  const options = {
    ...settings,
    ...settings.calibration_defaults
  };
  delete options.calibration_defaults;
  delete options.binding_groups;
  delete options.binding_freshness;
  delete options.runtime_mode;
  delete options.apply_owner;
  delete options.apply_enabled;
  await hass.connection.sendMessagePromise({
    type: "blind_control/update_options",
    options
  });
}
async function setOperation(hass, revision, mode, owner, apply, confirmed) {
  await hass.connection.sendMessagePromise({
    type: "blind_control/set_operation",
    expected_revision: revision,
    operation: { runtime_mode: mode, apply_owner: owner, apply_enabled: apply },
    confirm_null_writer: confirmed
  });
}
var root = /* @__PURE__ */ from_html(`<p class="callout error" role="alert">Verbindung unterbrochen — Anzeige möglicherweise veraltet. Bedienung gesperrt.</p>`);
var root_1 = /* @__PURE__ */ from_html(`<!> <!>`, 1);
var root_2 = /* @__PURE__ */ from_html(`<main class="transport-state"><p class="eyebrow">BLIND CONTROL · SHADOW</p> <h1>Shadow-Daten werden geladen</h1> <p>Die Anzeige wartet auf die laufende Home-Assistant-Projektion.</p></main>`);
var root_3 = /* @__PURE__ */ from_html(`<main class="transport-state error-state"><p class="eyebrow">BLIND CONTROL · SHADOW</p> <h1>Shadow-Projektion nicht verfügbar</h1> <p> </p> <button class="quiet-button" type="button">Erneut verbinden</button></main>`);
function Shell($$anchor, $$props) {
  push($$props, true);
  let snapshot2 = /* @__PURE__ */ state(null);
  let error = /* @__PURE__ */ state(null);
  let loading = /* @__PURE__ */ state(true);
  let saving = /* @__PURE__ */ state(false);
  async function refresh() {
    try {
      const next = await fetchSnapshot($$props.hass);
      set(snapshot2, next, true);
      set(error, null);
      return next;
    } catch (cause) {
      set(error, cause instanceof Error ? cause.message : "Shadow snapshot unavailable", true);
      return null;
    } finally {
      set(loading, false);
    }
  }
  async function saveSettings(settings) {
    set(saving, true);
    try {
      await updateOptions($$props.hass, settings);
      const confirmed = await refresh();
      if (!confirmed) throw new Error("Confirmed Shadow snapshot unavailable");
      return confirmed.settings;
    } finally {
      set(saving, false);
    }
  }
  async function changeOperation(mode, owner, apply, confirmed) {
    var _a2;
    if (!((_a2 = get(snapshot2)) == null ? void 0 : _a2.operation) || get(error)) throw new Error("Aktuelle Betriebsdaten fehlen");
    await setOperation($$props.hass, get(snapshot2).operation.revision, mode, owner, apply, confirmed);
    await refresh();
  }
  user_effect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 5e3);
    return () => window.clearInterval(timer);
  });
  var fragment = comment();
  var node = first_child(fragment);
  {
    var consequent_1 = ($$anchor2) => {
      var fragment_1 = root_1();
      var node_1 = first_child(fragment_1);
      {
        var consequent = ($$anchor3) => {
          var p = root();
          append($$anchor3, p);
        };
        if_block(node_1, ($$render) => {
          if (get(error)) $$render(consequent);
        });
      }
      var node_2 = sibling(node_1, 2);
      {
        let $0 = /* @__PURE__ */ user_derived(() => get(error) ? void 0 : saveSettings);
        let $1 = /* @__PURE__ */ user_derived(() => get(error) ? void 0 : changeOperation);
        App(node_2, {
          get snapshot() {
            return get(snapshot2);
          },
          get onSaveSettings() {
            return get($0);
          },
          get onOperation() {
            return get($1);
          },
          get saving() {
            return get(saving);
          }
        });
      }
      append($$anchor2, fragment_1);
    };
    var consequent_2 = ($$anchor2) => {
      var main = root_2();
      append($$anchor2, main);
    };
    var alternate = ($$anchor2) => {
      var main_1 = root_3();
      var p_1 = sibling(child(main_1), 4);
      var text = child(p_1);
      var button = sibling(p_1, 2);
      template_effect(() => set_text(text, get(error) ?? "Unbekannter Transportfehler"));
      delegated("click", button, () => void refresh());
      append($$anchor2, main_1);
    };
    if_block(node, ($$render) => {
      if (get(snapshot2)) $$render(consequent_1);
      else if (get(loading)) $$render(consequent_2, 1);
      else $$render(alternate, -1);
    });
  }
  append($$anchor, fragment);
  pop();
}
delegate(["click"]);
const panelCss = `/* Vite embeds this stylesheet in the panel bundle. */
:host {
  display: block;
  width: 100%;
  min-height: 100%;
  min-width: 320px;
  color-scheme: dark;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #12151b;
  color: #edf1f7;
  font-synthesis: none;
}

*, *::before, *::after { box-sizing: border-box; }

button, input { font: inherit; }

button { cursor: pointer; }

.panel-root { width: 100%; max-width: 1240px; margin-inline: auto; padding: 32px; }
.transport-state { margin: 14vh auto; max-width: 680px; padding: 32px; }
.error-state { border: 1px solid #765b30; border-radius: 12px; background: #30291f; }
.app-header { display: flex; justify-content: space-between; gap: 24px; align-items: flex-start; margin-bottom: 28px; }
.eyebrow { color: #92a0b5; font-size: 11px; font-weight: 700; letter-spacing: .14em; margin: 0 0 8px; }
h1, h2, h3, p { margin-top: 0; }
h1 { font-size: clamp(25px, 4vw, 38px); letter-spacing: -.03em; margin-bottom: 6px; }
h2 { font-size: 19px; letter-spacing: -.015em; margin-bottom: 0; }
h3 { font-size: 14px; margin: 22px 0 12px; }
.subtitle, .muted, .hint { color: #92a0b5; }
.subtitle { margin-bottom: 0; }
.header-status { border: 1px solid #384356; border-radius: 999px; color: #b7c3d6; display: flex; align-items: center; gap: 9px; padding: 9px 13px; white-space: nowrap; }
.status-dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.status-dot.blocked { background: #e5a84b; box-shadow: 0 0 0 4px #e5a84b1c; }
.status-dot.ready { background: #67d49a; box-shadow: 0 0 0 4px #67d49a1c; }
.status-dot.warning { background: #e5a84b; box-shadow: 0 0 0 4px #e5a84b1c; }
.status-dot.error { background: #ef7373; box-shadow: 0 0 0 4px #ef73731c; }
.tabs { display: flex; gap: 4px; border-bottom: 1px solid #2c3442; margin-bottom: 24px; }
.tab { background: transparent; border: 0; color: #92a0b5; padding: 12px 14px; border-bottom: 2px solid transparent; }
.tab:hover, .tab.active { color: #edf1f7; border-bottom-color: #6fb3ff; }
.content-grid, .diagnosis-layout, .settings-layout { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.diagnosis-layout, .settings-layout { grid-template-columns: minmax(0, 1.35fr) minmax(300px, .65fr); }
.card { min-width: 0; align-self: start; background: #1a1f28; border: 1px solid #2c3442; border-radius: 12px; padding: 22px; box-shadow: 0 12px 30px #080a0f30; }
.span-2 { grid-column: span 2; }
.decision-reason { font-size: 20px; line-height: 1.5; }
.rule-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; margin-top: 22px; }
.rule { border-top: 1px solid #384356; padding-top: 16px; }
.rule p { color: #b7c3d6; line-height: 1.5; margin: 8px 0 0; }
.operation-card .facts { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.operation-card .toggle { margin-block: 18px; font-size: 14px; line-height: 1.5; }
.stop-button { margin-top: 14px; }
select { color: #edf1f7; background: #12171e; padding: 10px; border: 1px solid #3a4657; border-radius: 8px; font: inherit; }
button:disabled { cursor: not-allowed; opacity: .55; }
select:focus-visible { outline: 3px solid #6fb3ff; outline-offset: 2px; }
.hero-card { background: linear-gradient(140deg, #202a38, #1a1f28 60%); }
.card-heading, .candidate-top, .metric-strip, .profile-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.badge { background: #273243; border: 1px solid #40516a; border-radius: 999px; color: #c9d5e7; font-size: 11px; font-weight: 700; letter-spacing: .08em; padding: 5px 9px; text-transform: uppercase; }
.badge.blocked, .badge.warning { background: #49371f; border-color: #765b30; color: #f0c477; }
.badge.ready { background: #1f4937; border-color: #397d5c; color: #9ce2b9; }
.badge.error { background: #4b2529; border-color: #87444b; color: #ffaaaa; }
.target-row { margin: 30px 0 24px; display: flex; align-items: baseline; gap: 12px; }
.target-value { font-size: clamp(48px, 9vw, 76px); font-weight: 700; letter-spacing: -.07em; }
.metric-strip { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; border-top: 1px solid #354051; padding-top: 16px; align-items: flex-start; }
.metric-strip div { display: grid; gap: 5px; min-width: 0; }
.metric-strip span, dt, .profile-header { color: #92a0b5; font-size: 12px; }
.metric-strip strong { color: #edf1f7; font-size: 13px; overflow-wrap: anywhere; }
.facts { display: grid; gap: 13px; margin: 25px 0 20px; }
.facts div { display: flex; justify-content: space-between; gap: 18px; border-bottom: 1px solid #2c3442; padding-bottom: 10px; }
dd { margin: 0; color: #d7e0ed; text-align: right; overflow-wrap: anywhere; }
.callout { background: #252c38; border-left: 3px solid #6fb3ff; color: #c9d5e7; font-size: 13px; margin: 0; padding: 11px 13px; }
.candidate-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-top: 20px; }
.candidate { background: #202630; border: 1px solid #303b4d; border-radius: 8px; padding: 13px; min-width: 0; }
.candidate.active { border-color: #527ca6; background: #202e3d; }
.candidate.paused { border-color: #735b34; background: #30291f; }
.candidate p { color: #b4c0d1; font-size: 12px; line-height: 1.45; margin: 10px 0; }
.candidate small { color: #7f8da1; display: block; font-size: 11px; overflow-wrap: anywhere; }
.candidate-top strong { font-size: 13px; }
.candidate-top span { color: #edf1f7; font-size: 14px; font-weight: 700; white-space: nowrap; }
.empty-state { color: #92a0b5; }
.side-stack { display: grid; gap: 16px; align-content: start; }
.trace-list { display: grid; gap: 8px; margin-top: 20px; }
.trace-list .candidate { border-radius: 8px; }
.plain-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 9px; }
.plain-list li { display: flex; justify-content: space-between; gap: 18px; color: #c6d0df; font-size: 13px; }
.plain-list span { color: #92a0b5; text-align: right; }
.source-list { display: grid; gap: 9px; margin-top: 16px; }
.source-list div { display: grid; grid-template-columns: minmax(0, .8fr) minmax(0, 1.2fr); gap: 12px; align-items: center; border-bottom: 1px solid #2c3442; padding-bottom: 9px; }
.source-list span { color: #b7c3d6; font-size: 12px; }
code { color: #91c8ff; font-size: 11px; overflow-wrap: anywhere; text-align: right; }
details { margin-top: 16px; }
summary { color: #b7c3d6; cursor: pointer; font-size: 13px; }
pre { background: #12171e; border: 1px solid #2c3442; border-radius: 8px; color: #b9d8f4; font-size: 11px; line-height: 1.5; margin: 12px 0 0; max-height: 300px; overflow: auto; padding: 12px; white-space: pre-wrap; }
.form-grid, .calibration-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin-top: 22px; }
label { color: #b7c3d6; display: grid; gap: 7px; font-size: 12px; }
input[type='number'] { background: #12171e; border: 1px solid #3a4657; border-radius: 8px; color: #edf1f7; min-height: 40px; padding: 8px 10px; width: 100%; }
input:focus-visible, button:focus-visible { outline: 3px solid #6fb3ff; outline-offset: 2px; }
.toggle { align-items: center; display: flex; gap: 8px; min-height: 40px; }
.toggle input { accent-color: #6fb3ff; width: 18px; height: 18px; }
.hint { font-size: 12px; line-height: 1.5; margin: 18px 0 0; }
.quiet-button { background: transparent; border: 1px solid #3a4657; border-radius: 8px; color: #b7c3d6; padding: 8px 11px; }
.quiet-button:hover { border-color: #6fb3ff; color: #edf1f7; }
.primary-button { background: #6fb3ff; border: 1px solid #8bc5ff; border-radius: 8px; color: #101820; padding: 8px 11px; font-weight: 700; }
.primary-button:disabled { cursor: not-allowed; opacity: .55; }
.button-row { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; }
.binding-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin-top: 20px; }
input[type='text'] { background: #12171e; border: 1px solid #3a4657; border-radius: 8px; color: #edf1f7; min-height: 40px; padding: 8px 10px; width: 100%; }
.ready { color: #9ce2b9; }
.warning { color: #f0c477; }
.error { color: #ffaaaa; }
.profile-table { margin-top: 20px; }
.profile-row { border-bottom: 1px solid #2c3442; display: grid; grid-template-columns: minmax(0, 1.4fr) repeat(2, minmax(90px, .6fr)); padding: 10px 0; }
.profile-row strong { color: #d7e0ed; font-size: 13px; }
.profile-row input { min-height: 34px; }
.profile-header { border-bottom-color: #465469; font-weight: 700; padding-top: 0; }

@media (max-width: 820px) {
  .rule-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .operation-card .facts { grid-template-columns: 1fr; }
  .panel-root { padding: 22px 16px; }
  .app-header { display: grid; }
  .content-grid, .diagnosis-layout, .settings-layout { grid-template-columns: 1fr; }
  .span-2 { grid-column: auto; }
  .candidate-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 520px) {
  .rule-grid { grid-template-columns: 1fr; }
  .candidate-grid, .form-grid, .calibration-grid, .binding-grid { grid-template-columns: 1fr; }
  .metric-strip { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .metric-strip div:last-child { grid-column: span 2; }
  .plain-list li { display: grid; gap: 4px; }
  .plain-list span { text-align: left; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior: auto !important; transition-duration: .01ms !important; animation-duration: .01ms !important; }
}
`;
class BlindControlPanel extends HTMLElement {
  constructor() {
    super();
    __publicField(this, "app");
    __publicField(this, "hassContext");
    __publicField(this, "panelRoot");
    this.panelRoot = this.attachShadow({ mode: "open" });
  }
  set hass(value) {
    if (this.hassContext) {
      this.hassContext.connection = value.connection;
    } else {
      this.hassContext = { connection: value.connection };
    }
    this.mountWhenReady();
  }
  get hass() {
    return this.hassContext;
  }
  connectedCallback() {
    this.mountWhenReady();
  }
  disconnectedCallback() {
    if (this.app) {
      unmount(this.app);
      this.app = void 0;
    }
  }
  mountWhenReady() {
    if (!this.isConnected || !this.hassContext || this.app) return;
    this.ensureStyles();
    this.app = mount(Shell, {
      target: this.panelRoot,
      props: { hass: this.hassContext }
    });
  }
  ensureStyles() {
    if (this.panelRoot.querySelector("style[data-blind-control-style]")) return;
    const style = document.createElement("style");
    style.dataset.blindControlStyle = "";
    style.textContent = panelCss;
    this.panelRoot.prepend(style);
  }
}
customElements.define("blind-control-panel", BlindControlPanel);
