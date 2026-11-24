# 스레드 밤 성과 정리 프롬프트 (작업 폴더에 report_prompt.md로 복사)

> 매일 밤 1번 실행(예: 22:00). 스케줄러 등록 예:
> Windows: `schtasks /Create /SC DAILY /ST 22:00 /TN "ThreadsReport" /TR "powershell -NoProfile -ExecutionPolicy Bypass -Command \"cd '<작업 폴더>'; Get-Content -Raw -Encoding utf8 report_prompt.md | claude -p --allowedTools Bash Read Write Glob <브라우저 도구 이름>\""`
> cron: `0 22 * * * cd "<작업 폴더>" && claude -p --allowedTools Bash Read Write Glob "<브라우저 도구 이름>" < report_prompt.md`

계정 주인이 맡긴 **읽기·정리 전용** 작업이다. 묻지 말고 처리한다. **게시·답글·팔로우·인용·삭제는 하지 않는다.** 결과 문서는 한국어.

## 할 일
1. 로컬 집계: `python scripts/report_history.py collect`
2. 측정(브라우저, 새 탭, 읽기만):
   - `https://www.threads.com/@<내 핸들>` → 로그인 계정이 맞는지 확인(아니면 "로그인 계정 다름, 측정 못 함"만 쓰고 끝). 팔로워 수.
   - 오늘 올린 글(collect의 posted_today)마다 글 상세를 열어 조회수·좋아요·댓글·리포스트. 못 읽으면 null("미확인").
   - 가능하면 인사이트(`https://www.threads.com/insights`)에서 최근 조회수 합계.
3. 저장: `python scripts/report_history.py save --json '<측정값>'` → 어제 대비 증감.
4. `logs/reports/report_YYYYMMDD.md`에 쓴다(짧게, 표 위주):
   - 팔로워 N명(어제 대비 ±), 최근 조회수 합계(±)
   - 오늘 올린 글 표(시각·제목·조회·좋아요·댓글·리포스트) + 가장 잘 나온 글 1개와 그 이유 한 줄
   - 활동 수(한도 대비): 글, 답글, 감사, 선팔, 일상 인사, 인용, 내 글 댓글 답
   - 이상 징후: 실패·건너뛴 슬롯, 제한 경고, 보류된 글, 대기열 잔량 3개 이하
   - 제안은 최대 1줄(근거 있는 것만)
5. (선택) 노션·구글 문서 같은 곳에도 남기고 싶으면 그 도구로 **맨 아래에 이어 붙인다**(기존 내용 덮어쓰기 금지). 실패하면 로컬 파일만 남기고 마지막 줄에 "외부 기록 실패: 이유".

## 규칙
- 지어낸 수치 금지. 못 읽은 값은 "미확인".
- 새 탭은 끝나면 닫는다.
- 주인만 보는 내부 문서라 운영 용어를 써도 된다.
