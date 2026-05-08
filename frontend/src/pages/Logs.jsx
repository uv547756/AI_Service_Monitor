import { useState, useCallback } from 'react';
import LogLine from '../components/LogLine';
import { fetchLogs } from '../api/client';
import { usePolling } from '../hooks/usePolling';

export default function Logs() {
  const [filters, setFilters] = useState({ service: '', severity: '', limit: 100 });

  const fetchFn = useCallback(() => {
    const params = { limit: filters.limit };
    if (filters.service) params.service = filters.service;
    if (filters.severity) params.severity = filters.severity;
    return fetchLogs(params);
  }, [filters]);

  const { data: logs, loading } = usePolling(fetchFn, 5000, [filters]);

  const updateFilter = (key, value) => setFilters(prev => ({ ...prev, [key]: value }));

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>Log Viewer</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>
          Terminal-style log viewer with filtering
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select value={filters.service}
          onChange={e => updateFilter('service', e.target.value)}
          className="px-3 py-2 rounded-lg text-sm border focus:outline-none focus:ring-1"
          style={{
            background: 'var(--color-surface-700)',
            borderColor: 'var(--color-border)',
            color: 'var(--color-text-primary)',
          }}>
          <option value="">All Services</option>
          {['nginx', 'docker', 'sshd', 'postgresql', 'redis', 'systemd', 'kernel', 'cron'].map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>

        <select value={filters.severity}
          onChange={e => updateFilter('severity', e.target.value)}
          className="px-3 py-2 rounded-lg text-sm border focus:outline-none focus:ring-1"
          style={{
            background: 'var(--color-surface-700)',
            borderColor: 'var(--color-border)',
            color: 'var(--color-text-primary)',
          }}>
          <option value="">All Severities</option>
          {['info', 'warning', 'error', 'critical'].map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>

        <select value={filters.limit}
          onChange={e => updateFilter('limit', parseInt(e.target.value))}
          className="px-3 py-2 rounded-lg text-sm border focus:outline-none focus:ring-1"
          style={{
            background: 'var(--color-surface-700)',
            borderColor: 'var(--color-border)',
            color: 'var(--color-text-primary)',
          }}>
          {[50, 100, 200, 500].map(n => (
            <option key={n} value={n}>Last {n} lines</option>
          ))}
        </select>
      </div>

      {/* Log viewer */}
      <div className="glass-card p-1">
        <div className="log-viewer" style={{ maxHeight: 'calc(100vh - 280px)', overflow: 'auto' }}>
          {loading && !logs ? (
            <p className="text-sm text-center py-8" style={{ color: 'var(--color-text-muted)' }}>Loading logs...</p>
          ) : logs?.length ? (
            logs.map((log, i) => <LogLine key={log.id} log={log} index={i} />)
          ) : (
            <p className="text-sm text-center py-8" style={{ color: 'var(--color-text-muted)' }}>No logs match your filters</p>
          )}
        </div>
      </div>
    </div>
  );
}
