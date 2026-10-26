# 임베딩·RAG 실전 — 실습 저장소

인프런 강의 「임베딩·RAG 실전」의 실습 코드와 데이터입니다. 임베딩과 검색의 원리(토큰 · 벡터 · BM25 · 근사 이웃 탐색 · 평가 지표)에서 시작해, 도서 추천 앱과 쿠버네티스 문서 RAG를 직접 만들고, 골든셋으로 재면서 하이브리드 검색 · 재정렬 · 맥락 검색으로 고쳐 나갑니다. 벡터가 못 하는 질문과 다른 길(집계 · 텍스트→SQL · 에이전트 검색), 서비스 운영(API · 권한 · 인젝션 · 트레이스 · 캐시 · 모델 교체 · 배포 전 자동 검사), 현업 사례 다시 만들기까지 수업마다 폴더가 있습니다.

- 수업별 안내(하는 것 · 파일 · 실행 명령 · 과제 · 풀이 · 프롬프트): [`lessons/`](lessons/) — 아래 [수업 목록](#수업-목록)
- 수업 속 프롬프트 원문 모음: [`PROMPTS.md`](PROMPTS.md)
- 코드 폴더 이름(`a1` … `e6`, `mission`)은 강의 순서와 같습니다. 모든 명령은 **저장소 맨 위 폴더에서** 실행합니다.

## 준비물
- macOS · Windows(PowerShell · WSL2) · Linux 중 하나, 디스크 여유 **10GB 이상** (임베딩 모델과 벡터 파일)
- 파이썬은 따로 설치하지 않아도 됩니다. `uv sync`가 이 저장소에 맞는 버전(3.11~3.12)을 알아서 받아 옵니다.
- **Docker Desktop** — PostgreSQL·pgvector 수업(B2)과 서비스 나누기 수업(D6)에서만 필요합니다.

## 설치
① uv 설치 — 운영체제에 맞는 명령 한 줄 (공식 안내: https://docs.astral.sh/uv/getting-started/installation/)

macOS · Linux · WSL2 (터미널):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env      # 또는 터미널을 새로 열기
```

Windows (PowerShell):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# 설치가 끝나면 PowerShell을 닫았다가 다시 엽니다
```

설치 확인 (운영체제 공통):
```bash
uv --version
uv python install 3.11
uv run python --version          # Python 3.11.x
```

② 저장소 받기와 도구 설치
```bash
git clone https://github.com/dante01yoon/embedding-rag-practice.git
cd embedding-rag-practice
uv sync
```

③ API 키 파일 만들기
```bash
cp .env.example .env      # .env 를 열어 OPENAI_API_KEY 자리에 내 키를 붙여 넣습니다
```

설치 확인:
```bash
uv run python -c "import sentence_transformers, bm25s, faiss, chromadb; print('준비 완료')"
```

## API 키와 모델
- 강의는 **OpenRouter** 키 하나로 LLM을 부릅니다. 코드는 OpenAI 파이썬 라이브러리를 쓰고, 주소만 OpenRouter로 바꿉니다.
- **키 만들기** (https://openrouter.ai/keys)
  1. https://openrouter.ai 에 가입·로그인하고, 크레딧을 조금 충전해 둡니다.
  2. 왼쪽 메뉴 **API Keys** → 오른쪽 위 **New Key**.
  3. **Name**에 알아보기 쉬운 이름(예: `rag-course`)을 적고, **Expiration**(만료 기간)을 고릅니다.
  4. **Credit limit**(사용 한도)을 작게 걸어 두면 안전합니다(예: Custom amount로 몇 달러).
  5. **Create**를 누릅니다. 인증 창이 뜨면 이메일로 온 코드를 넣습니다.
  6. 키는 이 창에서 **한 번만** 보입니다. 복사해서 `.env`의 `OPENAI_API_KEY=` 뒤에 붙여 넣습니다.
- **추천 모델** (강의 실습 전체 1회 비용은 2026년 10월 OpenRouter 가격으로 어림한 값)

  | `MODEL` 값 | 실습 전체 1회 | 특징 |
  |---|---|---|
  | `anthropic/claude-haiku-5.5` (기본) | 약 $0.6 | **강의 영상은 이 모델로 찍었습니다.** 결과 숫자가 영상과 같습니다. |
  | `qwen/qwen3.7-flash` | 약 $0.2 | 가장 쌉니다. 그림 입력·도구 호출 지원 |
  | `deepseek/deepseek-v4.1-flash` | 약 $0.25 | 그림 입력·도구 호출 지원 (출력 단가가 높아 답이 길면 비용이 늘어남) |

  모델은 `.env`의 `MODEL` 한 줄만 바꾸면 됩니다. 다른 모델은 결과 숫자가 영상과 조금 다를 수 있습니다.
- **LLM 답 캐시가 들어 있습니다.** `k8s/`, `books/`, `pdf/`, `chinook/`의 `llm_cache_*.json`에는 영상을 찍을 때 기본 모델이 준 답이 저장돼 있어서, 영상과 같은 질문 · 같은 모델이면 LLM을 다시 부르지 않습니다(비용 0, 숫자도 영상과 같음). 질문이나 프롬프트를 바꾸면 그 부분만 새로 호출합니다. 처음부터 직접 받아 보고 싶으면 해당 캐시 파일을 지우고 실행하세요.
- `.env`는 비밀 파일입니다. 깃허브에 올리거나 남에게 보내지 마세요(`.gitignore`에 들어 있습니다).

## 벡터 파일 만들기
벡터(`*.npy`)와 벡터 DB(Chroma) 파일은 용량이 커서 저장소에 넣지 않았습니다. LLM은 부르지 않으니 비용은 들지 않습니다. 한 번에 만들려면:

```bash
bash tools/make_vectors.sh
```

수업 순서대로 진행하면 대부분은 그 수업에서 저절로 만들어집니다. 따로 만들려면 아래 표의 명령을 씁니다.

| 파일 | 만드는 명령 | 쓰는 수업 |
|---|---|---|
| `books/book_vecs.npy` | `uv run python b2/embed_books.py` | A2 · B2 · B6-4 · B9-1 · C1-3 |
| `books/chroma/` | `uv run python b1/vector.py` | B1-3 · B1-6 |
| `books/chroma_b2/` | `uv run python b2/stores.py` (Docker 필요) | B2 |
| `k8s/index.npy` | `uv run python b3/index.py` | B3 |
| `k8s/vecs_200·500·1500.npy` | `uv run python b3/compare.py` | B3-3 |
| `k8s/vecs_ko_500.npy` · `vecs_en_500.npy` | `uv run python b5/evaluate.py` | B5 이후 거의 모든 수업 |
| `k8s/vecs_ko_ctx.npy` · `books/vecs_desc.npy` · `k8s/chroma_lc/` · `d7/idx/` | 그 수업 코드가 처음 실행될 때 자동 | B6-5 · E5 · B4-1 · D7 |
| `d9/docs` · `d9/index.json` · `d9/vecs.npy` | `uv run python d9/setup.py` | D9 |
| `vectors/docs_ko.npy` · `queries_ko.npy` | `uv run python tools/miracl_vectors.py` (위키 문단 32,651개, CPU에서 수십 분) | A5 · A6 |

## 처음 실행할 때 생기는 일
| 언제 | 무엇 | 크기·시간 |
|---|---|---|
| 임베딩 모델 첫 사용(A3부터) | `BAAI/bge-m3`를 허깅페이스에서 내려받음 | 약 2GB, 처음 한 번 몇 분 |
| 재정렬 수업(B6-2) | `BAAI/bge-reranker-v2-m3` 내려받음 | 약 2GB |
| PostgreSQL 수업(B2) | `bash b2/start_db.sh`로 pgvector 이미지를 받아 띄움 | 처음 한 번 수백 MB |

내려받은 모델은 `~/.cache/huggingface/hub`에 저장되고, 그다음부터는 바로 불러옵니다.

화면 앱은 이렇게 띄웁니다.
- Gradio(B1-6): `uv run python b1/app.py` → 터미널에 나온 주소를 브라우저로 엽니다.
- Streamlit(B4-2): `uv run streamlit run b4/chat.py`
- FastAPI(D1): `uv run uvicorn d1.api:app` → 주소 뒤에 `/docs`를 붙이면 API 설명 화면이 나옵니다.

## 자주 나는 오류
| 증상 | 원인 · 해결 |
|---|---|
| `openai.AuthenticationError` / 401 | `.env`가 없거나 키가 비었습니다. `cp .env.example .env` 후 키를 넣으세요. |
| `KeyError: 'MODEL'` | `.env`에 `MODEL=` 줄이 없습니다. `.env.example`을 다시 복사하세요. |
| `FileNotFoundError: ... .npy` | 벡터 파일을 아직 만들지 않았습니다. [벡터 파일 만들기](#벡터-파일-만들기)를 보세요. |
| `Cannot connect to the Docker daemon` | Docker Desktop을 실행하지 않았습니다. 앱을 켜고 다시 시도하세요. |
| `port 5433 is already allocated` | 전에 띄운 DB가 남아 있습니다. `docker rm -f rag-pg` 후 다시 실행하세요. |
| 그래프의 한글이 네모로 나옴 | `plt.rcParams["font.family"]`를 내 컴퓨터 글꼴로 바꿉니다(윈도우: `Malgun Gothic`). |
| 첫 실행이 오래 멈춘 것 같음 | 임베딩 모델(약 2GB)을 내려받는 중입니다. 한 번만 기다리면 됩니다. |

## 수업 목록
| # | 수업 | 코드 |
|---|---|---|
| | **섹션 0 · 시작하기** | |
| 1 | [강의 소개와 실습 환경 준비](lessons/01-S0/) | — |
| | **PART A · 기초 개념** | |
| 2 | [LLM, 토큰, 그리고 왜 검색이 필요한가](lessons/02-A1/) | [`a1/`](a1/) |
| 3 | [벡터와 유사도](lessons/03-A2/) | [`a2/`](a2/) |
| 4 | [임베딩은 어떻게 학습되나](lessons/04-A3/) | [`a3/`](a3/) |
| 5 | [TF-IDF에서 BM25까지](lessons/05-A4/) | [`a4/`](a4/) |
| 6 | [근사 이웃 탐색](lessons/06-A5/) | [`a5/`](a5/) |
| 7 | [검색이 잘 됐는지 재는 법](lessons/07-A6/) | [`a6/`](a6/) |
| | **B1 · 도서 추천 앱** | |
| 8 | [만들 앱 미리보기와 데이터 살펴보기](lessons/08-B1-1/) | [`b1/`](b1/) |
| 9 | [데이터 정제](lessons/09-B1-2/) | [`b1/`](b1/) · [`books/`](books/) |
| 10 | [벡터 DB에 넣고 문장으로 찾기](lessons/10-B1-3/) | [`b1/`](b1/) |
| 11 | [제로샷 분류: 소설과 비소설](lessons/11-B1-4/) | [`b1/`](b1/) |
| 12 | [분위기 점수 붙이기](lessons/12-B1-5/) | [`b1/`](b1/) |
| 13 | [추천 앱 화면 만들기](lessons/13-B1-6/) | [`b1/`](b1/) |
| | **B2 · 벡터 저장소** | |
| 14 | [벡터 저장소 세 가지: FAISS · Chroma · pgvector](lessons/14-B2-1/) | [`b2/`](b2/) |
| 15 | [사전 필터 vs 사후 필터](lessons/15-B2-2/) | [`b2/`](b2/) |
| | **B3 · RAG 기초** | |
| 16 | [RAG 한눈에 보기](lessons/16-B3-1/) | [`b3/`](b3/) |
| 17 | [문서 불러오기: 웹 문서와 PDF](lessons/17-B3-2/) | [`b3/`](b3/) |
| 18 | [청킹: 크기와 오버랩](lessons/18-B3-3/) | [`b3/`](b3/) |
| 19 | [40줄로 RAG 만들기](lessons/19-B3-4/) | [`b3/`](b3/) |
| | **B4 · 프레임워크와 화면** | |
| 20 | [LangChain으로 다시 만들기](lessons/20-B4-1/) | [`b4/`](b4/) |
| 21 | [Streamlit 채팅 화면](lessons/21-B4-2/) | [`b4/`](b4/) |
| | **B5 · 평가** | |
| 22 | [골든셋 만들기: LLM이 쓰고 사람이 검수](lessons/22-B5-1/) | [`b5/`](b5/) · [`k8s/`](k8s/) |
| 23 | [성적표: 키워드 vs 벡터 · 한국어 vs 영어](lessons/23-B5-2/) | [`b5/`](b5/) |
| | **B6 · 검색 개선** | |
| 24 | [하이브리드 검색: 키워드와 벡터 섞기](lessons/24-B6-1/) | [`b6/`](b6/) |
| 25 | [재정렬: 상위 20개를 다시 줄 세우기](lessons/25-B6-2/) | [`b6/`](b6/) |
| 26 | [질의 변환: 여러 질문 · 가상의 답](lessons/26-B6-3/) | [`b6/`](b6/) |
| 27 | [라우팅과 셀프 쿼리](lessons/27-B6-4/) | [`b6/`](b6/) |
| 28 | [맥락 검색 (contextual retrieval)](lessons/28-B6-5/) | [`b6/`](b6/) |
| 29 | [청킹 방법 다섯 가지 · 공정하게 비교하기](lessons/29-B6-6/) | [`b3x/`](b3x/) |
| 30 | [에이전트 청킹 · LLM이 읽고 경계를 정하면](lessons/30-B6-7/) | [`b3x/`](b3x/) |
| | **B7~B9 · 답의 품질과 고급 RAG** | |
| 31 | [근거만 쓰게 하기와 거절](lessons/31-B7-1/) | [`b7/`](b7/) |
| 32 | [LLM 심판: 근거 충실도 채점과 심판 검증](lessons/32-B7-2/) | [`b7/`](b7/) |
| 33 | [LangGraph로 스스로 고치는 RAG (CRAG)](lessons/33-B8-1/) | [`b8/`](b8/) |
| 34 | [Adaptive RAG: 질문의 종류를 보고 길 고르기](lessons/34-B8-2/) | [`b8/`](b8/) |
| 35 | [GraphRAG: 관계를 따라 찾기](lessons/35-B9-1/) | [`b9/`](b9/) |
| 36 | [표와 그림이 든 PDF · 멀티모달 RAG](lessons/36-B9-2/) | [`b9/`](b9/) |
| | **PART C · 벡터의 한계와 다른 길** | |
| 37 | [벡터가 원리상 못 찾는 질문 · LIMIT 축소판](lessons/37-C1-1/) | [`c1/`](c1/) |
| 38 | [긴 자료를 통째로 넣으면? · Lost in the Middle 다시 재기](lessons/38-C1-2/) | [`c1/`](c1/) |
| 39 | ["전부 몇 개?" 집계 질문](lessons/39-C1-3/) | [`c1/`](c1/) |
| 40 | [근거 없는 답 · 환각 재고 줄이기](lessons/40-C1-4/) | [`c1/`](c1/) |
| 41 | [에이전트 검색 · 벡터 대신 grep](lessons/41-C2-1/) | [`c2/`](c2/) |
| 42 | [질문을 SQL로 · 텍스트→SQL](lessons/42-C2-2/) | [`c2/`](c2/) |
| 43 | [한 표로 비교 · 질문마다 길 고르기](lessons/43-C2-3/) | [`c2/`](c2/) |
| | **PART D · 운영** | |
| 44 | [API로 띄우고 · 지연과 비용 재기](lessons/44-D1/) | [`d1/`](d1/) |
| 45 | [권한 필터와 누출 테스트](lessons/45-D2/) | [`d2/`](d2/) |
| 46 | [문서가 바뀌면 · 증분 색인](lessons/46-D3/) | [`d3/`](d3/) |
| 47 | [문서 속의 공격 · 간접 프롬프트 인젝션](lessons/47-D4/) | [`d4/`](d4/) |
| 48 | [로그와 트레이스 · 일어난 일을 나중에 찾기](lessons/48-D5/) | [`d5/`](d5/) |
| 49 | [서비스로 나누기 — API · 저장소 · 캐시](lessons/49-D6/) | [`d6/`](d6/) |
| 50 | [임베딩 모델 교체 — 버전 기록 · 새 색인 · 같은 골든셋 · 별칭 전환](lessons/50-D7/) | [`d7/`](d7/) |
| 51 | [배포 전 자동 검사 — 점수가 떨어지면 배포를 막는다](lessons/51-D8/) | [`d8/`](d8/) |
| 52 | [수집 자동화 — 바뀐 문서를 알아서 색인에](lessons/52-D9/) | [`d9/`](d9/) |
| | **PART E · 실무 사례 해부** | |
| 53 | [사례 · Anthropic 맥락 검색 끝까지 다시 만들기](lessons/53-E1/) | [`e1/`](e1/) |
| 54 | [사례 · Apple Music 다국어 검색 — 어휘 색인에 임베딩 더하기](lessons/54-E2/) | [`e2/`](e2/) |
| 55 | [사례 · LinkedIn 고객 지원 지식 그래프 — 우리 문서에서도 될까](lessons/55-E3/) | [`e3/`](e3/) |
| 56 | [사례 · Uber QueryGPT — 표가 많을 때 텍스트→SQL](lessons/56-E4/) | [`e4/`](e4/) |
| 57 | [현업 사례 · 사내 지식 챗봇 — '전부 알려줘'에는 다른 길](lessons/57-E5/) | [`e5/`](e5/) |
| 58 | [현업 사례 · 실시간 추천 — 방금 누른 것까지](lessons/58-E6/) | [`e6/`](e6/) |
| | **최종 미션** | |
| 59 | [최종 미션 — 지원서에 넣을 RAG 평가 리포트](lessons/59-M1/) | [`mission/`](mission/) |
| | **F · 통합 프로젝트 (업데이트 예정)** | |
| 60 | [통합 프로젝트 미리보기 — 전·월세 상담 챗봇 설계 (업데이트 예정)](lessons/60-F0/) | — |
## 데이터와 라이선스
- 코드: [MIT](LICENSE)
- 데이터는 원래 라이선스를 따릅니다. 출처와 조건은 [`DATA_LICENSES.md`](DATA_LICENSES.md)에 정리했습니다. 쿠버네티스 문서(CC BY 4.0), 한국어 위키백과에서 정리한 도서 목록(CC BY-SA 4.0), MIRACL 한국어(Apache 2.0 + 위키백과 CC BY-SA), Chinook(MIT), 공공누리 제1유형 PDF, 미국 연방정부 저작물 PDF.
