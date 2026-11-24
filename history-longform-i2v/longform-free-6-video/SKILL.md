---
name: longform-free-6-video
description: 컷 이미지를 ComfyUI(MiniMax H3)로 'A 이미지 → 다음 이미지 B' 7초 영상으로 자동 변환할 때 사용. '영상으로 바꿔줘', '클립 만들어줘' 요청.
---

# [무료] 이미지→영상 자동 변환 (A → B)

## 필요한 것
- 컷 이미지(images/, 번호순 이름)
- ComfyUI 실행 중 + 영상 노드·모델 설치 완료 — **ComfyUI 프로그램 자체의 설치는 사용자가 직접 합니다**(공식 설치 후 한 번 실행해 둠). 이 스킬은 설치해 주지 않고, 이미 설치된 ComfyUI 를 점검·안내만 합니다. 영상 노드·모델은 `longform-free-1-preflight` 가 확인·안내하고, 받는 것은 사용자 OK 후에 합니다. NVIDIA GPU 16GB 이상에서 확인됨.
- 파이썬 requests
- 비용: 없음(내 PC에서 생성). 7초 클립 1개당 RTX 5090 약 9분, RTX 5080 16GB 약 14분.

## 워크플로 (이 스킬은 제공하지 않는다 — 에이전트가 직접 만든다)
- 에이전트가 ComfyUI 에 **MiniMax H3 첫·끝 프레임 → 영상(터보 LoRA 포함)** 워크플로를 구성하고, **API 형식(.json)** 으로 저장해 둔다(기본 이름 `workflow_api.json`, 다른 이름이면 `--workflow 파일`).
- 스크립트는 그 파일에서 `LoadImage` 2개(첫·끝 프레임), `MiniMaxH3ImageToVideo`(프롬프트), `RandomNoise`(시드), `SaveVideo`(저장 이름)만 클래스 이름으로 찾아 채워서 보낸다. 그래프 구조·모델·설정값은 건드리지 않는다.
- 파일이 없으면 스크립트가 멈추고 만들어 달라고 알린다.

## 순서 (묻지 말고 자동으로 진행)
1. 시작 전에 클립 수와 예상 시간만 사용자에게 한 줄로 알린다.
2. `python scripts/comfy_i2v.py --workflow workflow_api.json --server http://127.0.0.1:8188`
   - images/ 의 각 컷이 **자기 이미지(A) → 다음 컷 이미지(B)** 로 이어지는 7초 클립이 되어 `clips/<컷>.mp4` 에 저장된다. 마지막 컷은 자기 자신으로 끝난다.
   - 이미 만든 컷은 건너뛰므로 중간에 끊겨도 같은 명령으로 이어진다. 특정 컷만: `--only C001 C005`
   - 포트는 사용자 ComfyUI 설정에 맞춘다.
3. 끝나면 실패 목록을 보여 주고, 실패한 컷은 같은 명령으로 한 번 더 시도한다. 그래도 안 되면 그 컷은 정지 이미지로 둔다(편집 단계에서 자동으로 줌 처리).
4. 곧바로 `longform-free-7-edit` 로 넘어간다.

## 다음 스킬
`longform-free-7-edit`

---
*Pro판에서는 컷 선정·모션 지시·결과 검수와 재시도가 더해집니다.*

---
만든이: sphereai.work (https://sphereai.work)
