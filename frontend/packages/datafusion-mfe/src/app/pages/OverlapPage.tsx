import React from 'react';
import { Paper, Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';

export const OverlapPage: React.FC = () => {
  const { t } = useTranslation();
  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>{t('overlap')}</Typography>
      <Typography variant="body2">Konfiguration der Überlappungsmerkmale folgt.</Typography>
    </Paper>
  );
};

