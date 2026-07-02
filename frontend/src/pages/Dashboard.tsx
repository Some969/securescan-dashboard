import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, BarChart3, Cookie, ListChecks, ShieldPlus } from 'lucide-react';
import StatCard from '../components/StatCard';
import LoadingSpinner from '../components/LoadingSpinner';
import { api } from '../lib/api';
import type { ScanHistoryItem, ScanReport } from '../types/scan';

export default function Dashboard() {
  const [scans, setScans] = useState<ScanHistoryItem[]>([]);
  const [recentReports, setRecentReports] = useState<ScanReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const history = await api.listScans();
        setScans(history);
        const reports = await Promise.all(history.slice(0, 5).map((item) => api.getScan(item.id)));
        setRecentReports(reports);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard.');
      } finally {
        setLoading(false);
      }
    }
    loadDashboard();
  }, []);

  const averageScore = useMemo(() => {
    if (scans.length === 0) return 0;
    return Math.round(scans.reduce((sum, scan) => sum + scan.risk_score, 0) / scans.length);
  }, [scans]);

  const seriousFindings = recentReports.reduce(
    (sum, report) => sum + report.summary.critical + report.summary.high,
    0,
  );
  const cookieIssues = recentReports.reduce(
    (sum, report) => sum + report.findings.filter((finding) => finding.affected_component === 'Cookie Security').length,
    0,
  );

  if (loading) {
    return <LoadingSpinner label="Loading dashboard..." />;
  }

  if (error) {
    return <p className="card p-5 text-red-200">{error}</p>;
  }

  return (
    <div className="space-y-8">
      <section className="flex flex-col gap-5 rounded-3xl border border-cyan-400/20 bg-slate-900/60 p-6 shadow-glow sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.3em] text-cyan-300">Defensive Security</p>
          <h1 className="mt-3 text-3xl font-black tracking-tight text-white sm:text-4xl">Website Security Overview</h1>
          <p className="mt-3 max-w-2xl text-slate-400">
            Run safe, lightweight checks for headers, TLS, redirects, information leakage, open ports, and frontend library hints.
          </p>
        </div>
        <Link to="/scan/new" className="inline-flex items-center justify-center gap-2 rounded-2xl bg-cyan-300 px-5 py-3 font-bold text-slate-950 hover:bg-cyan-200">
          <ShieldPlus size={18} /> Start New Scan
        </Link>
      </section>

      <section className="grid gap-4 md:grid-cols-4">
        <StatCard title="Total scans" value={scans.length} icon={<ListChecks size={22} />} hint="Saved in local SQLite history" />
        <StatCard title="Average risk score" value={averageScore} icon={<BarChart3 size={22} />} hint="Higher is better" />
        <StatCard title="High/Critical findings" value={seriousFindings} icon={<AlertTriangle size={22} />} hint="Based on the 5 most recent reports" />
        <StatCard title="Cookie issues" value={cookieIssues} icon={<Cookie size={22} />} hint="Derived from recent scan reports" />
      </section>

      <section className="card overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-800 px-5 py-4">
          <h2 className="text-lg font-semibold text-white">Recent Scans</h2>
          <Link to="/history" className="text-sm font-medium text-cyan-300 hover:text-cyan-200">View all</Link>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-800">
            <thead className="bg-slate-950/50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="table-cell">Target</th>
                <th className="table-cell">Date</th>
                <th className="table-cell">Score</th>
                <th className="table-cell">Grade</th>
                <th className="table-cell">Findings</th>
                <th className="table-cell">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {scans.slice(0, 6).length === 0 ? (
                <tr><td className="table-cell text-slate-400" colSpan={6}>No scans yet. Start your first scan.</td></tr>
              ) : (
                scans.slice(0, 6).map((scan) => (
                  <tr key={scan.id}>
                    <td className="table-cell max-w-xs truncate font-medium text-white">{scan.target_url}</td>
                    <td className="table-cell text-slate-400">{new Date(scan.scan_date).toLocaleString()}</td>
                    <td className="table-cell text-slate-300">{scan.risk_score}</td>
                    <td className="table-cell font-bold text-cyan-300">{scan.grade}</td>
                    <td className="table-cell text-slate-300">{scan.total_findings}</td>
                    <td className="table-cell"><Link className="text-cyan-300 hover:text-cyan-200" to={`/reports/${scan.id}`}>View report</Link></td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
