import json


def naive(text, size):
    """글자 수만 세서 자른다 (단어·문장 중간에서도 끊긴다)."""
    return [text[i:i + size] for i in range(0, len(text), size)]


def split(text, size, overlap):
    """문단을 이어 붙여 size 글자 안팎의 청크를 만들고, 앞 청크의 끝 overlap 글자를 다음 청크 앞에 겹친다."""
    chunks, cur = [], ""
    for para in text.split("\n\n"):
        if cur and len(cur) + len(para) > size:
            chunks.append(cur)
            tail = cur[-overlap:] if overlap else ""
            cur = tail[tail.find(" ") + 1:] if " " in tail else tail  # 겹치는 부분 (단어 중간에서 시작하지 않게)
        cur = (cur + "\n\n" + para).strip()
    if cur:
        chunks.append(cur)
    return chunks


if __name__ == "__main__":
    docs = json.load(open("k8s/docs_ko.json"))
    pod = next(d for d in docs if d["path"].endswith("pods/_index.md"))
    a, b = naive(pod["text"], 200)[:2]
    print("그냥 자르기 :", a[-25:].replace("\n", " "), "|", b[:25].replace("\n", " "))
    a, b = split(pod["text"], 500, 100)[:2]
    print("앞 청크 끝 :", a[-60:].replace("\n", " "))
    print("뒤 청크 앞 :", b[:60].replace("\n", " "))
    for size, overlap in [(200, 0), (500, 100), (1500, 300)]:
        chunks = [c for d in docs for c in split(d["text"], size, overlap)]
        print(f"크기 {size:5d} · 겹침 {overlap:3d} → 청크 {len(chunks):5d}개 · 평균 {sum(map(len, chunks)) // len(chunks)}자")
