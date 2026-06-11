"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { incidentsApi } from "@/lib/api/incidents";
import { StatusBadge } from "@/components/common/StatusBadge";
import { MetricCard } from "@/components/common/MetricCard";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { useRBAC } from "@/hooks/useRBAC";
import { formatDistanceToNow } from "date-fns";
import type { Incident, Severity, Status } from "@/types";
import { clsx } from "clsx";

const SEVERITIES: Severity[] = ["critical", "high", "medium", "low", "info"];
const STATUSES: Status[] = ["open", "in_progress", "resolved", "closed"];

export function IncidentDashboard() {
  const { can } = useRBAC();
  const [severity, setSeverity] = useState<string>("");
  const [status, setStatus] = useState<string>("");
  const [search, setSearch] = useState<string>("");
  const [page, setPage] = useState(1);

  const { data: stats } = useQuery({
    queryKey: ["incident-stats"],
    queryFn: () => incidentsApi.getStats().then((r) => r.data),
    refetchInterval: 30_000,
  });

  const { data, isLoading } = useQuery({
    queryKey: ["incidents", { severity, status, search, page }],
    queryFn: () =>
      incidentsApi
        .list({ severity: severity || undefined, status: status || undefined, search: search || undefined, page, size: 20 })
        .then((r) => r.data),
    refetchInterval: 15_000,
  });

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title="Open Incidents" value={stats?.open ?? "—"} color="red"
          icon={<span className="text-lg">🔴</span>} />
        <MetricCard title="Critical" value={stats?.critical ?? "—"} color="red"
          icon={<span className="text-lg">🚨</span>} />
        <MetricCard title="Resolved Today" value={stats?.resolvedToday ?? "—"} color="green"
          icon={<span className="text-lg">✅</span>} />
        <MetricCard title="Avg Resolution" value={stats ? `${stats.avgResolutionHours.toFixed(1)}h` : "—"}
          color="blue" icon={<span className="text-lg">⏱</span>} />
      </div>

      {/* Filters */}
      <div className="card flex flex-wrap items-center gap-3">
        <input
          type="text"
          placeholder="Search incidents..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="flex-1 min-w-48 bg-surface-elevated border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-600"
        />
        <select
          value={severity}
          onChange={(e) => { setSeverity(e.target.value); setPage(1); }}
          className="bg-surface-elevated border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-300 focus:outline-none"
        >
          <option value="">All Severities</option>
          {SEVERITIES.map((s) => <option key={s} value={s} className="capitalize">{s}</option>)}
        </select>
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          className="bg-surface-elevated border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-300 focus:outline-none"
        >
          <option value="">All Statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
        </select>
        {can("incidents", "write") && (
          <button className="btn-primary ml-auto">+ New Incident</button>
        )}
      </div>

      {/* Table */}
      <div className="card overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700/50">
                {["ID", "Title", "Severity", "Status", "Service", "Created", "Actions"].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/30">
              {isLoading ? (
                <tr><td colSpan={7}><LoadingSpinner /></td></tr>
              ) : data?.items.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-slate-500 text-sm">
                    No incidents found
                  </td>
                </tr>
              ) : (
                data?.items.map((incident) => (
                  <IncidentRow key={incident.id} incident={incident} canWrite={can("incidents", "write")} />
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-700/50">
            <span className="text-sm text-slate-400">
              {data.total} incidents · page {page} of {data.pages}
            </span>
            <div className="flex gap-2">
              <button
                disabled={page === 1}
                onClick={() => setPage((p) => p - 1)}
                className="btn-ghost disabled:opacity-40"
              >
                ← Prev
              </button>
              <button
                disabled={page >= data.pages}
                onClick={() => setPage((p) => p + 1)}
                className="btn-ghost disabled:opacity-40"
              >
                Next →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function IncidentRow({ incident, canWrite }: { incident: Incident; canWrite: boolean }) {
  return (
    <tr className="hover:bg-white/2 transition-colors">
      <td className="px-4 py-3 text-xs font-mono text-slate-500">
        {incident.id.slice(0, 8)}
      </td>
      <td className="px-4 py-3 max-w-xs">
        <p className="text-sm text-slate-200 font-medium truncate">{incident.title}</p>
        {incident.externalId && (
          <p className="text-xs text-slate-500 mt-0.5">{incident.externalSystem}: {incident.externalId}</p>
        )}
      </td>
      <td className="px-4 py-3">
        <StatusBadge type="severity" value={incident.severity} />
      </td>
      <td className="px-4 py-3">
        <StatusBadge type="status" value={incident.status} />
      </td>
      <td className="px-4 py-3 text-sm text-slate-400 font-mono">{incident.service}</td>
      <td className="px-4 py-3 text-xs text-slate-500 whitespace-nowrap">
        {formatDistanceToNow(new Date(incident.createdAt), { addSuffix: true })}
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <button className="text-xs text-brand-400 hover:text-brand-300 transition-colors">View</button>
          {canWrite && incident.status === "open" && (
            <button className="text-xs text-green-400 hover:text-green-300 transition-colors">Resolve</button>
          )}
        </div>
      </td>
    </tr>
  );
}
