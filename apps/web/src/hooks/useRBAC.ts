"use client";

import { useSession } from "next-auth/react";
import { useMemo } from "react";
import { can, getAccessibleRoutes } from "@/lib/rbac";
import type { Role } from "@/types";

export function useRBAC() {
  const { data: session } = useSession();
  const roles = useMemo(
    () => (session?.roles ?? []) as Role[],
    [session?.roles]
  );

  return {
    roles,
    can: (resource: string, action: "read" | "write" | "delete" | "approve") =>
      can(roles, resource, action),
    accessibleRoutes: getAccessibleRoutes(roles),
    isAdmin: roles.includes("admin"),
    isOperator: roles.includes("operator"),
    isAnalyst: roles.includes("analyst"),
    isCompliance: roles.includes("compliance"),
  };
}
