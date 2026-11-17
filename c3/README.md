# C3 · 문서가 수십만 개일 때 — 자료 받기와 폴더 안내

수업 61~66(C3)은 한국어 위키백과 문서 묶음에서 실습합니다. 문서 묶음은 용량이 커서 저장소에 넣지 않고 GitHub 릴리스에 올려 두었습니다. 이 안내대로 한 번만 받아 두면 여섯 수업을 모두 따라올 수 있습니다.

모든 명령은 **저장소 맨 위 폴더에서** 실행합니다.

## 무엇을 받나

| 묶음 | 파일 | 크기 | 필요한가 |
|---|---|---|---|
| 1만 개 | [`wiki-10k.tar.gz`](https://github.com/dante01yoon/embedding-rag-practice/releases/download/c3-data-v1/wiki-10k.tar.gz) | 내려받기 약 12MB · 풀면 약 55MB | **필수.** 이것만 받아도 여섯 수업을 따라올 수 있습니다. |
| 10만 개 | [`wiki-100k.tar.gz`](https://github.com/dante01yoon/embedding-rag-practice/releases/download/c3-data-v1/wiki-100k.tar.gz) | 내려받기 약 91MB · 풀면 약 440MB | 선택. 문서가 늘 때 시간이 어떻게 달라지는지 직접 재 보고 싶을 때 받습니다. |
| 약 65만 개(전체) | 없음 | — | 받지 않습니다. 전체 묶음은 수업에서 강사 화면으로만 봅니다. |

- 작은 묶음은 큰 묶음 안에 그대로 들어 있습니다(1만 ⊂ 10만 ⊂ 전체). 질문 21개의 근거 문서는 세 묶음 모두에 들어 있습니다.
- 문서 하나가 텍스트 파일 하나입니다. 파일 이름 앞의 `w000785` 같은 번호가 문서 번호입니다.
- `wiki-10k.tar.gz`에는 문서 목록 `wiki/docs.db`(SQLite, 문서 번호 · 경로 · 제목 10만 줄)가 함께 들어 있습니다. 10만 개 묶음도 이 파일을 같이 씁니다.

## 받아서 풀기

```bash
curl -L -O https://github.com/dante01yoon/embedding-rag-practice/releases/download/c3-data-v1/wiki-10k.tar.gz
tar -xzf wiki-10k.tar.gz
```

풀고 나면 저장소 맨 위에 이렇게 생깁니다.

```text
wiki/
  10k/000/w000122_김영환_1955년.txt …   문서 10,000개 (폴더 999개에 나뉘어 있음)
  docs.db                                문서 목록
```

10만 개 묶음도 받는다면 같은 자리에서 풉니다(`wiki/100k/`가 생깁니다).

```bash
curl -L -O https://github.com/dante01yoon/embedding-rag-practice/releases/download/c3-data-v1/wiki-100k.tar.gz
tar -xzf wiki-100k.tar.gz
```

`wiki/`는 `.gitignore`에 들어 있어 깃에 올라가지 않습니다. 다 풀었으면 `.tar.gz` 파일은 지워도 됩니다.

## 사전 점검 (API 키 없이 됩니다)

① `rg`(ripgrep)가 설치돼 있는지 확인합니다. 이 챕터에서 글자를 찾는 명령은 모두 `rg`입니다.

```bash
rg --version
```

없다면 설치합니다. macOS `brew install ripgrep` · Ubuntu/WSL2 `sudo apt install ripgrep` · Windows `winget install BurntSushi.ripgrep.MSVC` (그 밖의 방법: https://github.com/BurntSushi/ripgrep#installation)

② 문서 묶음이 제자리에 있는지 확인합니다.

```bash
uv run python c3/bench.py 서울
uv run python c3/find0.py 서울 | head -5
uv run python c3/show.py A
```

- `bench.py`는 받은 묶음만 잽니다. 1만 개만 받았다면 `1만` 칸 하나에 `716개`가 나옵니다(시간은 기기마다 다릅니다).
- `find0.py`는 첫 줄에 `상태: truncated`, 둘째 줄에 `문서 716개 중 20개`가 나옵니다.
- `show.py`는 강사의 실행 기록을 다시 보여 줍니다. 모델을 부르지 않습니다.

③ 색인에 쓰는 SQLite FTS5가 되는지 확인합니다.

```bash
uv run python -c "import sqlite3; sqlite3.connect(':memory:').execute('create virtual table t using fts5(x)'); print('FTS5 준비 완료')"
```

## 색인 만들기

pull 만들기 수업(64)부터는 BM25 색인이 필요합니다. 받은 묶음마다 한 번씩 만듭니다. 모델을 부르지 않으니 비용은 들지 않습니다.

```bash
uv run python c3/build_index.py 10k
```

- 색인은 `wiki/docs.db` 안에 `fts_10k` 표로 저장됩니다. 1만 개 묶음은 10초쯤 걸립니다.
- 10만 개 묶음을 받았다면 `uv run python c3/build_index.py 100k`도 실행합니다(강사 기기에서 75초).
- 색인을 만들기 전에 `pull`이나 `search`를 부르면 `no such table: fts_10k` 오류가 납니다.
- `wiki-10k.tar.gz`를 다시 풀면 `docs.db`가 새 파일로 바뀌어 색인이 사라집니다. 그때는 색인을 다시 만듭니다.

## API 키가 필요한 명령과 비용

| 명령 | 키 | 비용 |
|---|---|---|
| `bench.py` · `find0.py` · `build_index.py` · `try_tools.py` | 필요 없음 | 0 (모델을 부르지 않음) |
| `show.py` · `report.py` | 필요 없음 | 0 (강사의 기록만 다시 봄) |
| `agent.py` · `router.py` · `pull_k.py` | **OpenRouter 키 필요** | 질문 하나에 약 0.001~0.04달러 |
| `measure.py` · `judge.py` · `extra.py` · `oneshot.py` | **OpenRouter 키 필요** | 강사 기록으로 `measure.py` 315회 2.38달러, `extra.py` · `oneshot.py` 223회 1.35달러(`judge.py` 비용은 기록에 없음) |

- 키는 저장소 맨 위의 `.env`에 넣습니다([API 키와 모델](../README.md#api-키와-모델)). 비용은 강사가 기본 모델(`anthropic/claude-haiku-5.5`)로 돌린 기록의 값이고, 실행마다 조금씩 다릅니다.
- 이 챕터의 에이전트 실행은 측정용이라 LLM 답 캐시를 쓰지 않습니다. 같은 질문을 다시 돌리면 비용이 다시 듭니다.
- `agent.py` · `router.py` · `pull_k.py`에는 받은 묶음 이름(`10k` 또는 `100k`)을 적습니다. `router.py`와 `pull_k.py`는 이름을 빼면 전체 묶음(`all`)을 찾습니다.
- 강사의 실행 기록과 채점 결과가 저장소에 들어 있어서, 성적표와 실행 과정은 키 없이 `report.py`와 `show.py`로 볼 수 있습니다.

## 폴더 안내

| 파일 | 설명 | 수업 |
|---|---|---|
| `show.py` | 강사의 실행 기록을 도구 호출 한 줄씩 다시 보기. 이름: `A` · `raw` · `pull` · `miss` · `h04` | 61 · 63 · 64 · 65 |
| `logs/` | 「검색만」 실행 로그 둘(검색어마다 돌려받은 발췌 포함). 논문 읽기 수업의 과제 자료 | 61 |
| `make_logs.py` | 위 로그를 만든 코드(읽기용. 전체 묶음과 10만 개 묶음의 색인이 있어야 실행됩니다) | 61 |
| `bench.py` | 묶음마다 찾기 한 번의 시간과 파일 수를 재는 표. 첫 인자가 폴더면 그 폴더 하나만 잽니다 | 62 · 66 |
| `find0.py` | 첫 줄에 상태를 적어 돌려주는 find 첫 판 | 62 |
| `tools.py` | 문서 번호로 움직이는 도구 넷(`search` · `find` · `read` · `pull`)의 완성본 | 63 · 64 · 65 |
| `agent.py` | 질문 하나를 세 방식(`search` · `raw` · `pull`) 가운데 하나로 푸는 에이전트 완성본 | 63 · 64 · 65 |
| `steps/3/` · `steps/4/` | 수업 63 · 64를 마친 시점의 `tools.py` · `agent.py`(아래 설명) | 63 · 64 |
| `try_tools.py` | 모델 없이 도구만 직접 불러 보기 | 63 · 64 |
| `build_index.py` | 묶음 하나의 BM25 색인을 SQLite FTS5로 만들기 | 64 |
| `pull_k.py` | pull이 한 번에 가져오는 문서 수를 고정하고 질문 하나 풀기 | 64 |
| `measure.py` · `judge.py` | 전체 실측과 LLM 심판 채점 | 65 |
| `report.py` · `REPORT.md` | 성적표를 만드는 코드와 그 전체 출력 | 65 · 66 |
| `router.py` | 한 번에 답하기 → 끌어와서 뒤지기로 넘기는 라우터 | 66 |
| `extra.py` · `oneshot.py` | 보조 실험(끌어오는 개수 고정 · 라우터 · 한 번에 답하기)을 돌린 코드 | 64 · 66 |
| `questions.json` | 질문 21개(쉬운 10 · 어려운 8 · 자료에 없음 3), 정답, 근거 문장, 근거 문서 번호 | 전체 |
| `results.jsonl` · `judged.jsonl` · `extra.jsonl` · `runs/` · `config.json` | 강사의 실행 기록, 심판 판정, 실행 조건 | 전체 |
| `build_sets.py` · `questions_src.json` | 전체 문서에서 세 묶음과 `docs.db`를 만든 코드와 그 입력(읽기용) | — |

### `steps/`: 수업 단계별 코드

수업 63과 64에서는 `tools.py`와 `agent.py`를 조금씩 키워 갑니다. 그 수업을 마친 시점의 코드를 따로 넣어 두었습니다.

- [`steps/3/`](steps/3/): 수업 63을 마친 코드. 도구는 `find` · `read` 둘이고, 에이전트는 문서 묶음 전체를 직접 뒤집니다.
- [`steps/4/`](steps/4/): 수업 64를 마친 코드. `pull`과 작업 폴더가 더해지고, 에이전트가 `raw` · `pull` 두 방식을 고릅니다.
- `c3/` 바로 아래의 `tools.py` · `agent.py`가 수업 65에서 `search`까지 더한 완성본입니다.

`steps/`는 영상을 따라 입력한 코드와 견주어 보는 용도입니다. 수업 안내의 실행 명령은 모두 완성본(`c3/tools.py` · `c3/agent.py`)을 씁니다.

### 실행하면 생기는 것

- `c3/ws/`: pull 방식의 작업 폴더입니다. 끌어온 문서가 하드 링크로 들어오고, `try_tools.py`로 연습한 뒤에도 남아 있습니다. 통째로 지워도 됩니다(`.gitignore`에 들어 있습니다).
- `c3/runs/`: 에이전트가 질문 하나를 풀 때마다 실행 기록 파일이 하나씩 더해집니다(`agent.py`를 직접 실행할 때, `pull_k.py`를 실행할 때, `router.py`가 끌어와서 뒤지기로 넘길 때).

## 출처와 라이선스

- 문서 묶음은 **한국어 위키백과 2023년 11월 1일 덤프**에서 만들었습니다. Hugging Face [`wikimedia/wikipedia`](https://huggingface.co/datasets/wikimedia/wikipedia) 데이터셋의 `20231101.ko`(문서 647,897개)를 문서 하나당 텍스트 파일 하나로 저장하고, 그 가운데 1만 개와 10만 개를 골랐습니다.
- 라이선스는 [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)입니다. 고쳐서 다시 배포할 때도 출처를 밝히고 같은 조건을 지켜야 합니다.
- 각 파일의 첫 줄이 문서 제목입니다. 원문 주소는 `https://ko.wikipedia.org/wiki/` 뒤에 그 제목을 붙이면 됩니다(예: 첫 줄이 `넋업샨`이면 https://ko.wikipedia.org/wiki/넋업샨). 덤프 이후에 고쳐진 문서는 지금의 내용과 다를 수 있습니다.
- `c3/questions.json` · `c3/logs/` · `c3/runs/`의 질문, 근거 문장, 발췌도 이 문서들에서 나온 것이라 같은 라이선스를 따릅니다. 전체 정리는 [`DATA_LICENSES.md`](../DATA_LICENSES.md)에 있습니다.

---
수업 안내: [61](../lessons/61-C3-1/) · [62](../lessons/62-C3-2/) · [63](../lessons/63-C3-3/) · [64](../lessons/64-C3-4/) · [65](../lessons/65-C3-5/) · [66](../lessons/66-C3-6/) · [저장소 처음으로](../README.md)
