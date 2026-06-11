// ─────────────────────────────────────────────
// Core domain types for the AI Platform UI
// ─────────────────────────────────────────────

export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type Status = "open" | "in_progress" | "resolved" | "closed";
export type HealthStatus = "healthy" | "degraded" | "unhealthy" | "unknown";
export type AgentStatus = "idle" | "running" | "completed" | "failed" | "waiting_approval";
export type Role = "admin" | "operator" | "analyst" | "viewer" | "compliance";

// ── Pagination ─────────────────────────────
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface PaginationParams {
  page?: number;
  size?: number;
  sort?: string;
  order?: "asc" | "desc";
}

// ── Incident ───────────────────────────────
export interface Incident {
  id: string;
  title: string;
  description: string;
  severity: Severity;
  status: Status;
  service: string;
  environment: string;
  assignee?: string;
  tags: string[];
  createdAt: string;
  updatedAt: string;
  resolvedAt?: string;
  externalId?: string;       // ServiceNow / Jira ID
  externalSystem?: "servicenow" | "jira";
  rcaId?: string;
  evidence: Evidence[];
  timeline: TimelineEvent[];
}

export interface Evidence {
  id: string;
  type: "log" | "metric" | "trace" | "screenshot";
  content: string;
  timestamp: string;
  source: string;
}

export interface TimelineEvent {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  details?: string;
}

// ── RCA ────────────────────────────────────
export interface RCA {
  id: string;
  incidentId: string;
  rootCause: string;
  contributingFactors: string[];
  timeline: RCATimelineNode[];
  affectedServices: string[];
  suggestedFix: string;
  confidence: number;
  generatedAt: string;
  approvedBy?: string;
  approvedAt?: string;
}

export interface RCATimelineNode {
  timestamp: string;
  event: string;
  service: string;
  severity: Severity;
  isRootCause: boolean;
}

// ── Agent ──────────────────────────────────
export interface AgentTrace {
  id: string;
  agentType: string;
  sessionId: string;
  status: AgentStatus;
  startedAt: string;
  completedAt?: string;
  steps: AgentStep[];
  totalTokens: number;
  totalCostUsd: number;
  modelUsed: string;
  inputSummary: string;
  outputSummary?: string;
  errorMessage?: string;
  requiresApproval: boolean;
  approvedBy?: string;
}

export interface AgentStep {
  id: string;
  stepNumber: number;
  name: string;
  type: "llm_call" | "tool_call" | "decision" | "human_approval" | "memory_read" | "memory_write";
  status: "pending" | "running" | "completed" | "failed";
  input: Record<string, unknown>;
  output?: Record<string, unknown>;
  tokensUsed?: number;
  latencyMs?: number;
  startedAt: string;
  completedAt?: string;
  errorMessage?: string;
}

// ── Chat ───────────────────────────────────
export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  agentTraceId?: string;
  sources?: KnowledgeSource[];
  isStreaming?: boolean;
  metadata?: {
    model?: string;
    tokensUsed?: number;
    latencyMs?: number;
    confidence?: number;
  };
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: string;
  updatedAt: string;
}

// ── Knowledge / Search ─────────────────────
export interface KnowledgeSource {
  id: string;
  title: string;
  content: string;
  score: number;
  documentId: string;
  chunkIndex: number;
  metadata: Record<string, string>;
}

export interface SearchResult {
  sources: KnowledgeSource[];
  answer: string;
  queryTime: number;
  rerankScore?: number;
}

// ── Service Health ─────────────────────────
export interface ServiceHealth {
  id: string;
  name: string;
  namespace: string;
  status: HealthStatus;
  replicas: { ready: number; desired: number };
  cpu: number;
  memory: number;
  errorRate: number;
  p95LatencyMs: number;
  lastChecked: string;
  alerts: number;
}

// ── Cost ───────────────────────────────────
export interface CostRecord {
  date: string;
  model: string;
  agent: string;
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  costUsd: number;
}

export interface CostSummary {
  totalCostUsd: number;
  dailyAvgUsd: number;
  topModels: Array<{ model: string; costUsd: number }>;
  topAgents: Array<{ agent: string; costUsd: number }>;
  trend: Array<{ date: string; costUsd: number }>;
}

// ── Evaluation ─────────────────────────────
export interface EvalResult {
  id: string;
  runName: string;
  agentType: string;
  timestamp: string;
  metrics: {
    faithfulness: number;
    relevancy: number;
    groundedness: number;
    hallucination: number;
    toxicity: number;
    bias: number;
  };
  totalSamples: number;
  passRate: number;
  ciGateStatus: "pass" | "fail" | "warn";
}

// ── User / RBAC ────────────────────────────
export interface User {
  id: string;
  email: string;
  name: string;
  roles: Role[];
  department: string;
  lastLogin?: string;
  isActive: boolean;
  createdAt: string;
}

export interface Permission {
  resource: string;
  actions: ("read" | "write" | "delete" | "approve")[];
}

// ── Audit ──────────────────────────────────
export interface AuditLog {
  id: string;
  timestamp: string;
  userId: string;
  userName: string;
  action: string;
  resource: string;
  resourceId: string;
  ipAddress: string;
  userAgent: string;
  status: "success" | "failure";
  details?: Record<string, unknown>;
}
