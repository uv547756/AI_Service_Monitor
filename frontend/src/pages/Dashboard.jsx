import { useCallback } from 'react';
import { Link } from 'react-router-dom';
import StatsCard from '../components/StatsCard';
import StatusBadge from '../components/StatusBadge';
import { fetchMachines, fetchIssues, fetchCommands } from '../api/client';
import { usePolling } from '../hooks/usePolling';

export default function Dashboard() {
  const { data: machines } = usePolling(useCallback(() => fetchMachines(), []), 5000);
  const { data: issues } = usePolling(useCallback(() => fetchIssues({ limit: 10 }), []), 5000);
  const { data: commands } = usePolling(useCallback(() => fetchCommands({ limit: 10 }), []), 5000);

  const totalMachines = machines?.length || 0;
  const activeIssues = issues?.filter(i => i.status === 'open')?.length || 0;
  const criticalAlerts = issues?.filter(i => i.severity === 'critical')?.length || 0;
  const pendingCommands = commands?.filter(c => c.approval_status === 'pending')?.length || 0;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
          Dashboard
        </h1>
        <p className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>
          System overview and recent activity
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard title="Total Machines" value={totalMachines} icon="🖥️" color="blue" trend="Monitored hosts" />
        <StatsCard title="Active Issues" value={activeIssues} icon="⚠️" color="yellow" trend="Require attention" />
        <StatsCard title="Critical Alerts" value={criticalAlerts} icon="🔴" color="red" trend="Immediate action" />
        <StatsCard title="Pending Commands" value={pendingCommands} icon="⏳" color="purple" trend="Awaiting approval" />
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Issues */}
        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold" style={{ color: 'var(--color-text-primary)' }}>Recent Issues</h2>
            <Link to="/issues" className="text-xs font-medium" style={{ color: 'var(--color-accent-blue)' }}>View All →</Link>
          </div>
          <div className="space-y-3">
            {issues?.slice(0, 5)?.map(issue => (
              <Link key={issue.id} to={`/issues/${issue.id}`} className="block">
                <div className="flex items-center justify-between p-3 rounded-lg hover:opacity-80 transition-opacity"
                  style={{ background: 'var(--color-surface-700)' }}>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate" style={{ color: 'var(--color-text-primary)' }}>
                      {issue.summary || 'Untitled Issue'}
                    </p>
                    <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
                      {issue.service || 'unknown'} · {new Date(issue.created_at).toLocaleString()}
                    </p>
                  </div>
                  <StatusBadge status={issue.severity} />
                </div>
              </Link>
            )) || (
              <p className="text-sm text-center py-4" style={{ color: 'var(--color-text-muted)' }}>No issues found</p>
            )}
          </div>
        </div>

        {/* Machine Status */}
        <div className="glass-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold" style={{ color: 'var(--color-text-primary)' }}>Machine Status</h2>
            <Link to="/machines" className="text-xs font-medium" style={{ color: 'var(--color-accent-blue)' }}>View All →</Link>
          </div>
          <div className="space-y-3">
            {machines?.slice(0, 5)?.map(m => (
              <Link key={m.id} to={`/machines/${m.id}`} className="block">
                <div className="flex items-center justify-between p-3 rounded-lg hover:opacity-80 transition-opacity"
                  style={{ background: 'var(--color-surface-700)' }}>
                  <div className="flex items-center gap-3">
                    <span className={`status-dot ${m.status}`}></span>
                    <div>
                      <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>{m.hostname}</p>
                      <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{m.ip_address || m.os_info}</p>
                    </div>
                  </div>
                  <StatusBadge status={m.status} />
                </div>
              </Link>
            )) || (
              <p className="text-sm text-center py-4" style={{ color: 'var(--color-text-muted)' }}>No machines found</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
