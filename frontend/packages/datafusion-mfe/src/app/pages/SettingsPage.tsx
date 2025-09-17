import React from 'react';
import { Alert, Box, Button, Paper, Stack, TextField, Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useAppState } from '../state/AppState';

export const SettingsPage: React.FC = () => {
  const { t } = useTranslation();
  const { settings, setSettings, exportConfig, importConfig, runAsyncJson, loading, error, jobId, jobStatus, pollJob, clearJob } = useAppState();
  const [jsonA, setJsonA] = React.useState<string>('[\n  { "age_group": "18-29" }\n]');
  const [jsonB, setJsonB] = React.useState<string>('[\n  { "age_group": "18-29" }\n]');

  React.useEffect(() => {
    let timer: any;
    if (jobId && jobStatus === 'pending') {
      timer = setInterval(() => { pollJob(); }, 1500);
    }
    return () => { if (timer) clearInterval(timer); };
  }, [jobId, jobStatus, pollJob]);

  const onExport = () => {
    const blob = new Blob([exportConfig()], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'datafusion-config.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const onImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    f.text().then(importConfig).catch(err => alert(err?.message || String(err)));
  };

  const onRunAsync = async () => {
    try {
      const df_a = JSON.parse(jsonA);
      const df_b = JSON.parse(jsonB);
      await runAsyncJson({ df_a, df_b, ...settings });
    } catch (e: any) {
      alert(e?.message || String(e));
    }
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>{t('settings')}</Typography>
      <Stack spacing={2}>
        <Box display="flex" gap={2}>
          <TextField label="random_state" type="number" value={settings.random_state ?? ''} onChange={e => setSettings({ random_state: Number(e.target.value) })} />
          <TextField label="row_limit" type="number" value={settings.row_limit ?? ''} onChange={e => setSettings({ row_limit: e.target.value === '' ? null : Number(e.target.value) })} />
        </Box>
        <Box display="flex" gap={2}>
          <Button variant="outlined" onClick={onExport}>Export Config</Button>
          <Button variant="outlined" component="label">
            Import Config
            <input type="file" accept="application/json" hidden onChange={onImport} />
          </Button>
        </Box>
        <Typography variant="h6">Async (JSON) run</Typography>
        <Box display="flex" gap={2}>
          <TextField label="df_a JSON" value={jsonA} onChange={(e) => setJsonA(e.target.value)} fullWidth multiline minRows={6} />
          <TextField label="df_b JSON" value={jsonB} onChange={(e) => setJsonB(e.target.value)} fullWidth multiline minRows={6} />
        </Box>
        <Box display="flex" gap={2}>
          <Button variant="contained" onClick={onRunAsync} disabled={loading}>Start Async</Button>
          {jobId && <Button variant="outlined" onClick={clearJob}>Clear Job</Button>}
          {jobId && <Typography variant="body2">Job: {jobId} — Status: {jobStatus}</Typography>}
        </Box>
        {error && <Alert severity="error">{error}</Alert>}
      </Stack>
    </Paper>
  );
};

