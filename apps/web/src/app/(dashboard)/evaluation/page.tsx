import type { Metadata } from "next";
import { EvaluationDashboard } from "@/components/evaluation/EvaluationDashboard";

export const metadata: Metadata = { title: "Evaluation" };

export default function EvaluationPage() {
  return <EvaluationDashboard />;
}
