import React from 'react';
import { Paper, Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';

export const ResultsPage: React.FC = () => {
  const { t } = useTranslation();
  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>{t('results')}</Typography>
      <Typography variant="body2">Ergebnisdarstellung (MUI Data Grid) folgt.</Typography>
    </Paper>
  );
};

