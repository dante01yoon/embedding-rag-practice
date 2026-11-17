"""문서 수가 늘면 찾기 한 번이 얼마나 느려지나. 실행: python c3/bench.py [폴더] [낱말 …]
세 집합(1만 · 10만 · 전체)에서 같은 낱말이 든 파일을 rg로 찾고, 걸린 시간과 파일 수를 표로 찍는다.
제한 시간(20초)을 넘기면 '시간 초과'라고 적는다. 못 찾은 것(0개)과 시간 초과는 다른 상태다."""

import os
import subprocess
import sys
import time

SETS = {"1만": "wiki/10k", "10만": "wiki/100k", "전체": "wiki/all"}
LIMIT = 20  # 초

args = sys.argv[1:]
if args and os.path.isdir(args[0]):  # 첫 인자가 폴더면 그 폴더 하나만 잰다
    SETS = {"내 폴더": args.pop(0)}
# 받지 않은 묶음은 건너뛴다
SETS = {name: folder for name, folder in SETS.items() if os.path.isdir(folder)}
words = args or ["서울", "훈민정음"]
print(f"{'낱말':8}" + "".join(f"{name:>22}" for name in SETS))
for word in words:
    row = f"{word:8}"
    for folder in SETS.values():
        t0 = time.time()
        try:
            cmd = ["rg", "-l", "-i", "--no-ignore", "-e", word, folder]
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=LIMIT).stdout
            row += f"{time.time() - t0:>10.2f}초 {len(out.splitlines()):>8,}개"
        except subprocess.TimeoutExpired:
            row += f"{'시간 초과':>18}"
    print(row)
