import gradio as gr
import pandas as pd
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

books = pd.read_csv("books/books_mood.csv").set_index("pageid")
embed = HuggingFaceEmbeddings(model_name="BAAI/bge-m3", encode_kwargs={"normalize_embeddings": True})
db = Chroma(persist_directory="books/chroma", embedding_function=embed)  # 벡터 DB 수업에서 저장한 Chroma를 다시 연다


def search(query, kind, mood):
    hits = db.similarity_search(query, k=50)  # 넉넉히 50권 찾고 (거른 뒤에도 6권이 남게)
    found = books.loc[[int(h.page_content.split()[0]) for h in hits]]
    if kind != "전체":
        found = found[found["kind"] == kind]  # 소설/비소설 거르기
    if mood != "상관없음":
        found = found.sort_values(mood, ascending=False)  # 분위기 점수 순으로
    return found.head(6)


print(search("우주와 과학을 쉽게 알려 주는 책", "소설", "상관없음")[["title", "kind"]])


def recommend(query, kind, mood):
    cards = ""
    for _, b in search(query, kind, mood).iterrows():
        cards += (f"<div class='card'><b>{b['title']}</b><i>{b['author'] if isinstance(b['author'], str) else ''}</i>"
                  f"<span>{b['kind']}</span><p>{b['description'][:110]}…</p></div>")
    return f"<div class='grid'>{cards}</div>"


CSS = """.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.card{padding:16px;border-radius:12px;border:1px solid #444;display:flex;flex-direction:column;gap:6px}
.card b{font-size:18px}.card i{color:#999;font-style:normal}.card span{color:#5ec2b7;font-size:13px}.card p{font-size:14px;margin:0}"""

with gr.Blocks(title="의미로 찾는 도서 추천기") as app:
    gr.Markdown("## 의미로 찾는 도서 추천기")
    with gr.Row():
        query = gr.Textbox(label="어떤 책을 찾나요?", scale=3)
        kind = gr.Dropdown(["전체", "소설", "비소설"], value="전체", label="종류")
        mood = gr.Dropdown(["상관없음", "즐거운", "놀라운", "화나는", "긴장감", "슬픈"], value="상관없음", label="분위기")
    button = gr.Button("추천받기", variant="primary")
    out = gr.HTML()
    button.click(recommend, [query, kind, mood], out)
    gr.Markdown("데이터: 한국어 위키백과 책 문서 (CC BY-SA 4.0)")

app.launch(css=CSS)