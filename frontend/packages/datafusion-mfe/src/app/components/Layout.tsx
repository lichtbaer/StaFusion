import React from 'react';
import { AppBar, Box, Button, Container, Toolbar, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { LanguageSwitcher } from '../i18n/LanguageSwitcher';

export const Layout: React.FC<React.PropsWithChildren> = ({ children }) => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>Datafusion</Typography>
          <Button color="inherit" component={RouterLink} to="/">Upload</Button>
          <Button color="inherit" component={RouterLink} to="/overlap">Overlap</Button>
          <Button color="inherit" component={RouterLink} to="/targets">Targets</Button>
          <Button color="inherit" component={RouterLink} to="/settings">Settings</Button>
          <Button color="inherit" component={RouterLink} to="/results">Results</Button>
          <LanguageSwitcher />
        </Toolbar>
      </AppBar>
      <Container sx={{ py: 3, flexGrow: 1 }}>
        {children}
      </Container>
    </Box>
  );
};

