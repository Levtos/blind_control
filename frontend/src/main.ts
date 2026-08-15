import { mount, unmount } from 'svelte';
import Shell from './Shell.svelte';
import type { HassContext } from './lib/transport';
import panelCss from './app.css?inline';

class BlindControlPanel extends HTMLElement {
  private app: ReturnType<typeof mount> | undefined;
  private hassContext: HassContext | undefined;

  set hass(value: HassContext) {
    if (this.hassContext) {
      this.hassContext.connection = value.connection;
    } else {
      this.hassContext = { connection: value.connection };
    }
    this.mountWhenReady();
  }

  get hass(): HassContext | undefined {
    return this.hassContext;
  }

  connectedCallback(): void {
    this.mountWhenReady();
  }

  disconnectedCallback(): void {
    if (this.app) {
      unmount(this.app);
      this.app = undefined;
    }
  }

  private mountWhenReady(): void {
    if (!this.isConnected || !this.hassContext || this.app) return;
    this.ensureStyles();
    this.app = mount(Shell, {
      target: this,
      props: { hass: this.hassContext },
    });
  }

  private ensureStyles(): void {
    if (this.querySelector('style[data-blind-control-style]')) return;
    const style = document.createElement('style');
    style.dataset.blindControlStyle = '';
    style.textContent = panelCss;
    this.prepend(style);
  }
}

customElements.define('blind-control-panel', BlindControlPanel);
