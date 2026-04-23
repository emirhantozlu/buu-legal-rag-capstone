import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import BrandHeader from "@/components/BrandHeader";
import "@/styles/landing.css";

const cards = [
  {
    title: "BUÜ Lisansüstü Eğitim Yönetmeliği neleri düzenler?",
    emoji: "📘",
    body: "Yüksek lisans ve doktora programlarının kapsamını, sürelerini, ders ve sınav esaslarını açıklar.",
  },
  {
    title: "2547 Sayılı Yükseköğretim Kanunu hangi konuları kapsar?",
    emoji: "⚖️",
    body: "Yükseköğretim kurumlarının yapısını, görevlerini ve eğitim esaslarını resmi maddelere dayalı açıklar.",
  },
  {
    title: "Sınav sonuçlarına nasıl itiraz edilir?",
    emoji: "⏱️",
    body: "Not itirazı ve değerlendirme süreçlerini ilgili yönetmelik maddelerine göre açıklar.",
  },
];


export default function LandingPage() {
  const navigate = useNavigate();
  const [question, setQuestion] = useState("");

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!question.trim()) return;
    navigate("/chat", { state: { presetQuestion: question.trim() } });
  };

  const launchWithQuestion = (value: string) => {
    const trimmed = value.trim();
    if (!trimmed) return;
    navigate("/chat", { state: { presetQuestion: trimmed } });
  };

  return (
    <div className="landing-shell">
      <div className="landing-card">
        <BrandHeader />

        <section className="landing-hero">
          <p className="landing-eyebrow">Mevzuat Soru-Cevap Asistanı</p>
          <h1>Hoş geldiniz</h1>
          <p className="landing-subtitle">
            Üniversite mevzuatı ve yönetmelikler hakkında merak ettiğiniz her şeyi sorabilirsiniz. Resmi
            maddeleri kaynak göstererek açıklar.
          </p>
          <div className="landing-pill-row">
            <span className="landing-pill">2547 Sayılı Kanun</span>
            <span className="landing-pill">BUÜ Lisansüstü Yönetmeliği</span>
          </div>
        </section>

        <section className="landing-card-grid">
          {cards.map((card) => (
            <button
              key={card.title}
              type="button"
              className="info-card interactive"
              onClick={() => launchWithQuestion(card.title)}
            >
              <span className="info-card-emoji" aria-hidden>
                {card.emoji}
              </span>
              <h3>{card.title}</h3>
              <p>{card.body}</p>
            </button>
          ))}
        </section>

        <form className="landing-form" onSubmit={handleSubmit}>
          <label htmlFor="question" className="sr-only">
            Sorunuzu buraya yazın
          </label>
          <div className="landing-input">
            <input
              id="question"
              type="text"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Sorunuzu yazın..."
            />
            <button type="submit" aria-label="Soruyu gönder">
              ➜
            </button>
          </div>
          <p className="landing-hint">Cevaplar yalnızca sisteme yüklenen mevzuat metinlerine dayanır.</p>
        </form>
      </div>
    </div>
  );
}
