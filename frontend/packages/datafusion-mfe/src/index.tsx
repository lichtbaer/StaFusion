import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './app/App';

declare global {
  interface Window { __DATAFUSION_CONFIG__?: Record<string, unknown>; }
}

const rootEl = document.getElementById('root')!;
ReactDOM.createRoot(rootEl).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

