import React from 'react';
import { Box, Button, Paper, Typography, Alert } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useAppState } from '../state/AppState';
import { FileDrop } from '../components/FileDrop';

export const UploadPage: React.FC = () => {
  const { t } = useTranslation();
  const nav = useNavigate();
  const { setFiles, runUploadFusion, loading, error, runtime } = useAppState();
  const [a, setA] = React.useState<File | undefined>();
  const [b, setB] = React.useState<File | undefined>();

  const onChange = (setter: (f: File | undefined) => void) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) { setter(undefined); return; }
    const max = (runtime.maxUploadMb ?? 20) * 1024 * 1024;
    if (f.size > max) { alert(`File too large. Limit ${runtime.maxUploadMb} MB`); return; }
    setter(f);
  };

  const onRun = async () => {
    setFiles(a, b);
    await runUploadFusion();
    nav('/results');
  };
  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>{t('upload')}</Typography>
      <Box display="flex" gap={2}>
        <FileDrop label="Dataset A" maxBytes={(runtime.maxUploadMb ?? 20) * 1024 * 1024} onFile={setA} previewCsv />
        <FileDrop label="Dataset B" maxBytes={(runtime.maxUploadMb ?? 20) * 1024 * 1024} onFile={setB} previewCsv />
      </Box>
      {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
      <Box mt={2}>
        <Button variant="contained" onClick={onRun} disabled={!a || !b || loading}>{loading ? 'Running…' : 'Run Fusion'}</Button>
      </Box>
    </Paper>
  );
};

