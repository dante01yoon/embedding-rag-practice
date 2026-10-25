import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # .env 파일의 키·주소·모델 이름을 환경 변수로
client = OpenAI()
question = "Apple Music 검색 팀이 2026년 논문에서 결과 0건 비율을 얼마나 줄였어? 한 문장으로."

doc = open("a1/news.txt").read() if "--doc" in sys.argv else ""
prompt = f"참고 문서:\n{doc}\n\n질문: {question}" if doc else question

reply = client.chat.completions.create(model=os.environ["MODEL"], messages=[{"role": "user", "content": prompt}])
print("문서 붙임" if doc else "문서 없음", "→", reply.choices[0].message.content)
print("보낸 토큰:", reply.usage.prompt_tokens)
