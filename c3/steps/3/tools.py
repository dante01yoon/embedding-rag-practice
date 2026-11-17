"""문서 번호로만 움직이는 도구 둘: find · read.
한 질문을 푸는 동안의 상태(찾기 결과, 본 문서, 호출 기록)는 Box 하나가 가진다.
모델은 경로를 모른다. 문서 번호(w000123)만 주고받고, 번호를 실제 파일로 바꾸는 일은 여기서 한다.
모든 도구는 첫 줄에 상태를 적어 돌려준다:
ok · none · truncated · timeout · bad_request · out_of_scope"""

import re
import sqlite3
import subprocess
import time

PAGE = 20  # find가 한 번에 보여 주는 문서 수
READ_CHARS = 1200  # read가 한 번에 보여 주는 글자 수
FIND_TIMEOUT = 20  # find 한 번의 제한 시간(초)


class Box:
    def __init__(self, set_name):
        self.db = sqlite3.connect("wiki/docs.db")
        self.root = f"wiki/{set_name}"
        self.member = {"10k": " AND in10k=1", "100k": " AND in100k=1", "all": ""}[set_name]
        self.results = {}  # find 결과 이름(r1, r2 …) → 문서 번호 목록
        self.shown, self.opened = set(), set()  # find가 발췌를 보여 준 문서, read로 연 문서
        self.log = []  # 도구 호출 기록

    # ── 문서 번호 ↔ 파일 ──
    def _doc(self, num):  # 이 집합에 있는 문서만
        sql = f"SELECT path, title FROM docs WHERE id=?{self.member}"
        return self.db.execute(sql, (num,)).fetchone()

    def _num(self, doc_id):
        m = re.fullmatch(r"w(\d{6})", str(doc_id).strip())
        return int(m[1]) if m else None

    # ── 도구 ──
    def find(self, pattern, within=None, offset=0):
        """패턴(정규식, 대소문자 무시)이 든 문서 목록.
        within에 앞선 결과 이름을 주면 그 안에서만 찾는다"""
        t0 = time.time()
        if within is None:
            targets = [self.root]
        elif within in self.results:
            targets = [f"{self.root}/{self._doc(n)[0]}" for n in self.results[within]]
        else:
            names = ", ".join(self.results) or "없음"
            return f"상태: bad_request\n'{within}'라는 결과가 없습니다. 지금 있는 결과: {names}"
        files = []
        try:
            for i in range(0, len(targets), 1000):  # 파일 목록이 길면 나눠서
                left = FIND_TIMEOUT - (time.time() - t0)
                cmd = ["rg", "-l", "-i", "--no-ignore", "--no-messages", "-e", pattern, "--"]
                cmd += targets[i : i + 1000]
                p = subprocess.run(cmd, capture_output=True, text=True, timeout=max(0.1, left))
                if p.returncode == 2 and p.stderr.strip():
                    return f"상태: bad_request\n패턴을 읽지 못했습니다: {p.stderr.strip()[:200]}"
                files += p.stdout.splitlines()
        except subprocess.TimeoutExpired:
            return (
                f"상태: timeout\n{FIND_TIMEOUT}초 안에 끝나지 않았습니다. "
                "더 드문 낱말로 찾거나, within으로 범위를 좁혀 다시 찾으세요."
            )
        nums = sorted(int(re.search(r"/w(\d{6})_", f)[1]) for f in files)
        if not nums:
            return "상태: none\n일치하는 문서가 없습니다."
        rid = f"r{len(self.results) + 1}"
        self.results[rid] = nums
        offset = max(0, int(offset))
        page = nums[offset : offset + PAGE]
        more = offset + PAGE < len(nums)
        out = [
            f"상태: {'truncated' if more else 'ok'}",
            f"결과 {rid} · 문서 {len(nums):,}개 중 {offset + 1}~{offset + len(page)}번째"
            + (f" (다음 offset={offset + PAGE})" if more else ""),
        ]
        try:
            rx = re.compile(pattern, re.I)
        except re.error:
            rx = None
        for n in page:
            path, title = self._doc(n)
            text = open(f"{self.root}/{path}", encoding="utf-8").read()
            m = rx.search(text) if rx else None
            cut = " ".join(text[max(0, m.start() - 60) : m.end() + 60].split()) if m else ""
            self.shown.add(n)
            out.append(f"[w{n:06d}] {title} | …{cut}…")
        if more:
            out.append(
                f'결과가 많습니다. find(다른 패턴, within="{rid}")로 '
                "이 안에서 다시 찾거나 offset으로 이어 보세요."
            )
        return "\n".join(out)

    def read(self, doc_id, at=None, offset=0):
        """문서 하나를 1,200자씩. at에 패턴을 주면 그 패턴이 처음 나오는 곳 근처부터"""
        num = self._num(doc_id)
        if num is None:
            return "상태: bad_request\n문서 번호는 w000123 꼴입니다."
        doc = self._doc(num)
        if doc is None:
            return "상태: out_of_scope\n지금 볼 수 있는 범위에 없는 문서입니다."
        path, title = doc
        text = open(f"{self.root}/{path}", encoding="utf-8").read()
        head = f"[w{num:06d}] {title} · 전체 {len(text):,}자"
        start = max(0, int(offset))
        if at:
            try:
                m = re.compile(at, re.I).search(text, start)
            except re.error as e:
                return f"상태: bad_request\n패턴을 읽지 못했습니다: {e}"
            if not m:
                return f"상태: none\n{head} · {start}자 뒤로는 그 패턴이 없습니다."
            start = max(0, m.start() - 200)
        end = min(len(text), start + READ_CHARS)
        self.opened.add(num)
        return (
            f"상태: ok\n{head} 중 {start}~{end}"
            + (f" (다음 offset={end})" if end < len(text) else " (끝)")
            + f"\n{text[start:end]}"
        )

    def call(self, name, args):  # 이름별로 나눠 부르고, 잘못된 요청은 죽지 않고 상태로 돌려준다
        allowed = ["find", "read"]
        t0 = time.time()
        if name not in allowed:
            out = f"상태: bad_request\n지금 쓸 수 있는 도구는 {', '.join(allowed)}입니다."
        else:
            try:
                out = getattr(self, name)(**args)
            except (TypeError, ValueError) as e:
                # 인자 이름·개수가 틀렸거나, 숫자 자리에 글자가 왔을 때
                out = f"상태: bad_request\n인자가 맞지 않습니다: {e}"
        status = out.split("\n", 1)[0].replace("상태: ", "")
        sec = round(time.time() - t0, 2)
        entry = {"tool": name, "args": args, "status": status, "sec": sec, "chars": len(out)}
        self.log.append(entry)
        return out
