import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import RunForm from './run';

// mock global fetch and window.location for navigation
const mockFetch = jest.fn();
global.fetch = mockFetch;
const originalLocation = window.location;
beforeAll(() => {
  // @ts-ignore
  delete window.location;
  // @ts-ignore
  window.location = { href: '', assign: jest.fn() };
});
afterAll(() => {
  // @ts-ignore
  window.location = originalLocation;
});

describe('RunForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders all form elements', () => {
    render(<RunForm />);
    expect(screen.getByLabelText(/YouTube URL/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Video Language/i)).toBeInTheDocument();
    // Robustly handle possible MUI duplicated label
    expect(screen.getAllByLabelText(/Model Size/i).length).toBeGreaterThan(0);
    expect(screen.getByRole('button', { name: /Start Run/i })).toBeInTheDocument();
  });

  it('shows required error when URL is empty', async () => {
    render(<RunForm />);
    fireEvent.click(screen.getByRole('button', { name: /Start Run/i }));
    expect(await screen.findByText(/YouTube URL is required/i)).toBeInTheDocument();
  });

  it('shows toast when non-English language is selected', async () => {
    render(<RunForm />);
    fireEvent.mouseDown(screen.getByLabelText(/Video Language/i));
    const hindi = await screen.findByText(/Hindi/i);
    fireEvent.click(hindi);
    expect(await screen.findByText(/recommend using the 'Small' model/i)).toBeInTheDocument();
  });

  it('shows toast when Small model is selected', async () => {
    render(<RunForm />);
    fireEvent.mouseDown(screen.getAllByLabelText(/Model Size/i)[0]);
    const options = await screen.findAllByRole('option');
    const smallOption = options.find(opt => opt.textContent === 'Small');
    expect(smallOption).toBeDefined();
    fireEvent.click(smallOption!);
    expect(await screen.findByText(/provides better accuracy/i)).toBeInTheDocument();
  });

  it('submits the form and navigates on successful run', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ run_id: 'abc123' })
    });
    render(<RunForm />);
    fireEvent.change(screen.getByLabelText(/YouTube URL/i), { target: { value: 'http://yt.com/vid' } });
    fireEvent.click(screen.getByRole('button', { name: /Start Run/i }));
    await waitFor(() => {
      expect(window.location.href).toContain('/results/abc123');
    });
  });

  it('shows backend error response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({ error: 'Backend error!' })
    });
    render(<RunForm />);
    fireEvent.change(screen.getByLabelText(/YouTube URL/i), { target: { value: 'http://yt.com/vid' } });
    fireEvent.click(screen.getByRole('button', { name: /Start Run/i }));
    expect(await screen.findByText(/Backend error!/i)).toBeInTheDocument();
  });

  it('shows timeout error', async () => {
    mockFetch.mockImplementationOnce(() => new Promise((_, reject) => setTimeout(() => reject({ name: 'AbortError' }), 500)));
    render(<RunForm />);
    fireEvent.change(screen.getByLabelText(/YouTube URL/i), { target: { value: 'http://yt.com/vid' } });
    fireEvent.click(screen.getByRole('button', { name: /Start Run/i }));
    expect(await screen.findByText(/Backend took too long/i)).toBeInTheDocument();
  });
});
