---
name: longform-free-4-narration
description: 대본(script.txt)을 무료 엣지 TTS로 읽어 나레이션 mp3를 만들 때 사용. '나레이션 만들어줘', '무료 TTS' 요청.
---

# [무료] 무료 나레이션(엣지 TTS)

## 필요한 것
- edge-tts(`install_basics.py` 가 설치), ffmpeg
- 인터넷 연결
- 비용: 없음(무료)

## 순서
1. `python scripts/tts_edge.py script.txt narration` — 대본을 블록(빈 줄 구분)별로 읽어 `narration/narration.mp3` 와 블록별 길이표 `narration/timing.json` 을 만든다(편집 스킬이 자막·컷 타이밍에 사용). 끝나면 전체 길이를 출력.
   - 목소리 바꾸기: `--voice ko-KR-InJoonNeural`(남성) / 기본 `ko-KR-SunHiNeural`(여성). 속도: `--rate -5%`.
2. 사용자가 들어 보고 어색한 부분만 대본을 고쳐 다시 만든다.

## 알아둘 것
- 무료 서비스라 연결이 끊기면 실패할 수 있다 → 블록별로 3회 재시도하고, 그래도 안 되면 같은 명령을 다시 실행하면 만든 블록은 건너뛰고 이어서 한다.

## 다음 스킬 (끝나면 묻지 말고 바로 이어서 실행)
`longform-free-5-image`

---
*Pro판에서는 이 단계의 검사·검수·재시도가 자동으로 처리됩니다.*

---
만든이: sphereai.work (https://sphereai.work)
