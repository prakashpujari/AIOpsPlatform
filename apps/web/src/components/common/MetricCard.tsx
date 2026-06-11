import { clsx } from "clsx";

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: { value: number; label: string };
  icon?: React.ReactNode;
  color?: "blue" | "green" | "red" | "yellow" | "purple";
  className?: string;
}

const COLOR_STYLES = {
  blue: "text-blue-400 bg-blue-900/20 border-blue-700/30",
  green: "text-green-400 bg-green-900/20 border-green-700/30",
  red: "text-red-400 bg-red-900/20 border-red-700/30",
  yellow: "text-yellow-400 bg-yellow-900/20 border-yellow-700/30",
  purple: "text-purple-400 bg-purple-900/20 border-purple-700/30",
};

export function MetricCard({
  title, value, subtitle, trend, icon, color = "blue", className,
}: MetricCardProps) {
  return (
    <div className={clsx("metric-card", className)}>
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider truncate">
            {title}
          </p>
          <p className="text-2xl font-bold text-slate-100 mt-1">{value}</p>
          {subtitle && (
            <p className="text-xs text-slate-500 mt-0.5 truncate">{subtitle}</p>
          )}
        </div>
        {icon && (
          <div className={clsx("p-2 rounded-lg border", COLOR_STYLES[color])}>
            {icon}
          </div>
        )}
      </div>
      {trend && (
        <div className="flex items-center gap-1 mt-2">
          <span
            className={clsx(
              "text-xs font-medium",
              trend.value >= 0 ? "text-green-400" : "text-red-400"
            )}
          >
            {trend.value >= 0 ? "↑" : "↓"} {Math.abs(trend.value)}%
          </span>
          <span className="text-xs text-slate-500">{trend.label}</span>
        </div>
      )}
    </div>
  );
}
