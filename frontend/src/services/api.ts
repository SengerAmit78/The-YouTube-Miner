export async function runPipeline(params: { youtube_url: string; language: string; model_size: string }) {
  const resp = await fetch('/api/run', { method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}

export async function getStatus(runId: string) {
  const resp = await fetch(`/api/status/${runId}`);
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}

export async function getResult(runId: string) {
  const resp = await fetch(`/api/result/${runId}`);
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}

export async function processChunk(runId: string, index: number) {
  const resp = await fetch(`/api/result/${runId}/process_chunk`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chunk_index: index })
  });
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}

export async function getHistory() {
  const resp = await fetch('/api/history');
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}
