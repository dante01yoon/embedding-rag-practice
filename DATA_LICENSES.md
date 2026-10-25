# 데이터 출처와 라이선스

코드는 MIT입니다. 아래 데이터 파일은 각 원본의 라이선스를 따릅니다. 고쳐서 다시 배포할 때도 같은 조건(출처 표시 · 같은 조건 변경 허락)을 지켜 주세요.

| 파일 | 출처 | 라이선스 |
|---|---|---|
| `k8s/ko/`, `k8s/en/` (문서 원문), `k8s/docs_ko.json`, `k8s/docs_en.json`, `k8s/chunks.json` | Kubernetes 공식 문서 [kubernetes/website](https://github.com/kubernetes/website) `content/{ko,en}/docs/concepts` (commit bc7f3479, 2026-10-22) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) (`k8s/LICENSE`) |
| `k8s/qa_*.json*`, `k8s/ctx_ko.json`, `d9/` 실습 문서 | 위 쿠버네티스 문서를 바탕으로 만든 질문 · 맥락 문장 | CC BY 4.0 (원문 출처: Kubernetes 문서) |
| `books/books_ko_raw.csv` 및 `books/books_clean.csv`, `books_kind.csv`, `books_mood.csv`, `tagged_description.txt`, `queries_e2.json`, `e5/gold_hugo.json` | 한국어 위키백과의 책 문서(각 행의 `url`이 원문)를 정리 · 가공 | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) (같은 조건으로만 재배포) |
| `a4/miracl_ko/`, `vectors/docids_ko.json`, `vectors/queries_ko.tsv`, `vectors/qrels_ko.tsv` | [MIRACL](https://huggingface.co/datasets/miracl/miracl) (Zhang et al., 2023) 한국어 dev 질문 100개 · 판정 + 위키백과 문단 32,651개 | 질문 · 판정: [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0) · 문단: 위키백과 [CC BY-SA](https://creativecommons.org/licenses/by-sa/4.0/) |
| `chinook/chinook.sqlite` | [Chinook Database](https://github.com/lerocha/chinook-database) © 2008-2024 Luis Rocha | MIT (`chinook/LICENSE.md`) |
| `pdf/kogl_guide.pdf` | 공공저작물 저작권 관리 및 이용지침 해설서(2026), 한국문화정보원 — https://www.kogl.or.kr/edu/eduDataView.do?dataIdx=178 | [공공누리 제1유형](https://www.kogl.or.kr/info/licenseType1.do) (출처표시) |
| `pdf/irs_p501.pdf` | IRS Publication 501 (2025) — https://www.irs.gov/pub/irs-pdf/p501.pdf | 미국 연방정부 저작물 (17 U.S.C. §105, 퍼블릭 도메인) |
| `*/llm_cache_*.json` | 위 자료로 만든 프롬프트와 그에 대한 LLM 답(강의 녹화 때 기록) | 프롬프트 속 자료는 해당 원본 라이선스를 따릅니다 |
| `a1/news.txt`, `a3/sentences_*.txt`, `a4/docs_ko.txt`, `d2`·`d4`·`c1`의 "점검 암호" 같은 연습용 문장 | 강의용으로 직접 쓴 문장 (점검 암호 등은 지어낸 연습용 값) | MIT (코드와 같음) |

## 넣지 않은 데이터
- 영어 도서 목록(`books_en_raw.csv`): 실습 코드에서 쓰지 않고, 소개 글의 재배포 조건이 분명하지 않아 넣지 않았습니다.
- 벡터 · 벡터 DB 파일: 용량이 커서 넣지 않았습니다. 만드는 법은 [README](README.md#벡터-파일-만들기)에 있습니다.
