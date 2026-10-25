import json
import os
import sys
import textwrap

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()
embed = HuggingFaceEmbeddings(model_name="BAAI/bge-m3", encode_kwargs={"normalize_embeddings": True})
if not os.path.exists("k8s/chroma_lc"):  # 처음 한 번만 색인한다
    docs = [Document(d["text"], metadata={"title": d["title"], "path": d["path"]}) for d in json.load(open("k8s/docs_ko.json"))]
    chunks = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100).split_documents(docs)  # 청킹
    Chroma.from_documents(chunks, embed, persist_directory="k8s/chroma_lc")  # 벡터로 바꿔 저장
retriever = Chroma(persist_directory="k8s/chroma_lc", embedding_function=embed).as_retriever(search_kwargs={"k": 4})

prompt = ChatPromptTemplate.from_template(
    "아래 자료만 보고 답하세요. 문장 끝에 근거 번호를 [1]처럼 붙이세요. 자료에 없으면 모른다고 답하세요.\n\n{context}\n\n질문: {question}")


def number(docs):  # 청크에 번호를 붙여 이어 붙인다 (40줄 RAG와 같은 일)
    return "\n\n".join(f"[{i + 1}] {d.metadata['title']}\n{d.page_content}" for i, d in enumerate(docs))


llm = ChatOpenAI(model=os.environ["MODEL"])
chain = {"context": retriever | number, "question": RunnablePassthrough()} | prompt | llm | StrOutputParser()

if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "서비스와 인그레스는 무엇이 다른가요?"
    for line in ("답: " + chain.invoke(question)).splitlines():
        print(textwrap.fill(line, 60))
    for i, d in enumerate(retriever.invoke(question)):  # 출처를 보이려고 한 번 더 검색 (챗봇에서는 한 번으로 줄인다)
        print(f"  [{i + 1}] {d.metadata['title']} · {d.metadata['path']}")
