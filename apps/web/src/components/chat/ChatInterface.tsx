"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useSession } from "next-auth/react";
import { v4 as uuidv4 } from "uuid";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { clsx } from "clsx";
import toast from "react-hot-toast";
import { useChatStore, activeSessionSelector } from "@/store/chatStore";
import { chatApi, streamChat } from "@/lib/api/chat";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import type { ChatMessage } from "@/types";
import { formatDistanceToNow } from "date-fns";

function SendIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5" />
    </svg>
  );
}

function PlusIcon() {
  return (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
    </svg>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={clsx("flex gap-3", isUser ? "flex-row-reverse" : "flex-row")}>
      {/* Avatar */}
      <div
        className={clsx(
          "w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold flex-shrink-0 mt-1",
          isUser ? "bg-brand-600 text-white" : "bg-slate-700 text-slate-300"
        )}
      >
        {isUser ? "U" : "AI"}
      </div>

      {/* Content */}
      <div className={clsx("max-w-[75%] min-w-0", isUser ? "items-end" : "items-start", "flex flex-col gap-1")}>
        <div
          className={clsx(
            "rounded-2xl px-4 py-3 text-sm",
            isUser
              ? "bg-brand-600 text-white rounded-tr-sm"
              : "bg-surface-elevated text-slate-200 rounded-tl-sm border border-slate-700/50"
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose-dark prose prose-sm max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content + (message.isStreaming ? "▋" : "")}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Metadata */}
        <div className="flex items-center gap-3 px-1">
          <span className="text-xs text-slate-500">
            {formatDistanceToNow(new Date(message.timestamp), { addSuffix: true })}
          </span>
          {message.metadata?.model && (
            <span className="text-xs text-slate-600">{message.metadata.model}</span>
          )}
          {message.metadata?.tokensUsed && (
            <span className="text-xs text-slate-600">
              {message.metadata.tokensUsed.toLocaleString()} tokens
            </span>
          )}
        </div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-1">
            {message.sources.slice(0, 3).map((src) => (
              <span
                key={src.id}
                className="px-2 py-0.5 rounded-full bg-brand-900/30 text-brand-400 text-xs border border-brand-700/30"
                title={src.content.slice(0, 200)}
              >
                {src.title.slice(0, 40)}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

const SUGGESTED_PROMPTS = [
  "What caused the recent P1 incident on payment-service?",
  "Show me all critical incidents in the last 24 hours",
  "What is the root cause of the database connection failures?",
  "Generate a remediation plan for the Kafka consumer lag issue",
];

export function ChatInterface() {
  const { data: session } = useSession();
  const {
    sessions, addSession, addMessage, updateStreamingMessage,
    finalizeStreamingMessage, setStreaming, isStreaming, activeSessionId,
    setActiveSession,
  } = useChatStore();
  const activeSession = useChatStore(activeSessionSelector);

  const [input, setInput] = useState("");
  const [initializing, setInitializing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeSession?.messages]);

  const createNewSession = useCallback(async () => {
    setInitializing(true);
    try {
      const { data } = await chatApi.createSession();
      addSession(data);
    } catch {
      toast.error("Failed to create chat session");
    } finally {
      setInitializing(false);
    }
  }, [addSession]);

  useEffect(() => {
    if (!activeSessionId && sessions.length === 0) {
      createNewSession();
    }
  }, [activeSessionId, sessions.length, createNewSession]);

  async function handleSend(text?: string) {
    const content = (text ?? input).trim();
    if (!content || isStreaming || !activeSession) return;

    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    const userMsg: ChatMessage = {
      id: uuidv4(),
      role: "user",
      content,
      timestamp: new Date().toISOString(),
    };

    const assistantMsgId = uuidv4();
    const assistantMsg: ChatMessage = {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
      isStreaming: true,
    };

    addMessage(activeSession.id, userMsg);
    addMessage(activeSession.id, assistantMsg);
    setStreaming(true);

    abortRef.current = new AbortController();

    try {
      await streamChat(
        activeSession.id,
        content,
        (chunk) => updateStreamingMessage(activeSession.id, assistantMsgId, chunk),
        (metadata) => finalizeStreamingMessage(activeSession.id, assistantMsgId, metadata as ChatMessage["metadata"]),
        abortRef.current.signal,
      );
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        finalizeStreamingMessage(activeSession.id, assistantMsgId);
        toast.error("Failed to get response");
      }
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  }

  function handleInputChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }

  return (
    <div className="flex h-full gap-4 -m-6 p-6">
      {/* Session list */}
      <div className="w-56 flex-shrink-0 flex flex-col gap-2">
        <button
          onClick={createNewSession}
          disabled={initializing}
          className="btn-primary flex items-center justify-center gap-2 w-full"
        >
          <PlusIcon />
          New Chat
        </button>
        <div className="overflow-y-auto space-y-1 flex-1">
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => setActiveSession(s.id)}
              className={clsx(
                "w-full text-left px-3 py-2 rounded-lg text-xs transition-colors truncate",
                s.id === activeSessionId
                  ? "bg-brand-600/20 text-brand-300 border border-brand-600/30"
                  : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
              )}
            >
              {s.title || `Chat ${s.id.slice(0, 8)}`}
            </button>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col min-w-0 bg-surface-card rounded-xl border border-slate-700/50 overflow-hidden">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {!activeSession || activeSession.messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-6 text-center">
              <div>
                <p className="text-xl font-semibold text-slate-200">
                  Enterprise AI Copilot
                </p>
                <p className="text-sm text-slate-400 mt-1">
                  Ask about incidents, run RCA, search knowledge base
                </p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-xl">
                {SUGGESTED_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => void handleSend(prompt)}
                    className="text-left p-3 rounded-xl bg-surface-elevated border border-slate-700/50 hover:border-brand-600/50 text-sm text-slate-400 hover:text-slate-200 transition-all"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            activeSession.messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-slate-700/50 p-4">
          <div className="flex items-end gap-3 bg-surface-elevated rounded-xl border border-slate-700/50 px-4 py-3">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask about incidents, infrastructure, or knowledge base..."
              rows={1}
              disabled={isStreaming}
              className="flex-1 bg-transparent text-sm text-slate-100 placeholder-slate-500 resize-none focus:outline-none min-h-[24px] max-h-[200px]"
            />
            <button
              onClick={() => void handleSend()}
              disabled={!input.trim() || isStreaming || !activeSession}
              className="p-2 rounded-lg bg-brand-600 hover:bg-brand-700 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-colors flex-shrink-0"
            >
              {isStreaming ? (
                <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              ) : (
                <SendIcon />
              )}
            </button>
          </div>
          <p className="text-xs text-slate-600 text-center mt-2">
            Shift+Enter for new line · Enter to send · All conversations are audited
          </p>
        </div>
      </div>
    </div>
  );
}
