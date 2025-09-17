import React from 'react';
import { Alert, Box, Paper, Typography } from '@mui/material';
import { useDropzone } from 'react-dropzone';

export type FileDropProps = {
  label: string;
  accept?: string[]; // extensions: ['.csv', '.parquet']
  maxBytes: number;
  onFile: (file: File | undefined) => void;
  previewCsv?: boolean;
};

export const FileDrop: React.FC<FileDropProps> = ({ label, accept = ['.csv', '.parquet'], maxBytes, onFile, previewCsv }) => {
  const [error, setError] = React.useState<string | undefined>(undefined);
  const [file, setFile] = React.useState<File | undefined>(undefined);
  const [csvPreview, setCsvPreview] = React.useState<string[][] | undefined>(undefined);

  const onDrop = React.useCallback((accepted: File[]) => {
    const f = accepted[0];
    if (!f) return;
    if (f.size > maxBytes) {
      setError(`File too large. Limit ${(maxBytes / (1024 * 1024)).toFixed(0)} MB`);
      return;
    }
    setError(undefined);
    setFile(f);
    onFile(f);
    if (previewCsv && f.name.toLowerCase().endsWith('.csv')) {
      // Parse a small preview quickly
      f.slice(0, Math.min(f.size, 200 * 1024)).text().then(text => {
        const lines = text.split(/\r?\n/).slice(0, 6);
        const cells = lines.map(l => l.split(','));
        setCsvPreview(cells);
      }).catch(() => setCsvPreview(undefined));
    } else {
      setCsvPreview(undefined);
    }
  }, [maxBytes, onFile, previewCsv]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, multiple: false, accept: accept.reduce((acc, ext) => ({ ...acc, [ext]: [] }), {} as any) });

  return (
    <Box>
      <Typography variant="subtitle2" gutterBottom>{label}</Typography>
      <Paper variant="outlined" {...getRootProps()} sx={{ p: 2, textAlign: 'center', borderStyle: 'dashed', cursor: 'pointer', bgcolor: isDragActive ? 'action.hover' : 'inherit' }}>
        <input {...getInputProps()} />
        <Typography variant="body2">{isDragActive ? 'Drop the file here…' : 'Drag & drop or click to select (CSV/Parquet)'}</Typography>
        {file && <Typography variant="caption" display="block" sx={{ mt: 1 }}>{file.name} ({(file.size / (1024 * 1024)).toFixed(2)} MB)</Typography>}
      </Paper>
      {error && <Alert severity="error" sx={{ mt: 1 }}>{error}</Alert>}
      {csvPreview && (
        <Box sx={{ mt: 1, overflow: 'auto' }}>
          <Typography variant="caption">CSV preview (first rows):</Typography>
          <Box component="table" sx={{ width: '100%', borderCollapse: 'collapse' }}>
            <tbody>
              {csvPreview.map((row, i) => (
                <tr key={i}>
                  {row.map((cell, j) => (
                    <td key={j} style={{ border: '1px solid #ddd', padding: 4, fontSize: 12 }}>{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </Box>
        </Box>
      )}
    </Box>
  );
};