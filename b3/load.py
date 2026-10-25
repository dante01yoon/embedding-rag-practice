import json
import pathlib
import re

docs = []
for path in sorted(pathlib.Path("k8s/ko").rglob("*.md")):  # 쿠버네티스 한국어 문서 (CC BY 4.0)
    raw = path.read_text()
    _, front, body = raw.split("---", 2)  # 맨 위 설정 부분(front matter)과 본문 나누기
    title = re.search(r"^title:\s*(.+)$", front, re.M).group(1).strip('"')
    text = re.sub(r'\{\{< glossary_tooltip text="([^"]+)"[^>]*>\}\}', r"\1", body)  # 용어 툴팁 → 글자만
    text = re.sub(r"\{\{[<%].*?[%>]\}\}", "", text)  # 나머지 웹사이트용 태그는 지운다
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)  # 주석 지우기
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    docs.append({"path": str(path), "title": title, "text": text})

pod = next(d for d in docs if d["path"].endswith("pods/_index.md"))
print(pod["text"][:300])

json.dump(docs, open("k8s/docs_ko.json", "w"), ensure_ascii=False)
print("문서", len(docs), "개 · 글자", sum(len(d["text"]) for d in docs))
