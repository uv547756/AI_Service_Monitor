import { useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import StatusBadge from '../components/StatusBadge';
import LogLine from '../components/LogLine';
import { fetchMachine } from '../api/client';
import { usePolling } from '../hooks/usePolling';

export default function MachineDetail() {
  const { id } = useParams();
  const { data, loading } = usePolling(useCallback(() => fetchMachine(id), [id]), 5000);

  if (loading && !data) {
    return <div className="text-center py-12" style={{ color: 'var(--color-text-muted)' }}>Loading...</div>;
  }
  if (!data) {
    return <div className="text-center py-12" style={{ color: 'var(--color-text-muted)' }}>Machine not found</div>;
  }

  const { machine, recent_logs, issue_counts } = data;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--color-text-muted)' }}>
        <Link to="/machines" style={{ color: 'var(--color-accent-blue)' }}>Machines</Link>
        <span>›</span>
        <span style={{ color: 'var(--color-text-primary)' }}>{machine.hostname}</span>
      </div>

      {/* Machine Header */}
      <div className="glass-card p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl flex items-center justify-center text-2xl"
              style={{ background: 'var(--color-surface-600)' }}>🖥️</div>
            <div>
              <h1 className="text-xl font-bold" style={{ color: 'var(--color-text-primary)' }}>{machine.hostname}</h1>
              <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>{machine.ip_address}</p>
            </div>
          </div>
          <StatusBadge status={machine.status} size="lg" />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          {[
            { label: 'OS', value: machine.os_info },
            { label: 'CPU', value: machine.cpu },
            { label: 'RAM', value: machine.ram_total_gb ? `${machine.ram_total_gb} GB` : '—' },
            { label: 'Disk', value: machine.disk_used_pct ? `${machine.disk_used_pct}% of ${machine.disk_total_gb} GB` : '—' },
            { label: 'Uptime', value: machine.uptime },
            { label: 'Last Seen', value: machine.last_seen ? new Date(machine.last_seen).toLocaleString() : '—' },
            { label: 'Open Issues', value: issue_counts?.open || 0 },
            { label: 'Resolved', value: issue_counts?.resolved || 0 },
          ].map(({ label, value }) => (
            <div key={label} className="p-3 rounded-lg" style={{ background: 'var(--color-surface-700)' }}>
              <p className="text-xs mb-1" style={{ color: 'var(--color-text-muted)' }}>{label}</p>
              <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>{value || '—'}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Logs */}
      <div className="glass-card p-5">
        <h2 className="text-base font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>
          Recent Logs ({recent_logs?.length || 0})
        </h2>
        <div className="log-viewer max-h-96 overflow-y-auto">
          {recent_logs?.length ? (
            recent_logs.map((log, i) => <LogLine key={log.id} log={log} index={i} />)
          ) : (
            <p className="text-sm py-4 text-center" style={{ color: 'var(--color-text-muted)' }}>No recent logs</p>
          )}
        </div>
      </div>
    </div>
  );
}
