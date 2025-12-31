import React from "react";
import { Box, Stepper, Step, StepLabel, StepIconProps } from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import HourglassTopIcon from "@mui/icons-material/HourglassTop";

const steps = ["Download", "VAD", "Chunking"];

function getStepIndex(statusStep: string | undefined): number {
  switch (statusStep) {
    case "downloading":
      return 0;
    case "vad":
      return 1;
    case "chunking":
      return 2;
    default:
      return -1;
  }
}

function StepIconComponent(props: StepIconProps) {
  const { active, completed, icon } = props;
  if (completed) {
    return <CheckCircleIcon style={{ color: '#2e7d32' }} fontSize="medium" />; // green
  }
  if (active) {
    // blue
    return <Box sx={{ width: 18, height: 18, bgcolor: '#1976d2', borderRadius: '50%', display: 'inline-block', border: '2.5px solid #1976d2' }} />;
  }
  // gray
  return <Box sx={{ width: 18, height: 18, bgcolor: '#e0e0e0', borderRadius: '50%', display: 'inline-block', border: '2.5px solid #e0e0e0' }} />;
}

const PipelineStepper: React.FC<{ currentStep?: string }> = ({ currentStep }) => {
  const activeStep = getStepIndex(currentStep);
  const finished = activeStep === -1;

  return (
    <Box sx={{ width: '100%', my: 3 }}>
      <Stepper
        alternativeLabel
        activeStep={finished ? steps.length : activeStep}
        connector={null}
      >
        {steps.map((label, i) => (
          <Step key={label} completed={i < activeStep || finished} active={i === activeStep && !finished}>
            <StepLabel StepIconComponent={StepIconComponent}>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>
    </Box>
  );
};

export default PipelineStepper;
