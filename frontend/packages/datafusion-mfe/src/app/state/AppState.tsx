import React from 'react';
import { ApiClient } from '../api/client';
import type { RuntimeConfig } from '../App';

export type FuseResponse = {
  fused?: Array<Record<string, any>>;
  a_enriched?: Array<Record<string, any>>;
  b_enriched?: Array<Record<string, any>>;
  metrics_a_to_b?: Record<string, Record<string, number>>;
  metrics_b_to_a?: Record<string, Record<string, number>>;
};

export type AppSettings = {
  prefer_pycaret?: boolean;
  random_state?: number;
  row_limit?: number | null;
  overlap_features?: string[] | null;
  targets_from_a?: string[] | null;
  targets_from_b?: string[] | null;
  columns_include?: string[] | null;
  columns_exclude?: string[] | null;
};

export type AppState = {
  runtime: RuntimeConfig;
  client: ApiClient;
  fileA?: File;
  fileB?: File;
  settings: AppSettings;
  result?: FuseResponse;
  loading: boolean;
  error?: string;
  setFiles: (a?: File, b?: File) => void;
  setSettings: (s: Partial<AppSettings>) => void;
  resetResult: () => void;
  runUploadFusion: () => Promise<void>;
};

const AppStateContext = React.createContext<AppState | undefined>(undefined);

export const AppStateProvider: React.FC<React.PropsWithChildren<{ runtime: RuntimeConfig }>> = ({ runtime, children }) => {
  const client = React.useMemo(() => new ApiClient({ apiBase: runtime.apiBase, authEnabled: runtime.authEnabled, jwtToken: runtime.jwtToken }), [runtime.apiBase, runtime.authEnabled, runtime.jwtToken]);
  const [fileA, setFileA] = React.useState<File | undefined>(undefined);
  const [fileB, setFileB] = React.useState<File | undefined>(undefined);
  const [settings, setSettingsState] = React.useState<AppSettings>({ prefer_pycaret: true, random_state: 42, row_limit: null, overlap_features: null, targets_from_a: null, targets_from_b: null, columns_include: null, columns_exclude: null });
  const [result, setResult] = React.useState<FuseResponse | undefined>(undefined);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | undefined>(undefined);

  const setFiles = (a?: File, b?: File) => { setFileA(a); setFileB(b); };
  const setSettings = (s: Partial<AppSettings>) => { setSettingsState(prev => ({ ...prev, ...s })); };
  const resetResult = () => setResult(undefined);

  const runUploadFusion = async () => {
    if (!fileA || !fileB) { setError('Both files are required'); return; }
    setLoading(true); setError(undefined);
    try {
      const form = new FormData();
      form.append('file_a', fileA, fileA.name);
      form.append('file_b', fileB, fileB.name);
      if (settings.overlap_features) settings.overlap_features.forEach(v => form.append('overlap_features', v));
      if (settings.targets_from_a) settings.targets_from_a.forEach(v => form.append('targets_from_a', v));
      if (settings.targets_from_b) settings.targets_from_b.forEach(v => form.append('targets_from_b', v));
      if (typeof settings.prefer_pycaret === 'boolean') form.append('prefer_pycaret', String(settings.prefer_pycaret));
      if (typeof settings.random_state === 'number') form.append('random_state', String(settings.random_state));
      if (Array.isArray(settings.columns_include)) settings.columns_include.forEach(v => form.append('columns_include', v));
      if (Array.isArray(settings.columns_exclude)) settings.columns_exclude.forEach(v => form.append('columns_exclude', v));
      if (typeof settings.row_limit === 'number') form.append('row_limit', String(settings.row_limit));

      const res = await client.postForm('/v1/fuse/upload', form);
      setResult(res as FuseResponse);
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  const value: AppState = {
    runtime,
    client,
    fileA,
    fileB,
    settings,
    result,
    loading,
    error,
    setFiles,
    setSettings,
    resetResult,
    runUploadFusion
  };

  return <AppStateContext.Provider value={value}>{children}</AppStateContext.Provider>;
};

export const useAppState = (): AppState => {
  const ctx = React.useContext(AppStateContext);
  if (!ctx) throw new Error('useAppState must be used within AppStateProvider');
  return ctx;
};

