import type { OpenPort } from '../types/scan';

interface OpenPortsTableProps {
  openPorts?: OpenPort[];
  command?: string;
  error?: string | null;
  nmapAvailable?: boolean;
}

export default function OpenPortsTable({ openPorts = [], command, error, nmapAvailable }: OpenPortsTableProps) {
  return (
    <section className="card p-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Open Ports</h2>
          <p className="text-sm text-slate-400">Uses lightweight Nmap top-ports scanning only.</p>
        </div>
        {command && <code className="rounded-lg bg-slate-950 px-3 py-2 text-xs text-cyan-200">{command}</code>}
      </div>

      {nmapAvailable === false && (
        <p className="mt-4 rounded-xl border border-yellow-400/30 bg-yellow-500/10 p-3 text-sm text-yellow-100">
          Nmap is not installed. Install Nmap to enable open port checks.
        </p>
      )}
      {error && <p className="mt-4 rounded-xl border border-red-400/30 bg-red-500/10 p-3 text-sm text-red-200">{error}</p>}

      <div className="mt-5 overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-800">
          <thead className="text-left text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="table-cell">Port</th>
              <th className="table-cell">Protocol</th>
              <th className="table-cell">State</th>
              <th className="table-cell">Service</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {openPorts.length === 0 ? (
              <tr><td className="table-cell text-slate-400" colSpan={4}>No open ports reported by this check.</td></tr>
            ) : (
              openPorts.map((port) => (
                <tr key={`${port.port}-${port.protocol}`}>
                  <td className="table-cell font-semibold text-white">{port.port}</td>
                  <td className="table-cell text-slate-300">{port.protocol}</td>
                  <td className="table-cell text-slate-300">{port.state}</td>
                  <td className="table-cell text-slate-300">{port.service}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
