import type { Metadata } from "next";
import { CostDashboard } from "@/components/costs/CostDashboard";

export const metadata: Metadata = { title: "Cost Dashboard" };

export default function CostsPage() {
  return <CostDashboard />;
}
