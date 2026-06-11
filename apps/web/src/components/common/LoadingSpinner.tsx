import { clsx } from "clsx";

export function LoadingSpinner({ className }: { className?: string }) {
  return (
    <div className={clsx("flex items-center justify-center p-8", className)}>
      <svg className="w-8 h-8 animate-spin text-brand-500" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>
  );
}

export function PageLoader() {
  return (
    <div className="flex-1 flex items-center justify-center">
      <LoadingSpinner />
    </div>
  );
}
