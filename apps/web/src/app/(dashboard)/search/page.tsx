import type { Metadata } from "next";
import { KnowledgeSearch } from "@/components/search/KnowledgeSearch";

export const metadata: Metadata = { title: "Knowledge Search" };

export default function SearchPage() {
  return <KnowledgeSearch />;
}
