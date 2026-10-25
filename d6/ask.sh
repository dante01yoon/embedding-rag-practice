# 질문 하나를 API에 보내 답과 캐시 여부를 본다
curl -s --get http://127.0.0.1:8001/ask --data-urlencode "q=$1" | python3 -c "import json,sys; r=json.load(sys.stdin); print(('캐시' if r['cached'] else '새로') + f\" · {r['sec']}초 · \" + r['answer'][:80])"
