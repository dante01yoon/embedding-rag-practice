from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-m3")


def sim(a, b):  # 두 문장의 코사인 유사도
    va, vb = model.encode([a, b], normalize_embeddings=True)
    return round(float(va @ vb), 2)


pairs = [
    ("같은 단어 다른 뜻", "배가 아파서 병원에 갔다", "배를 타고 섬에 갔다"),
    ("다른 단어 같은 뜻", "배가 아파서 병원에 갔다", "복통이 심해서 진료를 받았다"),
    ("한국어 · 영어", "강아지에게 줄 사료를 찾고 있어요", "I'm looking for food for my puppy"),
    ("반대말", "이 영화는 정말 재미있다", "이 영화는 정말 재미없다"),
    ("숫자만 다름", "기준금리가 3%로 올랐다", "기준금리가 5%로 올랐다"),
]
for name, a, b in pairs:
    print(f"{name:10s} {sim(a, b)}  | {a} ↔ {b}")
