import pandas as pd
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

books = pd.read_csv("books/books_clean.csv")
lines = open("books/tagged_description.txt").read().splitlines()
print(len(lines), "권")
print(lines[0][:60])

docs = [Document(page_content=line) for line in lines]
embed = HuggingFaceEmbeddings(model_name="BAAI/bge-m3", encode_kwargs={"normalize_embeddings": True})
vector = embed.embed_query("마법 학교")
print(len(vector), vector[:3])

ids = [line.split()[0] for line in lines]
db = Chroma.from_documents(docs, embed, ids=ids, persist_directory="books/chroma")

question = "마법 학교에서 친구들과 모험하는 이야기"
for doc, score in db.similarity_search_with_score(question, k=5):
    print(round(score, 3), doc.page_content[:40])


def recommend(query, k=5):
    hits = db.similarity_search(query, k=k)
    nums = [int(h.page_content.split()[0]) for h in hits]
    return books.set_index("pageid").loc[nums, ["title", "author"]]


print(recommend("전쟁의 상처를 견디는 가족"))
