import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import LoadingSpinner from '../components/LoadingSpinner';
import { api } from '../lib/api';
import type { ScanHistoryItem } from '../types/scan';

export default function ScanHistory() {
  const [scans, setScans] = useState<ScanHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  async function loadScans() {
    try {
      const data = await api.listScans();
      setScans(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load scans.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadScans();
  }, []);

  async function handleDelete(scanId: number) {
    const confirmed = window.confirm('Delete this scan from history?');
    if (!confirmed) return;

    setDeletingId(scanId);
    try {
      await api.deleteScan(scanId);
      setScans((current) => current.filter((scan) => scan.id !== scanId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete scan.');
    } finally {
      setDeletingId(null);
    }
  }

  if (loading) return <LoadingSpinner label="Loading scan history..." />;

  return (
    <div className="space-y-6">
      <section className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-cyan-300">History</p>
          <h1 className="mt-2 text-3xl font-black text-white">Previous Scans</h1>
          <p className="mt-2 text-slate-400">Review, open, or delete previous scan reports.</p>
        </div>
        <Link to="/scan/new" className="rounded-2xl bg-cyan-300 px-5 py-3 text-center font-bold text-slate-950 hover:bg-cyan-200">
          Run new scan
        </Link>
      </section>

      {error && <p className="card p-4 text-red-200">{error}</p>}

      <section className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-800">
            <thead className="bg-slate-950/50 text-left text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="table-cell">Target</th>
                <th className="table-cell">Date</th>
                <th className="table-cell">Risk score</th>
                <th className="table-cell">Grade</th>
                <th className="table-cell">Findings</th>
                <th className="table-cell">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {scans.length === 0 ? (
                <tr><td className="table-cell text-slate-400" colSpan={6}>No saved scans yet.</td></tr>
              ) : (
                scans.map((scan) => (
                  <tr key={scan.id}>
                    <td className="table-cell max-w-xs truncate font-medium text-white">{scan.target_url}</td>
                    <td className="table-cell text-slate-400">{new Date(scan.scan_date).toLocaleString()}</td>
                    <td className="table-cell text-slate-300">{scan.risk_score}</td>
                    <td className="table-cell font-bold text-cyan-300">{scan.grade}</td>
                    <td className="table-cell text-slate-300">{scan.total_findings}</td>
                    <td className="table-cell">
                      <div className="flex flex-wrap gap-2">
                        <Link to={`/reports/${scan.id}`} className="rounded-lg bg-slate-800 px-3 py-2 text-sm text-cyan-300 hover:bg-slate-700">
                          View report
                        </Link>
                        <button
                          onClick={() => handleDelete(scan.id)}
                          disabled={deletingId === scan.id}
                          className="rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-200 hover:bg-red-500/20 disabled:opacity-50"
                        >
                          {deletingId === scan.id ? 'Deleting...' : 'Delete'}
                        </button>
                      </div>
                    </td>
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
