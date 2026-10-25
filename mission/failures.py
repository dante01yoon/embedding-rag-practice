import collections
import json

rows = json.load(open("mission/rows.json"))  # report.py가 남긴 질문별 기록


def cause(r):  # 실패를 원인별로: 검색 → 답 거절 → 자료 밖 내용 순서로 본다
    if not r["hit"]:
        return "검색 실패"
    if r["refused"]:
        return "찾고도 거절"
    if not r["faithful"]:
        return "자료 밖 내용"
    return None


c = collections.Counter(filter(None, map(cause, rows)))
for k, n in c.most_common():
    ex = next(r for r in rows if cause(r) == k)
    print(f"{k:<8} | {n}개 · 예: {ex['q'][:38]}")
print(f"실패 합계 {sum(c.values())}/{len(rows)}")
