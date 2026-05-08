import { useCallback, useState } from 'react';
import StatusBadge from '../components/StatusBadge';
import { fetchCommands, approveCommand, rejectCommand } from '../api/client';
import { usePolling } from '../hooks/usePolling';

export default function Commands() {
  const { data: commands, loading, refetch } = usePolling(useCallback(() => fetchCommands({ limit: 50 }), []), 5000);
  const [acting, setActing] = useState(null);

  const handleApprove = async (id) => {
    setActing(id);
    try {
      await approveCommand(id);
      refetch();
    } catch (e) {
      alert(e?.response?.data?.detail || 'Failed to approve');
    } finally {
      setActing(null);
    }
  };

  const handleReject = async (id) => {
    setActing(id);
    try {
      await rejectCommand(id);
      refetch();
    } catch (e) {
      alert(e?.response?.data?.detail || 'Failed to reject');
    } finally {
      setActing(null);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>Commands</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--color-text-secondary)' }}>
          Track all suggested, approved, and executed commands
        </p>
      </div>

      {loading && !commands ? (
        <div className="text-center py-12" style={{ color: 'var(--color-text-muted)' }}>Loading...</div>
      ) : (
        <div className="space-y-3">
          {commands?.length ? commands.map(cmd => (
            <div key={cmd.id} className="glass-card p-5">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <StatusBadge status={cmd.approval_status} />
                  {cmd.safe_to_auto_execute && (
                    <span className="text-xs px-2 py-0.5 rounded-full"
                      style={{ background: 'rgba(52,211,153,0.1)', color: 'var(--color-severity-healthy)' }}>
                      auto-safe
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {cmd.approval_status === 'pending' && (
                    <>
                      <button
                        onClick={() => handleApprove(cmd.id)}
                        disabled={acting === cmd.id}
                        className="text-xs font-medium px-3 py-1.5 rounded-lg transition-colors"
                        style={{
                          background: 'rgba(52,211,153,0.15)',
                          color: 'var(--color-severity-healthy)',
                          border: '1px solid rgba(52,211,153,0.3)',
                          cursor: acting === cmd.id ? 'wait' : 'pointer',
                          opacity: acting === cmd.id ? 0.5 : 1,
                        }}>
                        {acting === cmd.id ? '...' : '✓ Approve'}
                      </button>
                      <button
                        onClick={() => handleReject(cmd.id)}
                        disabled={acting === cmd.id}
                        className="text-xs font-medium px-3 py-1.5 rounded-lg transition-colors"
                        style={{
                          background: 'rgba(239,68,68,0.15)',
                          color: 'var(--color-severity-critical)',
                          border: '1px solid rgba(239,68,68,0.3)',
                          cursor: acting === cmd.id ? 'wait' : 'pointer',
                          opacity: acting === cmd.id ? 0.5 : 1,
                        }}>
                        {acting === cmd.id ? '...' : '✗ Reject'}
                      </button>
                    </>
                  )}
                  <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                    {cmd.created_at ? new Date(cmd.created_at).toLocaleString() : ''}
                  </span>
                </div>
              </div>

              {/* Command text */}
              <code className="block text-sm p-3 rounded-lg mb-3"
                style={{
                  background: 'var(--color-surface-900)',
                  color: 'var(--color-accent-cyan)',
                  fontFamily: 'monospace',
                  border: '1px solid var(--color-border)',
                }}>
                $ {cmd.command_text}
              </code>

              {/* Meta */}
              <div className="flex items-center gap-4 text-xs" style={{ color: 'var(--color-text-muted)' }}>
                <span>Machine: {cmd.machine_id?.substring(0, 8)}</span>
                {cmd.approved_by && <span>Approved by: {cmd.approved_by}</span>}
                {cmd.approved_at && <span>At: {new Date(cmd.approved_at).toLocaleString()}</span>}
              </div>

              {/* Executions */}
              {cmd.executions?.length > 0 && (
                <div className="mt-3 space-y-2">
                  {cmd.executions.map(ex => (
                    <div key={ex.id} className="p-3 rounded-lg text-sm"
                      style={{ background: 'var(--color-surface-700)' }}>
                      <div className="flex items-center gap-3 mb-2">
                        <StatusBadge status={ex.status} />
                        <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                          Exit: {ex.exit_code} · {ex.completed_at ? new Date(ex.completed_at).toLocaleString() : ''}
                        </span>
                      </div>
                      {ex.stdout && (
                        <pre className="text-xs p-2 rounded overflow-x-auto"
                          style={{ background: 'var(--color-surface-900)', color: 'var(--color-severity-healthy)', whiteSpace: 'pre-wrap' }}>
                          {ex.stdout}
                        </pre>
                      )}
                      {ex.stderr && (
                        <pre className="text-xs p-2 rounded overflow-x-auto mt-1"
                          style={{ background: 'var(--color-surface-900)', color: 'var(--color-severity-critical)', whiteSpace: 'pre-wrap' }}>
                          {ex.stderr}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )) : (
            <p className="text-center py-8" style={{ color: 'var(--color-text-muted)' }}>No commands found</p>
          )}
        </div>
      )}
    </div>
  );
}
