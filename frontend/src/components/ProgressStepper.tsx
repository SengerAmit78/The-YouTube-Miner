import React from 'react';
import { Stepper, Step, StepLabel, Box } from '@mui/material';

const steps = [
  'Downloading',
  'VAD',
  'Chunking',
  'Transcribing',
  'Comparing',
  'Done',
];

interface ProgressStepperProps {
  activeStep: number;
}

const ProgressStepper: React.FC<ProgressStepperProps> = ({ activeStep }) => (
  <Box sx={{ width: '100%', my: 4 }}>
    <Stepper activeStep={activeStep} alternativeLabel>
      {steps.map((label) => (
        <Step key={label}>
          <StepLabel>{label}</StepLabel>
        </Step>
      ))}
    </Stepper>
  </Box>
);

export default ProgressStepper;

