"""pull이 한 번에 가져오는 문서 수를 고정하고 질문 하나를 푼다.
실행: python c3/pull_k.py <질문 id> <개수> [10k|100k|all]
개수를 고정하려고 두 가지를 바꾼다:
① 도구가 k를 자르는 범위(PULL_MIN·PULL_MAX)를 둘 다 그 개수로
② 도구 설명서의 「k는 50~300」 문구."""

import json
import sys

sys.path.insert(0, "c3")
import agent  # noqa: E402
import tools  # noqa: E402

qid, k = sys.argv[1], int(sys.argv[2])
set_name = sys.argv[3] if len(sys.argv) > 3 else "all"
tools.PULL_MIN = tools.PULL_MAX = k  # pull이 k를 이 범위로 자르므로 항상 k개
agent.TOOLS["pull"][0] = agent.tool(
    "pull",
    f"검색기(BM25) 상위 {k}개 문서를 작업 폴더로 가져온다"
    f"(한 번에 항상 {k}개, 작업 폴더 전체 1,500개까지). "
    "이미 있는 문서는 건너뛴다. 순위 상위 20개의 문서 번호와 제목을 미리 보여 준다.",
    {"query": agent.S},
    ["query"],
)
q = next(x for x in json.load(open("c3/questions.json")) if x["id"] == qid)
r = agent.solve(q, "pull", set_name)
print(
    f"한 번에 {k}개 · {r['status']} · 턴 {r['turns']} · 도구 {len(r['tools'])}번 · "
    f"작업 폴더 {r['work']}개 · 입력 {r['tokens_in']:,} · ${r['cost']:.4f} · {r['sec']}초"
)
print(r["answer"][-120:])
