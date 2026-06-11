import { clsx } from "clsx";
import type { Severity, Status, HealthStatus } from "@/types";

const SEVERITY_STYLES: Record<Severity, string> = {
  critical: "badge-critical",
  high: "badge-high",
  medium: "badge-medium",
  low: "badge-low",
  info: "badge-info",
};

const STATUS_STYLES: Record<Status, string> = {
  open: "bg-red-900/40 text-red-300 border border-red-700/50",
  in_progress: "bg-yellow-900/40 text-yellow-300 border border-yellow-700/50",
  resolved: "bg-green-900/40 text-green-300 border border-green-700/50",
  closed: "bg-slate-800 text-slate-400 border border-slate-700",
};

const HEALTH_STYLES: Record<HealthStatus, string> = {
  healthy: "bg-green-900/40 text-green-300 border border-green-700/50",
  degraded: "bg-yellow-900/40 text-yellow-300 border border-yellow-700/50",
  unhealthy: "bg-red-900/40 text-red-300 border border-red-700/50",
  unknown: "bg-slate-800 text-slate-400 border border-slate-700",
};

interface Props {
  type: "severity" | "status" | "health";
  value: Severity | Status | HealthStatus;
  className?: string;
}

export function StatusBadge({ type, value, className }: Props) {
  const styles =
    type === "severity"
      ? SEVERITY_STYLES[value as Severity]
      : type === "status"
      ? STATUS_STYLES[value as Status]
      : HEALTH_STYLES[value as HealthStatus];

  return (
    <span
      className={clsx(
        "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium capitalize",
        styles,
        className
      )}
    >
      {value.replace("_", " ")}
    </span>
  );
}
