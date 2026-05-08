import { useCallback } from 'react';
import { Link } from 'react-router-dom';
import StatusBadge from '../components/StatusBadge';
import { fetchMachines } from '../api/client';
import { usePolling } from '../hooks/usePolling';

export default function Machines() {
  const { data: machines, loading } = usePolling(useCallback(() => fetchMachines(), []), 5000);

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>Machines</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>
          {machines?.length || 0} monitored hosts
        </p>
      </div>

      {loading && !machines ? (
        <div className="text-center py-12" style={{ color: 'var(--color-text-muted)' }}>Loading...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {machines?.map(m => (
            <Link key={m.id} to={`/machines/${m.id}`} className="block">
              <div className="glass-card p-5 h-full">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span className={`status-dot ${m.status}`}></span>
                    <h3 className="text-base font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                      {m.hostname}
                    </h3>
                  </div>
                  <StatusBadge status={m.status} />
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span style={{ color: 'var(--color-text-muted)' }}>OS</span>
                    <span style={{ color: 'var(--color-text-secondary)' }}>{m.os_info || '—'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span style={{ color: 'var(--color-text-muted)' }}>IP</span>
                    <span style={{ color: 'var(--color-text-secondary)' }}>{m.ip_address || '—'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span style={{ color: 'var(--color-text-muted)' }}>Uptime</span>
                    <span style={{ color: 'var(--color-text-secondary)' }}>{m.uptime || '—'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span style={{ color: 'var(--color-text-muted)' }}>Disk</span>
                    <span style={{ color: 'var(--color-text-secondary)' }}>{m.disk_used_pct ? `${m.disk_used_pct}%` : '—'}</span>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t text-xs" style={{ borderColor: 'var(--color-border)', color: 'var(--color-text-muted)' }}>
                  Last seen: {m.last_seen ? new Date(m.last_seen).toLocaleString() : 'Never'}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
