"""상태를 돌려주는 find 첫 판(다음 수업에서 tools.py로 키운다).
실행: python c3/find0.py <패턴> [폴더] [제한 시간]
첫 줄에 상태를 적는다: ok(다 보여 줌) · none(없음) · truncated(많아서 잘림)
· timeout(시간 초과) · bad_request(명령 실패)"""

import subprocess
import sys

ROOT, LIMIT, PAGE = "wiki/10k", 20, 20


def find(pattern, root=ROOT, limit=LIMIT):
    try:
        cmd = ["rg", "-l", "-i", "--no-ignore", "-e", pattern, root]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=limit)
    except subprocess.TimeoutExpired:
        return f"상태: timeout\n{limit}초 안에 끝나지 않았습니다. 더 드문 낱말로 찾으세요."
    if p.returncode == 2:  # rg가 패턴을 읽지 못했거나 폴더가 없을 때(0: 찾음, 1: 없음, 2: 실패)
        return f"상태: bad_request\n명령이 실패했습니다: {p.stderr.strip()[:120]}"
    files = sorted(p.stdout.splitlines())
    if not files:
        return "상태: none\n일치하는 문서가 없습니다."
    more = len(files) > PAGE
    return (
        f"상태: {'truncated' if more else 'ok'}\n"
        f"문서 {len(files):,}개 중 {min(PAGE, len(files))}개\n" + "\n".join(files[:PAGE])
    )


if __name__ == "__main__":  # python c3/find0.py <패턴> [폴더] [제한 시간(초)]
    pattern, *rest = sys.argv[1:]
    print(find(pattern, *rest[:1], *[int(x) for x in rest[1:2]]))
