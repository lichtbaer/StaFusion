export type RequestConfig = {
  apiBase?: string;
  authEnabled?: boolean;
  jwtToken?: string;
};

export class ApiClient {
  private readonly apiBase: string;
  private readonly authEnabled: boolean;
  private readonly jwtToken?: string;

  constructor(cfg: RequestConfig = {}) {
    const globalCfg = (window as any).__DATAFUSION_CONFIG__ ?? {};
    this.apiBase = cfg.apiBase ?? globalCfg.apiBase ?? '';
    this.authEnabled = cfg.authEnabled ?? !!globalCfg.authEnabled;
    this.jwtToken = cfg.jwtToken ?? globalCfg.jwtToken;
  }

  async get(path: string, init: RequestInit = {}) {
    return this.request(path, { method: 'GET', ...init });
  }

  async post(path: string, body: any, init: RequestInit = {}) {
    return this.request(path, { method: 'POST', body: JSON.stringify(body), headers: { 'Content-Type': 'application/json', ...(init.headers || {}) }, ...init });
  }

  async postForm(path: string, form: FormData, init: RequestInit = {}) {
    // Let browser set multipart/form-data boundary
    return this.request(path, { method: 'POST', body: form, ...init });
  }

  async request(path: string, init: RequestInit = {}) {
    const headers = new Headers(init.headers);
    if (this.authEnabled && this.jwtToken) headers.set('Authorization', `Bearer ${this.jwtToken}`);
    const res = await fetch(this.apiBase + path, { ...init, headers });
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`HTTP ${res.status}: ${text}`);
    }
    const contentType = res.headers.get('content-type') || '';
    if (contentType.includes('application/json')) return res.json();
    return res.text();
  }
}

