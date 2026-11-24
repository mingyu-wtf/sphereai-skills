---
name: longform-free-7-edit
description: 이미지·나레이션·대본으로 리모션이 자동 편집(느린 확대·자막)해 영상을 만들 때 사용. '가편집 만들어줘', '자막 입혀줘', '영상 조립' 요청.
---

# [무료] 가편집·자막·렌더

## 필요한 것
- images/, narration.mp3
- ffmpeg
- 비용: 없음

## 방식 A (기본): 리모션 최소판 — 이미지 + 자막 + 나레이션
리모션이 이미지를 나레이션 길이에 맞춰 천천히 확대/이동시키고 자막을 입혀 한 번에 렌더한다. 이 스킬에 들어 있는 **새 최소 템플릿**(`remotion_template/`)만 쓴다(특정 채널의 디자인·브랜딩 없음).

1. 준비물(작업 폴더): `images/C001.jpg…`(번호순), `script.txt`(블록은 빈 줄로 구분), `narration/narration.mp3`, `narration/timing.json`(나레이션 스킬 결과).
2. `python auto_edit.py --images-only` — 타임라인만 만들고 설치·용량을 알려 준다(아무것도 설치하지 않음). 사용자에게 알린다: Node.js 18+ 필요, 첫 설치에 수백 MB(무료).
3. 사용자 OK 후 `python auto_edit.py --images-only --yes` → `final.mp4`. 경로가 깊으면(윈도우 260자 한도) 스크립트가 알려 주니 `--work C:\lf_edit` 처럼 짧은 폴더를 지정한다.
4. 하는 일: 블록 길이를 이미지 수로 나눠 컷 길이 결정 · 줌인/줌아웃/좌우 이동 순환(1.00↔1.10배, 이지 적용) · 블록 대본을 24자 한 줄 자막(흰 글씨+검은 외곽선)으로 시간 배분 · 나레이션.
5. 한글 폰트가 있는 PC 필요(Windows 맑은 고딕, Mac 애플 SD 산돌고딕 기본 포함).

## 방식 B (Node 가 없을 때): ffmpeg 가편집
`python simple_draft.py images narration/narration.mp3 draft.mp4` — 확대만 하는 단순 가편집(자막 없음). 자막은 편집 프로그램에서 대본을 붙여 넣어 입힌다.

## 다음 스킬 (끝나면 묻지 말고 바로 이어서 실행)
`longform-free-8-finish`

---
*Pro판에서는 이 단계의 검사·검수·재시도가 자동으로 처리됩니다.*

---
만든이: sphereai.work (https://sphereai.work)
