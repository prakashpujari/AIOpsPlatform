import type { Metadata } from "next";
import { ServiceHealthDashboard } from "@/components/health/ServiceHealthDashboard";

export const metadata: Metadata = { title: "Service Health" };

export default function HealthPage() {
  return <ServiceHealthDashboard />;
}
