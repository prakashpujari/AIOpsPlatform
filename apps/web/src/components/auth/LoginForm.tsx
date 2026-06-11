"use client";

import { signIn } from "next-auth/react";
import { useState } from "react";
import toast from "react-hot-toast";

export function LoginForm() {
  const [loading, setLoading] = useState(false);

  async function handleKeycloakLogin() {
    setLoading(true);
    try {
      await signIn("keycloak", { callbackUrl: "/chat" });
    } catch {
      toast.error("Login failed. Please try again.");
      setLoading(false);
    }
  }

  return (
    <div className="card space-y-4">
      <div className="space-y-1">
        <h2 className="text-lg font-semibold text-slate-100">Sign in to your account</h2>
        <p className="text-sm text-slate-400">
          Use your enterprise SSO credentials
        </p>
      </div>

      <button
        onClick={handleKeycloakLogin}
        disabled={loading}
        className="w-full flex items-center justify-center gap-3 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-3 px-4 rounded-lg transition-colors"
      >
        {loading ? (
          <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        ) : (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 5.25a3 3 0 0 1 3 3m3 0a6 6 0 0 1-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1 1 21.75 8.25Z" />
          </svg>
        )}
        {loading ? "Redirecting to SSO..." : "Continue with Enterprise SSO"}
      </button>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-slate-700" />
        </div>
        <div className="relative flex justify-center">
          <span className="px-3 bg-surface-card text-xs text-slate-500">
            Keycloak OAuth2 / OIDC
          </span>
        </div>
      </div>

      <div className="flex flex-col gap-2">
        {["admin · Full platform access", "operator · Incident management", "analyst · Read + analysis", "viewer · Read only"].map((line) => {
          const [role, desc] = line.split(" · ");
          return (
            <div key={role} className="flex items-center gap-2 text-xs text-slate-500">
              <span className="w-2 h-2 rounded-full bg-slate-600 flex-shrink-0" />
              <span className="capitalize font-medium text-slate-400">{role}</span>
              <span>—</span>
              <span>{desc}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
