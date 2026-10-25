#!/usr/bin/env bash
# 깃허브에 올리지 않은 벡터 파일(*.npy)을 한 번에 만든다. LLM은 부르지 않는다(비용 0).
# 저장소 맨 위 폴더에서:  bash tools/make_vectors.sh
# 필요한 수업에서 각 파일을 따로 만들어도 된다 (README의 표 참고).
set -euo pipefail
uv run python b2/embed_books.py    # books/book_vecs.npy      (A2·B2·B6·B9·C1)
uv run python b3/index.py          # k8s/index.npy            (B3)
uv run python b3/compare.py        # k8s/vecs_200·500·1500.npy (B3)
uv run python b5/evaluate.py       # k8s/vecs_ko_500·en_500.npy (B5 이후 거의 모든 수업)
uv run python d9/setup.py          # d9/docs · index.json · vecs.npy (D9)
uv run python tools/miracl_vectors.py  # vectors/docs_ko·queries_ko.npy (A5·A6, 가장 오래 걸림)
echo "벡터 파일 준비 완료"
