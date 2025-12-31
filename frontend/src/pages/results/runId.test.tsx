import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { act } from 'react-dom/test-utils';
import { BrowserRouter } from 'react-router-dom';

import ResultsView from './ResultsViewNew';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({ runId: 'testid' })
}));

it('renders ResultsView with router context and params', () => {
  render(
    <BrowserRouter>
      <ResultsView />
    </BrowserRouter>
  );
});

beforeEach(() => {
  global.fetch = jest.fn().mockImplementation((input) => {
    if (typeof input === 'string' && input.includes('/status/')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ step: 'downloading' }),
      });
    }
    if (typeof input === 'string' && input.includes('/result/')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(null) });
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
  });
});

it('shows loading and processing status UI during pipeline run', async () => {
  render(
    <BrowserRouter>
      <ResultsView />
    </BrowserRouter>
  );
  expect(screen.getByText(/Processing Run/i)).toBeInTheDocument();
  await waitFor(() => {
    expect(
      screen.getAllByText((content, node) => !!node?.textContent && node.textContent.includes('Downloading')).length
    ).toBeGreaterThan(0);
  });
});

it('shows error message when API fetch fails', async () => {
  // Mock fetch to throw on /status/
  global.fetch = jest.fn().mockImplementation((input) => {
    if (typeof input === 'string' && input.includes('/status/')) {
      return Promise.reject(new Error('Network error'));
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
  });

  render(
    <BrowserRouter>
      <ResultsView />
    </BrowserRouter>
  );
  await waitFor(() => {
    expect(
      screen.getAllByText((content, node) => !!node?.textContent && node.textContent.includes('Error fetching pipeline status')).length
    ).toBeGreaterThan(0);
  });
});

it('shows download links and chunk selection in done state', async () => {
  // Mock fetch to immediately return 'done' and a mock result
  const mockResult = {
    webm_url: '/audio.webm',
    wav_url: '/audio.wav',
    caption_url: '/captions.vtt',
    chunkFiles: ['/chunk1.wav', '/chunk2.wav'],
  };
  global.fetch = jest.fn().mockImplementation((input) => {
    if (typeof input === 'string' && input.includes('/status/')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ step: 'done' }),
      });
    }
    if (typeof input === 'string' && input.includes('/result/')) {
      return Promise.resolve({
        ok: true, json: () => Promise.resolve(mockResult),
      });
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
  });

  render(
    <BrowserRouter>
      <ResultsView />
    </BrowserRouter>
  );

  jest.useFakeTimers();
  // Wait for post-processing message *to appear*
  await waitFor(() => {
    expect(screen.getByText(/Creating results, please wait/i)).toBeInTheDocument();
  });
  // Fast-forward the 2s post-processing timer
  act(() => {
    jest.runOnlyPendingTimers();
  });
  // Wait for post-processing to disappear and buttons/radios to show
  await waitFor(() => {
    expect(screen.queryByText(/Creating results, please wait/i)).not.toBeInTheDocument();
    expect(screen.getByText('WEBM')).toBeInTheDocument();
    expect(screen.getByText('WAV')).toBeInTheDocument();
    expect(screen.getByText('Captions')).toBeInTheDocument();
    expect(screen.getAllByRole('radio').length).toBeGreaterThanOrEqual(2);
  });
  jest.useRealTimers();

  // Chunk section label
  expect(
    screen.getAllByText((content, node) => !!node?.textContent && /Audio Chunks|Chunks|Chunk/i.test(node.textContent)).length
  ).toBeGreaterThan(0);
});

it('shows semantic matching score result after chunk comparison', async () => {
  // Arrange backend for done state and chunk comparison processing
  const mockResult = {
    webm_url: '/audio.webm',
    wav_url: '/audio.wav',
    caption_url: '/captions.vtt',
    chunkFiles: ['/chunk1.wav', '/chunk2.wav'],
  };
  const mockComparison = {
    similarity_percent: 91,
    transcript_url: '/transcript.txt',
    compare_text: 'ASR: something. Caption: something.',
    asr_text: 'something',
    caption_text: 'something else',
  };

  let processChunkCalled = false;

  global.fetch = jest.fn().mockImplementation((input) => {
    if (typeof input === 'string' && input.includes('/status/')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ step: 'done' }),
      });
    }
    if (typeof input === 'string' && input.includes('/result/') && input.includes('/process_chunk')) {
      processChunkCalled = true;
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mockComparison) });
    }
    if (typeof input === 'string' && input.includes('/result/')) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockResult),
      });
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
  });

  render(
    <BrowserRouter>
      <ResultsView />
    </BrowserRouter>
  );

  jest.useFakeTimers();
  // Wait for post-processing message *to appear*
  await waitFor(() => {
    expect(screen.getByText(/Creating results, please wait/i)).toBeInTheDocument();
  });
  // Fast-forward the 2s post-processing timer
  act(() => {
    jest.runOnlyPendingTimers();
  });
  // Wait for post-processing to disappear and buttons/radios to show
  await waitFor(() => {
    expect(screen.queryByText(/Creating results, please wait/i)).not.toBeInTheDocument();
    expect(screen.getByText('WEBM')).toBeInTheDocument();
    expect(screen.getByText('WAV')).toBeInTheDocument();
    expect(screen.getByText('Captions')).toBeInTheDocument();
    expect(screen.getAllByRole('radio').length).toBeGreaterThanOrEqual(2);
  });
  jest.useRealTimers();

  // Select the first chunk and trigger comparison
  const radios = screen.getAllByRole('radio');
  fireEvent.click(radios[0]);
  const compareBtn = screen.getByRole('button', { name: /Generate Transcript|Compare|Transcript/i });
  fireEvent.click(compareBtn);

  // Semantic matching score, percent, and reason should show up
  await waitFor(() => {
    expect(
      screen.getAllByText((content, node) => !!node?.textContent && node.textContent.includes('Semantic Matching Score')).length
    ).toBeGreaterThan(0);
    expect(screen.getAllByText((content, node) => !!node?.textContent && node.textContent.includes('91')).length).toBeGreaterThan(0);
    expect(screen.getAllByText((content, node) => !!node?.textContent && /match closely in meaning|somewhat similar|differ significantly/i.test(node.textContent)).length).toBeGreaterThan(0);
  });
  expect(processChunkCalled).toBe(true);
});
