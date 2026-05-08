/**
 * Single log line in the terminal-style viewer. Color-coded by severity.
 */
export default function LogLine({ log, index }) {
  const severity = (log.severity || 'info').toLowerCase();
  const ts = log.timestamp
    ? new Date(log.timestamp).toLocaleTimeString('en-US', { hour12: false })
    : '';

  return (
    <div className={`log-line ${severity}`}>
      <span style={{ color: 'var(--color-text-muted)', marginRight: '12px', userSelect: 'none' }}>
        {String(index + 1).padStart(4, ' ')}
      </span>
      <span style={{ color: 'var(--color-text-muted)', marginRight: '12px' }}>{ts}</span>
      {log.service && (
        <span style={{ color: 'var(--color-accent-cyan)', marginRight: '12px' }}>
          [{log.service}]
        </span>
      )}
      <span>{log.message || '—'}</span>
    </div>
  );
}
