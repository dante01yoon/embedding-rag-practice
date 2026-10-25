from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained("BAAI/bge-m3")
print("사전 크기:", tok.vocab_size)
sentences = {"en": "Which dog food should I buy?", "ko": "강아지 사료 뭘 사야 할까?"}

for lang, s in sentences.items():
    pieces = tok.tokenize(s)  # 문장을 모델이 읽는 조각(토큰)으로 자른다
    print(lang, len(pieces), "토큰:", " | ".join(pieces))
    print("   번호:", tok.convert_tokens_to_ids(pieces))  # 모델에 실제로 들어가는 것
