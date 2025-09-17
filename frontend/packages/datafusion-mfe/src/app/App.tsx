import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createTheme, CssBaseline, ThemeProvider } from '@mui/material';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { I18nProvider } from './i18n/i18n';
import { Layout } from './components/Layout';
import { UploadPage } from './pages/UploadPage';
import { OverlapPage } from './pages/OverlapPage';
import { TargetsPage } from './pages/TargetsPage';
import { SettingsPage } from './pages/SettingsPage';
import { ResultsPage } from './pages/ResultsPage';
import { AppStateProvider } from './state/AppState';

export type RuntimeConfig = {
  apiBase?: string;
  authEnabled?: boolean;
  jwtToken?: string;
  lang?: 'en' | 'de';
  maxUploadMb?: number;
  persistenceEnabled?: boolean;
};

const queryClient = new QueryClient();

type AppProps = {
  runtimeConfig?: RuntimeConfig;
};

export const App: React.FC<AppProps> = ({ runtimeConfig }) => {
  const theme = React.useMemo(() => createTheme({ palette: { mode: 'light' } }), []);
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <I18nProvider defaultLang={runtimeConfig?.lang ?? (window as any).__DATAFUSION_CONFIG__?.defaultLang ?? 'en'}>
        <QueryClientProvider client={queryClient}>
          <AppStateProvider runtime={{
            apiBase: runtimeConfig?.apiBase ?? (window as any).__DATAFUSION_CONFIG__?.apiBase,
            authEnabled: runtimeConfig?.authEnabled ?? (window as any).__DATAFUSION_CONFIG__?.authEnabled,
            jwtToken: runtimeConfig?.jwtToken ?? (window as any).__DATAFUSION_CONFIG__?.jwtToken,
            lang: runtimeConfig?.lang ?? (window as any).__DATAFUSION_CONFIG__?.defaultLang ?? 'en',
            maxUploadMb: runtimeConfig?.maxUploadMb ?? (window as any).__DATAFUSION_CONFIG__?.maxUploadMb ?? 20,
            persistenceEnabled: runtimeConfig?.persistenceEnabled ?? (window as any).__DATAFUSION_CONFIG__?.persistenceEnabled,
          }}>
            <BrowserRouter>
              <Layout>
                <Routes>
                  <Route path="/" element={<UploadPage />} />
                  <Route path="/overlap" element={<OverlapPage />} />
                  <Route path="/targets" element={<TargetsPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                  <Route path="/results" element={<ResultsPage />} />
                </Routes>
              </Layout>
            </BrowserRouter>
          </AppStateProvider>
        </QueryClientProvider>
      </I18nProvider>
    </ThemeProvider>
  );
};

