import type { Role } from "@/types";

type Action = "read" | "write" | "delete" | "approve";

interface ResourcePermissions {
  [role: string]: Action[];
}

const PERMISSIONS: Record<string, ResourcePermissions> = {
  incidents: {
    admin: ["read", "write", "delete", "approve"],
    operator: ["read", "write"],
    analyst: ["read"],
    viewer: ["read"],
    compliance: ["read"],
  },
  rca: {
    admin: ["read", "write", "delete", "approve"],
    operator: ["read", "write", "approve"],
    analyst: ["read", "write"],
    viewer: ["read"],
    compliance: ["read"],
  },
  agents: {
    admin: ["read", "write", "delete", "approve"],
    operator: ["read", "approve"],
    analyst: ["read"],
    viewer: ["read"],
    compliance: ["read"],
  },
  knowledge: {
    admin: ["read", "write", "delete"],
    operator: ["read", "write"],
    analyst: ["read", "write"],
    viewer: ["read"],
    compliance: ["read"],
  },
  users: {
    admin: ["read", "write", "delete"],
    operator: [],
    analyst: [],
    viewer: [],
    compliance: ["read"],
  },
  audit: {
    admin: ["read"],
    operator: [],
    analyst: [],
    viewer: [],
    compliance: ["read"],
  },
  costs: {
    admin: ["read"],
    operator: ["read"],
    analyst: ["read"],
    viewer: [],
    compliance: ["read"],
  },
  evaluation: {
    admin: ["read", "write"],
    operator: ["read"],
    analyst: ["read", "write"],
    viewer: ["read"],
    compliance: ["read"],
  },
};

export function can(roles: Role[], resource: string, action: Action): boolean {
  const resourcePerms = PERMISSIONS[resource];
  if (!resourcePerms) return false;
  return roles.some((role) => resourcePerms[role]?.includes(action) ?? false);
}

export function getAccessibleRoutes(roles: Role[]): string[] {
  const routes = ["/chat", "/health", "/search"];
  if (can(roles, "incidents", "read")) routes.push("/incidents");
  if (can(roles, "rca", "read")) routes.push("/rca");
  if (can(roles, "agents", "read")) routes.push("/agents");
  if (can(roles, "costs", "read")) routes.push("/costs");
  if (can(roles, "evaluation", "read")) routes.push("/evaluation");
  if (can(roles, "users", "read")) routes.push("/admin");
  if (can(roles, "audit", "read")) routes.push("/audit");
  return routes;
}
