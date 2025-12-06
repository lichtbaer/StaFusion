import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ApiClient } from './client';

// Mock global fetch
global.fetch = vi.fn();

describe('ApiClient', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (global.fetch as any).mockClear();
  });

  it('should initialize with default config', () => {
    const client = new ApiClient();
    expect(client).toBeInstanceOf(ApiClient);
  });

  it('should initialize with custom config', () => {
    const client = new ApiClient({
      apiBase: 'http://example.com',
      authEnabled: true,
      jwtToken: 'test-token',
    });
    expect(client).toBeInstanceOf(ApiClient);
  });

  it('should make GET request', async () => {
    const mockResponse = { data: 'test' };
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
      headers: new Headers({ 'content-type': 'application/json' }),
    });

    const client = new ApiClient({ apiBase: 'http://example.com' });
    const result = await client.get('/test');

    expect(global.fetch).toHaveBeenCalledWith(
      'http://example.com/test',
      expect.objectContaining({
        method: 'GET',
      })
    );
    expect(result).toEqual(mockResponse);
  });

  it('should make POST request with JSON body', async () => {
    const mockResponse = { success: true };
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
      headers: new Headers({ 'content-type': 'application/json' }),
    });

    const client = new ApiClient({ apiBase: 'http://example.com' });
    const body = { test: 'data' };
    const result = await client.post('/test', body);

    expect(global.fetch).toHaveBeenCalledWith(
      'http://example.com/test',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(body),
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
      })
    );
    expect(result).toEqual(mockResponse);
  });

  it('should add Authorization header when auth is enabled', async () => {
    const mockResponse = { data: 'test' };
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
      headers: new Headers({ 'content-type': 'application/json' }),
    });

    const client = new ApiClient({
      apiBase: 'http://example.com',
      authEnabled: true,
      jwtToken: 'test-token',
    });
    await client.get('/test');

    expect(global.fetch).toHaveBeenCalledWith(
      'http://example.com/test',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer test-token',
        }),
      })
    );
  });

  it('should handle errors', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
      status: 404,
      text: async () => 'Not Found',
    });

    const client = new ApiClient({ apiBase: 'http://example.com' });

    await expect(client.get('/test')).rejects.toThrow('HTTP 404: Not Found');
  });

  it('should start async job', async () => {
    const mockResponse = { job_id: 'test-job-id' };
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
      headers: new Headers({ 'content-type': 'application/json' }),
    });

    const client = new ApiClient({ apiBase: 'http://example.com' });
    const body = { df_a: [], df_b: [] };
    const result = await client.startAsync(body);

    expect(global.fetch).toHaveBeenCalledWith(
      'http://example.com/v1/fuse/async',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify(body),
      })
    );
    expect(result).toEqual(mockResponse);
  });

  it('should get job status', async () => {
    const mockResponse = { status: 'pending' };
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
      headers: new Headers({ 'content-type': 'application/json' }),
    });

    const client = new ApiClient({ apiBase: 'http://example.com' });
    const result = await client.getJob('test-job-id');

    expect(global.fetch).toHaveBeenCalledWith(
      'http://example.com/v1/fuse/async/test-job-id',
      expect.objectContaining({
        method: 'GET',
      })
    );
    expect(result).toEqual(mockResponse);
  });
});
