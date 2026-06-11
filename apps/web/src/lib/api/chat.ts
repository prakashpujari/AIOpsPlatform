import { apiClient } from "./client";
import type { ChatSession, SearchResult } from "@/types";

export const chatApi = {
  createSession: () =>
    apiClient.post<ChatSession>("/api/v1/chat/sessions"),

  getSessions: () =>
    apiClient.get<ChatSession[]>("/api/v1/chat/sessions"),

  getSession: (id: string) =>
    apiClient.get<ChatSession>(`/api/v1/chat/sessions/${id}`),

  deleteSession: (id: string) =>
    apiClient.delete(`/api/v1/chat/sessions/${id}`),

  search: (query: string, topK = 5) =>
    apiClient.post<SearchResult>("/api/v1/search", { query, top_k: topK }),
};

export async function streamChat(
  sessionId: string,
  message: string,
  onChunk: (chunk: string) => void,
  onDone: (metadata: Record<string, unknown>) => void,
  signal?: AbortSignal
): Promise<void> {
  const session = await import("next-auth/react").then((m) => m.getSession());
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/api/v1/chat/sessions/${sessionId}/stream`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${session?.accessToken ?? ""}`,
      },
      body: JSON.stringify({ message }),
      signal,
    }
  );

  if (!response.ok) throw new Error(`Stream error: ${response.status}`);
  if (!response.body) throw new Error("No response body");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const text = decoder.decode(value, { stream: true });
    const lines = text.split("\n");
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6);
        if (data === "[DONE]") {
          onDone({});
        } else {
          try {
            const parsed = JSON.parse(data) as { content?: string; metadata?: Record<string, unknown> };
            if (parsed.content) onChunk(parsed.content);
            if (parsed.metadata) onDone(parsed.metadata);
          } catch {
            onChunk(data);
          }
        }
      }
    }
  }
}
