import React from 'react';
import { Paper, Tabs, Tab } from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { useAppState } from '../state/AppState';

export const ResultsPage: React.FC = () => {
  const { result } = useAppState();
  const [tab, setTab] = React.useState<'fused' | 'a_enriched' | 'b_enriched'>('fused');

  const rows = React.useMemo(() => {
    const data = (result as any)?.[tab] as Array<Record<string, any>> | undefined;
    return (data || []).map((r, i) => ({ id: i, ...r }));
  }, [result, tab]);

  const columns: GridColDef[] = React.useMemo(() => {
    const first = rows?.[0];
    if (!first) return [];
    return Object.keys(first).filter(k => k !== 'id').map((k) => ({ field: k, headerName: k, flex: 1 }));
  }, [rows]);

  return (
    <Paper sx={{ p: 2, height: '80vh' }}>
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 1 }}>
        <Tab label="Fused" value="fused" />
        <Tab label="A Enriched" value="a_enriched" />
        <Tab label="B Enriched" value="b_enriched" />
      </Tabs>
      <div style={{ height: 'calc(100% - 48px)' }}>
        <DataGrid rows={rows} columns={columns} density="compact" disableRowSelectionOnClick pagination autoPageSize />
      </div>
    </Paper>
  );
};

