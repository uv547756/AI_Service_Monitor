import { useCallback } from 'react';
import { Link } from 'react-router-dom';
import StatusBadge from '../components/StatusBadge';
import { fetchIssues } from '../api/client';
import { usePolling } from '../hooks/usePolling';

export default function Issues() {
  const { data: issues, loading } = usePolling(useCallback(() => fetchIssues({ limit: 50 }), []), 5000);

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>Issues & Alerts</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>
          {issues?.length || 0} detected issues
        </p>
      </div>

      <div className="glass-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr style={{ background: 'var(--color-surface-700)' }}>
              {['Severity', 'Service', 'Summary', 'Status', 'Time'].map(h => (
                <th key={h} className="text-left px-4 py-3 font-medium text-xs uppercase tracking-wider"
                  style={{ color: 'var(--color-text-muted)' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading && !issues ? (
              <tr><td colSpan={5} className="text-center py-8" style={{ color: 'var(--color-text-muted)' }}>Loading...</td></tr>
            ) : issues?.length ? (
              issues.map(issue => (
                <tr key={issue.id} className="border-t hover:opacity-80 transition-opacity cursor-pointer"
                  style={{ borderColor: 'var(--color-border)' }}>
                  <td className="px-4 py-3"><StatusBadge status={issue.severity} /></td>
                  <td className="px-4 py-3" style={{ color: 'var(--color-accent-cyan)' }}>{issue.service || '—'}</td>
                  <td className="px-4 py-3">
                    <Link to={`/issues/${issue.id}`} style={{ color: 'var(--color-text-primary)' }}
                      className="hover:underline">
                      {issue.summary?.substring(0, 80) || 'Untitled'}
                      {issue.summary?.length > 80 ? '...' : ''}
                    </Link>
                  </td>
                  <td className="px-4 py-3"><StatusBadge status={issue.status} /></td>
                  <td className="px-4 py-3 whitespace-nowrap" style={{ color: 'var(--color-text-muted)' }}>
                    {issue.created_at ? new Date(issue.created_at).toLocaleString() : '—'}
                  </td>
                </tr>
              ))
            ) : (
              <tr><td colSpan={5} className="text-center py-8" style={{ color: 'var(--color-text-muted)' }}>No issues found</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
