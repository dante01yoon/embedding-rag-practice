import sys

sys.path.insert(0, "b3")
from chunk import split  # noqa: E402


def test_long_paragraph_ends():  # 문단 하나가 크기보다 길어도 끝나야 한다 (겹침 계산이 제자리를 돌면 멈추지 않는다)
    text = "가나다 " * 2000
    assert 0 < len(split(text, 500, 100)) < 50


def test_overlap_is_shared():  # 앞 청크의 끝이 다음 청크 앞에 겹친다
    text = "\n\n".join(f"문단 {i} " + "내용 " * 60 for i in range(10))
    a, b = split(text, 500, 100)[:2]
    assert a[-30:] in b


def test_keeps_all_text():  # 겹침 없이 자르면 원문 글자가 빠지지 않는다
    text = "\n\n".join(f"문단 {i} 끝" for i in range(200))
    assert "".join(split(text, 300, 0)).replace("\n", "") == text.replace("\n", "")
