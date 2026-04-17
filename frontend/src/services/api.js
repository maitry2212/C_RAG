import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
});

// ── Health ─────────────────────────────────────
export const checkHealth = () => api.get('/health');

// ── Ingest ─────────────────────────────────────
export const ingestFile = (file, type) => {
  const form = new FormData();
  form.append('file', file);
  if (type) form.append('source_type', type);
  return api.post('/ingest', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

export const ingestURL = (url, type) => {
  const form = new FormData();
  form.append('url', url);
  if (type) form.append('source_type', type);
  return api.post('/ingest', form);
};

// ── Query ──────────────────────────────────────
export const queryPipeline = (question) =>
  api.post('/query', { question });

export const getQueryHistory = () => api.get('/history');

// ── Graph structure ────────────────────────────
export const getGraphNodes = () => api.get('/graph/nodes');
export const getGraphEdges = () => api.get('/graph/edges');

// ── Node state inspection ──────────────────────
export const getNodeState = (nodeId) =>
  api.get(`/node/${nodeId}/state`);

export default api;
