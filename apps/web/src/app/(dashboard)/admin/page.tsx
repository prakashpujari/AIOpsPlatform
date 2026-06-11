import type { Metadata } from "next";
import { UserAdminDashboard } from "@/components/admin/UserAdminDashboard";

export const metadata: Metadata = { title: "User Administration" };

export default function AdminPage() {
  return <UserAdminDashboard />;
}
