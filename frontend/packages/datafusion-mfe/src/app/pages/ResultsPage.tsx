import React from 'react';
import { Box, Button, Paper, Tabs, Tab } from '@mui/material';
import { DataGrid, GridColDef, GridToolbarColumnsButton, GridToolbarContainer, GridToolbarDensitySelector, GridToolbarFilterButton } from '@mui/x-data-grid';
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
      <Box display="flex" gap={1} sx={{ mb: 1 }}>
        <Button size="small" variant="outlined" onClick={() => downloadJson(tab, rows)}>Download JSON</Button>
        <Button size="small" variant="outlined" onClick={() => downloadCsv(tab, rows)}>Download CSV</Button>
      </Box>
      <div style={{ height: 'calc(100% - 88px)' }}>
        <DataGrid rows={rows} columns={columns} density="compact" disableRowSelectionOnClick pagination autoPageSize slots={{ toolbar: CustomToolbar }} />
      </div>
    </Paper>
  );
};

function CustomToolbar() {
  return (
    <GridToolbarContainer>
      <GridToolbarColumnsButton />
      <GridToolbarFilterButton />
      <GridToolbarDensitySelector />
    </GridToolbarContainer>
  );
}

function downloadJson(name: string, rows: any[]) {
  const data = rows.map(({ id, ...rest }) => rest);
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `${name}.json`; a.click(); URL.revokeObjectURL(url);
}

function downloadCsv(name: string, rows: any[]) {
  const data = rows.map(({ id, ...rest }) => rest);
  if (!data.length) return;
  const headers = Object.keys(data[0]);
  const lines = [headers.join(',')].concat(
    data.map(r => headers.map(h => csvEscape(r[h])).join(','))
  );
  const blob = new Blob([lines.join('\n')], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `${name}.csv`; a.click(); URL.revokeObjectURL(url);
}

function csvEscape(v: any): string {
  if (v == null) return '';
  const s = String(v);
  if (/[",\n]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
  return s;
}

