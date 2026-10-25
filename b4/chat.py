import streamlit as st
from langchain_core.output_parsers import StrOutputParser

from chain import llm, number, prompt, retriever  # 지난 수업의 부품을 그대로 쓴다

st.title("쿠버네티스 문서 챗봇")
if "messages" not in st.session_state:
    st.session_state.messages = []  # 대화 기록 (화면이 다시 그려져도 남는다)


def show_sources(docs):
    with st.expander("출처"):
        for i, d in enumerate(docs):
            st.markdown(f"[{i + 1}] **{d['title']}** · `{d['path']}`")


for m in st.session_state.messages:  # 지난 대화를 다시 그린다
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("sources"):
            show_sources(m["sources"])

if question := st.chat_input("쿠버네티스에 대해 물어보세요"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    docs = retriever.invoke(question)  # 검색은 한 번만
    sources = [d.metadata for d in docs]
    with st.chat_message("assistant"):
        stream = (prompt | llm | StrOutputParser()).stream({"context": number(docs), "question": question})
        answer = st.write_stream(stream)  # 글자가 만들어지는 대로 흘려 보여 준다
        show_sources(sources)
    st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
