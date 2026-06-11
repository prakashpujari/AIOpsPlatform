"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { StatusBadge } from "@/components/common/StatusBadge";
import { MetricCard } from "@/components/common/MetricCard";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import type { ServiceHealth, HealthStatus } from "@/types";
import { clsx } from "clsx";
import { formatDistanceToNow } from "date-fns";

function HealthBar({ value, max = 100, color }: { value: number; max?: number; color: string }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div className={clsx("h-full rounded-full transition-all", color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-400 w-10 text-right">{value.toFixed(1)}%</span>
    </div>
  );
}

export function ServiceHealthDashboard() {
  const { data: services, isLoading } = useQuery({
    queryKey: ["service-health"],
    queryFn: () =>
      apiClient.get<ServiceHealth[]>("/api/v1/health/services").then((r) => r.data),
    refetchInterval: 15_000,
  });

  const healthy = services?.filter((s) => s.status === "healthy").length ?? 0;
  const degraded = services?.filter((s) => s.status === "degraded").length ?? 0;
  const unhealthy = services?.filter((s) => s.status === "unhealthy").length ?? 0;

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        <MetricCard title="Healthy" value={healthy} color="green"
          subtitle={`of ${services?.length ?? 0} services`} />
        <MetricCard title="Degraded" value={degraded} color="yellow" />
        <MetricCard title="Unhealthy" value={unhealthy} color="red" />
      </div>

      {/* Service grid */}
      {isLoading ? (
        <LoadingSpinner />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          {(services ?? []).map((svc) => (
            <ServiceCard key={svc.id} service={svc} />
          ))}
        </div>
      )}
    </div>
  );
}

function ServiceCard({ service }: { service: ServiceHealth }) {
  const cpuColor = service.cpu > 85 ? "bg-red-500" : service.cpu > 70 ? "bg-yellow-500" : "bg-green-500";
  const memColor = service.memory > 85 ? "bg-red-500" : service.memory > 70 ? "bg-yellow-500" : "bg-green-500";

  return (
    <div className="card space-y-3">
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-slate-200 font-mono truncate">{service.name}</p>
          <p className="text-xs text-slate-500">{service.namespace}</p>
        </div>
        <StatusBadge type="health" value={service.status} />
      </div>

      {/* Replicas */}
      <div className="flex items-center gap-2">
        <div className="flex gap-1">
          {Array.from({ length: service.replicas.desired }).map((_, i) => (
            <div
              key={i}
              className={clsx(
                "w-3 h-3 rounded-full",
                i < service.replicas.ready ? "bg-green-500" : "bg-slate-600"
              )}
            />
          ))}
        </div>
        <span className="text-xs text-slate-500">
          {service.replicas.ready}/{service.replicas.desired} replicas
        </span>
      </div>

      {/* Metrics */}
      <div className="space-y-2">
        <div>
          <div className="flex justify-between text-xs text-slate-500 mb-1">
            <span>CPU</span>
          </div>
          <HealthBar value={service.cpu} color={cpuColor} />
        </div>
        <div>
          <div className="flex justify-between text-xs text-slate-500 mb-1">
            <span>Memory</span>
          </div>
          <HealthBar value={service.memory} color={memColor} />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 pt-1 border-t border-slate-700/50">
        <div className="text-center">
          <p className={clsx("text-sm font-semibold", service.errorRate > 1 ? "text-red-400" : "text-green-400")}>
            {service.errorRate.toFixed(2)}%
          </p>
          <p className="text-xs text-slate-500">Error Rate</p>
        </div>
        <div className="text-center">
          <p className={clsx("text-sm font-semibold", service.p95LatencyMs > 2000 ? "text-red-400" : service.p95LatencyMs > 1000 ? "text-yellow-400" : "text-slate-200")}>
            {service.p95LatencyMs}ms
          </p>
          <p className="text-xs text-slate-500">P95</p>
        </div>
        <div className="text-center">
          <p className={clsx("text-sm font-semibold", service.alerts > 0 ? "text-red-400" : "text-slate-400")}>
            {service.alerts}
          </p>
          <p className="text-xs text-slate-500">Alerts</p>
        </div>
      </div>

      <p className="text-xs text-slate-600">
        Updated {formatDistanceToNow(new Date(service.lastChecked), { addSuffix: true })}
      </p>
    </div>
  );
}
