import sys

from sentence_transformers import SentenceTransformer
from show import save_heatmap

lang = sys.argv[1] if len(sys.argv) > 1 else "ko"
sentences = open(f"a3/sentences_{lang}.txt").read().splitlines()  # 한 줄 = 문장 하나
print(len(sentences), "문장", sentences[-1:])

model = SentenceTransformer("BAAI/bge-m3")
vecs = model.encode(sentences, normalize_embeddings=True)  # 문장마다 숫자 1024개, 길이 1
print(vecs.shape)  # (문장 수, 숫자 개수)

scores = vecs @ vecs.T  # 두 문장이 얼마나 비슷한가 (1에 가까울수록 비슷)
print(scores[0].round(2))  # 첫 문장과 나머지
save_heatmap(scores, sentences, f"a3/heatmap_{lang}.png")
