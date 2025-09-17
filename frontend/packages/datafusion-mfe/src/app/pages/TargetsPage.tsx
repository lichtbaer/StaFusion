import React from 'react';
import { Paper, Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';

export const TargetsPage: React.FC = () => {
  const { t } = useTranslation();
  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>{t('targets')}</Typography>
      <Typography variant="body2">Auswahl der Zielvariablen folgt.</Typography>
    </Paper>
  );
};

