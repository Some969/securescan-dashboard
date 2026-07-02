import { Link, NavLink } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/scan/new', label: 'New Scan' },
  { to: '/history', label: 'History' },
];

export default function Navbar() {
  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur">
      <nav className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-3">
          <div className="rounded-xl border border-cyan-400/30 bg-cyan-400/10 p-2 text-cyan-300">
            <ShieldCheck size={24} />
          </div>
          <div>
            <p className="text-lg font-bold tracking-tight text-white">SecureScan Dashboard</p>
            <p className="text-xs text-slate-400">Defensive website security checks</p>
          </div>
        </Link>

        <div className="flex flex-wrap gap-2">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `rounded-xl px-4 py-2 text-sm font-medium transition ${
                  isActive
                    ? 'bg-cyan-400 text-slate-950'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </div>
      </nav>
    </header>
  );
}
