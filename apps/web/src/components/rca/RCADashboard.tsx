"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { formatDistanceToNow } from "date-fns";
import type { RCA } from "@/types";
import { clsx } from "clsx";

export function RCADashboard() {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { data: rcaList, isLoading } = useQuery({
    queryKey: ["rca-list"],
    queryFn: () =>
      apiClient.get<{ items: RCA[] }>("/api/v1/rca").then((r) => r.data.items),
  });

  const selectedRCA = rcaList?.find((r) => r.id === selectedId);

  return (
    <div className="flex gap-6 h-full -m-6 p-6">
      {/* List */}
      <div className="w-80 flex-shrink-0 flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
          RCA Reports
        </h2>
        {isLoading ? (
          <LoadingSpinner />
        ) : (
          <div className="space-y-2 overflow-y-auto">
            {(rcaList ?? []).map((rca) => (
              <button
                key={rca.id}
                onClick={() => setSelectedId(rca.id)}
                className={clsx(
                  "w-full text-left p-3 rounded-xl border transition-all",
                  selectedId === rca.id
                    ? "bg-brand-600/20 border-brand-600/50 text-slate-100"
                    : "bg-surface-card border-slate-700/50 text-slate-400 hover:border-slate-600"
                )}
              >
                <p className="text-sm font-medium truncate">Incident {rca.incidentId.slice(0, 8)}</p>
                <p className="text-xs mt-1 truncate">{rca.rootCause.slice(0, 60)}...</p>
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-xs text-slate-500">
                    {formatDistanceToNow(new Date(rca.generatedAt), { addSuffix: true })}
                  </span>
                  <span className={clsx(
                    "text-xs px-1.5 py-0.5 rounded-full",
                    rca.confidence > 0.8 ? "bg-green-900/40 text-green-400" : "bg-yellow-900/40 text-yellow-400"
                  )}>
                    {(rca.confidence * 100).toFixed(0)}% confidence
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Detail */}
      <div className="flex-1 min-w-0">
        {selectedRCA ? (
          <RCADetail rca={selectedRCA} />
        ) : (
          <div className="h-full flex items-center justify-center text-slate-500">
            Select an RCA report to view details
          </div>
        )}
      </div>
    </div>
  );
}

function RCADetail({ rca }: { rca: RCA }) {
  return (
    <div className="card space-y-6 h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-100">
            Root Cause Analysis
          </h2>
          <p className="text-sm text-slate-400 mt-0.5">
            Incident {rca.incidentId} ·{" "}
            {formatDistanceToNow(new Date(rca.generatedAt), { addSuffix: true })}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className={clsx(
            "px-3 py-1 rounded-full text-sm font-medium",
            rca.confidence > 0.8
              ? "bg-green-900/40 text-green-300 border border-green-700/50"
              : "bg-yellow-900/40 text-yellow-300 border border-yellow-700/50"
          )}>
            {(rca.confidence * 100).toFixed(0)}% confidence
          </span>
          {rca.approvedBy && (
            <span className="px-3 py-1 rounded-full text-sm bg-brand-900/40 text-brand-300 border border-brand-700/50">
              ✓ Approved
            </span>
          )}
        </div>
      </div>

      {/* Root cause */}
      <section>
        <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">Root Cause</h3>
        <div className="p-4 bg-red-900/10 border border-red-700/30 rounded-xl">
          <p className="text-sm text-slate-200">{rca.rootCause}</p>
        </div>
      </section>

      {/* Contributing factors */}
      <section>
        <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
          Contributing Factors
        </h3>
        <ul className="space-y-2">
          {rca.contributingFactors.map((factor, i) => (
            <li key={i} className="flex gap-2 text-sm text-slate-300">
              <span className="text-slate-500 flex-shrink-0 mt-0.5">•</span>
              {factor}
            </li>
          ))}
        </ul>
      </section>

      {/* Suggested fix */}
      <section>
        <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">Suggested Fix</h3>
        <div className="p-4 bg-green-900/10 border border-green-700/30 rounded-xl">
          <p className="text-sm text-slate-200">{rca.suggestedFix}</p>
        </div>
      </section>

      {/* Timeline */}
      <section>
        <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">Event Timeline</h3>
        <div className="relative pl-6">
          <div className="absolute left-2 top-0 bottom-0 w-px bg-slate-700" />
          {rca.timeline.map((node, i) => (
            <div key={i} className="relative mb-4 last:mb-0">
              <div className={clsx(
                "absolute -left-4 top-1 w-3 h-3 rounded-full border-2",
                node.isRootCause
                  ? "bg-red-500 border-red-400"
                  : "bg-slate-600 border-slate-500"
              )} />
              <div className="bg-surface-elevated rounded-lg p-3 border border-slate-700/50">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-mono text-slate-500">
                    {new Date(node.timestamp).toLocaleTimeString()}
                  </span>
                  <span className="text-xs text-slate-500">{node.service}</span>
                </div>
                <p className="text-sm text-slate-200">{node.event}</p>
                {node.isRootCause && (
                  <span className="inline-block mt-1.5 px-2 py-0.5 text-xs bg-red-900/40 text-red-300 rounded-full border border-red-700/50">
                    Root Cause
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Affected services */}
      <section>
        <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">Affected Services</h3>
        <div className="flex flex-wrap gap-2">
          {rca.affectedServices.map((svc) => (
            <span key={svc} className="px-2.5 py-1 bg-surface-elevated rounded-lg text-sm text-slate-300 border border-slate-700/50 font-mono">
              {svc}
            </span>
          ))}
        </div>
      </section>
    </div>
  );
}
