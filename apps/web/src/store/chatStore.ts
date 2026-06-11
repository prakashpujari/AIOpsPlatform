import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ChatMessage, ChatSession } from "@/types";

interface ChatState {
  sessions: ChatSession[];
  activeSessionId: string | null;
  isStreaming: boolean;
  streamingContent: string;

  setActiveSession: (id: string) => void;
  addSession: (session: ChatSession) => void;
  removeSession: (id: string) => void;
  addMessage: (sessionId: string, message: ChatMessage) => void;
  updateStreamingMessage: (sessionId: string, messageId: string, chunk: string) => void;
  finalizeStreamingMessage: (sessionId: string, messageId: string, metadata?: ChatMessage["metadata"]) => void;
  setStreaming: (value: boolean) => void;
  clearStreamingContent: () => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      sessions: [],
      activeSessionId: null,
      isStreaming: false,
      streamingContent: "",

      setActiveSession: (id) => set({ activeSessionId: id }),

      addSession: (session) =>
        set((s) => ({ sessions: [session, ...s.sessions], activeSessionId: session.id })),

      removeSession: (id) =>
        set((s) => ({
          sessions: s.sessions.filter((x) => x.id !== id),
          activeSessionId: s.activeSessionId === id ? null : s.activeSessionId,
        })),

      addMessage: (sessionId, message) =>
        set((s) => ({
          sessions: s.sessions.map((sess) =>
            sess.id === sessionId
              ? { ...sess, messages: [...sess.messages, message] }
              : sess
          ),
        })),

      updateStreamingMessage: (sessionId, messageId, chunk) =>
        set((s) => ({
          streamingContent: s.streamingContent + chunk,
          sessions: s.sessions.map((sess) =>
            sess.id === sessionId
              ? {
                  ...sess,
                  messages: sess.messages.map((msg) =>
                    msg.id === messageId
                      ? { ...msg, content: msg.content + chunk }
                      : msg
                  ),
                }
              : sess
          ),
        })),

      finalizeStreamingMessage: (sessionId, messageId, metadata) =>
        set((s) => ({
          isStreaming: false,
          streamingContent: "",
          sessions: s.sessions.map((sess) =>
            sess.id === sessionId
              ? {
                  ...sess,
                  messages: sess.messages.map((msg) =>
                    msg.id === messageId
                      ? { ...msg, isStreaming: false, metadata: metadata ?? msg.metadata }
                      : msg
                  ),
                }
              : sess
          ),
        })),

      setStreaming: (value) => set({ isStreaming: value }),
      clearStreamingContent: () => set({ streamingContent: "" }),
    }),
    {
      name: "aiops-chat",
      partialize: (s) => ({ sessions: s.sessions, activeSessionId: s.activeSessionId }),
    }
  )
);

export const activeSessionSelector = (s: ChatState) =>
  s.sessions.find((x) => x.id === s.activeSessionId) ?? null;
