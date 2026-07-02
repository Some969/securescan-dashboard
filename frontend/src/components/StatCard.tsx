import type { ReactNode } from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon?: ReactNode;
  hint?: string;
}

export default function StatCard({ title, value, icon, hint }: StatCardProps) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-slate-400">{title}</p>
          <p className="mt-2 text-3xl font-bold text-white">{value}</p>
          {hint && <p className="mt-2 text-xs text-slate-500">{hint}</p>}
        </div>
        {icon && <div className="rounded-xl bg-slate-800 p-3 text-cyan-300">{icon}</div>}
      </div>
    </div>
  );
}
