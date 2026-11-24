# 스레드 화면 조작 절차 (브라우저 자동화 공통)

스레드는 공식 게시 API를 개인 계정에 쉽게 열어 주지 않기 때문에, **이미 로그인된 내 브라우저**를 자동화 도구로 움직여서 올린다. 도구는 무엇이든 된다.

| 도구 | 쓰는 법 |
|---|---|
| Claude in Chrome (크롬 확장) | 아래 순서를 화면 보며 클릭·입력. 단축키(Shift+Enter, Ctrl+Enter)는 키 입력 도구로 |
| Playwright MCP / Playwright 스크립트 | 아래 코드 조각을 그대로 응용 |
| 그 밖의 "로그인된 브라우저 프로필을 코드로 다루는" 도구 | Playwright 문법이면 그대로, 아니면 같은 순서로 |

공통 원칙
- **항상 새 탭**에서 작업하고 끝나면 닫는다. 사용자가 쓰던 탭은 건드리지 않는다.
- 로그인이 풀려 있으면 **대신 로그인하지 않는다**(비밀번호 입력 금지). 실패로 기록하고 멈춘다.
- 한 번의 도구 호출은 2분 안에 끝나게 잘게 나눈다(답글 2~3개, 팔로우 3~4명씩).
- **눌렀다고 끝난 게 아니다.** 새로고침해서 실제로 붙었는지 본 뒤에만 기록한다.

## 0. 로그인 계정 확인
1. `https://www.threads.com/` 열기.
2. 왼쪽 메뉴의 프로필 링크(`a[href^="/@"]`)가 config.json의 `handle`과 같은지 확인.
3. 다르면 `python scripts/mark.py slot <slot> failed "로그인 계정 다름"` 하고 멈춘다.

## 1. 본 글(1/2) 올리기
1. "새로운 스레드" 버튼 클릭.
   - 버튼이 두 개 잡혀 **작성창(dialog)이 2개** 뜰 수 있다. `[role="dialog"]` 개수를 세서 2개면 빈 쪽을 "취소"로 닫는다.
2. dialog 안 `[contenteditable="true"]` 클릭 → 줄마다 글자 입력, 줄바꿈은 **Shift+Enter**(빈 줄은 두 번). Enter만 누르면 게시될 수 있다.
3. dialog의 innerText로 입력이 원문과 같은지 확인.
4. **게시 버튼은 이름이 정확히 "게시"인 것만** 누른다. "게시물 인용", "게시물 옵션"과 이름이 겹쳐서 부분 일치로 찾으면 엉뚱한 버튼을 누른다(빈 인용 창이 열리고 원래 글은 안 올라감).
5. 4초 이상 기다린 뒤 내 프로필(`https://www.threads.com/@<내 핸들>`)을 연다. 맨 위 글이 **고정글일 수 있으니** 본문 첫 줄로 방금 글인지 확인하고 글 주소(`/post/...`)를 얻는다.
6. 안 올라갔으면 **1회만** 다시 시도. 그래도 안 되면 실패로 기록(중복 게시가 더 위험하다).

## 2. 2/2(신청하는 법·링크 칸) 달기
타래("스레드에 추가")로 한 번에 올리면 **마지막 칸이 빠진 채 올라가는 일이 있다.** 그래서 1/2를 먼저 올리고, 그 글에 내 답글로 2/2를 단다.
1. 방금 올린 글 페이지를 연다.
2. 답글 입력창 클릭 → 2/2 입력(줄바꿈 Shift+Enter).
3. **Ctrl+Enter로 제출**한다. "답글" 버튼은 이름이 같은 버튼이 여러 개라 잘못 누르기 쉽다.
4. 새로고침 후 2/2 첫 줄이 보이는지 확인. 같은 답글이 2개 붙었으면 하나를 더보기(⋯) → 삭제.

## 3. 남의 글에 하트 + 답글
1. 글 페이지를 연다(검색 결과에서 바로 달지 않는다).
2. 하트는 **본문 영역 안의 첫 "좋아요" 버튼**. 왼쪽 메뉴에도 "좋아요"가 있어서 페이지 전체에서 찾으면 메뉴를 누른다. 눌린 상태는 "좋아요 취소".
3. 답글 입력창 클릭 → 입력 → Ctrl+Enter.
4. 원글 새로고침 또는 내 프로필 "답글" 탭(`/@<내 핸들>/replies`) 맨 위에서 확인한 뒤 기록.

## 4. 팔로우
1. 상대 프로필을 연다 → 최근 글 하나에 하트.
2. 이름이 정확히 "팔로우"인 버튼 클릭 → "팔로잉"으로 바뀌었는지 확인. 이미 "팔로잉"이면 건너뜀.

## 5. 인용(리포스트 + 내 생각)
1. 글의 "리포스트" 버튼 → 메뉴에서 "인용".
2. 작성창에 내 생각 1~3줄 입력 → "게시"(정확히 일치) → 내 프로필에서 확인.
3. "인용" 메뉴가 계속 안 열리면(시간 초과) 그 글은 포기하고 넘어간다. 같은 동작을 연타하지 않는다.

## Playwright 문법 예시 (도구가 Playwright 계열일 때)
```js
// page = 새 탭. 아래는 1/2 게시 예시
await page.goto('https://www.threads.com/');
const me = await page.locator('a[href^="/@"]').first().getAttribute('href');   // "/@<내 핸들>" 인지 확인
await page.getByRole('button', { name: '새로운 스레드' }).first().click();
const dialogs = page.locator('[role="dialog"]');
// dialogs.count() 가 2면 빈 쪽 취소
const box = dialogs.last().locator('[contenteditable="true"]').first();
await box.click();
for (const [i, line] of lines.entries()) {          // lines = 1/2 본문을 줄로 나눈 배열
  if (line) await page.keyboard.insertText(line);
  if (i < lines.length - 1) await page.keyboard.press('Shift+Enter');
}
const typed = await dialogs.last().innerText();       // 원문과 비교
await dialogs.last().getByRole('button', { name: '게시', exact: true }).click();
await new Promise(r => setTimeout(r, 4000));          // 도구에 따라 waitForTimeout이 없을 수 있음

// 2/2: 글 페이지에서
await page.goto(postUrl);
await page.getByRole('textbox').first().click();
// 줄마다 insertText + Shift+Enter 후
await page.keyboard.press('Control+Enter');
```
- 사람 사이·동작 사이에 20~40초 쉰다(`seconds_between_people`). 한 번에 몰아서 하지 않는다.
- 셀렉터는 스레드 화면이 바뀌면 달라질 수 있다. 버튼을 못 찾으면 화면을 다시 읽고(접근성 트리·스냅샷) 이름으로 찾는다. 추측으로 좌표를 누르지 않는다.
