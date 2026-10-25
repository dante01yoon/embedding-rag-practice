"""히트맵 그리기 도우미 — 수업에서는 heatmap.py만 본다."""
import matplotlib.pyplot as plt
from matplotlib import font_manager

# 한글 글꼴: 이 컴퓨터에 있는 것 하나만 고른다(없는 글꼴을 넣으면 경고가 쏟아진다)
_have = {f.name for f in font_manager.fontManager.ttflist}
plt.rcParams["font.family"] = next((f for f in ("AppleGothic", "Malgun Gothic", "NanumGothic") if f in _have), "DejaVu Sans")


def save_heatmap(scores, sentences, path):
    n = len(sentences)
    fig, ax = plt.subplots(figsize=(12.5, 8.8))
    ax.imshow(scores, cmap="YlOrRd", vmin=0, vmax=1)
    labels = [s if len(s) <= 30 else s[:29] + "…" for s in sentences]
    ax.set_xticks(range(n), labels, rotation=35, ha="right", fontsize=13)
    ax.set_yticks(range(n), labels, fontsize=13)
    for i in range(n):
        for j in range(n):
            ax.text(j, i, f"{scores[i, j]:.2f}", ha="center", va="center", fontsize=14,
                    color="white" if scores[i, j] > 0.7 else "black")
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    print("저장:", path)
