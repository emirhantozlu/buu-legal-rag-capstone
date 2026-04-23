import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import BrandHeader from "@/components/BrandHeader";
import "@/styles/landing.css";

const cards = [
  {
    title: "BUU Lisansustu Egitim Yonetmeligi neleri duzenler?",
    emoji: "Kitap",
    body: "Yuksek lisans ve doktora programlarinin kapsamini, surelerini, ders ve sinav esaslarini aciklar.",
  },
  {
    title: "2547 Sayili Yuksekogretim Kanunu hangi konulari kapsar?",
    emoji: "Hukuk",
    body: "Yuksekogretim kurumlarinin yapisini, gorevlerini ve egitim esaslarini resmi maddelere dayali aciklar.",
  },
  {
    title: "Sinav sonuclarina nasil itiraz edilir?",
    emoji: "Surec",
    body: "Not itirazi ve degerlendirme sureclerini ilgili yonetmelik maddelerine gore aciklar.",
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
          <p className="landing-eyebrow">Mevzuat Soru-Cevap Asistani</p>
          <h1>Hos geldiniz</h1>
          <p className="landing-subtitle">
            Universite mevzuati ve yonetmelikler hakkinda merak ettiginiz her seyi sorabilirsiniz. Resmi
            maddeleri kaynak gostererek aciklar.
          </p>
          <div className="landing-pill-row">
            <span className="landing-pill">2547 Sayili Kanun</span>
            <span className="landing-pill">BUU Lisansustu Yonetmeligi</span>
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
            Sorunuzu buraya yazin
          </label>
          <div className="landing-input">
            <input
              id="question"
              type="text"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Sorunuzu yazin..."
            />
            <button type="submit" aria-label="Soruyu gonder">
              Gonder
            </button>
          </div>
          <p className="landing-hint">Cevaplar yalnizca sisteme yuklenen mevzuat metinlerine dayanir.</p>
        </form>
      </div>
    </div>
  );
}
