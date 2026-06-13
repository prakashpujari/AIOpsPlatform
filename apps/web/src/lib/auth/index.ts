import NextAuth from "next-auth";
import KeycloakProvider from "next-auth/providers/keycloak";
import CredentialsProvider from "next-auth/providers/credentials";
import { authConfig } from "./config";

const isDevelopment = process.env.NODE_ENV === "development";

const providers = isDevelopment
  ? [
      CredentialsProvider({
        name: "Development Login",
        credentials: {
          email: { label: "Email", type: "email" },
          password: { label: "Password", type: "password" },
        },
        async authorize(credentials) {
          if (credentials?.email) {
            return {
              id: "user-1",
              email: credentials.email,
              name: credentials.email.split("@")[0],
              image: null,
              roles: ["admin", "operator", "analyst"],
            };
          }
          return null;
        },
      }),
    ]
  : [
      KeycloakProvider({
        clientId: process.env.KEYCLOAK_CLIENT_ID ?? "",
        clientSecret: process.env.KEYCLOAK_CLIENT_SECRET ?? "",
        issuer: process.env.KEYCLOAK_ISSUER ?? "",
      }),
    ];

export const { handlers, auth, signIn, signOut } = NextAuth({
  ...authConfig,
  providers,
});
