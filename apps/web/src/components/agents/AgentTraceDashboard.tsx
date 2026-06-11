"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { StatusBadge } from "@/components/common/StatusBadge";
import { formatDistanceToNow, formatDuration, intervalToDuration } from "date-fns";
import type { AgentTrace, AgentStep } from "@/types";
import { clsx } from "clsx";

const STEP_TYPE_COLORS: Record<AgentStep["type"], string> = {
  llm_call: "bg-purple-900/40 text-purple-300 border-purple-700/50",
  tool_call: "bg-blue-900/40 text-blue-300 border-blue-700/50",
  decision: "bg-yellow-900/40 text-yellow-300 border-yellow-700/50",
  human_approval: "bg-red-900/40 text-red-300 border-red-700/50",
  memory_read: "bg-cyan-900/40 text-cyan-300 border-cyan-700/50",
  memory_write: "bg-teal-900/40 text-teal-300 border-teal-700/50",
};

export function AgentTraceDashboard() {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const { data: traces, isLoading } = useQuery({
    queryKey: ["agent-traces"],
    queryFn: () =>
      apiClient.get<{ items: AgentTrace[] }>("/api/v1/agents/traces").then((r) => r.data.items),
    refetchInterval: 10_000,
  });

  const selected = traces?.find((t) => t.id === selectedId);

  return (
    <div className="flex gap-6 h-full -m-6 p-6">
      {/* Trace list */}
      <div className="w-80 flex-shrink-0 flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Agent Traces</h2>
        {isLoading ? (
          <LoadingSpinner />
        ) : (
          <div className="space-y-2 overflow-y-auto">
            {(traces ?? []).map((trace) => (
              <button
                key={trace.id}
                onClick={() => setSelectedId(trace.id)}
                className={clsx(
                  "w-full text-left p-3 rounded-xl border transition-all",
                  selectedId === trace.id
                    ? "bg-brand-600/20 border-brand-600/50"
                    : "bg-surface-card border-slate-700/50 hover:border-slate-600"
                )}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold text-slate-200 uppercase">{trace.agentType}</span>
                  <AgentStatusDot status={trace.status} />
                </div>
                <p className="text-xs text-slate-400 truncate">{trace.inputSummary}</p>
                <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                  <span>{trace.steps.length} steps</span>
                  <span>${trace.totalCostUsd.toFixed(4)}</span>
                  <span>{formatDistanceToNow(new Date(trace.startedAt), { addSuffix: true })}</span>
                </div>
                {trace.requiresApproval && !trace.approvedBy && (
                  <div className="mt-2 px-2 py-1 bg-yellow-900/30 border border-yellow-700/50 rounded text-xs text-yellow-300">
                    ⚠ Awaiting approval
                  </div>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Detail */}
      <div className="flex-1 min-w-0">
        {selected ? (
          <TraceDetail trace={selected} />
        ) : (
          <div className="h-full flex items-center justify-center text-slate-500">
            Select a trace to inspect
          </div>
        )}
      </div>
    </div>
  );
}

function AgentStatusDot({ status }: { status: AgentTrace["status"] }) {
  const colors = {
    idle: "bg-slate-500",
    running: "bg-blue-500 animate-pulse",
    completed: "bg-green-500",
    failed: "bg-red-500",
    waiting_approval: "bg-yellow-500 animate-pulse",
  };
  return <span className={clsx("w-2 h-2 rounded-full flex-shrink-0", colors[status])} />;
}

function TraceDetail({ trace }: { trace: AgentTrace }) {
  const [expandedStep, setExpandedStep] = useState<string | null>(null);

  const durationMs = trace.completedAt
    ? new Date(trace.completedAt).getTime() - new Date(trace.startedAt).getTime()
    : Date.now() - new Date(trace.startedAt).getTime();

  return (
    <div className="card space-y-5 h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-lg font-semibold text-slate-100 uppercase">{trace.agentType}</h2>
            <AgentStatusDot status={trace.status} />
            <span className="text-sm text-slate-400 capitalize">{trace.status.replace("_", " ")}</span>
          </div>
          <p className="text-xs font-mono text-slate-500 mt-0.5">{trace.sessionId}</p>
        </div>
        <div className="text-right text-sm">
          <p className="text-slate-300">{trace.modelUsed}</p>
          <p className="text-slate-500">{trace.totalTokens.toLocaleString()} tokens · ${trace.totalCostUsd.toFixed(4)}</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Steps", value: trace.steps.length },
          { label: "Duration", value: `${(durationMs / 1000).toFixed(1)}s` },
          { label: "Tokens", value: trace.totalTokens.toLocaleString() },
          { label: "Cost", value: `$${trace.totalCostUsd.toFixed(4)}` },
        ].map((stat) => (
          <div key={stat.label} className="bg-surface-elevated rounded-lg p-3 border border-slate-700/50">
            <p className="text-xs text-slate-400 mb-1">{stat.label}</p>
            <p className="text-lg font-semibold text-slate-100">{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Approval banner */}
      {trace.requiresApproval && !trace.approvedBy && (
        <div className="flex items-center justify-between p-4 bg-yellow-900/20 border border-yellow-700/50 rounded-xl">
          <div>
            <p className="text-sm font-medium text-yellow-300">Human Approval Required</p>
            <p className="text-xs text-yellow-500 mt-0.5">This action requires operator approval before execution</p>
          </div>
          <div className="flex gap-2">
            <button className="px-3 py-1.5 rounded-lg bg-green-700 hover:bg-green-600 text-white text-sm font-medium transition-colors">
              Approve
            </button>
            <button className="px-3 py-1.5 rounded-lg bg-red-700 hover:bg-red-600 text-white text-sm font-medium transition-colors">
              Reject
            </button>
          </div>
        </div>
      )}

      {/* Steps */}
      <section>
        <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">Execution Steps</h3>
        <div className="space-y-2">
          {trace.steps.map((step) => (
            <div key={step.id} className="border border-slate-700/50 rounded-xl overflow-hidden">
              <button
                onClick={() => setExpandedStep(expandedStep === step.id ? null : step.id)}
                className="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/2 transition-colors text-left"
              >
                <span className="text-xs text-slate-500 w-6 text-right flex-shrink-0">
                  {step.stepNumber}
                </span>
                <span className={clsx(
                  "px-2 py-0.5 rounded-full text-xs border",
                  STEP_TYPE_COLORS[step.type]
                )}>
                  {step.type.replace("_", " ")}
                </span>
                <span className="text-sm text-slate-200 flex-1 truncate">{step.name}</span>
                {step.latencyMs && (
                  <span className="text-xs text-slate-500">{step.latencyMs}ms</span>
                )}
                {step.tokensUsed && (
                  <span className="text-xs text-slate-500">{step.tokensUsed} tok</span>
                )}
                <StepStatusIcon status={step.status} />
              </button>

              {expandedStep === step.id && (
                <div className="border-t border-slate-700/50 p-4 bg-surface-elevated space-y-3">
                  <div>
                    <p className="text-xs text-slate-400 mb-1">Input</p>
                    <pre className="text-xs font-mono text-slate-300 bg-surface rounded p-3 overflow-x-auto">
                      {JSON.stringify(step.input, null, 2)}
                    </pre>
                  </div>
                  {step.output && (
                    <div>
                      <p className="text-xs text-slate-400 mb-1">Output</p>
                      <pre className="text-xs font-mono text-slate-300 bg-surface rounded p-3 overflow-x-auto">
                        {JSON.stringify(step.output, null, 2)}
                      </pre>
                    </div>
                  )}
                  {step.errorMessage && (
                    <div className="p-3 bg-red-900/20 border border-red-700/50 rounded-lg text-sm text-red-300">
                      {step.errorMessage}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function StepStatusIcon({ status }: { status: AgentStep["status"] }) {
  if (status === "completed")
    return <span className="text-green-400 text-sm flex-shrink-0">✓</span>;
  if (status === "failed")
    return <span className="text-red-400 text-sm flex-shrink-0">✗</span>;
  if (status === "running")
    return (
      <svg className="w-3.5 h-3.5 animate-spin text-blue-400 flex-shrink-0" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    );
  return <span className="text-slate-600 text-sm flex-shrink-0">○</span>;
}
