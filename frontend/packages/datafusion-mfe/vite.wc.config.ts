import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    lib: {
      entry: 'src/wc.tsx',
      name: 'DatafusionApp',
      fileName: () => 'web-component.js',
      formats: ['es']
    },
    rollupOptions: {
      output: { inlineDynamicImports: true }
    },
    outDir: 'dist-wc'
  }
});

