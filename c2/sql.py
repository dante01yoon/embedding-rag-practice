import csv
import json
import os
import re
import sqlite3

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
llm = OpenAI()
CACHE = "books/llm_cache_c2.json"
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def ask(prompt):
    if prompt not in cache:
        r = llm.chat.completions.create(model=os.environ["MODEL"], messages=[{"role": "user", "content": prompt}], temperature=0)
        cache[prompt] = r.choices[0].message.content.strip()
    return cache[prompt]


db = sqlite3.connect(":memory:")  # 도서 목록을 SQL 표로
db.execute("CREATE TABLE books (title TEXT, author TEXT, genre TEXT, year INTEGER, kind TEXT, sad REAL)")
for r in csv.DictReader(open("books/books_mood.csv")):
    m = re.search(r"\d{3,4}", r["published"])  # '1949년 6월 8일' → 1949
    db.execute("INSERT INTO books VALUES (?,?,?,?,?,?)", (r["title"], r["author"], r["genre"], int(m.group()) if m else None, r["kind"], float(r["슬픈"] or 0)))

SCHEMA = "CREATE TABLE books (title TEXT, author TEXT, genre TEXT, year INTEGER, kind TEXT, sad REAL)  -- sad: 슬픈 정도 0~1"
Q = [("헤밍웨이 책은 몇 권이에요?", "SELECT count(*) FROM books WHERE author LIKE '%헤밍웨이%'"),
     ("히가시노 게이고 책은 몇 권이에요?", "SELECT count(*) FROM books WHERE author LIKE '%히가시노%'"),
     ("도스토옙스키 책은 몇 권이에요?", "SELECT count(*) FROM books WHERE author LIKE '%도스토옙스키%'"),
     ("하인라인 책은 몇 권이에요?", "SELECT count(*) FROM books WHERE author LIKE '%하인라인%'"),
     ("SF 책은 몇 권이에요?", "SELECT count(*) FROM books WHERE genre LIKE '%SF%'"),
     ("추리 소설은 몇 권이에요?", "SELECT count(*) FROM books WHERE genre LIKE '%추리%'"),
     ("1900년 이전에 나온 책은 몇 권이에요?", "SELECT count(*) FROM books WHERE year < 1900"),
     ("2000년 이후에 나온 책은 몇 권이에요?", "SELECT count(*) FROM books WHERE year >= 2000"),
     ("소설이 아닌 책은 몇 권이에요?", "SELECT count(*) FROM books WHERE kind = '비소설'"),
     ("책이 가장 많은 작가는 누구예요?", "SELECT author FROM books WHERE author != '' GROUP BY author ORDER BY count(*) DESC LIMIT 1"),
     ("고골의 책 중 가장 먼저 나온 책은?", "SELECT title FROM books WHERE author LIKE '%고골%' AND year IS NOT NULL ORDER BY year LIMIT 1"),
     ("SF 책 중 가장 슬픈 책은?", "SELECT title FROM books WHERE genre = 'SF' ORDER BY sad DESC LIMIT 1")]  # (질문, 정답 SQL)
HINT = "\n예시 값: author는 '어니스트 헤밍웨이'처럼 성과 이름 전체, genre는 'SF', '추리 소설', '소설', kind는 '소설' 또는 '비소설'"
RULE = "\n규칙: 사람 이름과 장르는 표기가 여러 가지라 = 대신 LIKE '%핵심어%'로 찾으세요. author가 빈 칸('')인 책은 작가 미상입니다."


def to_sql(q, extra):  # 질문 → SQL 한 줄
    sql = ask(f"SQLite 표:\n{SCHEMA}{extra}\n\n질문에 답하는 SQL 한 줄만 출력하세요. 설명 없이.\n질문: {q}")
    return re.sub(r"^```\w*|```$", "", sql.strip()).strip()


def run(sql):
    try:
        return db.execute(sql).fetchall()
    except sqlite3.Error as e:
        return [(f"에러: {e}",)]


for name, extra in [("스키마만", ""), ("규칙", RULE), ("예시 값까지", HINT + RULE)]:
    right = 0
    for q, gold in Q:
        sql = to_sql(q, extra)
        got, want = run(sql)[:1] or [(None,)], run(gold)
        right += got[0][0] == want[0][0]
        if got[0][0] != want[0][0]:
            print(f"  ✗ {q} | {sql.split('FROM books')[-1].strip()[:48]} | {got[0][0]!r} (정답 {want[0][0]!r})")
    print(f"{name} | 맞힘 {right}/{len(Q)}")
json.dump(cache, open(CACHE, "w"), ensure_ascii=False)
