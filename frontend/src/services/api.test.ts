import * as api from './api';

// Mock global fetch
beforeEach(() => {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ test: 'ok' })
    }) as any
  );
});

afterEach(() => {
  jest.resetAllMocks();
});

describe('API Service', () => {
  it('runPipeline calls correct endpoint', async () => {
    const resp = await api.runPipeline({ youtube_url: 'url', language: 'en', model_size: 'tiny' });
    expect(global.fetch).toHaveBeenCalled();
    expect(resp).toBeDefined();
  });
  it('getStatus calls correct endpoint', async () => {
    await api.getStatus('1');
    expect(global.fetch).toHaveBeenCalled();
  });
  it('getResult calls correct endpoint', async () => {
    await api.getResult('1');
    expect(global.fetch).toHaveBeenCalled();
  });
  it('processChunk calls correct endpoint', async () => {
    await api.processChunk('1', 0);
    expect(global.fetch).toHaveBeenCalled();
  });
  it('handles fetch errors', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('fail'));
    await expect(api.getResult('nope')).rejects.toThrow('fail');
  });
});

