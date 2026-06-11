import { can, getAccessibleRoutes } from "@/lib/rbac";
import type { Role } from "@/types";

describe("RBAC — can()", () => {
  it("admin can do everything on incidents", () => {
    expect(can(["admin"], "incidents", "read")).toBe(true);
    expect(can(["admin"], "incidents", "write")).toBe(true);
    expect(can(["admin"], "incidents", "delete")).toBe(true);
    expect(can(["admin"], "incidents", "approve")).toBe(true);
  });

  it("viewer can only read incidents", () => {
    expect(can(["viewer"], "incidents", "read")).toBe(true);
    expect(can(["viewer"], "incidents", "write")).toBe(false);
    expect(can(["viewer"], "incidents", "delete")).toBe(false);
  });

  it("viewer cannot access users resource", () => {
    expect(can(["viewer"], "users", "read")).toBe(false);
  });

  it("compliance can read audit and users", () => {
    expect(can(["compliance"], "audit", "read")).toBe(true);
    expect(can(["compliance"], "users", "read")).toBe(true);
    expect(can(["compliance"], "users", "write")).toBe(false);
  });

  it("operator cannot read audit logs", () => {
    expect(can(["operator"], "audit", "read")).toBe(false);
  });

  it("multi-role union works", () => {
    const roles: Role[] = ["viewer", "compliance"];
    expect(can(roles, "audit", "read")).toBe(true);
    expect(can(roles, "incidents", "read")).toBe(true);
    expect(can(roles, "incidents", "write")).toBe(false);
  });

  it("unknown resource returns false", () => {
    expect(can(["admin"], "nonexistent", "read")).toBe(false);
  });
});

describe("RBAC — getAccessibleRoutes()", () => {
  it("admin gets all routes", () => {
    const routes = getAccessibleRoutes(["admin"]);
    expect(routes).toContain("/chat");
    expect(routes).toContain("/incidents");
    expect(routes).toContain("/admin");
    expect(routes).toContain("/audit");
    expect(routes).toContain("/costs");
  });

  it("viewer gets limited routes", () => {
    const routes = getAccessibleRoutes(["viewer"]);
    expect(routes).toContain("/chat");
    expect(routes).toContain("/incidents");
    expect(routes).not.toContain("/admin");
    expect(routes).not.toContain("/audit");
    expect(routes).not.toContain("/costs");
  });

  it("compliance gets audit and admin", () => {
    const routes = getAccessibleRoutes(["compliance"]);
    expect(routes).toContain("/audit");
    expect(routes).toContain("/admin");
  });
});
