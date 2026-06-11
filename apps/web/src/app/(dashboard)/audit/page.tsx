import type { Metadata } from "next";
import { AuditDashboard } from "@/components/audit/AuditDashboard";

export const metadata: Metadata = { title: "Audit Log" };

export default function AuditPage() {
  return <AuditDashboard />;
}
