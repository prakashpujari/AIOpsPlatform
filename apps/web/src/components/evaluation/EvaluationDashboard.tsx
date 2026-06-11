"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import type { EvalResult } from "@/types";
import { clsx } from "clsx";
import { format } from "date-fns";
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar,
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip,
} from "recharts";

const METRIC_THRESHOLDS: Record<string, { pass: number; warn: number }> = {
  faithfulness: { pass: 0.8, warn: 0.6 },
  relevancy: { pass: 0.75, warn: 0.55 },
  groundedness: { pass: 0.8, warn: 0.6 },
  hallucination: { pass: 0.1, warn: 0.2 },
  toxicity: { pass: 0.05, warn: 0.1 },
  bias: { pass: 0.1, warn: 0.2 },
};

function metricColor(metric: string, value: number): string {
  const t = METRIC_THRESHOLDS[metric];
  if (!t) return "text-slate-300";
  const isLower = metric === "hallucination" || metric === "toxicity" || metric === "bias";
  if (isLower) {
    return value <= t.pass ? "text-green-400" : value <= t.warn ? "text-yellow-400" : "text-red-400";
  }
  return value >= t.pass ? "text-green-400" : value >= t.warn ? "text-yellow-400" : "text-red-400";
}

export function EvaluationDashboard() {
  const { data: runs, isLoading } = useQuery({
    queryKey: ["eval-runs"],
    queryFn: () =>
      apiClient.get<EvalResult[]>("/api/v1/evaluation/runs").then((r) => r.data),
  });

  const latest = runs?.[0];

  const radarData = latest
    ? Object.entries(latest.metrics).map(([key, value]) => ({
        metric: key.charAt(0).toUpperCase() + key.slice(1),
        value: key === "hallucination" || key === "toxicity" || key === "bias"
          ? (1 - value) * 100
          : value * 100,
        fullMark: 100,
      }))
    : [];

  return (
    <div className="space-y-6">
      {isLoading ? (
        <LoadingSpinner />
      ) : (
        <>
          {/* Latest run header */}
          {latest && (
            <div className="card flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-100">{latest.runName}</h2>
                <p className="text-sm text-slate-400 mt-0.5">
                  {latest.agentType} · {format(new Date(latest.timestamp), "PPpp")} · {latest.totalSamples} samples
                </p>
              </div>
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <p className="text-2xl font-bold text-slate-100">{(latest.passRate * 100).toFixed(1)}%</p>
                  <p className="text-xs text-slate-400">Pass Rate</p>
                </div>
                <span className={clsx(
                  "px-3 py-1.5 rounded-full text-sm font-semibold",
                  latest.ciGateStatus === "pass"
                    ? "bg-green-900/40 text-green-300 border border-green-700/50"
                    : latest.ciGateStatus === "warn"
                    ? "bg-yellow-900/40 text-yellow-300 border border-yellow-700/50"
                    : "bg-red-900/40 text-red-300 border border-red-700/50"
                )}>
                  CI Gate: {latest.ciGateStatus.toUpperCase()}
                </span>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Radar chart */}
            {latest && (
              <div className="card">
                <h3 className="text-sm font-semibold text-slate-300 mb-4">Quality Radar</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="#334155" />
                    <PolarAngleAxis dataKey="metric" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                    <Radar name="Score" dataKey="value" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.25} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Metric breakdown */}
            {latest && (
              <div className="card">
                <h3 className="text-sm font-semibold text-slate-300 mb-4">Metric Scores</h3>
                <div className="space-y-3">
                  {Object.entries(latest.metrics).map(([key, value]) => {
                    const isLower = key === "hallucination" || key === "toxicity" || key === "bias";
                    const pct = isLower ? (1 - value) * 100 : value * 100;
                    const barColor = pct >= 80 ? "bg-green-500" : pct >= 60 ? "bg-yellow-500" : "bg-red-500";
                    return (
                      <div key={key}>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-slate-300 capitalize">{key}</span>
                          <span className={metricColor(key, value)}>
                            {isLower ? `${(value * 100).toFixed(1)}%` : `${(value * 100).toFixed(1)}%`}
                          </span>
                        </div>
                        <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                          <div className={clsx("h-full rounded-full", barColor)} style={{ width: `${pct}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Run history */}
          <div className="card overflow-hidden p-0">
            <div className="px-4 py-3 border-b border-slate-700/50">
              <h3 className="text-sm font-semibold text-slate-300">Evaluation History</h3>
            </div>
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700/30">
                  {["Run", "Agent", "Date", "Faithfulness", "Relevancy", "Hallucination", "Pass Rate", "CI Gate"].map((h) => (
                    <th key={h} className="px-4 py-2.5 text-left text-xs font-medium text-slate-400 uppercase tracking-wider whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/20">
                {(runs ?? []).map((run) => (
                  <tr key={run.id} className="hover:bg-white/2">
                    <td className="px-4 py-3 text-sm text-slate-200">{run.runName}</td>
                    <td className="px-4 py-3 text-xs text-slate-400 font-mono">{run.agentType}</td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      {format(new Date(run.timestamp), "MMM d, HH:mm")}
                    </td>
                    <td className="px-4 py-3">
                      <span className={metricColor("faithfulness", run.metrics.faithfulness)}>
                        {(run.metrics.faithfulness * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={metricColor("relevancy", run.metrics.relevancy)}>
                        {(run.metrics.relevancy * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={metricColor("hallucination", run.metrics.hallucination)}>
                        {(run.metrics.hallucination * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-200">
                      {(run.passRate * 100).toFixed(1)}%
                    </td>
                    <td className="px-4 py-3">
                      <span className={clsx(
                        "px-2 py-0.5 rounded-full text-xs font-medium",
                        run.ciGateStatus === "pass"
                          ? "bg-green-900/40 text-green-300"
                          : run.ciGateStatus === "warn"
                          ? "bg-yellow-900/40 text-yellow-300"
                          : "bg-red-900/40 text-red-300"
                      )}>
                        {run.ciGateStatus}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
