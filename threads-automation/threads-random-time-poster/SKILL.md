---
name: threads-random-time-poster
description: (기본판) 스레드 글을 정각이 아닌 무작위 시각에 알아서 올리는 러너. 10분마다 할 일만 확인하고 없으면 Claude를 부르지 않아 토큰이 거의 안 든다. 윈도우 작업 스케줄러·cron 등록, 1/2 본문 + 2/2 답글 게시 절차 포함. Threads random-time auto poster.
---

# 스레드 무작위 시각 예약 게시 러너

대기열(`data/queue.json`)에 쌓인 글을 하루 몇 번, **매일 다른 무작위 시각**에 올리고 소통 회차·소재 조사 회차도 같이 돌린다. 게시는 받은 사람의 **로그인된 브라우저**를 자동화 도구(Claude in Chrome, Playwright 등)로 움직여서 한다.

시작 안내 스킬 `threads-coupang-start-here`의 1~3단계(계정 준비, 작업 폴더, 대기열 첫 글)를 먼저 끝낸 뒤 쓴다.

## 들어 있는 것
| 파일 | 하는 일 |
|---|---|
| `scripts/due.py` | 오늘 계획을 무작위 시각으로 만들고(하루 한 번), 지금 할 일만 JSON으로 출력. 없으면 `[]` |
| `scripts/mark.py` | 슬롯 완료·실패, 대기열 상태, 소통 기록, 오늘 건수·남은 한도, 제한 경고 시 중단 |
| `scripts/run.ps1` / `scripts/run.sh` | 스케줄러가 부르는 러너. 할 일이 있을 때만 `claude -p` 실행, 잠금 파일로 겹침 방지 |
| `scripts/config.example.json` | 설정 예시(시각, 한도, 키워드, 경로, 허용 도구) |
| `scripts/queue.example.json` | 대기열 형식 |
| `references/prompt_template.md` | 자동 실행 때 Claude가 받는 운영 프롬프트 틀 |
| `references/browser_steps.md` | 스레드 화면 조작 절차와 함정(게시 버튼 오매칭, 작성창 2개, 타래 누락 등) |

## 설치 (한 번)
1. 작업 폴더를 만든다. 예: `threads-ops/`
   ```
   threads-ops/
     config.json          <- scripts/config.example.json 복사 후 고침
     prompt.md            <- references/prompt_template.md 복사 후 <...> 고침
     references/browser_steps.md
     scripts/  due.py mark.py run.ps1 run.sh
               report_history.py(threads-daily-report 스킬에서)
     data/queue.json      <- scripts/queue.example.json 참고
   ```
2. `config.json`에서 꼭 고칠 것: `handle`, `display_name`, `channel_intro`, `browser.tool`, `claude_allowed_tools`(쓰는 브라우저 도구의 MCP 이름. 예: `mcp__claude-in-chrome__*`, `mcp__playwright__*`), 처음 쓰는 날짜로 `limits.ramps.*.start_date`.
3. 시험: 작업 폴더에서 `python scripts/due.py --show` → 오늘 계획이 무작위 시각으로 찍히는지 본다. `python scripts/mark.py targets` → 한도가 보이는지 본다.
4. **첫 이틀은 대화 세션에서 손으로** 돌린다: "지금 할 일" JSON을 직접 붙여 prompt.md대로 한 회차씩 시키고, 회차당 걸린 시간·도구 호출 수를 본다. 문제가 없을 때만 스케줄러를 건다.

## 스케줄러 등록
- 브라우저가 켜져 있고 스레드에 로그인돼 있어야 한다(PC 절전·로그아웃 상태면 실패로 기록되고 끝난다).
- `claude` 명령이 터미널에서 로그인된 상태여야 한다.

**Windows 작업 스케줄러** (10분마다, 관리자 권한 불필요):
```
schtasks /Create /SC MINUTE /MO 10 /TN "ThreadsOps" /TR "powershell -NoProfile -ExecutionPolicy Bypass -File \"<작업 폴더 전체 경로>\scripts\run.ps1\""
```
끄기: `schtasks /Change /TN "ThreadsOps" /DISABLE`, 지우기: `schtasks /Delete /TN "ThreadsOps" /F`.
**macOS·Linux cron** (`crontab -e`):
```
*/10 * * * * /bin/bash "<작업 폴더 전체 경로>/scripts/run.sh"
```
cron에서 `claude`·`python3`를 못 찾으면 run.sh 맨 위에 `export PATH=...`를 넣는다.

## 하루가 돌아가는 방식
- 08:30 이전·23:30 이후에는 아무것도 하지 않는다(`active_hours`).
- 그날 첫 호출 때 계획 파일 `plan/plan_YYYYMMDD.json`을 만든다: 글 슬롯마다 기준 시각에서 -15~+40분 무작위, 글 사이 최소 130분, 소통 회차 -10~+25분, 소재 조사 1회.
- 슬롯 시각이 되면 2시간 창 안에서 한 번 실행된다. 창이 지나면 `skipped`(밀린 글을 몰아 올리지 않는다).
- 한 번에 최대 2건. 대기열이 비면 글 슬롯은 기다리고, 대기열이 `queue_min`보다 적을 때만 조사 회차가 돈다.

## 게시 규칙 (prompt.md에 들어 있음)
- 대기열 항목이 "대기"가 아니면 올리지 않는다(중복 게시 방지).
- 올리기 직전 `verify_before_post`의 공식 페이지로 금액·기간을 다시 대조. 안 맞으면 보류.
- 1/2를 먼저 올리고, 내 글에 답글로 2/2를 단다. 타래 한 번에 올리기는 마지막 칸이 빠지는 일이 있어서 쓰지 않는다.
- 게시 후 프로필을 새로고침해서 실제로 올라갔는지 본 뒤에만 `게시됨`으로 기록. 재시도는 1번만.
- 제한·경고 화면이 뜨면 즉시 `mark.py stop` → 그날은 더 하지 않는다.

## 출력
설치 점검 결과(오늘 계획, 한도), 스케줄러 등록 명령, 첫 회차 기록.

---
만든이: sphereai.work (https://sphereai.work)
