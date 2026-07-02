import type { SecurityHeaderMissing, SecurityHeaderPresent } from '../types/scan';

interface HeaderCheckCardProps {
  present?: SecurityHeaderPresent[];
  missing?: SecurityHeaderMissing[];
  error?: string;
}

export default function HeaderCheckCard({ present = [], missing = [], error }: HeaderCheckCardProps) {
  return (
    <section className="card p-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Security Headers</h2>
          <p className="text-sm text-slate-400">Checks common browser security headers.</p>
        </div>
        <span className="rounded-full bg-slate-800 px-3 py-1 text-sm text-slate-300">
          {present.length} present / {missing.length} missing
        </span>
      </div>

      {error && <p className="mt-4 rounded-xl border border-red-400/30 bg-red-500/10 p-3 text-sm text-red-200">{error}</p>}

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <div>
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-emerald-300">Present</h3>
          <div className="space-y-3">
            {present.length === 0 && <p className="text-sm text-slate-500">No required headers detected.</p>}
            {present.map((header) => (
              <div key={header.name} className="rounded-xl border border-emerald-400/20 bg-emerald-400/5 p-4">
                <p className="font-semibold text-white">{header.name}</p>
                <p className="mt-1 break-all text-xs text-slate-400">{header.value}</p>
                <p className="mt-2 text-sm text-slate-400">{header.explanation}</p>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-yellow-300">Missing</h3>
          <div className="space-y-3">
            {missing.length === 0 && <p className="text-sm text-slate-500">No required headers missing.</p>}
            {missing.map((header) => (
              <div key={header.name} className="rounded-xl border border-yellow-400/20 bg-yellow-400/5 p-4">
                <p className="font-semibold text-white">{header.name}</p>
                <p className="mt-2 text-sm text-slate-400">{header.explanation}</p>
                <p className="mt-2 text-sm text-yellow-100">{header.recommendation}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
