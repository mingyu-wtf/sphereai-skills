---
name: longform-free-6-video-t2v
description: 텍스트 프롬프트만으로 ComfyUI(MiniMax H3 · 터보 8스텝 / 20스텝 고화질 2가지)에서 7초 영상 클립을 자동 생성할 때 사용. '텍스트로 영상 만들어줘', 'T2V', '프롬프트로 클립 만들어줘' 요청. 이미지가 없어도 된다.
---

# [무료] 텍스트→영상 자동 생성 (T2V, 터보·20스텝)

이미지 없이 프롬프트(.txt)만으로 클립을 만든다. 인물 얼굴·장면을 컷마다 똑같이 유지해야 하면 이미지→영상 스킬(`longform-free-6-video`)을 쓴다. T2V는 컷마다 얼굴이 달라질 수 있다.

## 필요한 것
- `prompts/` 폴더의 프롬프트 .txt (파일 1개 = 클립 1개, 이름순. 예: `B01_씬1.txt`). 영어로 쓴다.
- ComfyUI 실행 중 + MiniMax H3 영상 노드·모델·터보 LoRA 설치 완료(ComfyUI 설치는 사용자가 직접. 노드·모델 점검은 `longform-free-1-preflight`). NVIDIA 16GB 이상.
- 파이썬 requests
- 비용: 없음(내 PC). 7초 클립 1개 RTX 5080 16GB 약 14분(5080 실측: 터보 T2V 1클립 약 11분).

## 워크플로 (스킬 안에 포함: 터보·20스텝 2개)
스킬 폴더에 ComfyUI API 형식 워크플로 2개가 있다. `--mode turbo`(기본)는 `workflow_api_turbo.json`, `--mode 20step`은 `workflow_api_20step.json`. 스크립트가 읽어 클래스 이름으로 프롬프트·시드·해상도·길이·저장 이름만 채운다. 다른 워크플로를 쓰려면 `--workflow 파일`. 터보 파일이 없으면 스크립트 안의 코드로 같은 그래프를 조립한다. 터보 구성:
UNETLoader(`minimax_h3_fl2va_pruned_int8_convrot`) → `MiniMaxH3TurboLoRA` → `MiniMaxH3ImageToVideo`(**first_frame·last_frame 연결 안 함 = 순수 T2V**) → RandomNoise · KSamplerSelect(`res_multistep`) · BasicScheduler(`simple`, **8스텝**) · BasicGuider → SamplerCustomAdvanced → VAEDecode + VAEDecodeAudio → CreateVideo(24fps) → SaveVideo. 해상도 1536×864, 175프레임(약 7초). 세로 영상은 `--width 864 --height 1536`.

| 모드 | 스텝 | 길이 | 5080 소요 | 구성 차이 |
|---|---|---|---|---|
| `turbo`(기본) | 8 | 175프레임≈7초 | 클립당 약 11~14분(T2V 실측 11분) | 터보 LoRA + SamplerCustomAdvanced |
| `20step` | 20 | 192프레임=8초 | 클립당 약 46분(문서 기록, 이 스킬로는 미실측) | 터보 없음, `MiniMaxH3SigmaShift`(12/6) + KSampler(cfg 1) |
빠른 확인·대량은 turbo, 최종 화질 우선이면 20step. 사용: `python scripts/comfy_t2v.py --mode 20step`

## 순서 (묻지 말고 자동으로 진행)
1. 시작 전에 클립 수와 예상 시간(터보 개수×14분, 20step 개수×46분)만 한 줄로 알린다.
2. `python scripts/comfy_t2v.py --server http://127.0.0.1:8188 [--mode 20step]`
   - 클립은 `clips/<프롬프트 파일명>.mp4` 로 저장. 이미 있으면 건너뛰므로 끊겨도 같은 명령으로 이어진다. 특정 블록만: `--only B01 B05`
   - 포트는 사용자 ComfyUI 설정에 맞춘다. 메모리 부족이면 `--low-vram`(화질이 약간 흐려짐).
3. 끝나면 실패 목록을 보여 주고 실패한 것만 같은 명령으로 한 번 더. 그래도 안 되면 프롬프트를 단순하게 고쳐 다시 한다.
4. 곧바로 `longform-free-7-edit-t2v` 로 넘어간다.

## 프롬프트 작성 규칙 (확정된 것)
- 첫 문장 = 스타일 고정 문구(모든 블록 동일). 다음에 시대·장소 한 줄 고정(예: "Late 16th century Joseon Korea, autumn 1592 AD"). 현대 고증 금지.
- 원테이크: "One single unbroken continuous camera take, 8 seconds, no cuts" + 카메라 이동 서술. 멀티샷: `[0s-2s] ... [2s-4s] Hard cut ...` 타임스탬프로 한 클립에 여러 샷.
- 인물은 나이·얼굴·갑옷·위치까지 구체적으로. 침묵 문장("characters remain silent, mouths closed, no talking, no lip movement")을 넣고 "speaks/mouth open" 단어는 쓰지 않는다.
- 끝에 효과음 지시("ambient sound effects only ... NO music, NO score, NO soundtrack"). 안 넣으면 브금이 섞여 나온다.
- dissolve/fade/morph 같은 전환어와 "no X" 식 부정문은 피한다.

## 운영 주의
- ComfyUI가 가끔 죽는다. 완료 감지는 HTTP 폴링이라 서버가 꺼지면 스크립트가 대기 상태로 남는다 → 서버를 다시 켜고 스크립트를 재실행한다(만든 건 건너뜀).
- 클립 길이는 17의 배수+5 프레임 격자에 맞춰진다(175≈7초, 192=8초).

## 실측 기록
- 2026-11-05 RTX 5080 16GB, 터보 8스텝, 1536×864, 175프레임, 첫·끝프레임 없음: 1클립 성공, 약 11분. 20스텝은 미실행(문서 기록 약 46분).

## 다음 스킬
`longform-free-7-edit-t2v`

---
만든이: sphereai.work (https://sphereai.work)
