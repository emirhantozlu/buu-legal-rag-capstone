import { ReactNode } from "react";

import { Role, SourceItem } from "@/types/chat";

interface ChatBubbleProps {
  role: Role;
  content: string | ReactNode;
  sources?: SourceItem[];
}

export function ChatBubble({ role, content, sources }: ChatBubbleProps) {
  const isUser = role === "user";

  return (
    <div style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start" }}>
      <div
        style={{
          maxWidth: "640px",
          background: isUser ? "var(--buu-cyan)" : "#ffffff",
          color: isUser ? "#ffffff" : "#0c2659",
          padding: "1rem 1.25rem",
          borderRadius: isUser ? "20px 20px 4px 20px" : "20px 20px 20px 4px",
          boxShadow: isUser
            ? "0 10px 25px rgba(46, 167, 201, 0.28)"
            : "0 12px 32px rgba(12, 38, 89, 0.08)",
          fontSize: "0.98rem",
          lineHeight: 1.5,
        }}
      >
        {typeof content === "string" ? <p style={{ margin: 0, whiteSpace: "pre-line" }}>{content}</p> : content}
        {!isUser && sources && sources.length > 0 && (
          <div
            style={{
              marginTop: "0.85rem",
              borderTop: "1px solid rgba(12, 38, 89, 0.08)",
              paddingTop: "0.75rem",
              display: "flex",
              flexWrap: "wrap",
              gap: "0.4rem",
            }}
          >
            {sources.map((source, index) => (
              <span
                key={`${source.chunk_id}-${index}`}
                style={{
                  fontSize: "0.78rem",
                  background: "var(--buu-light)",
                  color: "var(--buu-navy)",
                  padding: "0.25rem 0.6rem",
                  borderRadius: "999px",
                  border: "1px solid rgba(12, 38, 89, 0.08)",
                }}
              >
                {source.doc_name || "Kaynak"} {source.article_no ? `– ${source.article_no}` : ""}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
