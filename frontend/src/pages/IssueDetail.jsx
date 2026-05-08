import { useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import StatusBadge from '../components/StatusBadge';
import { fetchIssue } from '../api/client';
import { usePolling } from '../hooks/usePolling';

export default function IssueDetail() {
  const { id } = useParams();
  const { data: issue, loading } = usePolling(useCallback(() => fetchIssue(id), [id]), 5000);

  if (loading && !issue) {
    return <div className="text-center py-12" style={{ color: 'var(--color-text-muted)' }}>Loading...</div>;
  }
  if (!issue) {
    return <div className="text-center py-12" style={{ color: 'var(--color-text-muted)' }}>Issue not found</div>;
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--color-text-muted)' }}>
        <Link to="/issues" style={{ color: 'var(--color-accent-blue)' }}>Issues</Link>
        <span>›</span>
        <span style={{ color: 'var(--color-text-primary)' }}>{issue.id?.substring(0, 8)}</span>
      </div>

      {/* Issue Header */}
      <div className="glass-card p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h1 className="text-xl font-bold mb-2" style={{ color: 'var(--color-text-primary)' }}>
              {issue.summary || 'Untitled Issue'}
            </h1>
            <div className="flex items-center gap-3 text-sm">
              <span style={{ color: 'var(--color-text-muted)' }}>
                {issue.machine?.hostname || 'Unknown'} · {issue.service || 'unknown'}
              </span>
              <span style={{ color: 'var(--color-text-muted)' }}>
                {issue.created_at ? new Date(issue.created_at).toLocaleString() : ''}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <StatusBadge status={issue.severity} size="lg" />
            <StatusBadge status={issue.status} size="lg" />
          </div>
        </div>

        {/* Confidence bar */}
        {issue.confidence != null && (
          <div className="mt-4">
            <div className="flex justify-between text-xs mb-1">
              <span style={{ color: 'var(--color-text-muted)' }}>AI Confidence</span>
              <span style={{ color: 'var(--color-text-secondary)' }}>{(issue.confidence * 100).toFixed(0)}%</span>
            </div>
            <div className="w-full h-2 rounded-full overflow-hidden" style={{ background: 'var(--color-surface-700)' }}>
              <div className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${issue.confidence * 100}%`,
                  background: issue.confidence > 0.8
                    ? 'var(--color-severity-healthy)'
                    : issue.confidence > 0.5
                      ? 'var(--color-severity-warning)'
                      : 'var(--color-severity-critical)',
                }}></div>
            </div>
          </div>
        )}
      </div>

      {/* AI Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-card p-5">
          <h2 className="text-base font-semibold mb-3 flex items-center gap-2"
            style={{ color: 'var(--color-text-primary)' }}>
            🤖 AI Analysis
          </h2>
          <div className="space-y-4">
            <div>
              <p className="text-xs font-medium uppercase tracking-wider mb-1"
                style={{ color: 'var(--color-text-muted)' }}>Summary</p>
              <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                {issue.summary || '—'}
              </p>
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wider mb-1"
                style={{ color: 'var(--color-text-muted)' }}>Root Cause</p>
              <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                {issue.root_cause || '—'}
              </p>
            </div>
          </div>
        </div>

        {/* Commands */}
        <div className="glass-card p-5">
          <h2 className="text-base font-semibold mb-3 flex items-center gap-2"
            style={{ color: 'var(--color-text-primary)' }}>
            ⚡ Commands
          </h2>
          {issue.commands?.length ? (
            <div className="space-y-4">
              {issue.commands.map(cmd => (
                <div key={cmd.id} className="p-3 rounded-lg" style={{ background: 'var(--color-surface-700)' }}>
                  <div className="flex items-center justify-between mb-2">
                    <StatusBadge status={cmd.approval_status} />
                    {cmd.approved_by && (
                      <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                        by {cmd.approved_by}
                      </span>
                    )}
                  </div>
                  <code className="block text-sm p-2 rounded mt-2"
                    style={{
                      background: 'var(--color-surface-900)',
                      color: 'var(--color-accent-cyan)',
                      fontFamily: 'monospace',
                    }}>
                    $ {cmd.command_text}
                  </code>

                  {/* Execution results */}
                  {cmd.executions?.map(ex => (
                    <div key={ex.id} className="mt-3 p-2 rounded text-xs"
                      style={{ background: 'var(--color-surface-900)' }}>
                      <div className="flex items-center gap-2 mb-1">
                        <StatusBadge status={ex.status} />
                        <span style={{ color: 'var(--color-text-muted)' }}>
                          exit code: {ex.exit_code}
                        </span>
                      </div>
                      {ex.stdout && (
                        <pre className="mt-1" style={{ color: 'var(--color-severity-healthy)', whiteSpace: 'pre-wrap' }}>
                          {ex.stdout}
                        </pre>
                      )}
                      {ex.stderr && (
                        <pre className="mt-1" style={{ color: 'var(--color-severity-critical)', whiteSpace: 'pre-wrap' }}>
                          {ex.stderr}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>No commands generated</p>
          )}
        </div>
      </div>

      {/* Log Context */}
      {issue.trigger_log && (
        <div className="glass-card p-5">
          <h2 className="text-base font-semibold mb-3" style={{ color: 'var(--color-text-primary)' }}>
            📋 Log Context
          </h2>
          <div className="log-viewer max-h-96 overflow-y-auto">
            {issue.trigger_log.raw_context ? (
              issue.trigger_log.raw_context.split('\n').map((line, i) => {
                const isError = /error|failed|fatal|critical/i.test(line);
                const isWarning = /warning|warn/i.test(line);
                const cls = isError ? 'error' : isWarning ? 'warning' : 'info';
                return (
                  <div key={i} className={`log-line ${cls}`}>
                    <span style={{ color: 'var(--color-text-muted)', marginRight: 12, userSelect: 'none' }}>
                      {String(i + 1).padStart(4, ' ')}
                    </span>
                    {line}
                  </div>
                );
              })
            ) : (
              <div className="log-line info">
                <span style={{ color: 'var(--color-text-muted)', marginRight: 12 }}>   1</span>
                {issue.trigger_log.message || '—'}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
