/**
 * Stats card for the dashboard overview.
 */
export default function StatsCard({ title, value, icon, trend, color = 'blue' }) {
  const gradients = {
    blue: 'linear-gradient(135deg, rgba(91,138,245,0.12), rgba(91,138,245,0.04))',
    green: 'linear-gradient(135deg, rgba(52,211,153,0.12), rgba(52,211,153,0.04))',
    yellow: 'linear-gradient(135deg, rgba(251,191,36,0.12), rgba(251,191,36,0.04))',
    red: 'linear-gradient(135deg, rgba(248,113,113,0.12), rgba(248,113,113,0.04))',
    purple: 'linear-gradient(135deg, rgba(139,108,247,0.12), rgba(139,108,247,0.04))',
  };

  const iconColors = {
    blue: 'var(--color-accent-blue)',
    green: 'var(--color-severity-healthy)',
    yellow: 'var(--color-severity-warning)',
    red: 'var(--color-severity-critical)',
    purple: 'var(--color-accent-purple)',
  };

  return (
    <div className="glass-card p-5 animate-fade-in">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider mb-2"
            style={{ color: 'var(--color-text-muted)' }}>
            {title}
          </p>
          <p className="text-3xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
            {value ?? '—'}
          </p>
          {trend && (
            <p className="text-xs mt-2" style={{ color: 'var(--color-text-secondary)' }}>
              {trend}
            </p>
          )}
        </div>
        <div className="w-11 h-11 rounded-xl flex items-center justify-center text-xl"
          style={{ background: gradients[color] }}>
          <span style={{ color: iconColors[color] }}>{icon}</span>
        </div>
      </div>
    </div>
  );
}
