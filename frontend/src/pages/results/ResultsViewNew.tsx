import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Container, Typography, Box, Button, CircularProgress, Alert, Radio, RadioGroup, FormControlLabel,
  Paper, Tooltip, Snackbar, IconButton, LinearProgress, Stack
} from '@mui/material';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import PipelineStepper from '../components/PipelineStepper';
import { Link as RouterLink } from 'react-router-dom';
import HomeIcon from '@mui/icons-material/Home';

const POLL_INTERVAL = 2000; // ms
const BACKEND_BASE = 'http://localhost:8000';
const cardMaxWidth = 540;

const ResultsView: React.FC = () => {
  const { runId } = useParams<{ runId: string }>();
  const [prevRunId, setPrevRunId] = useState<string | undefined>(undefined);

  useEffect(() => {
    if (prevRunId !== runId) {
      setPrevRunId(runId);
      setShowPostProcessing(false);
      setResultReady(false);
      console.log('[RESULTS] runId changed, flags reset.');
    }
  }, [runId]);
  const [showPostProcessing, setShowPostProcessing] = useState(false);
  const [resultReady, setResultReady] = useState(false);

  const [status, setStatus] = useState<any>(null);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedChunk, setSelectedChunk] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [comparisonResult, setComparisonResult] = useState<any>(null);
  const [transcriptUrl, setTranscriptUrl] = useState<string | null>(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMsg, setSnackbarMsg] = useState('');
  const [compareText, setCompareText] = useState('');

  useEffect(() => {
    setShowPostProcessing(false);
    setResultReady(false);
  }, [runId]);

  useEffect(() => {
    console.log('[RESULTS] Effect for post-processing called:', { statusStep: status?.step, result, resultReady, showPostProcessing });
    if (status?.step === 'done' && result && !resultReady && !showPostProcessing) {
      setShowPostProcessing(true);
    }
  }, [status?.step, result, resultReady, showPostProcessing]);

  useEffect(() => {
    if (showPostProcessing && !resultReady) {
      const t = setTimeout(() => {
        setShowPostProcessing(false);
        setResultReady(true);
        console.log('[RESULTS] Timer done, setResultReady TRUE');
      }, 2000);
      return () => clearTimeout(t);
    }
  }, [showPostProcessing, resultReady]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    setLoading(true);
    setError(null);
    const poll = async () => {
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 300000); // 5 minutes
        const statusRes = await fetch(`${BACKEND_BASE}/status/${runId}`);
        const statusData = await statusRes.json();
        setStatus(statusData);
        if (statusData.step === 'done') {
          const resultRes = await fetch(`${BACKEND_BASE}/result/${runId}`);
          const resultData = await resultRes.json();
          setResult(resultData);
          setTranscriptUrl(resultData.transcript_url || null);
          setLoading(false);
          clearInterval(interval);
        } else if (statusData.step === 'error') {
          setError(statusData.error_message || 'Pipeline errored');
          setLoading(false);
          clearInterval(interval);
        } else {
          setLoading(true);
        }
      } catch (err: any) {
        setError('Error fetching pipeline status');
        setLoading(false);
        clearInterval(interval);
      }
    };
    poll();
    interval = setInterval(poll, POLL_INTERVAL);
    return () => { clearInterval(interval); };
  }, [runId]);

  console.log('[RENDER] status:', status);
  console.log('[RENDER] result:', result);
  console.log('[RENDER] resultReady:', resultReady, 'showPostProcessing:', showPostProcessing);

  const webmUrl = result?.webm_url ? `${BACKEND_BASE}${result.webm_url}` : '';
  const wavUrl = result?.wav_url ? `${BACKEND_BASE}${result.wav_url}` : '';
  const captionUrl = result?.caption_url ? `${BACKEND_BASE}${result.caption_url}` : '';
  const chunkFiles = result?.chunkFiles || [];

  const handleCompare = async () => {
    if (!selectedChunk) return;
    setProcessing(true);
    setComparisonResult(null);
    setTranscriptUrl(null);
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 300000); // 5 minutes
      const resp = await fetch(`${BACKEND_BASE}/result/${runId}/process_chunk`, {
        signal: controller.signal,
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chunk_path: selectedChunk })
      });
      const data = await resp.json();
      clearTimeout(timeout);
      if (controller.signal.aborted) throw new Error('Request timed out. Please try again.');
      if (!resp.ok) {
        if (data && data.error) throw new Error(data.error);
        if (data && data.detail) throw new Error(data.detail);
        throw new Error('Chunk processing failed');
      }
      setComparisonResult(data.similarity_percent || data.similarity || '(no value)');
      setTranscriptUrl(data.transcript_url ? `${BACKEND_BASE}${data.transcript_url}` : null);
      setCompareText(data.compare_text || '');
      setSnackbarMsg('Comparison complete!');
      setSnackbarOpen(true);
    } catch (err: any) {
      if (err.name === 'AbortError') {
        setComparisonResult('Backend took too long to respond.');
      } else if (err.message) {
        setComparisonResult(err.message);
      } else {
        setComparisonResult('An unknown error occurred. Please contact support.');
      }
      setTranscriptUrl(null);
      setSnackbarMsg('Comparison failed.');
      setSnackbarOpen(true);
    } finally {
      setProcessing(false);
    }
  };

  const chunkBoxStyles = {
    maxHeight: 180,
    overflowY: chunkFiles.length > 4 ? 'scroll' : 'visible',
    border: '1px solid #e0e0e0',
    borderRadius: 2,
    p: 1,
    backgroundColor: '#fafafa',
    minHeight: 70,
  };

  return (
    <Container maxWidth="sm" sx={{ py: { xs: 1, md: 3 } }}>
      <Box display="flex" alignItems="center" justifyContent="flex-start" sx={{ mb: 2 }}>
        <Button
          component={RouterLink}
          to="/run"
          startIcon={<HomeIcon />}
          variant="outlined"
          color="primary"
          sx={{ fontWeight: 600 }}
        >
          Home
        </Button>
      </Box>
      <Box display="flex" alignItems="center" justifyContent="center" sx={{ mb: 3 }}>
        <Paper elevation={3} sx={{ width: '100%', maxWidth: cardMaxWidth, py: 2, px: { xs: 2, sm: 4 }, borderRadius: 4, textAlign: 'center' }}>
          <Typography variant="h3" gutterBottom sx={{ fontWeight: 700, letterSpacing: 0.5 }}>
            The YouTube Miner
          </Typography>
        </Paper>
      </Box>
      {((loading && !result) || showPostProcessing) && (
        <Box display="flex" alignItems="center" justifyContent="center" sx={{ minHeight: 320, flexDirection: 'column' }}>
          <Paper elevation={3} sx={{ minWidth: 340, width: '100%', maxWidth: cardMaxWidth, p: { xs: 2, sm: 3 }, borderRadius: 4, textAlign: 'center', mb: 3 }}>
            <LinearProgress color="primary" sx={{ mb: 1, height: 7, borderRadius: 20 }} />
            <Typography variant="h5" gutterBottom sx={{ mt: 3, fontWeight: 700 }}>
              Processing Run
            </Typography>
            <PipelineStepper currentStep={status?.step} />
            <Typography variant="body1" sx={{ mb: 2, mt: 2 }}>
              {showPostProcessing
                ? 'Creating results, please wait...'
                : status && status.step && status.step !== 'starting'
                  ? (status.step === 'downloading' ? 'Downloading audio/caption file...' :
                     status.step === 'vad' ? 'Detecting speech regions (VAD)...' :
                     status.step === 'chunking' ? 'Splitting audio into chunks...' :
                     status.step === 'done' ? 'Initial processing complete.' :
                     status.step === 'error' ? 'An error occurred during processing.' :
                     `Processing: ${status.step}`)
                  : 'Starting pipeline...'}
            </Typography>
          </Paper>
        </Box>
      )}
      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
      {result && resultReady && (
        <>
          <Paper elevation={2} sx={{ mb: 3, p: 2, width: '100%', maxWidth: cardMaxWidth, mx: 'auto' }}>
            <Typography variant="h6" gutterBottom>Download Files</Typography>
            <Stack direction="row" spacing={3} justifyContent="flex-start" alignItems="flex-end" sx={{ mb: 1 }}>
              <Box textAlign="left">
                <Tooltip title="Download extracted audio (WEBM format)">
                  <span>
                    <Button variant="outlined" href={webmUrl} target="_blank" download startIcon={<FileDownloadIcon />} disabled={!webmUrl}>WEBM</Button>
                  </span>
                </Tooltip>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                  Extracted audio file from YouTube video (WEBM format)
                </Typography>
              </Box>
              <Box textAlign="left">
                <Tooltip title="Download extracted audio (WAV)">
                  <span>
                    <Button variant="outlined" href={wavUrl} target="_blank" download startIcon={<FileDownloadIcon />} disabled={!wavUrl}>WAV</Button>
                  </span>
                </Tooltip>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                  Clean processed audio file (WAV Format)
                </Typography>
              </Box>
              <Box textAlign="left">
                <Tooltip title="Download caption file (VTT/SRT)">
                  <span>
                    <Button variant="outlined" href={captionUrl} target="_blank" download startIcon={<FileDownloadIcon />} disabled={!captionUrl}>Captions</Button>
                  </span>
                </Tooltip>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                  YouTube captions file (VTT format)
                </Typography>
              </Box>
            </Stack>
          </Paper>

          <Paper elevation={2} sx={{ mb: 3, p: 2, width: '100%', maxWidth: cardMaxWidth, mx: 'auto' }}>
            <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
              <Typography variant="h6">Audio Chunks</Typography>
              <Typography variant="body2" color="text.secondary" fontWeight="bold">{`Number of chunks: ${chunkFiles.length}`}</Typography>
            </Box>
            {chunkFiles.length ? (
              <Box sx={chunkBoxStyles}>
                <RadioGroup
                  value={selectedChunk || ''}
                  onChange={e => setSelectedChunk(e.target.value)}
                  name="chunk-select"
                >
                  {chunkFiles.map((chunkPath: string, i: number) => {
                    const chunkUrl = `${BACKEND_BASE}${chunkPath}`;
                    return (
                      <Box
                        key={chunkPath}
                        display="flex"
                        alignItems="center"
                        justifyContent="space-between"
                        sx={{ mb: 0.5, borderBottom: i !== chunkFiles.length-1 ? '1px solid #f0f0f0' : 'none', pb: 0.5 }}
                      >
                        <Box display="flex" alignItems="center" gap={1}>
                          <FormControlLabel
                            value={chunkPath}
                            control={<Radio />}
                            label={<b>{`Chunk ${i + 1}`}</b>}
                          />
                        </Box>
                        <Tooltip title="Download chunk audio (WAV)"><span>
                          <Button href={chunkUrl} target="_blank" variant="outlined" size="small" startIcon={<FileDownloadIcon />}>Download</Button>
                        </span></Tooltip>
                      </Box>
                    );
                  })}
                </RadioGroup>
              </Box>
            ) : (
              <Typography>No chunks available.</Typography>
            )}
          </Paper>

          <Box my={2} display="flex" justifyContent="center">
            <Button
              variant="contained"
              color="primary"
              disabled={!selectedChunk || processing}
              onClick={handleCompare}
              sx={{ minWidth: 210 }}
            >
              {processing ? <><CircularProgress size={20} color="inherit" sx={{ mr: 1 }}/><span>Processing Comparison...</span></> : 'Generate Transcript & Compare'}
            </Button>
          </Box>

          <Paper elevation={2} sx={{ mb: 3, p: 2, width: '100%', maxWidth: cardMaxWidth, mx: 'auto' }}>
            <Typography variant="h6" gutterBottom>ASR Transcript vs Caption Comparison</Typography>
            {comparisonResult !== null ? (
              <Box sx={{ mt: 1 }}>
                <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '0 8px' }}>
                  <tbody>
                    <tr>
                      <td style={{ fontWeight: 600, fontSize: 17, color: '#1976d2', verticalAlign: 'middle', width: 240 }} colSpan={2}>
  Semantic Matching Score: <span style={{ fontWeight: 700, fontSize: 22, color: '#2e7d32', letterSpacing: 0.6, marginLeft: 10 }}>
  {typeof comparisonResult === 'number' || (typeof comparisonResult === 'string' && /%/.test(comparisonResult)) ? `${comparisonResult}%` : comparisonResult}
  </span>
</td>
                    </tr>
                  </tbody>
                </table>
                {typeof comparisonResult === 'number' && (
  <div style={{ fontSize: '1em', margin: '10px 0 2px 0', color: '#333' }}>
    <strong>Reason:</strong> {comparisonResult >= 85 ? 'The transcript and YouTube caption match closely in meaning.' : (comparisonResult >= 60 ? 'The transcript and caption are somewhat similar but have notable differences.' : 'The transcript and caption differ significantly for this segment.')}
  </div>
)}
                {transcriptUrl && (
                  <Box mt={2}>
                    <Tooltip title="Download the transcript file for the selected chunk (TXT format)">
                      <span>
                        <Button variant="contained" color="primary" href={transcriptUrl} target="_blank" download startIcon={<FileDownloadIcon />}>
                          Download ASR Transcript
                        </Button>
                      </span>
                    </Tooltip>
                  </Box>
                )}
              </Box>
            ) : (
              <Typography color="text.secondary">Select a chunk and click “Generate Transcript & Compare” to view the result.</Typography>
            )}
          </Paper>

          <Box my={3} display="flex" justifyContent="flex-end">
            <Typography variant="subtitle1" color="text.secondary" sx={{ fontWeight: 700 }}>
              Presented by: Amit Senger
            </Typography>
          </Box>

          <Snackbar
            anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
            open={snackbarOpen}
            autoHideDuration={3400}
            onClose={() => setSnackbarOpen(false)}
            message={snackbarMsg}
            action={
              <IconButton size="small" aria-label="close" color="inherit" onClick={() => setSnackbarOpen(false)}>
                ×
              </IconButton>
            }
          />
        </>
      )}
    </Container>
  );
};

export default ResultsView;

