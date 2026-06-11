import type { Metadata } from "next";
import { RCADashboard } from "@/components/rca/RCADashboard";

export const metadata: Metadata = { title: "Root Cause Analysis" };

export default function RCAPage() {
  return <RCADashboard />;
}
