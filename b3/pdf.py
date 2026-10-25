import pdfplumber
from pypdf import PdfReader

PAGE = 7  # 8번째 장 (책 14~15쪽이 한 장에 펼쳐져 있다)

# 1) 그냥 읽기: 글자는 나오지만 머리말이 섞이고, 순서가 뒤집히고, 표가 줄글로 뭉개진다
naive = PdfReader("pdf/kogl_guide.pdf").pages[PAGE].extract_text()
print("--- 그냥 읽기 ---")
print(naive[naive.find("6. 공공누리"):][:480])

# 2) 고쳐 읽기: 펼친 두 쪽을 왼쪽·오른쪽으로 잘라 따로 읽고, 맨 위 머리말 두 줄을 버린다
with pdfplumber.open("pdf/kogl_guide.pdf") as pdf:
    page = pdf.pages[PAGE]
    half = page.width / 2
    text = ""
    for x0, x1 in [(0, half), (half, page.width)]:
        lines = page.crop((x0, 0, x1, page.height)).extract_text().splitlines()
        text += "\n".join(lines[2:]) + "\n"  # 쪽 번호 · 머리말 버리기
print("--- 고쳐 읽기 ---")
print(text[:480])
for name, t in [("그냥 읽기", naive), ("고쳐 읽기", text)]:
    print(name, "· 5번이 6번보다 앞에 있나?", t.find("5. 공공누리") < t.find("6. 공공누리"))
