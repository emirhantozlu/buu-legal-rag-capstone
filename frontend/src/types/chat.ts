export type Role = "user" | "assistant";

export interface ChatMessage {
  role: Role;
  content: string;
  sources?: SourceItem[];
  retrievedChunks?: RetrievedChunk[];
}

export interface SourceItem {
  chunk_id?: string;
  doc_name?: string;
  article_no?: string;
  score?: number;
}

export interface RetrievedChunk {
  chunk_id?: string;
  doc_name?: string;
  article_no?: string;
  heading?: string;
  text?: string;
  score: number;
}

export interface ChatResponse {
  answer: string;
  is_fallback: boolean;
  queries: string[];
  sources: SourceItem[];
  retrieved_chunks: RetrievedChunk[];
}

export interface ChatRequest {
  question: string;
  chat_history?: { role: Role; content: string }[];
}
