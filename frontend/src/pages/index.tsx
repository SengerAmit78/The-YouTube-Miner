import React from 'react';
import { Container, Button, Typography, Paper } from '@mui/material';
import { useNavigate } from 'react-router-dom';
// import Logo from '../assets/logo.svg'; // Uncomment and add your logo file if you have one

const Landing: React.FC = () => {
  const navigate = useNavigate();
  return (
    <Container maxWidth="sm" sx={{ pt: { xs: 5, md: 10 } }}>
      <Paper elevation={3} sx={{ p: { xs: 2, sm: 4 }, mt: { xs: 4, sm: 8 }, borderRadius: 4, textAlign: 'center' }}>
        {/* Logo Section (optional - add a logo.png/svg in src/assets and uncomment below) */}
        {/* <Box mb={2} display="flex" justifyContent="center"><img src={Logo} alt="The YouTube Miner Logo" style={{ height: 70 }}/></Box> */}
        <Typography variant="h3" gutterBottom sx={{ fontWeight: 700, letterSpacing: 0.5 }}>
          The YouTube Miner
        </Typography>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Enterprise-Grade VAD & ASR Comparison Pipeline
        </Typography>
        {/* Tagline */}
        <Typography variant="subtitle1" color="text.secondary" sx={{ mt: 2, mb: 4 }}>
          Automatically extract usable speech from any YouTube video, split it into accurate chunks, transcribe segments with open-source ASR, and compare with captions using semantic similarity—all with no paid APIs or vendor lock-in.
        </Typography>
        <Button
          variant="contained"
          size="large"
          sx={{ mt: 4, px: 4, py: 1.3, fontSize: 20, borderRadius: 2 }}
          onClick={() => navigate('/run')}
        >
          Start New Run
        </Button>
      </Paper>
    </Container>
  );
};

export default Landing;
