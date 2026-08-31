# 실행 기록

`run.sh` 가 매 실행마다 여기에 한 파일을 쓴다. **명세는 `../testcase.md` 에 있고, 결과는 여기에만 있다.**

```
<backend>-<UTC timestamp>.tsv     한 번의 실행
latest-<backend>.tsv              그 백엔드의 가장 최근 실행 (심볼릭 링크)
```

파일 앞머리의 `#` 줄이 그 실행의 환경이다 — 백엔드, 두 노드, 이미지, **저장소 커밋**, 커널 버전.
결과는 이 환경과 함께 읽어야 의미가 있다. 본문은 `case / status / detail` 세 칸이고
status 는 `PASS` / `FAIL` / `SKIP` 이다.

기본적으로 커밋하지 않는다(환경마다 달라지므로). 남길 만한 실행은 `git add -f` 로 넣는다.

```bash
column -t -s $'\t' latest-en.tsv        # 보기
awk -F'\t' '$2=="FAIL"' latest-en.tsv   # 실패만
```
