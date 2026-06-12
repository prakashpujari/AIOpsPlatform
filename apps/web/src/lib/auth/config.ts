import type { NextAuthConfig } from "next-auth";
import type { JWT } from "next-auth/jwt";

declare module "next-auth" {
  interface Session {
    accessToken: string;
    refreshToken: string;
    roles: string[];
    user: {
      id: string;
      name?: string | null;
      email?: string | null;
      image?: string | null;
    };
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
    refreshToken?: string;
    accessTokenExpires?: number;
    roles?: string[];
    sub?: string;
    error?: string;
  }
}

async function refreshAccessToken(token: JWT): Promise<JWT> {
  try {
    const url = `${process.env.KEYCLOAK_ISSUER}/protocol/openid-connect/token`;
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        client_id: process.env.KEYCLOAK_CLIENT_ID ?? "",
        client_secret: process.env.KEYCLOAK_CLIENT_SECRET ?? "",
        grant_type: "refresh_token",
        refresh_token: token.refreshToken ?? "",
      }),
    });
    const refreshed = await response.json() as {
      access_token: string;
      refresh_token: string;
      expires_in: number;
    };
    if (!response.ok) throw refreshed;
    return {
      ...token,
      accessToken: refreshed.access_token,
      refreshToken: refreshed.refresh_token,
      accessTokenExpires: Date.now() + refreshed.expires_in * 1000,
    };
  } catch {
    return { ...token, error: "RefreshAccessTokenError" };
  }
}

export const authConfig: NextAuthConfig = {
  secret: process.env.NEXTAUTH_SECRET,
  // Base URL for callbacks (required for proper redirect handling)
  url: process.env.NEXTAUTH_URL,
  providers: [],
  callbacks: {
    async jwt({ token, account, profile }) {
      if (account) {
        const keycloakProfile = profile as Record<string, unknown> | undefined;
        const realmAccess = keycloakProfile?.["realm_access"] as { roles?: string[] } | undefined;
        return {
          ...token,
          accessToken: account.access_token,
          refreshToken: account.refresh_token,
          accessTokenExpires: (account.expires_at ?? 0) * 1000,
          roles: realmAccess?.roles ?? [],
        };
      }
      if (Date.now() < (token.accessTokenExpires ?? 0)) return token;
      return refreshAccessToken(token);
    },
    async session({ session, token }) {
      return {
        ...session,
        accessToken: token.accessToken ?? "",
        refreshToken: token.refreshToken ?? "",
        roles: token.roles ?? [],
        user: { ...session.user, id: token.sub ?? "" },
      };
    },
    authorized({ auth, request: { nextUrl } }) {
      const isLoggedIn = !!auth?.user;
      const isPublic = ["/login", "/api/auth"].some((p) =>
        nextUrl.pathname.startsWith(p)
      );
      if (isPublic) return true;
      if (!isLoggedIn) return Response.redirect(new URL("/login", nextUrl));
      return true;
    },
  },
  pages: {
    signIn: "/login",
    error: "/login",
  },
  session: { strategy: "jwt", maxAge: 8 * 60 * 60 },
};
