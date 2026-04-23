import { useMemo } from "react";

import { ChatMessage, ChatRequest, ChatResponse } from "@/types/chat";

const DEFAULT_BASE_URL = "/api";

export function useChatApi(baseUrl?: string) {
  const resolvedBase = baseUrl || import.meta.env.VITE_API_BASE_URL || DEFAULT_BASE_URL;

  async function postJson<T>(path: string, body: unknown): Promise<T> {
    const response = await fetch(`${resolvedBase}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const message = await response.text();
      throw new Error(message || "API request failed");
    }

    return (await response.json()) as T;
  }

  async function requestAnswer(question: string, history: ChatMessage[]): Promise<ChatResponse> {
    const payload: ChatRequest = {
      question,
      chat_history: history.map((msg) => ({ role: msg.role, content: msg.content })),
    };
    return postJson<ChatResponse>("/chat/answer", payload);
  }

  async function debugRetrieval(question: string, history: ChatMessage[]) {
    const payload: ChatRequest = {
      question,
      chat_history: history.map((msg) => ({ role: msg.role, content: msg.content })),
    };
    return postJson("/retrieval/debug", payload);
  }

  return useMemo(
    () => ({ requestAnswer, debugRetrieval, baseUrl: resolvedBase }),
    [resolvedBase]
  );
}
