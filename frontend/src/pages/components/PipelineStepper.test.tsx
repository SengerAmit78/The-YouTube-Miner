import React from 'react';
import { render, screen } from '@testing-library/react';
import PipelineStepper from './PipelineStepper';

describe('PipelineStepper', () => {
  it('renders all steps', () => {
    render(<PipelineStepper currentStep="downloading" />);
    expect(screen.getByText(/Download/)).toBeInTheDocument();
    expect(screen.getByText(/VAD/)).toBeInTheDocument();
    expect(screen.getByText(/Chunking/)).toBeInTheDocument();
  });

  it('renders correct active step for vad', () => {
    render(<PipelineStepper currentStep="vad" />);
    expect(screen.getByText(/VAD/)).toBeInTheDocument();
  });

  it('renders completed state when finished', () => {
    render(<PipelineStepper currentStep="unexpected" />); // triggers finished
    expect(screen.getByText(/Download/)).toBeInTheDocument();
    expect(screen.getByText(/VAD/)).toBeInTheDocument();
    expect(screen.getByText(/Chunking/)).toBeInTheDocument();
  });
});
