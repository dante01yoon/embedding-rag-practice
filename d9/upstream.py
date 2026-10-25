"""오늘 바뀐 문서 (연습용): 동기화 도구가 원래 수정 시각을 그대로 둔 채 내용을 바꾼 문서, 새 문서, 지운 문서"""
import os

f = "d9/docs/configuration__configmap.md"
st = os.stat(f)
text = open(f).read().replace("1MiB를 초과할 수 없다", "2MiB를 초과할 수 없다")
open(f, "w").write(text)
os.utime(f, (st.st_atime, st.st_mtime))  # 내용은 바뀌었는데 수정 시각은 어제 그대로
open("d9/docs/notice__maintenance.md", "w").write("# 점검 공지\n\n[연습용 공지] 다음 클러스터 정기 점검은 11월 4일 화요일 새벽 2시에 진행한다. 점검 중에는 새 파드를 배포할 수 없다.")
os.remove("d9/docs/architecture__cgroups.md")
print("바뀐 문서: 컨피그맵(시각 그대로) · 새 문서: 점검 공지 · 지운 문서: cgroups")
