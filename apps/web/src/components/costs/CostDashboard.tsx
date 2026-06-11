"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { MetricCard } from "@/components/common/MetricCard";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import type { CostSummary } from "@/types";
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from "recharts";
import { format } from "date-fns";

const COLORS = ["#3b82f6", "#8b5cf6", "#22c55e", "#f59e0b", "#ef4444"];

export function CostDashboard() {
  const { data: summary, isLoading } = useQuery({
    queryKey: ["cost-summary"],
    queryFn: () =>
      apiClient.get<CostSummary>("/api/v1/costs/summary").then((r) => r.data),
  });

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard title="Total Cost (30d)" value={`$${(summary?.totalCostUsd ?? 0).toFixed(2)}`} color="blue" />
        <MetricCard title="Daily Average" value={`$${(summary?.dailyAvgUsd ?? 0).toFixed(2)}`} color="purple" />
        <MetricCard title="Top Model" value={summary?.topModels[0]?.model ?? "—"} subtitle={`$${(summary?.topModels[0]?.costUsd ?? 0).toFixed(2)}`} color="green" />
        <MetricCard title="Top Agent" value={summary?.topAgents[0]?.agent ?? "—"} subtitle={`$${(summary?.topAgents[0]?.costUsd ?? 0).toFixed(2)}`} color="yellow" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cost trend */}
        <div className="card lg:col-span-2">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Daily Cost Trend</h3>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={summary?.trend ?? []}>
              <defs>
                <linearGradient id="costGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 11 }}
                tickFormatter={(v: string) => format(new Date(v), "MMM d")} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }}
                tickFormatter={(v: number) => `$${v.toFixed(2)}`} />
              <Tooltip
                contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                labelStyle={{ color: "#f1f5f9" }}
                formatter={(v: number) => [`$${v.toFixed(4)}`, "Cost"]}
              />
              <Area type="monotone" dataKey="costUsd" stroke="#3b82f6" fill="url(#costGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* By model */}
        <div className="card">
          <h3 className="text-sm font-semibold text-slate-300 mb-4">Cost by Model</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={summary?.topModels ?? []}
                dataKey="costUsd"
                nameKey="model"
                cx="50%" cy="50%"
                innerRadius={50}
                outerRadius={80}
                paddingAngle={3}
              >
                {(summary?.topModels ?? []).map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                formatter={(v: number) => [`$${v.toFixed(4)}`, "Cost"]}
              />
              <Legend formatter={(v: string) => <span className="text-xs text-slate-400">{v}</span>} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* By agent */}
      <div className="card">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">Cost by Agent</h3>
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={summary?.topAgents ?? []} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
            <XAxis type="number" tick={{ fill: "#94a3b8", fontSize: 11 }}
              tickFormatter={(v: number) => `$${v.toFixed(2)}`} />
            <YAxis type="category" dataKey="agent" tick={{ fill: "#94a3b8", fontSize: 11 }} width={120} />
            <Tooltip
              contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
              formatter={(v: number) => [`$${v.toFixed(4)}`, "Cost"]}
            />
            <Bar dataKey="costUsd" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
