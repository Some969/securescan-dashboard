import { useEffect, useState } from 'react';
import { Download, TriangleAlert } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import FindingsTable from '../components/FindingsTable';
import HeaderCheckCard from '../components/HeaderCheckCard';
import LoadingSpinner from '../components/LoadingSpinner';
import OpenPortsTable from '../components/OpenPortsTable';
import RiskScoreCard from '../components/RiskScoreCard';
import SSLStatusCard from '../components/SSLStatusCard';
import StatCard from '../components/StatCard';
import { api } from '../lib/api';
import type { CookieResult, FrontendLibraryHint, ScanReport } from '../types/scan';

export default function Report() {
  const { scanId } = useParams();
  const [report, setReport] = useState<ScanReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  useEffect(() => {
    async function loadReport() {
      try {
        const id = Number(scanId);
        if (!Number.isFinite(id)) throw new Error('Invalid scan ID.');
        const data = await api.getScan(id);
        setReport(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load report.');
      } finally {
        setLoading(false);
      }
    }
    loadReport();
  }, [scanId]);

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(null), 3000);
    return () => window.clearTimeout(timer);
  }, [toast]);

  async function handleExportPdf() {
    if (!report || !scanId) return;

    try {
      setDownloadingPdf(true);
      const blob = await api.downloadPdf(Number(scanId));
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `scan_${report.target_url.replace(/[^a-zA-Z0-9._-]/g, '_')}_${report.id}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      setToast({ type: 'success', message: 'PDF report downloaded successfully.' });
    } catch (err) {
      setToast({ type: 'error', message: err instanceof Error ? err.message : 'Unable to export the PDF report.' });
    } finally {
      setDownloadingPdf(false);
    }
  }

  if (loading) return <LoadingSpinner label="Loading report..." />;
  if (error) return <p className="card p-5 text-red-200">{error}</p>;
  if (!report) return <p className="card p-5 text-slate-300">Report not found.</p>;

  const redirect = report.checks.redirect ?? {};
  const serverLeakage = report.checks.server_leakage ?? {};
  const libraries = report.checks.libraries?.libraries ?? [];
  const cookieCheck = report.checks.cookies ?? {};
  const cookieResults = (cookieCheck.results ?? []) as CookieResult[];
  const cookieSummary = cookieCheck.summary ?? { missing_secure: 0, missing_httponly: 0, missing_samesite: 0 };
  const exposedHeaders = (serverLeakage.exposed_headers as Array<{ name: string; value: string; severity: string }> | undefined) ?? [];

  return (
    <div className="space-y-8">
      <section className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-cyan-300">Scan Report</p>
          <h1 className="mt-2 break-all text-3xl font-black text-white">{report.target_url}</h1>
          <p className="mt-2 text-slate-400">Scanned on {new Date(report.scan_date).toLocaleString()}</p>
        </div>
        <Link to="/scan/new" className="rounded-2xl bg-cyan-300 px-5 py-3 text-center font-bold text-slate-950 hover:bg-cyan-200">
          Run another scan
        </Link>
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.2fr_2fr]">
        <div className="space-y-3">
          <RiskScoreCard score={report.risk_score} grade={report.grade} />
          <button
            type="button"
            onClick={handleExportPdf}
            disabled={downloadingPdf}
            className="inline-flex items-center justify-center gap-2 rounded-2xl bg-cyan-300 px-4 py-3 font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {downloadingPdf ? <LoadingSpinner label="Preparing PDF..." /> : <><Download size={18} /> Export PDF</>}
          </button>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <StatCard title="Critical" value={report.summary.critical} />
          <StatCard title="High" value={report.summary.high} />
          <StatCard title="Medium" value={report.summary.medium} />
          <StatCard title="Low" value={report.summary.low} />
          <StatCard title="Info" value={report.summary.info} />
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <SSLStatusCard ssl={report.checks.ssl} />

        <section className="card p-6">
          <h2 className="text-lg font-semibold text-white">HTTPS Redirect</h2>
          <div className="mt-4 space-y-3 text-sm">
            <InfoRow label="Checked URL" value={String(redirect.checked_url ?? 'Unknown')} />
            <InfoRow label="Redirects to HTTPS" value={redirect.redirects_to_https ? 'Yes' : 'No'} />
            <InfoRow label="Final URL" value={String(redirect.final_url ?? 'Unknown')} />
            <InfoRow label="Final status" value={String(redirect.final_status_code ?? 'Unknown')} />
          </div>
          {redirect.error ? <p className="mt-4 rounded-xl border border-red-400/30 bg-red-500/10 p-3 text-sm text-red-200">{String(redirect.error)}</p> : null}
        </section>
      </section>

      <HeaderCheckCard
        present={report.checks.headers?.present}
        missing={report.checks.headers?.missing}
        error={report.checks.headers?.error}
      />

      <section className="grid gap-6 lg:grid-cols-2">
        <section className="card p-6">
          <h2 className="text-lg font-semibold text-white">Server Information Leakage</h2>
          <div className="mt-4 space-y-3">
            {exposedHeaders.length === 0 ? (
              <p className="text-sm text-slate-400">No configured information leakage headers were detected.</p>
            ) : (
              exposedHeaders.map((header) => (
                <div key={header.name} className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                  <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                    <p className="font-semibold text-white">{header.name}</p>
                    <p className="text-xs uppercase text-slate-500">{header.severity}</p>
                  </div>
                  <p className="mt-2 break-all text-sm text-slate-400">{header.value}</p>
                </div>
              ))
            )}
          </div>
          {serverLeakage.error ? <p className="mt-4 rounded-xl border border-red-400/30 bg-red-500/10 p-3 text-sm text-red-200">{String(serverLeakage.error)}</p> : null}
        </section>

        <section className="card p-6">
          <h2 className="text-lg font-semibold text-white">Frontend Library Hints</h2>
          <div className="mt-4 space-y-3">
            {libraries.length === 0 ? (
              <p className="text-sm text-slate-400">No common frontend libraries were detected from script URLs.</p>
            ) : (
              libraries.map((library: FrontendLibraryHint, index: number) => (
                <div key={`${library.name}-${index}`} className="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
                  <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                    <p className="font-semibold text-white">{library.name} {library.version ? `v${library.version}` : ''}</p>
                    <p className="text-xs uppercase text-slate-500">{library.status}</p>
                  </div>
                  <p className="mt-2 break-all text-sm text-slate-400">{library.source}</p>
                </div>
              ))
            )}
          </div>
          {report.checks.libraries?.error ? <p className="mt-4 rounded-xl border border-red-400/30 bg-red-500/10 p-3 text-sm text-red-200">{report.checks.libraries.error}</p> : null}
        </section>
      </section>

      <OpenPortsTable
        openPorts={report.checks.ports?.open_ports}
        command={report.checks.ports?.command}
        error={report.checks.ports?.error}
        nmapAvailable={report.checks.ports?.nmap_available}
      />

      <section className="card p-6">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-white">Cookie Security</h2>
          {cookieCheck.error ? <span className="rounded-full border border-red-400/30 bg-red-500/10 px-3 py-1 text-xs text-red-200">{cookieCheck.error}</span> : null}
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-4">
          <SummaryTile label="Cookies Found" value={cookieCheck.cookies_found ?? 0} />
          <SummaryTile label="Missing Secure" value={cookieSummary.missing_secure} />
          <SummaryTile label="Missing HttpOnly" value={cookieSummary.missing_httponly} />
          <SummaryTile label="Missing SameSite" value={cookieSummary.missing_samesite} />
        </div>
        <div className="mt-5 overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-800">
            <thead className="bg-slate-950/50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="table-cell">Cookie Name</th>
                <th className="table-cell">Secure</th>
                <th className="table-cell">HttpOnly</th>
                <th className="table-cell">SameSite</th>
                <th className="table-cell">Expiration</th>
                <th className="table-cell">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {cookieResults.length === 0 ? (
                <tr>
                  <td className="table-cell py-4 text-slate-400" colSpan={6}>{cookieCheck.status ?? 'No cookie data was reported.'}</td>
                </tr>
              ) : (
                cookieResults.map((cookie) => {
                  const configured = Boolean(cookie.secure && cookie.httponly && cookie.samesite);
                  return (
                    <tr key={`${cookie.name}-${cookie.domain}-${cookie.path}`}>
                      <td className="table-cell font-medium text-white">{cookie.name}</td>
                      <td className="table-cell text-slate-300">{cookie.secure ? 'Yes' : 'No'}</td>
                      <td className="table-cell text-slate-300">{cookie.httponly ? 'Yes' : 'No'}</td>
                      <td className="table-cell text-slate-300">{cookie.samesite || 'Not set'}</td>
                      <td className="table-cell text-slate-300">{cookie.expires || 'Not set'}</td>
                      <td className="table-cell">
                        <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${configured ? 'bg-emerald-500/15 text-emerald-300' : 'bg-amber-500/15 text-amber-300'}`}>
                          {configured ? 'Configured correctly' : 'Needs attention'}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card p-6">
        <h2 className="text-lg font-semibold text-white">Recommendations</h2>
        {report.recommendations.length === 0 ? (
          <p className="mt-3 text-sm text-slate-400">No recommendations generated.</p>
        ) : (
          <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-slate-300">
            {report.recommendations.map((recommendation) => (
              <li key={recommendation}>{recommendation}</li>
            ))}
          </ul>
        )}
      </section>

      <FindingsTable findings={report.findings} />

      {toast ? (
        <div className={`fixed right-4 top-4 z-50 rounded-2xl px-4 py-3 text-sm shadow-lg ${toast.type === 'success' ? 'bg-emerald-500/15 text-emerald-300' : 'bg-red-500/15 text-red-200'}`}>
          <div className="flex items-center gap-2">
            {toast.type === 'error' ? <TriangleAlert size={16} /> : null}
            <span>{toast.message}</span>
          </div>
        </div>
      ) : null}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1 rounded-xl bg-slate-950/50 p-3 sm:flex-row sm:items-center sm:justify-between">
      <span className="text-slate-400">{label}</span>
      <span className="break-all font-medium text-white">{value}</span>
    </div>
  );
}

function SummaryTile({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950/50 p-4">
      <p className="text-sm text-slate-400">{label}</p>
      <p className="mt-2 text-2xl font-bold text-white">{value}</p>
    </div>
  );
}
