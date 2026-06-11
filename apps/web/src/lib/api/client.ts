import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from "axios";
import { getSession } from "next-auth/react";

function createApiClient(baseURL: string): AxiosInstance {
  const client = axios.create({
    baseURL,
    timeout: 30_000,
    headers: { "Content-Type": "application/json" },
  });

  client.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
    const session = await getSession();
    if (session?.accessToken) {
      config.headers.Authorization = `Bearer ${session.accessToken}`;
    }
    return config;
  });

  client.interceptors.response.use(
    (res) => res,
    async (error) => {
      if (error.response?.status === 401) {
        window.location.href = "/login";
      }
      return Promise.reject(error instanceof Error ? error : new Error(String(error)));
    }
  );

  return client;
}

export const apiClient = createApiClient(
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
);

export const gatewayClient = createApiClient(
  process.env.NEXT_PUBLIC_AI_GATEWAY_URL ?? "http://localhost:8001"
);
