import { apiClient } from "./client";
import type { Incident, PaginatedResponse, PaginationParams } from "@/types";

export interface IncidentFilters extends PaginationParams {
  severity?: string;
  status?: string;
  service?: string;
  search?: string;
  from?: string;
  to?: string;
}

export const incidentsApi = {
  list: (params: IncidentFilters = {}) =>
    apiClient.get<PaginatedResponse<Incident>>("/api/v1/incidents", { params }),

  get: (id: string) =>
    apiClient.get<Incident>(`/api/v1/incidents/${id}`),

  create: (data: Partial<Incident>) =>
    apiClient.post<Incident>("/api/v1/incidents", data),

  update: (id: string, data: Partial<Incident>) =>
    apiClient.patch<Incident>(`/api/v1/incidents/${id}`, data),

  resolve: (id: string, resolution: string) =>
    apiClient.post<Incident>(`/api/v1/incidents/${id}/resolve`, { resolution }),

  createExternal: (id: string, system: "servicenow" | "jira") =>
    apiClient.post<{ externalId: string; url: string }>(
      `/api/v1/incidents/${id}/external`,
      { system }
    ),

  getStats: () =>
    apiClient.get<{
      open: number;
      critical: number;
      resolvedToday: number;
      avgResolutionHours: number;
    }>("/api/v1/incidents/stats"),
};
