from transformers import AutoTokenizer

pairs = [
    ("Which dog food should I buy?", "강아지 사료 뭘 사야 할까?"),
    ("The central bank raised interest rates today.", "오늘 중앙은행이 기준금리를 올렸다."),
    ("Search results with zero hits fell by 86 percent.", "검색 결과가 0건인 비율이 86% 줄었다."),
    ("Please summarize this contract in three lines.", "이 계약서를 세 줄로 요약해 주세요."),
]
names = {"bge-m3": "BAAI/bge-m3", "gpt2": "openai-community/gpt2"}  # 여러 언어용 · 영어 위주

for name, path in names.items():
    tok = AutoTokenizer.from_pretrained(path)
    en = sum(len(tok.tokenize(e)) for e, k in pairs)
    ko = sum(len(tok.tokenize(k)) for e, k in pairs)
    print(f"{name:7} 사전 {tok.vocab_size:,} | 영어 {en} · 한국어 {ko} 토큰 → {ko / en:.1f}배")
