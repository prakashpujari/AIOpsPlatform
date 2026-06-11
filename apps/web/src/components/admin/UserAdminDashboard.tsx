"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import { useRBAC } from "@/hooks/useRBAC";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import type { User, Role } from "@/types";
import { clsx } from "clsx";
import { formatDistanceToNow } from "date-fns";

const ROLE_STYLES: Record<Role, string> = {
  admin: "bg-red-900/40 text-red-300 border-red-700/50",
  operator: "bg-blue-900/40 text-blue-300 border-blue-700/50",
  analyst: "bg-purple-900/40 text-purple-300 border-purple-700/50",
  viewer: "bg-slate-700 text-slate-300 border-slate-600",
  compliance: "bg-yellow-900/40 text-yellow-300 border-yellow-700/50",
};

export function UserAdminDashboard() {
  const { can } = useRBAC();
  const [search, setSearch] = useState("");

  const { data: users, isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: () =>
      apiClient.get<User[]>("/api/v1/admin/users").then((r) => r.data),
  });

  const filtered = (users ?? []).filter(
    (u) =>
      u.name.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase())
  );

  if (!can("users", "read")) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-slate-500">You do not have permission to access user administration.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-100">User Administration</h1>
          <p className="text-sm text-slate-400 mt-0.5">{users?.length ?? 0} users</p>
        </div>
        {can("users", "write") && (
          <button className="btn-primary">+ Invite User</button>
        )}
      </div>

      {/* Search */}
      <div className="card">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name or email..."
          className="w-full bg-surface-elevated border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-600"
        />
      </div>

      {/* Table */}
      <div className="card overflow-hidden p-0">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-700/50">
              {["User", "Roles", "Department", "Last Login", "Status", "Actions"].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/30">
            {isLoading ? (
              <tr><td colSpan={6}><LoadingSpinner /></td></tr>
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-12 text-slate-500 text-sm">
                  No users found
                </td>
              </tr>
            ) : (
              filtered.map((user) => (
                <tr key={user.id} className="hover:bg-white/2 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-xs font-semibold text-white flex-shrink-0">
                        {user.name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-slate-200">{user.name}</p>
                        <p className="text-xs text-slate-500">{user.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {user.roles.map((role) => (
                        <span key={role} className={clsx("px-2 py-0.5 rounded-full text-xs border capitalize", ROLE_STYLES[role])}>
                          {role}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-400">{user.department}</td>
                  <td className="px-4 py-3 text-xs text-slate-500">
                    {user.lastLogin
                      ? formatDistanceToNow(new Date(user.lastLogin), { addSuffix: true })
                      : "Never"}
                  </td>
                  <td className="px-4 py-3">
                    <span className={clsx(
                      "px-2 py-0.5 rounded-full text-xs border",
                      user.isActive
                        ? "bg-green-900/40 text-green-300 border-green-700/50"
                        : "bg-slate-700 text-slate-400 border-slate-600"
                    )}>
                      {user.isActive ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {can("users", "write") && (
                      <div className="flex gap-2">
                        <button className="text-xs text-brand-400 hover:text-brand-300">Edit</button>
                        {can("users", "delete") && (
                          <button className="text-xs text-red-400 hover:text-red-300">Deactivate</button>
                        )}
                      </div>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
