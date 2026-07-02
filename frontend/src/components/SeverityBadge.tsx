import type { Severity } from '../types/scan';

const severityClasses: Record<Severity, string> = {
  critical: 'border-red-400/40 bg-red-500/15 text-red-200',
  high: 'border-orange-400/40 bg-orange-500/15 text-orange-200',
  medium: 'border-yellow-400/40 bg-yellow-500/15 text-yellow-100',
  low: 'border-blue-400/40 bg-blue-500/15 text-blue-200',
  info: 'border-slate-500/40 bg-slate-500/15 text-slate-200',
};

interface SeverityBadgeProps {
  severity: Severity;
}

export default function SeverityBadge({ severity }: SeverityBadgeProps) {
  return (
    <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold capitalize ${severityClasses[severity]}`}>
      {severity}
    </span>
  );
}
