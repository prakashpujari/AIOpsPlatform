"use client";

import { useState, useCallback } from "react";
import { chatApi } from "@/lib/api/chat";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import type { SearchResult } from "@/types";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { clsx } from "clsx";

export function KnowledgeSearch() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const { data } = await chatApi.search(query, 5);
      setResult(data);
    } catch {
      setError("Search failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [query]);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-100">Knowledge Search</h1>
        <p className="text-sm text-slate-400 mt-1">
          Hybrid BM25 + semantic search across all ingested documents
        </p>
      </div>

      {/* Search bar */}
      <div className="flex gap-3">
        <div className="flex-1 relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && void handleSearch()}
            placeholder="Search incidents, runbooks, procedures, policies..."
            className="w-full bg-surface-card border border-slate-700 rounded-xl px-4 py-3 pr-10 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-600 focus:ring-1 focus:ring-brand-600/50"
          />
        </div>
        <button
          onClick={() => void handleSearch()}
          disabled={!query.trim() || loading}
          className="btn-primary px-6 flex items-center gap-2"
        >
          {loading ? (
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
            </svg>
          )}
          Search
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-900/20 border border-red-700/50 rounded-xl text-sm text-red-300">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-4 animate-fade-in">
          {/* Answer */}
          <div className="card">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-slate-300">AI-Synthesized Answer</h3>
              <span className="text-xs text-slate-500">{result.queryTime.toFixed(0)}ms</span>
            </div>
            <div className="prose-dark prose prose-sm max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{result.answer}</ReactMarkdown>
            </div>
          </div>

          {/* Sources */}
          <div>
            <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">
              Source Documents ({result.sources.length})
            </h3>
            <div className="space-y-3">
              {result.sources.map((src, i) => (
                <div key={src.id} className="card hover:border-slate-600 transition-colors">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3 min-w-0">
                      <span className="flex-shrink-0 w-6 h-6 rounded-full bg-brand-600/20 text-brand-400 text-xs font-semibold flex items-center justify-center">
                        {i + 1}
                      </span>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-slate-200 truncate">{src.title}</p>
                        <p className="text-xs text-slate-400 mt-1 line-clamp-3">{src.content}</p>
                        <div className="flex flex-wrap gap-2 mt-2">
                          {Object.entries(src.metadata).slice(0, 3).map(([k, v]) => (
                            <span key={k} className="text-xs text-slate-500">
                              <span className="text-slate-600">{k}:</span> {v}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                    <div className="flex-shrink-0 text-right">
                      <span className={clsx(
                        "text-xs font-medium px-2 py-0.5 rounded-full",
                        src.score > 0.8
                          ? "bg-green-900/40 text-green-300"
                          : src.score > 0.6
                          ? "bg-yellow-900/40 text-yellow-300"
                          : "bg-slate-700 text-slate-400"
                      )}>
                        {(src.score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {!result && !loading && (
        <div className="card text-center py-12">
          <p className="text-slate-400 text-sm">
            Search across runbooks, incident reports, SOPs, and knowledge articles
          </p>
          <div className="flex flex-wrap justify-center gap-2 mt-4">
            {[
              "payment service outage playbook",
              "database failover procedure",
              "mortgage origination workflow",
              "kafka consumer lag remediation",
            ].map((example) => (
              <button
                key={example}
                onClick={() => { setQuery(example); void handleSearch(); }}
                className="text-xs px-3 py-1.5 bg-surface-elevated border border-slate-700 rounded-full text-slate-400 hover:text-slate-200 hover:border-slate-600 transition-colors"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
