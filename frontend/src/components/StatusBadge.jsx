/**
 * Reusable status/severity badge.
 */
export default function StatusBadge({ status, size = 'sm' }) {
  if (!status) return null;
  const s = status.toLowerCase();
  const sizeClass = size === 'lg' ? 'text-sm px-3 py-1' : '';
  return <span className={`badge badge-${s} ${sizeClass}`}>{status}</span>;
}
