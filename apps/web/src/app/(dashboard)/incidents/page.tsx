import type { Metadata } from "next";
import { IncidentDashboard } from "@/components/incidents/IncidentDashboard";

export const metadata: Metadata = { title: "Incidents" };

export default function IncidentsPage() {
  return <IncidentDashboard />;
}
