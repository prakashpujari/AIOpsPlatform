"use client";

import { useSession, signOut } from "next-auth/react";
import { usePathname } from "next/navigation";
import { useRBAC } from "@/hooks/useRBAC";
import { useState } from "react";
import { clsx } from "clsx";

const PAGE_TITLES: Record<string, string> = {
  "/chat": "AI Chat",
  "/incidents": "Incident Dashboard",
  "/rca": "Root Cause Analysis",
  "/agents": "Agent Trace Viewer",
  "/search": "Knowledge Search",
  "/health": "Service Health",
  "/costs": "Cost Dashboard",
  "/evaluation": "Evaluation",
  "/admin": "User Administration",
  "/audit": "Audit Log",
};

function BellIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
    </svg>
  );
}

export function Header() {
  const { data: session } = useSession();
  const pathname = usePathname();
  const { roles } = useRBAC();
  const [menuOpen, setMenuOpen] = useState(false);

  const title = Object.entries(PAGE_TITLES).find(([key]) =>
    pathname.startsWith(key)
  )?.[1] ?? "Dashboard";

  const initials = session?.user?.name
    ?.split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2) ?? "??";

  return (
    <header className="h-16 flex items-center justify-between px-6 border-b border-slate-700/50 bg-surface-card flex-shrink-0">
      <h1 className="text-lg font-semibold text-slate-100">{title}</h1>

      <div className="flex items-center gap-3">
        {/* Role badges */}
        <div className="hidden md:flex items-center gap-1.5">
          {roles.slice(0, 2).map((role) => (
            <span
              key={role}
              className="px-2 py-0.5 rounded-full text-xs font-medium bg-brand-600/20 text-brand-300 border border-brand-600/30 capitalize"
            >
              {role}
            </span>
          ))}
        </div>

        {/* Notifications */}
        <button className="relative p-2 rounded-lg hover:bg-white/5 text-slate-400 hover:text-slate-100 transition-colors">
          <BellIcon />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
        </button>

        {/* User menu */}
        <div className="relative">
          <button
            onClick={() => setMenuOpen((o) => !o)}
            className="flex items-center gap-2.5 p-1.5 rounded-lg hover:bg-white/5 transition-colors"
          >
            <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-xs font-semibold text-white">
              {initials}
            </div>
            <div className="hidden md:block text-left">
              <p className="text-sm font-medium text-slate-100 leading-none">
                {session?.user?.name ?? "User"}
              </p>
              <p className="text-xs text-slate-400 mt-0.5 leading-none">
                {session?.user?.email ?? ""}
              </p>
            </div>
          </button>

          {menuOpen && (
            <div className="absolute right-0 top-full mt-2 w-48 bg-surface-card border border-slate-700 rounded-xl shadow-xl z-50 overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-700">
                <p className="text-xs text-slate-400">Signed in as</p>
                <p className="text-sm font-medium text-slate-100 truncate">
                  {session?.user?.email}
                </p>
              </div>
              <button
                onClick={() => signOut({ callbackUrl: "/login" })}
                className="w-full text-left px-4 py-2.5 text-sm text-red-400 hover:bg-red-900/20 transition-colors"
              >
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
