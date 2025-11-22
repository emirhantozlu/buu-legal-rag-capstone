# src/app/streamlit_app.py

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import streamlit as st

from src.rag.pipeline import RAGPipeline


# -------------------------------------------------------------------
# Uygulama başlatılırken RAG pipeline'ı tek kez yükle (session_state)
# -------------------------------------------------------------------
def get_pipeline() -> RAGPipeline:
    if "rag_pipeline" not in st.session_state:
        st.session_state["rag_pipeline"] = RAGPipeline()
    return st.session_state["rag_pipeline"]


def init_session_state():
    if "messages" not in st.session_state:
        # chat geçmişini tutalım: {"role": "user"/"assistant", "content": "..."}
        st.session_state["messages"] = []


# -------------------------------------------------------------------
# Streamlit UI
# -------------------------------------------------------------------
def main():
    st.set_page_config(
        page_title="BUÜ LLM RAG – Mevzuat Asistanı",
        page_icon="⚖️",
        layout="wide",
    )

    init_session_state()
    rag = get_pipeline()

    # Sidebar
    st.sidebar.title("⚙️ Ayarlar")
    st.sidebar.markdown(
        """
Bu arayüz, **2547 sayılı Yükseköğretim Kanunu** ve  
**BUÜ Lisansüstü Eğitim-Öğretim Yönetmeliği**  
üzerinde çalışan RAG tabanlı bir asistandır.
"""
    )
    show_debug = st.sidebar.checkbox("Teknik detayları göster (retrieval sonuçları)", value=False)

    st.title("BUÜ LLM RAG – Mevzuat Soru-Cevap Asistanı")
    st.markdown(
        """
Doğal dilde soru sorarak, üniversite mevzuatıyla ilgili yanıtlar alabilirsiniz.  
Cevaplar, yalnızca sisteme yüklenen **kanun ve yönetmelik maddelerine** dayanır.
"""
    )

    # Daha önceki mesajları göster (chat arayüzü)
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Kullanıcıdan yeni soru
    user_input = st.chat_input("Sorunuzu yazın ve Enter'a basın...")

    if user_input:
        # Kullanıcı mesajını ekrana yaz
        st.session_state["messages"].append(
            {"role": "user", "content": user_input}
        )
        with st.chat_message("user"):
            st.markdown(user_input)

        # Asistan cevabı
        with st.chat_message("assistant"):
            with st.spinner("Yanıt hazırlanıyor..."):
                answer_text = rag.answer(user_input)
                st.markdown(answer_text)

        st.session_state["messages"].append(
            {"role": "assistant", "content": answer_text}
        )

        # Opsiyonel: debug için retrieval sonuçlarını göster
        if show_debug:
            # query_rewriter + retrieve akışını yeniden çalıştırmak yerine
            # sadece son cevabı gösteriyoruz; istersen buraya daha detaylı
            # debug bilgileri ekleyebiliriz.
            st.sidebar.markdown("---")
            st.sidebar.markdown("🔍 **Debug modu şu an sadece cevap metnini gösteriyor.**")



if __name__ == "__main__":
    main()
