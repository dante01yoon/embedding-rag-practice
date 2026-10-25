# 01. 강의 소개와 실습 환경 준비

> 섹션 0 · 시작하기 · 수업 1 / 60 · [전체 목록](../../README.md#수업-목록)

## 이 수업에서 하는 것

- uv를 설치하고, 실습 폴더에서 uv sync, 그리고 .env에 키를 넣으면 준비 끝이에요. 막히면 README의 자주 나는 오류 표를 먼저 보세요.

## 실행

설치와 키 준비는 [저장소 README의 설치](../../README.md#설치)를 따라 합니다. 영상에서 친 명령:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
uv --version
uv python install 3.11
uv run python --version
ls
uv sync
cp .env.example .env
cat .env
uv run python -c "import sentence_transformers, bm25s, faiss, chromadb; print('준비 완료')"
docker --version
```

---
[전체 프롬프트 모음](../../PROMPTS.md) · [저장소 처음으로](../../README.md)
