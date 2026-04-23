import { useState } from "react";

import { RetrievedChunk } from "@/types/chat";

interface RetrievalPanelProps {
  chunks: RetrievedChunk[];
  onClose?: () => void;
}

export function RetrievalPanel({ chunks, onClose }: RetrievalPanelProps) {
  const [expandedChunk, setExpandedChunk] = useState<string | null>(null);

  const toggleChunk = (key: string) => {
    setExpandedChunk((prev) => (prev === key ? null : key));
  };

  return (
    <aside className="retrieval-panel">
      <header>
        <div>
          <p className="retrieval-label">Kaynak ongoruleri</p>
          <h4>En ilgili maddeler</h4>
        </div>
        <div className="retrieval-actions">
          <span className="retrieval-count">{chunks.length ? `${chunks.length} kayit` : "-"}</span>
          {onClose && (
            <button type="button" className="retrieval-close" onClick={onClose}>
              Kapat
            </button>
          )}
        </div>
      </header>

      {!chunks.length ? (
        <p className="retrieval-empty">Henuz kaynak bilgisi yok. Bir soru sorun.</p>
      ) : (
        <div className="retrieval-chunks">
          {chunks.map((chunk, index) => {
            const chunkKey = chunk.chunk_id || `${chunk.doc_name || "doc"}-${chunk.article_no || index}`;
            const isExpanded = expandedChunk === chunkKey;
            const snippet = chunk.text || "";
            const truncated = snippet.length > 220 ? `${snippet.slice(0, 220)}...` : snippet;

            return (
              <article key={chunkKey} className="chunk-card" data-expanded={isExpanded}>
                <p className="chunk-title">
                  {chunk.doc_name} {chunk.article_no ? ` - ${chunk.article_no}` : ""}
                </p>
                {chunk.heading && <p className="chunk-heading">{chunk.heading}</p>}
                {snippet && (
                  <>
                    <p className={`chunk-text${isExpanded ? " expanded" : ""}`}>{isExpanded ? snippet : truncated}</p>
                    <button
                      type="button"
                      className="chunk-toggle"
                      onClick={() => toggleChunk(chunkKey)}
                      aria-expanded={isExpanded}
                    >
                      {isExpanded ? "Metni gizle" : "Metni oku"}
                    </button>
                  </>
                )}
                <span className="chunk-score">Skor: {chunk.score.toFixed(2)}</span>
              </article>
            );
          })}
        </div>
      )}
    </aside>
  );
}
