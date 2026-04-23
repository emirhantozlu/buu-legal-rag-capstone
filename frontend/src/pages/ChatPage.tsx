import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";

import BrandHeader from "@/components/BrandHeader";
import { ChatBubble } from "@/components/ChatBubble";
import { RetrievalPanel } from "@/components/RetrievalPanel";
import { useChatApi } from "@/hooks/useChatApi";
import { ChatMessage, RetrievedChunk, SourceItem } from "@/types/chat";

import "@/styles/chat.css";

interface LocationState {
  presetQuestion?: string;
}

const quickPrompts = [
  "Lisansustu programlara basvuru sartlari nelerdir?",
  "Ders muafiyetini hangi kosullarda talep edebilirim?",
  "2547 sayili kanuna gore tez savunmasi suresi nedir?",
];

export default function ChatPage() {
  const location = useLocation();
  const { presetQuestion } = (location.state as LocationState) || {};

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState(presetQuestion ?? "");
  const [isLoading, setIsLoading] = useState(false);
  const [latestChunks, setLatestChunks] = useState<RetrievedChunk[]>([]);
  const [showRetrieval, setShowRetrieval] = useState(false);
  const { requestAnswer } = useChatApi();
  const bootstrapped = useRef(false);
  const feedRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    requestAnimationFrame(() => {
      feedRef.current?.scrollTo({ top: feedRef.current.scrollHeight, behavior: "smooth" });
    });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (presetQuestion && !bootstrapped.current) {
      bootstrapped.current = true;
      void handleSend(presetQuestion);
    }
  }, [presetQuestion]);

  async function handleSend(forceQuestion?: string) {
    const question = (forceQuestion ?? input).trim();
    if (!question || isLoading) return;

    const userMessage: ChatMessage = { role: "user", content: question };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await requestAnswer(question, [...messages, userMessage]);
      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.answer,
        sources: response.sources as SourceItem[],
        retrievedChunks: response.retrieved_chunks,
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setLatestChunks(response.retrieved_chunks);
    } catch (error) {
      const assistantMessage: ChatMessage = {
        role: "assistant",
        content:
          error instanceof Error
            ? `Yanit alinamadi: ${error.message}`
            : "Yanit alinamadi. Lutfen tekrar deneyin.",
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } finally {
      setIsLoading(false);
    }
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    void handleSend();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void handleSend();
    }
  };

  return (
    <div className="chat-shell">
      <section className="chat-panel">
        <div className="chat-panel-header">
          <BrandHeader compact />
          <div className="chat-meta">
            <span className="status-dot" aria-hidden />
            <span className="status-text">API baglantisi aktif</span>
          </div>
          <button
            type="button"
            className="panel-toggle"
            onClick={() => setShowRetrieval((prev) => !prev)}
          >
            {showRetrieval ? "Kaynak panelini gizle" : "Kaynak panelini ac"}
          </button>
        </div>

        <div ref={feedRef} className="chat-feed">
          {messages.length === 0 && !isLoading && (
            <div className="chat-empty">
              <p>Hazirsaniz sorunuzu yazin ya da asagidaki orneklerden birini secin.</p>
              <div className="quick-prompts">
                {quickPrompts.map((prompt) => (
                  <button key={prompt} type="button" onClick={() => void handleSend(prompt)}>
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((message, index) => (
            <ChatBubble key={index} role={message.role} content={message.content} sources={message.sources} />
          ))}
          {isLoading && <ChatBubble role="assistant" content="Yanit hazirlaniyor..." />}
        </div>

        <form className="chat-input" onSubmit={handleSubmit}>
          <textarea
            value={input}
            placeholder="Sorunuzu yazin..."
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={handleKeyDown}
            rows={2}
          />
          <button type="submit" disabled={isLoading || !input.trim()} aria-label="Soruyu gonder">
            Gonder
          </button>
        </form>
      </section>
      {showRetrieval && <RetrievalPanel chunks={latestChunks} onClose={() => setShowRetrieval(false)} />}
    </div>
  );
}
