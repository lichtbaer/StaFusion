import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { AppStateProvider, useAppState, type AppSettings } from './AppState';
import { ApiClient } from '../api/client';

// Mock ApiClient
vi.mock('../api/client');

describe('AppState', () => {
  const mockRuntime = {
    apiBase: 'http://localhost:8000',
    authEnabled: false,
    jwtToken: undefined,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with default settings', () => {
    const { result } = renderHook(() => useAppState(), {
      wrapper: ({ children }) => (
        <AppStateProvider runtime={mockRuntime}>{children}</AppStateProvider>
      ),
    });

    expect(result.current.settings).toEqual({
      prefer_pycaret: true,
      random_state: 42,
      row_limit: null,
      overlap_features: null,
      targets_from_a: null,
      targets_from_b: null,
      columns_include: null,
      columns_exclude: null,
    });
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeUndefined();
    expect(result.current.result).toBeUndefined();
  });

  it('should set files', () => {
    const { result } = renderHook(() => useAppState(), {
      wrapper: ({ children }) => (
        <AppStateProvider runtime={mockRuntime}>{children}</AppStateProvider>
      ),
    });

    const fileA = new File(['content'], 'a.csv', { type: 'text/csv' });
    const fileB = new File(['content'], 'b.csv', { type: 'text/csv' });

    act(() => {
      result.current.setFiles(fileA, fileB);
    });

    expect(result.current.fileA).toBe(fileA);
    expect(result.current.fileB).toBe(fileB);
  });

  it('should update settings', () => {
    const { result } = renderHook(() => useAppState(), {
      wrapper: ({ children }) => (
        <AppStateProvider runtime={mockRuntime}>{children}</AppStateProvider>
      ),
    });

    const newSettings: Partial<AppSettings> = {
      prefer_pycaret: false,
      random_state: 100,
      row_limit: 50,
    };

    act(() => {
      result.current.setSettings(newSettings);
    });

    expect(result.current.settings.prefer_pycaret).toBe(false);
    expect(result.current.settings.random_state).toBe(100);
    expect(result.current.settings.row_limit).toBe(50);
  });

  it('should reset result', () => {
    const { result } = renderHook(() => useAppState(), {
      wrapper: ({ children }) => (
        <AppStateProvider runtime={mockRuntime}>{children}</AppStateProvider>
      ),
    });

    // Set a result first
    act(() => {
      (result.current as any).setResult({ fused: [{ test: 1 }] });
    });

    expect((result.current as any).result).toBeDefined();

    act(() => {
      result.current.resetResult();
    });

    expect(result.current.result).toBeUndefined();
  });

  it('should export and import config', () => {
    const { result } = renderHook(() => useAppState(), {
      wrapper: ({ children }) => (
        <AppStateProvider runtime={mockRuntime}>{children}</AppStateProvider>
      ),
    });

    // Update settings
    act(() => {
      result.current.setSettings({ prefer_pycaret: false, random_state: 99 });
    });

    // Export config
    const exported = result.current.exportConfig();
    expect(exported).toContain('"prefer_pycaret": false');
    expect(exported).toContain('"random_state": 99');

    // Reset settings
    act(() => {
      result.current.setSettings({ prefer_pycaret: true, random_state: 42 });
    });

    // Import config
    act(() => {
      result.current.importConfig(exported);
    });

    expect(result.current.settings.prefer_pycaret).toBe(false);
    expect(result.current.settings.random_state).toBe(99);
  });

  it('should clear job', () => {
    const { result } = renderHook(() => useAppState(), {
      wrapper: ({ children }) => (
        <AppStateProvider runtime={mockRuntime}>{children}</AppStateProvider>
      ),
    });

    // Set job state
    act(() => {
      (result.current as any).setJobId('test-job-id');
      (result.current as any).setJobStatus('pending');
    });

    expect((result.current as any).jobId).toBe('test-job-id');
    expect((result.current as any).jobStatus).toBe('pending');

    // Clear job
    act(() => {
      result.current.clearJob();
    });

    expect(result.current.jobId).toBeUndefined();
    expect(result.current.jobStatus).toBeUndefined();
  });
});
