import React from 'react';
import { render, screen } from '@testing-library/react';
import ProgressStepper from './ProgressStepper';

describe('ProgressStepper', () => {
  it('renders all hardcoded steps', () => {
    render(<ProgressStepper activeStep={2} />);
    expect(screen.getByText(/Downloading/i)).toBeInTheDocument();
    expect(screen.getByText(/VAD/i)).toBeInTheDocument();
    expect(screen.getByText(/Chunking/i)).toBeInTheDocument();
    expect(screen.getByText(/Transcribing/i)).toBeInTheDocument();
    expect(screen.getByText(/Comparing/i)).toBeInTheDocument();
    expect(screen.getByText(/Done/i)).toBeInTheDocument();
  });

  it('renders correct number of steps and the expected active step label', () => {
    const { container } = render(<ProgressStepper activeStep={4} />);
    // Check number of step labels
    expect(container.querySelectorAll('.MuiStepLabel-label').length).toBe(6);
    // 'Comparing' step is expected to be present
    expect(screen.getByText(/Comparing/i)).toBeInTheDocument();
  });
});
