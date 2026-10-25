import json
import os
import re
import sqlite3

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
llm = OpenAI()
CACHE = "chinook/llm_cache_e4.json"
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def ask(prompt):  # 답과 입력 토큰을 함께 저장
    if prompt not in cache:
        r = llm.chat.completions.create(model=os.environ["MODEL"], messages=[{"role": "user", "content": prompt}], temperature=0)
        cache[prompt] = [r.choices[0].message.content.strip(), r.usage.prompt_tokens]
    return cache[prompt]


db = sqlite3.connect("chinook/chinook.sqlite")  # 음반 가게 예제 DB (표 11개)
SCHEMA = {n: s for n, s in db.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")}
Q = [("AC/DC의 앨범은 몇 개예요?", "SELECT count(*) FROM Album a JOIN Artist r ON a.ArtistId = r.ArtistId WHERE r.Name = 'AC/DC'"),
     ("Rock 장르 곡은 몇 곡이에요?", "SELECT count(*) FROM Track t JOIN Genre g ON t.GenreId = g.GenreId WHERE g.Name = 'Rock'"),
     ("가장 많이 팔린 장르는? 판매 수량 기준", "SELECT g.Name FROM InvoiceLine l JOIN Track t ON l.TrackId = t.TrackId JOIN Genre g ON t.GenreId = g.GenreId GROUP BY g.GenreId ORDER BY sum(l.Quantity) DESC LIMIT 1"),
     ("매출 합계가 가장 큰 나라는?", "SELECT BillingCountry FROM Invoice GROUP BY BillingCountry ORDER BY sum(Total) DESC LIMIT 1"),
     ("돈을 가장 많이 쓴 고객의 성은?", "SELECT c.LastName FROM Customer c JOIN Invoice i ON c.CustomerId = i.CustomerId GROUP BY c.CustomerId ORDER BY sum(i.Total) DESC LIMIT 1"),
     ("담당 고객이 가장 많은 직원의 성은?", "SELECT e.LastName FROM Employee e JOIN Customer c ON c.SupportRepId = e.EmployeeId GROUP BY e.EmployeeId ORDER BY count(*) DESC LIMIT 1"),
     ("Grunge 재생목록에 든 곡은 몇 곡?", "SELECT count(*) FROM PlaylistTrack pt JOIN Playlist p ON pt.PlaylistId = p.PlaylistId WHERE p.Name = 'Grunge'"),
     ("가장 긴 곡의 제목은?", "SELECT Name FROM Track ORDER BY Milliseconds DESC LIMIT 1"),
     ("2013년 총매출은? 소수 둘째 자리까지", "SELECT round(sum(Total), 2) FROM Invoice WHERE strftime('%Y', InvoiceDate) = '2013'"),
     ("MPEG audio file 형식인 곡은 몇 곡?", "SELECT count(*) FROM Track t JOIN MediaType m ON t.MediaTypeId = m.MediaTypeId WHERE m.Name = 'MPEG audio file'"),
     ("곡이 가장 많은 앨범의 제목은?", "SELECT a.Title FROM Track t JOIN Album a ON t.AlbumId = a.AlbumId GROUP BY a.AlbumId ORDER BY count(*) DESC LIMIT 1"),
     ("브라질 고객은 몇 명?", "SELECT count(*) FROM Customer WHERE Country = 'Brazil'")]


def to_sql(q, tables):  # 고른 표의 스키마만 주고 SQL 한 줄
    sql, tok = ask("SQLite 표:\n" + "\n\n".join(SCHEMA[t] for t in tables) + f"\n\n질문에 답하는 SQL 한 줄만 출력하세요. 설명 없이.\n질문: {q}")
    m = re.search(r"(SELECT|WITH)\b.*", sql, re.S | re.I)  # 앞에 설명을 붙여도 SELECT부터만
    return re.sub(r"```", "", m.group(0) if m else sql).strip(), tok


def pick(q):  # 표 고르기: 이름 목록만 보고 필요한 표를 고른다
    ans, tok = ask("데이터베이스 표 이름: " + ", ".join(SCHEMA) + f"\n\n아래 질문에 답하는 데 필요한 표 이름만 쉼표로 출력하세요.\n질문: {q}")
    return [t for t in SCHEMA if re.search(rf"\b{t}\b", ans)], tok


def run(sql):
    try:
        rows = db.execute(sql).fetchall()
        return rows[0][0] if rows else None  # 첫 줄의 첫 칸만 비교 (열을 더 붙여도 정답)
    except sqlite3.Error as e:
        return f"에러: {e}"


for name in ["표 전부", "표 고르기"]:
    right, tokens = 0, 0
    for q, gold in Q:
        tables, t1 = (list(SCHEMA), 0) if name == "표 전부" else pick(q)
        sql, t2 = to_sql(q, tables)
        ok = run(sql) == run(gold)
        right, tokens = right + ok, tokens + t1 + t2
        if not ok:
            print(f"  ✗ {q} | 고른 표 {tables}")
    print(f"{name} | 맞힘 {right}/{len(Q)} · 질문당 입력 {tokens / len(Q):,.0f}토큰")
json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
