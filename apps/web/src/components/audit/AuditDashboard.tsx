"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { useRBAC } from "@/hooks/useRBAC";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import type { AuditLog, PaginatedResponse } from "@/types";
import { clsx } from "clsx";
import { format } from "date-fns";

export function AuditDashboard() {
  const { can } = useRBAC();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["audit-logs", { search, page, status }],
    queryFn: () =>
      apiClient
        .get<PaginatedResponse<AuditLog>>("/api/v1/audit", {
          params: { search: search || undefined, page, size: 25, status: status || undefined },
        })
        .then((r) => r.data),
    refetchInterval: 30_000,
  });

  if (!can("audit", "read")) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-slate-500">You do not have permission to view audit logs.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-100">Audit Log</h1>
        <p className="text-sm text-slate-400 mt-0.5">
          All platform actions are immutably logged for compliance
        </p>
      </div>

      {/* Filters */}
      <div className="card flex flex-wrap gap-3">
        <input
          type="text"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          placeholder="Filter by user, action, or resource..."
          className="flex-1 min-w-48 bg-surface-elevated border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-600"
        />
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          className="bg-surface-elevated border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-300 focus:outline-none"
        >
          <option value="">All Statuses</option>
          <option value="success">Success</option>
          <option value="failure">Failure</option>
        </select>
        <button className="btn-ghost text-sm">Export CSV</button>
      </div>

      {/* Table */}
      <div className="card overflow-hidden p-0">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-700/50">
              {["Timestamp", "User", "Action", "Resource", "Status", "IP"].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/20">
            {isLoading ? (
              <tr><td colSpan={6}><LoadingSpinner /></td></tr>
            ) : data?.items.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-12 text-slate-500 text-sm">
                  No audit logs found
                </td>
              </tr>
            ) : (
              data?.items.map((log) => (
                <tr key={log.id} className="hover:bg-white/2 transition-colors font-mono text-xs">
                  <td className="px-4 py-2.5 text-slate-500 whitespace-nowrap">
                    {format(new Date(log.timestamp), "yyyy-MM-dd HH:mm:ss")}
                  </td>
                  <td className="px-4 py-2.5">
                    <p className="text-slate-300">{log.userName}</p>
                    <p className="text-slate-600 text-[10px]">{log.userId.slice(0, 12)}</p>
                  </td>
                  <td className="px-4 py-2.5 text-slate-300">{log.action}</td>
                  <td className="px-4 py-2.5">
                    <span className="text-slate-400">{log.resource}</span>
                    <span className="text-slate-600">/{log.resourceId.slice(0, 8)}</span>
                  </td>
                  <td className="px-4 py-2.5">
                    <span className={clsx(
                      "px-1.5 py-0.5 rounded text-[10px] border",
                      log.status === "success"
                        ? "bg-green-900/30 text-green-400 border-green-700/40"
                        : "bg-red-900/30 text-red-400 border-red-700/40"
                    )}>
                      {log.status}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-slate-500">{log.ipAddress}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {data && data.pages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-700/50">
            <span className="text-xs text-slate-400">
              {data.total.toLocaleString()} events · page {page} of {data.pages}
            </span>
            <div className="flex gap-2">
              <button disabled={page === 1} onClick={() => setPage((p) => p - 1)} className="btn-ghost disabled:opacity-40 text-xs">← Prev</button>
              <button disabled={page >= data.pages} onClick={() => setPage((p) => p + 1)} className="btn-ghost disabled:opacity-40 text-xs">Next →</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
