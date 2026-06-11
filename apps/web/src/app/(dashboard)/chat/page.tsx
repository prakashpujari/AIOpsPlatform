import type { Metadata } from "next";
import { ChatInterface } from "@/components/chat/ChatInterface";

export const metadata: Metadata = { title: "AI Chat" };

export default function ChatPage() {
  return <ChatInterface />;
}
