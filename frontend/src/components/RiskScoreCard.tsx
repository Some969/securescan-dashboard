interface RiskScoreCardProps {
  score: number;
  grade: string;
}

function scoreTone(score: number) {
  if (score >= 85) return 'text-emerald-300 border-emerald-400/40 bg-emerald-400/10';
  if (score >= 70) return 'text-cyan-300 border-cyan-400/40 bg-cyan-400/10';
  if (score >= 55) return 'text-yellow-300 border-yellow-400/40 bg-yellow-400/10';
  if (score >= 40) return 'text-orange-300 border-orange-400/40 bg-orange-400/10';
  return 'text-red-300 border-red-400/40 bg-red-400/10';
}

export default function RiskScoreCard({ score, grade }: RiskScoreCardProps) {
  const tone = scoreTone(score);

  return (
    <div className="card p-6">
      <p className="text-sm text-slate-400">Risk Score</p>
      <div className="mt-4 flex items-end justify-between gap-4">
        <div>
          <p className="text-5xl font-extrabold text-white">{score}</p>
          <p className="mt-2 text-sm text-slate-400">Out of 100</p>
        </div>
        <div className={`rounded-2xl border px-5 py-3 text-center ${tone}`}>
          <p className="text-xs uppercase tracking-[0.2em]">Grade</p>
          <p className="text-3xl font-black">{grade}</p>
        </div>
      </div>
      <div className="mt-6 h-3 overflow-hidden rounded-full bg-slate-800">
        <div className="h-full rounded-full bg-cyan-300" style={{ width: `${score}%` }} />
      </div>
    </div>
  );
}
