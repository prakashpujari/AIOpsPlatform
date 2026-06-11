import { auth } from "@/lib/auth";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { can } from "@/lib/rbac";
import type { Role } from "@/types";

const PUBLIC_PATHS = ["/login", "/api/auth", "/api/health"];

const PROTECTED_ROUTES: Array<{ path: string; resource: string; action: "read" }> = [
  { path: "/admin", resource: "users", action: "read" },
  { path: "/audit", resource: "audit", action: "read" },
  { path: "/costs", resource: "costs", action: "read" },
  { path: "/evaluation", resource: "evaluation", action: "read" },
];

export default auth((req) => {
  const { nextUrl, auth: session } = req as NextRequest & { auth: { roles?: string[] } | null };

  const isPublic = PUBLIC_PATHS.some((p) => nextUrl.pathname.startsWith(p));
  if (isPublic) return NextResponse.next();

  if (!session) {
    return NextResponse.redirect(new URL(`/login?callbackUrl=${nextUrl.pathname}`, req.url));
  }

  const roles = (session.roles ?? []) as Role[];
  const restricted = PROTECTED_ROUTES.find((r) => nextUrl.pathname.startsWith(r.path));
  if (restricted && !can(roles, restricted.resource, restricted.action)) {
    return NextResponse.redirect(new URL("/chat", req.url));
  }

  return NextResponse.next();
});

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
