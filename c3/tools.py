"""문서 번호로만 움직이는 도구 넷: search · find · read · pull.
한 질문을 푸는 동안의 상태(볼 수 있는 문서, 찾기 결과, 작업 폴더)는 Box 하나가 가진다.
모델은 경로를 모른다. 문서 번호(w000123)만 주고받고, 번호를 실제 파일로 바꾸는 일은 여기서 한다.
모든 도구는 첫 줄에 상태를 적어 돌려준다:
ok · none · truncated · timeout · bad_request · out_of_scope"""

import os
import re
import shutil
import sqlite3
import subprocess
import time

from kiwipiepy import Kiwi

PAGE = 20  # find가 한 번에 보여 주는 문서 수
READ_CHARS = 1200  # read가 한 번에 보여 주는 글자 수
FIND_TIMEOUT = 20  # find 한 번의 제한 시간(초)
PULL_MIN, PULL_MAX = 50, 300  # pull 한 번에 가져오는 문서 수(가져오는 건 싸고, 읽는 게 비싸다)
WORK_MAX = 1500  # 작업 폴더 전체 상한
SNIPPET = 700  # search가 문서마다 보여 주는 글자 수
kiwi = Kiwi()


def match_query(text):  # 검색어를 색인과 같은 방법(Kiwi 형태소)으로 나눠 FTS5 질의로
    toks = dict.fromkeys(
        t.form.lower().replace('"', "") for t in kiwi.tokenize(text) if t.tag[0] in "NVS"
    )
    toks = [w for w in toks if any(c.isalnum() for c in w)]
    return toks, " OR ".join(f'"{w}"' for w in toks)


class Box:
    def __init__(self, set_name, mode="raw", run_id="demo"):
        self.set, self.mode = set_name, mode  # mode: search | raw | pull
        self.db = sqlite3.connect("wiki/docs.db")
        self.root = f"wiki/{set_name}"
        self.member = {"10k": " AND in10k=1", "100k": " AND in100k=1", "all": ""}[set_name]
        self.ws = f"c3/ws/{run_id}"  # pull 방식의 작업 폴더
        self.work = set()  # 작업 폴더에 들어온 문서 번호
        self.results = {}  # find 결과 이름(r1, r2 …) → 문서 번호 목록
        self.shown, self.opened = set(), set()  # search·find가 발췌를 보여 준 문서, read로 연 문서
        self.log = []  # 도구 호출 기록
        if mode == "pull":
            os.makedirs(self.ws, exist_ok=True)

    def close(self):
        if self.mode == "pull" and self.ws.startswith("c3/ws/") and os.path.isdir(self.ws):
            shutil.rmtree(self.ws)

    # ── 문서 번호 ↔ 파일 ──
    def _doc(self, num):  # 이 집합에 있는 문서만
        sql = f"SELECT path, title FROM docs WHERE id=?{self.member}"
        return self.db.execute(sql, (num,)).fetchone()

    def _num(self, doc_id):
        m = re.fullmatch(r"w(\d{6})", str(doc_id).strip())
        return int(m[1]) if m else None

    def _ranked(self, query, k):
        toks, q = match_query(query)
        if not q:
            return toks, []
        t = f"fts_{self.set}"
        sql = f"SELECT rowid FROM {t} WHERE {t} MATCH ? ORDER BY bm25({t}, 5.0, 1.0) LIMIT ?"
        return toks, [r[0] for r in self.db.execute(sql, (q, k))]

    # ── 도구 ──
    def search(self, query):
        """검색기 상위 5개 문서에서, 검색어가 가장 많이 겹치는 700자씩"""
        toks, top = self._ranked(query, 5)
        if not top:
            return "상태: none\n검색 결과가 없습니다. 검색어를 바꿔 보세요."
        out = ["상태: ok"]
        for num in top:
            path, title = self._doc(num)
            text = open(f"{self.root}/{path}", encoding="utf-8").read()
            best = max(
                range(0, max(1, len(text) - SNIPPET // 2), SNIPPET // 2),
                key=lambda s: sum(
                    text[s : s + SNIPPET].lower().count(w) for w in toks if len(w) > 1
                ),
            )
            self.shown.add(num)
            end = min(len(text), best + SNIPPET)
            head = f"[w{num:06d}] {title} · 전체 {len(text):,}자 중 {best}~{end}"
            out.append(f"{head}\n{text[best:end]}")
        return "\n\n".join(out)

    def find(self, pattern, within=None, offset=0):
        """패턴(정규식, 대소문자 무시)이 든 문서 목록.
        within에 앞선 결과 이름을 주면 그 안에서만 찾는다"""
        t0 = time.time()
        if self.mode == "pull" and not self.work:
            return "상태: none\n작업 폴더가 비어 있습니다. 먼저 pull로 문서를 가져오세요."
        if within is None:
            targets = [self.ws if self.mode == "pull" else self.root]
        elif within in self.results:
            base = self.ws if self.mode == "pull" else self.root
            targets = [f"{base}/{self._doc(n)[0]}" for n in self.results[within]]
        else:
            names = ", ".join(self.results) or "없음"
            out = f"상태: bad_request\n'{within}'라는 결과가 없습니다. 지금 있는 결과: {names}"
            if self._num(within) is not None:  # 문서 번호를 넣었다
                out += ". 한 문서 안에서 찾으려면 read(문서 번호, at=패턴)을 쓰세요."
            return out
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
        base = self.ws if self.mode == "pull" else self.root
        for n in page:
            path, title = self._doc(n)
            text = open(f"{base}/{path}", encoding="utf-8").read()
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
        if doc is None or (self.mode == "pull" and num not in self.work):
            hint = " pull로 먼저 가져오세요." if self.mode == "pull" else ""
            return "상태: out_of_scope\n지금 볼 수 있는 범위에 없는 문서입니다." + hint
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

    def pull(self, query, k=100):
        """검색기 상위 k개 문서를 작업 폴더에 더한다(이미 있는 문서는 건너뜀).
        순위 상위 20개 제목을 미리 보여 준다"""
        k = max(PULL_MIN, min(int(k), PULL_MAX))
        _, top = self._ranked(query, k)
        if not top:
            return "상태: none\n검색 결과가 없습니다. 검색어를 바꿔 보세요."
        new = 0
        for num in top:
            if num in self.work or len(self.work) >= WORK_MAX:
                continue
            path = self._doc(num)[0]
            dst = f"{self.ws}/{path}"
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            try:
                os.link(f"{self.root}/{path}", dst)  # 복사 없이 같은 파일에 이름 하나 더
            except OSError:
                shutil.copyfile(f"{self.root}/{path}", dst)
            self.work.add(num)
            new += 1
        head = [
            f"[w{n:06d}] {self._doc(n)[1]}" + ("" if n in self.work else " (상한이라 못 가져옴)")
            for n in top[:20]
        ]
        state = "ok" if new else "none"
        note = ""
        if not new:
            note = (
                "\n새로 들어온 문서가 없습니다. "
                "검색어를 바꾸거나, 가져온 문서 안에서 find·read로 확인하세요."
            )
        return (
            f"상태: {state}\n"
            f"새로 가져옴 {new}개 · 이미 있음 {len(top) - new}개 · "
            f"작업 폴더 {len(self.work):,}개(상한 {WORK_MAX:,}){note}\n"
            f"순위 미리보기(상위 {len(head)}):\n" + "\n".join(head)
        )

    def call(self, name, args):  # 이름별로 나눠 부르고, 잘못된 요청은 죽지 않고 상태로 돌려준다
        by_mode = {"search": ["search"], "raw": ["find", "read"], "pull": ["pull", "find", "read"]}
        allowed = by_mode[self.mode]
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
