interface LoadingSpinnerProps {
  label?: string;
}

export default function LoadingSpinner({ label = 'Loading...' }: LoadingSpinnerProps) {
  return (
    <div className="flex items-center gap-3 text-sm text-slate-300">
      <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-600 border-t-cyan-300" />
      <span>{label}</span>
    </div>
  );
}
