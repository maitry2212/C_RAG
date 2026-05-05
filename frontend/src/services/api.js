import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120000,
});

api.interceptors.request.use((config) => {
  const stored = localStorage.getItem('auth');
  if (stored) {
    const { access_token } = JSON.parse(stored);
    if (access_token) {
      config.headers.Authorization = `Bearer ${access_token}`;
    }
  }
  return config;
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

// ── Chat & Query ───────────────────────────────
export const getChats = () => api.get('/chats/');
export const createChat = (title) => api.post('/chats/', { title });
export const deleteChat = (chatId) => api.delete(`/chats/${chatId}`);

export const queryPipeline = (chatId, question) =>
  api.post('/query', { chat_id: chatId, question });

export const getQueryHistory = (chatId) => api.get(`/chats/${chatId}/history`);

// ── Graph structure ────────────────────────────
export const getGraphNodes = () => api.get('/graph/nodes');
export const getGraphEdges = () => api.get('/graph/edges');

// ── Node state inspection ──────────────────────
export const getNodeState = (nodeId) =>
  api.get(`/node/${nodeId}/state`);

export default api;
