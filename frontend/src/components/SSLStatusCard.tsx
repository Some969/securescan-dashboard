interface SSLStatusCardProps {
  ssl?: Record<string, unknown>;
}

function valueText(value: unknown) {
  if (value === true) return 'Yes';
  if (value === false) return 'No';
  if (value === null || value === undefined || value === '') return 'Unknown';
  return String(value);
}

export default function SSLStatusCard({ ssl = {} }: SSLStatusCardProps) {
  const rows = [
    ['HTTPS enabled', valueText(ssl.https_enabled)],
    ['Certificate valid', valueText(ssl.certificate_valid)],
    ['Issuer', valueText(ssl.issuer)],
    ['Expires at', valueText(ssl.expires_at)],
    ['Days left', valueText(ssl.days_left)],
  ];

  return (
    <section className="card p-6">
      <h2 className="text-lg font-semibold text-white">SSL/TLS Status</h2>
      <div className="mt-4 space-y-3">
        {rows.map(([label, value]) => (
          <div key={label} className="flex flex-col gap-1 rounded-xl bg-slate-950/50 p-3 sm:flex-row sm:items-center sm:justify-between">
            <span className="text-sm text-slate-400">{label}</span>
            <span className="break-all text-sm font-medium text-white">{value}</span>
          </div>
        ))}
      </div>
      {ssl.error ? (
        <p className="mt-4 rounded-xl border border-red-400/30 bg-red-500/10 p-3 text-sm text-red-200">
          {String(ssl.error)}
        </p>
      ) : null}
    </section>
  );
}
