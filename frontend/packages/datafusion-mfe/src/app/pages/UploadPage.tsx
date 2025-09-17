import React from 'react';
import { Box, Button, Paper, Typography } from '@mui/material';
import { useTranslation } from 'react-i18next';

export const UploadPage: React.FC = () => {
  const { t } = useTranslation();
  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>{t('upload')}</Typography>
      <Box>
        <Typography variant="body2">CSV/Parquet Upload UI folgt (20 MB Limit).</Typography>
      </Box>
      <Box mt={2}>
        <Button variant="contained" disabled>Nächster Schritt</Button>
      </Box>
    </Paper>
  );
};

