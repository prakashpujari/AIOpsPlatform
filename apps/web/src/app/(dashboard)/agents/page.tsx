import type { Metadata } from "next";
import { AgentTraceDashboard } from "@/components/agents/AgentTraceDashboard";

export const metadata: Metadata = { title: "Agent Traces" };

export default function AgentsPage() {
  return <AgentTraceDashboard />;
}
