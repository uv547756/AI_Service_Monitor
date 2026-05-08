/**
 * API client — all backend communication goes through here.
 * Uses /api prefix in dev (proxied by Vite) or direct URL in production.
 */
import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || '/api';
const API_KEY = import.meta.env.VITE_API_KEY || 'changeme-dev-key';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
  },
});

export const fetchMachines = () => api.get('/machines').then(r => r.data);
export const fetchMachine = (id) => api.get(`/machines/${id}`).then(r => r.data);
export const fetchLogs = (params) => api.get('/logs', { params }).then(r => r.data);
export const fetchIssues = (params) => api.get('/issues', { params }).then(r => r.data);
export const fetchIssue = (id) => api.get(`/issues/${id}`).then(r => r.data);
export const fetchCommands = (params) => api.get('/commands', { params }).then(r => r.data);
export const approveCommand = (id) => api.patch(`/commands/${id}/approve`).then(r => r.data);
export const rejectCommand = (id) => api.patch(`/commands/${id}/reject`).then(r => r.data);

export default api;
