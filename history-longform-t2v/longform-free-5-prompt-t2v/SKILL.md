---
name: longform-free-5-prompt-t2v
description: 역사·전쟁 롱폼(또는 숏폼)을 실사 영상으로, 이미지 없이 텍스트→영상(t2v)만으로 만들 때 사용. '실사 t2v 롱폼', '텍스트로 실사 영상', '장면표에서 t2v 프롬프트 조립', 't2v 프롬프트 검사' 요청. 생성은 longform-free-6-video-t2v 가 한다.
---

# [무료] 실사 t2v 롱폼 제작 (대본 → 장면표 → 프롬프트 → 생성 → 검수)

이미지 단계를 건너뛰고 **대본 블록 1개 = 8초 실사 클립 1개**를 글만으로 뽑는다.
생성은 `longform-free-6-video-t2v`(터보 8스텝 / 20스텝, `comfy_t2v.py`)가 하고, 이 스킬은 **프롬프트를 틀 없이 일관되게 만들고 생성 전에 걸러내는 것**을 맡는다.

## 필요한 것
- ComfyUI 와 MiniMax H3 가 설치돼 있을 것(점검은 `longform-free-1-preflight`).
- 파이썬 3.9+. 대본(블록으로 나뉜 것)이 있을 것(없으면 대본 스킬).
- 비용 없음(내 PC 생성). 클립당 5090 약 9~15분, RTX 5080 16GB 약 14분.

## 순서 (묻지 말고 자동 진행, 설치·다운로드만 OK 받기)
1. **장면표 쓰기**: `references/scenes_template.json` 을 복사해 `scenes.json` 으로 채운다. 대본 블록 1개 = 장면 1개.
   - `project`: 비율(16:9/9:16), 시대·장소, **시대 고증 잠금 문장**(세기·지역 + 금지할 양식), 음향.
   - `casting`: 반복해 나오는 인물의 고정 문형(얼굴·나이·복장). 장면에서 `cast` 로 불러 쓴다.
   - 장면마다: `opening`(첫 프레임부터 보일 것) / `development`(원테이크 전개) 또는 `shots`(멀티샷) / `light`(역광) / `camera` / `lens_hits`(2~6개).
   - 쓰는 규칙은 `references/realistic_t2v_rules.md`. 원테이크와 멀티샷을 장면 성격에 따라 섞는다.
2. **조립**: `python scripts/build_t2v_prompts.py scenes.json --out .` → `prompts/C001_<장면>.txt …`(프롬프트 본문만 들어 있음 = 생성 스킬이 그대로 읽는 파일), `prompts.txt`(검사용 모음), `narration_map.txt`(클립↔나레이션 원문), `prompt_map.csv`
3. **검사**: `python scripts/lint_t2v_prompts.py prompts.txt` — 글자 수, 필수 문구, 금지어(전환어·잔혹 어휘·현대 사물·립싱크 암시), 한글, 렌즈 히트 개수, 중앙 정면·역광 여부. 걸리면 `scenes.json` 을 고쳐 2번부터 다시(생성 전에 걸러야 시간이 안 샌다).
4. **시험 생성**: `longform-free-6-video-t2v` 로 1개만 뽑아 본다: `python ../longform-free-6-video-t2v/scripts/comfy_t2v.py --prompts prompts --out clips --only C001 [--mode 20step]`. 시작 전에 클립 수와 예상 시간(터보 클립당 약 14분, 20스텝 약 46분, ×1.3)을 한 줄로 알린다.
5. **전체 생성**: `--only` 없이 같은 명령. 끊겨도 같은 명령으로 이어진다.
6. **검수**: `references/realistic_t2v_rules.md` §8 체크리스트로 클립을 본다. 걸린 컷은 `scenes.json` 을 고쳐 그 컷만 다시 뽑는다(`--only C007`, 파일 지우기). 같은 컷을 2번 고쳐도 안 되면 정지 이미지로 두거나 이미지→영상 스킬로 대신하고 알린다.
7. **저장·보고**: 채택본은 `clips/`, 반려본은 `clips/_미사용/`, 최종 프롬프트는 `prompts/` 에 남기고 `작업보고.txt` 를 쓴다(§7).
8. 끝나면 `longform-free-7-edit-t2v` 로 이어서 간다.

## 지킬 것
- 인물 얼굴이 컷마다 달라질 수 있다. 일대기물은 뒷모습·옆모습·원경 위주로 쓴다.
- 프롬프트는 영어, 화면에 글자·자막·워터마크를 넣지 않는다.
- 구글 로그인·계정 생성·ComfyUI 설치는 대신 하지 않는다. 모델 다운로드는 사용자 OK 후에만.
- 첫·끝프레임 없이 터보 8스텝 T2V 생성은 RTX 5080 에서 1클립 성공을 확인했다(20스텝은 미실행). 막히면 이미지 1장을 먼저 만들어 이미지→영상 스킬로 대신한다.

---
만든이: sphereai.work (https://sphereai.work)
