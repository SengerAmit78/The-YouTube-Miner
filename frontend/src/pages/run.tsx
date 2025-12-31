import React, { useState } from 'react';
import { Container, TextField, Select, MenuItem, Button, Typography, InputLabel, FormControl, Box, Alert, Paper, Tooltip, InputAdornment, Snackbar, IconButton } from '@mui/material';
import LinkIcon from '@mui/icons-material/Link';
import LanguageIcon from '@mui/icons-material/Language';
import TuneIcon from '@mui/icons-material/Tune';
import InfoIcon from '@mui/icons-material/InfoOutlined';

const languageOptions = [
  { value: 'en', label: 'English' },
  { value: 'hi', label: 'Hindi' },
  { value: 'fr', label: 'French' },
  { value: 'mr', label: 'Marathi' },
  { value: 'ta', label: 'Tamil' },
];

const modelOptions = [
  { value: 'tiny', label: 'Tiny' },
  { value: 'small', label: 'Small' }
];

const RunForm: React.FC = () => {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [language, setLanguage] = useState('en');
  const [modelSize, setModelSize] = useState('tiny');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string|null>(null);

  // Toast state
  const [toast, setToast] = useState<{ open: boolean, message: string }>({ open: false, message: '' });
  const [lastToast, setLastToast] = useState<string>('');

  // Track last toasts for avoiding repeats
  const [langToastShown, setLangToastShown] = useState(false);
  const [modelToastShown, setModelToastShown] = useState(false);

  const handleLangChange = (val: string) => {
    setLanguage(val);
    // If non-English language is selected, select 'small' model by default; if English, select 'tiny'
    if (val !== 'en') {
      setModelSize('small');
    } else {
      setModelSize('tiny');
    }
    // Show language toast when selecting not English
    if (val !== 'en' && !langToastShown) {
      setToast({
        open: true,
        message: "For better transcription accuracy in non-English languages, recommend using the 'Small' model size."
      });
      setLastToast('nonen');
      setLangToastShown(true);
    }
  };


  const handleModelChange = (val: string) => {
    setModelSize(val);
    // Show model performance toast for Small
    if (val === 'small' && !modelToastShown) {
      setToast({
        open: true,
        message: "The 'Small' model provides better accuracy but may take longer to process."
      });
      setLastToast('small');
      setModelToastShown(true);
    }
  };

  const handleToastClose = () => {
    setToast((prev) => ({ ...prev, open: false }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    if (!youtubeUrl) {
      setError("YouTube URL is required");
      setLoading(false);
      return;
    }
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 300000); // 5 minutes

      const response = await fetch("http://localhost:8000/run", {
        signal: controller.signal,
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          youtube_url: youtubeUrl,
          language,
          model_size: modelSize
        }),
      });
      const data = await response.json();
      clearTimeout(timeout);
      if (controller.signal.aborted) throw new Error("Request timed out. Please try again.");
      if (!response.ok) {
        // More helpful error based on backend
        if (data && data.error) throw new Error(data.error);
        if (data && data.detail) throw new Error(data.detail);
        throw new Error("Pipeline run failed");
      }
      window.location.href = `/results/${data.run_id}`;
    } catch (err: any) {
      if (err.name === 'AbortError') {
        setError('Backend took too long to respond. Please try again later.');
      } else if (err.message) {
        setError(err.message);
      } else {
        setError('An unknown error occurred. Please contact support.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Paper elevation={3} sx={{ p: { xs: 2, sm: 4 }, borderRadius: 4 }}>
        {/* App Title & Task Section */}
        <Box mb={3}>
          <Typography variant="h3" gutterBottom sx={{ fontWeight: 700, letterSpacing: 0.3 }}>
            The YouTube Miner
          </Typography>
          <Typography variant="h6" sx={{ fontWeight: 700, color: 'text.secondary', letterSpacing: 0.2 }} gutterBottom>
            VAD & ASR Comparison Pipeline
          </Typography>
        </Box>
        <Box mb={4}>
          <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 500 }}>
            <b>What This Pipeline Does</b>
          </Typography>
          <Typography variant="body2" sx={{ mb: 0, display: 'block', color: 'text.secondary' }}>
            Extract clean audio from YouTube videos, split into 30-second chunks (removing silence/music), transcribe using open-source ASR, and compare with YouTube captions.
          </Typography>
        </Box>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {/* Run Configuration Section */}
        <Box component="form" onSubmit={handleSubmit}>
          <Typography variant="subtitle1" sx={{ mt: 2, mb: 1, fontWeight: 500 }}>
            <b>Run Configuration</b>
          </Typography>
          <Tooltip title="Paste a YouTube video URL (e.g., https://youtube.com/watch?v=...)" placement="top">
            <TextField
              fullWidth
              margin="normal"
              label="YouTube URL"
              required
              value={youtubeUrl}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setYoutubeUrl(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <LinkIcon color="action" />
                  </InputAdornment>
                )
              }}
              helperText="Paste a YouTube link to analyze."
            />
          </Tooltip>
          <Tooltip title="Select the spoken language found in the video (impacts VAD and ASR behavior)">
            <FormControl fullWidth margin="normal" variant="outlined">
              <InputLabel id="language-label" shrink><LanguageIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />Video Language</InputLabel>
              <Select
                fullWidth
                labelId="language-label"
                label={<><LanguageIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />Video Language</>}
                value={language}
                onChange={e => handleLangChange(e.target.value)}
              >
                {languageOptions.map(option => <MenuItem key={option.value} value={option.value}>{option.label}</MenuItem>)}
              </Select>
              <Typography variant="caption" sx={{ color: 'text.secondary', ml: 2 }}>Language for VAD & ASR</Typography>
            </FormControl>
          </Tooltip>
          <Tooltip title="Choose the transcription model size (tradeoff: speed vs. accuracy)">
            <FormControl fullWidth margin="normal" variant="outlined">
              <InputLabel id="model-label" shrink><TuneIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />Model Size</InputLabel>
              <Select
                fullWidth
                labelId="model-label"
                label={<><TuneIcon fontSize="small" sx={{ mr: 1, verticalAlign: 'middle' }} />Model Size</>}
                value={modelSize}
                onChange={e => handleModelChange(e.target.value)}
              >
                {modelOptions.map(option => <MenuItem key={option.value} value={option.value}>{option.label}</MenuItem>)}
              </Select>
              <Typography variant="caption" sx={{ color: 'text.secondary', ml: 2 }}>Tiny (fastest), Small (higher quality)</Typography>
            </FormControl>
          </Tooltip>
          <Button
            type="submit"
            fullWidth
            variant="contained"
            color="primary"
            disabled={loading}
            sx={{ mt: 3, py: 1.5, fontSize: 18, fontWeight: 'bold', borderRadius: 2 }}
          >
            {loading ? 'Starting...' : 'Start Run'}
          </Button>
        </Box>
        {/* Right aligned Presented by text at bottom */}
        <Box my={4} display="flex" justifyContent="flex-end">
          <Typography variant="subtitle1" color="text.secondary" sx={{ fontWeight: 700 }}>
            Presented by: Amit Senger
          </Typography>
        </Box>
        {/* Snackbar/toast for info/warnings - always bottom-center for readability */}
        <Snackbar
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
          open={toast.open}
          autoHideDuration={3500}
          onClose={handleToastClose}
          message={toast.message}
          action={
            <IconButton size="small" aria-label="close" color="inherit" onClick={handleToastClose}>
              <InfoIcon fontSize="small" />
            </IconButton>
          }
        />
      </Paper>
    </Container>
  );
};

export default RunForm;
