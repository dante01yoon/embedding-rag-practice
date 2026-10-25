import json
import sys

LANG = sys.argv[1] if len(sys.argv) > 1 else "ko"
rows = [json.loads(line) for line in open(f"k8s/qa_{LANG}.jsonl")]
# 사람이 하나씩 읽고 내린 판단 (번호 = 0부터)
DROP = {"ko": {2: "문서 속 예시 명령을 그대로 묻는다", 22: "답이 아니라 '어디서 찾느냐'를 묻는다"}, "en": {}}[LANG]
FIX = {"ko": {13: "파드 스펙에 runtimeClassName을 지정하려면 클러스터에 그 런타임클래스가 먼저 설정되어 있어야 하나요?"}, "en": {}}[LANG]
HAND = {"ko": [{"question": "디플로이먼트를 이전 버전으로 되돌리려면 어떻게 하나요?", "path": "k8s/ko/workloads/controllers/deployment.md"}], "en": []}[LANG]

kept = []
for i, r in enumerate(rows):
    if i in DROP:
        print(f"빼기 {i:2d}: {DROP[i]} · {r['question'][:40]}")
        continue
    if i in FIX:
        print(f"고침 {i:2d}: {r['question'][:30]} → {FIX[i][:30]}")
        r["question"] = FIX[i]
    kept.append(r)
kept += HAND  # 사람이 직접 쓴 질문도 섞는다
json.dump(kept, open(f"k8s/qa_{LANG}_reviewed.json", "w"), ensure_ascii=False, indent=1)
print(f"생성 {len(rows)}개 → 검수 후 {len(kept)}개 (직접 쓴 질문 {len(HAND)}개 포함)")
