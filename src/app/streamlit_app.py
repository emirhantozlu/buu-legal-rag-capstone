from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import streamlit as st

from src.rag.pipeline import RAGPipeline


def get_pipeline() -> RAGPipeline:
    if "rag_pipeline" not in st.session_state:
        st.session_state["rag_pipeline"] = RAGPipeline()
    return st.session_state["rag_pipeline"]


def init_session_state() -> None:
    if "messages" not in st.session_state:
        st.session_state["messages"] = []


def main() -> None:
    st.set_page_config(
        page_title="BUU LLM RAG - Mevzuat Soru-Cevap Asistani",
        page_icon="⚖️",
        layout="wide",
    )

    init_session_state()
    rag = get_pipeline()

    st.sidebar.title("Ayarlar")
    st.sidebar.markdown(
        """
Bu arayuz, **2547 sayili Yuksekogretim Kanunu** ve
**BUU Lisansustu Egitim-Ogretim Yonetmeligi**
uzerinde calisan RAG tabanli bir asistandir.
"""
    )
    show_debug = st.sidebar.checkbox(
        "Teknik detaylari goster (retrieval sonuclari)",
        value=False,
    )

    st.title("BUU LLM RAG - Mevzuat Soru-Cevap Asistani")
    st.markdown(
        """
Dogal dilde soru sorarak universite mevzuatiyla ilgili yanitlar alabilirsiniz.
Cevaplar, yalnizca sisteme yuklenen **kanun ve yonetmelik maddelerine** dayanir.
"""
    )

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Sorunuzu yazin ve Enter'a basin...")

    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Yanit hazirlaniyor..."):
                stream = rag.answer_stream(
                    user_input,
                    chat_history=st.session_state["messages"],
                )

                answer_placeholder = st.empty()
                full_answer = ""

                for chunk in stream:
                    full_answer += chunk
                    answer_placeholder.markdown(full_answer)

        st.session_state["messages"].append({"role": "assistant", "content": full_answer})

        if show_debug:
            st.sidebar.markdown("---")
            st.sidebar.markdown("**Debug modu: su an sadece cevap metnini gosteriyor.**")


if __name__ == "__main__":
    main()
