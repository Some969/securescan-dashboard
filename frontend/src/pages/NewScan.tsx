import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';
import { api } from '../lib/api';

export default function NewScan() {
  const [targetUrl, setTargetUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const report = await api.runScan(targetUrl);
      navigate(`/reports/${report.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Scan failed.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <section className="card p-6 sm:p-8">
        <div className="flex items-start gap-4">
          <div className="rounded-2xl border border-cyan-400/30 bg-cyan-400/10 p-3 text-cyan-300">
            <ShieldCheck size={28} />
          </div>
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.25em] text-cyan-300">New Scan</p>
            <h1 className="mt-2 text-3xl font-black text-white">Run a defensive website scan</h1>
            <p className="mt-2 text-slate-400">
              Only scan websites you own or have explicit permission to test. The scanner avoids aggressive or exploit-based checks.
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-5">
          <div>
            <label htmlFor="targetUrl" className="text-sm font-medium text-slate-300">Website URL</label>
            <input
              id="targetUrl"
              value={targetUrl}
              onChange={(event) => setTargetUrl(event.target.value)}
              placeholder="https://example.com"
              required
              className="mt-2 w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-300 focus:ring-4 focus:ring-cyan-300/10"
            />
            <p className="mt-2 text-xs text-slate-500">If you enter example.com, the backend automatically normalizes it to https://example.com.</p>
          </div>

          {error && <p className="rounded-xl border border-red-400/30 bg-red-500/10 p-3 text-sm text-red-200">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="inline-flex w-full items-center justify-center rounded-2xl bg-cyan-300 px-5 py-3 font-bold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
          >
            {loading ? 'Scanning...' : 'Run Scan'}
          </button>
        </form>
      </section>

      {loading && (
        <div className="card p-5">
          <LoadingSpinner label="Running safe scanner modules. This may take a moment if Nmap is enabled." />
        </div>
      )}
    </div>
  );
}
