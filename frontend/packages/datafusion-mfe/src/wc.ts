import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './app/App';

class DatafusionAppElement extends HTMLElement {
  private root?: ReactDOM.Root;

  static get observedAttributes() {
    return ['api-base', 'auth-enabled', 'jwt-token', 'lang', 'max-upload-mb', 'persistence-enabled'];
  }

  connectedCallback() {
    const shadow = this.attachShadow({ mode: 'open' });
    const mountPoint = document.createElement('div');
    shadow.appendChild(mountPoint);
    this.root = ReactDOM.createRoot(mountPoint);
    this.render();
  }

  attributeChangedCallback() {
    this.render();
  }

  disconnectedCallback() {
    this.root?.unmount();
  }

  private readConfig() {
    const attr = (name: string) => this.getAttribute(name);
    return {
      apiBase: attr('api-base') ?? (window as any).__DATAFUSION_CONFIG__?.apiBase,
      authEnabled: this.hasAttribute('auth-enabled') || (window as any).__DATAFUSION_CONFIG__?.authEnabled,
      jwtToken: attr('jwt-token') ?? (window as any).__DATAFUSION_CONFIG__?.jwtToken,
      lang: attr('lang') ?? (window as any).__DATAFUSION_CONFIG__?.defaultLang ?? 'en',
      maxUploadMb: Number(attr('max-upload-mb') ?? (window as any).__DATAFUSION_CONFIG__?.maxUploadMb ?? 20),
      persistenceEnabled: this.hasAttribute('persistence-enabled') || (window as any).__DATAFUSION_CONFIG__?.persistenceEnabled,
    } as const;
  }

  private render() {
    const cfg = this.readConfig();
    this.root?.render(
      <React.StrictMode>
        <App runtimeConfig={cfg} />
      </React.StrictMode>
    );
  }
}

customElements.define('datafusion-app', DatafusionAppElement);

