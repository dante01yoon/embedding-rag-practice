import itertools
import random
import re

import bm25s
import numpy as np
from sentence_transformers import SentenceTransformer

random.seed(0)
NAMES = ["민준", "서연", "도윤", "하은", "시우", "지유", "주원", "서윤", "하준", "지아", "예준", "하린", "지호", "수아", "건우", "윤서",
         "우진", "채원", "선우", "지민", "현우", "다은", "유준", "예은", "정우", "소율", "승우", "예린", "준서", "수빈", "지훈", "가은",
         "준우", "민서", "은우", "다인", "연우", "서아", "유찬", "시은", "이안", "나은", "한결", "채은", "로운", "아린"]  # 46명
COLORS = ["빨간", "파란", "노란", "초록", "보라", "하얀", "검은", "분홍", "주황", "회색", "갈색", "하늘색", "금색", "은색", "연두",
          "남색", "베이지", "청록", "자주", "민트", "살구", "버건디", "카키", "올리브", "라벤더", "산호", "크림", "와인", "네이비", "레몬"]
ITEMS = ["고양이", "기차", "우산", "자전거", "모자", "컵", "의자", "연필", "풍선", "시계", "가방", "장갑", "양말", "공", "책", "꽃병",
         "베개", "나비", "로봇", "배", "열쇠", "등대", "거북이", "곰인형", "선풍기", "주전자", "망원경", "기타", "물고기", "드럼", "버스", "구름", "별", "사탕", "팽이"]
things = [c + i for c in COLORS for i in ITEMS]  # "파란고양이"처럼 1,050가지
random.shuffle(things)

pairs = list(itertools.combinations(range(len(NAMES)), 2))  # 46명 중 두 명 고르기 = 1,035가지
likes = {i: [] for i in range(len(NAMES))}
queries = []
for t, (a, b) in zip(things, pairs):  # 좋아하는 것마다 정확히 두 사람 · 모든 두 사람 조합이 한 번씩
    likes[a].append(t)
    likes[b].append(t)
    queries.append((t, {a, b}))
docs = [f"{NAMES[i]}이 좋아하는 것: " + ", ".join(likes[i]) for i in range(len(NAMES))]
print(f"사람 {len(docs)}명 · 질문 {len(queries)}개 · 한 사람이 좋아하는 것 {len(likes[0])}개쯤")
print(docs[0][:80], "…")


def recall(ranked):  # 상위 2개에 정답 두 사람이 다 들어 있는 비율
    return np.mean([set(r[:2]) == gold for r, (_, gold) in zip(ranked, queries)])


model = SentenceTransformer("BAAI/bge-m3")
dv = model.encode(docs, normalize_embeddings=True)
questions = [f"좋아하는 것이 {t}인 사람은 누구인가요?" for t, _ in queries]
qv = model.encode(questions, normalize_embeddings=True, batch_size=64)
vec = [list(np.argsort(-(dv @ q))) for q in qv]

bm = bm25s.BM25()
bm.index([d.replace(",", " ").split() for d in docs], show_progress=False)
kw = [list(bm.retrieve([re.search(r"좋아하는 것이 (.+)인 사람", q).group(1).split()], k=len(docs), show_progress=False)[0][0]) for q in questions]  # 질문에서 찾을 대상만 꺼내 키워드로
print(f"Recall@2 | 벡터(bge-m3 1024차원) {recall(vec):.2f} · 키워드(BM25) {recall(kw):.2f}")
