# -*- coding: utf-8 -*-
"""[무료] ComfyUI(MiniMax H3 터보 8스텝 또는 20스텝 고화질)로 텍스트 프롬프트만으로 영상(T2V)을 순차 생성. 이미 만든 블록은 건너뛰어 이어서 한다.
입력: prompts/ 폴더의 .txt (파일 1개 = 클립 1개, 이름순. 예: B01_씬1.txt). 이미지는 쓰지 않는다.
사용: python comfy_t2v.py --server http://127.0.0.1:8189 [--mode turbo|20step] [--only B01 B05]
워크플로는 코드가 직접 조립한다(워크플로 JSON 파일 불필요). 첫·끝프레임을 연결하지 않으면 순수 T2V가 된다.
주의: 7초(175프레임) 클립 1개에 RTX 5080 16GB 약 14분(I2V 실측; T2V 터보는 첫 실측 후 갱신). 서버가 꺼지면 같은 명령으로 이어진다."""
import argparse, json, os, time, uuid
from pathlib import Path

UNET = "minimax_h3_fl2va_pruned_int8_convrot.safetensors"
CLIP = "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"
TURBO_LORA = r"minimaxh3\minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors"   # 윈도 경로 구분자 \ 그대로(리눅스 ComfyUI면 / 로)
VAE_V, VAE_A = "minimax_h3_video_vae_fp16.safetensors", "minimax_h3_audio_vae_fp32.safetensors"
WIDTH, HEIGHT, LENGTH, STEPS = 1536, 864, 175, 8   # 175프레임 ≈ 7초(24fps). 세로 영상이면 --width 864 --height 1536


def build_workflow(prompt, tag, width, height, length, low_vram=False):
    """터보 8스텝 T2V 그래프. first_frame/last_frame 을 아예 연결하지 않는다."""
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": UNET, "weight_dtype": "default"}},
        "1b": {"class_type": "MiniMaxH3TurboLoRA", "inputs": {"model": ["1", 0], "lora_name": TURBO_LORA, "strength": 1.0, "low_vram": low_vram}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP, "type": "minimax", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": VAE_V}},
        "4": {"class_type": "VAELoader", "inputs": {"vae_name": VAE_A}},
        "7": {"class_type": "MiniMaxH3ImageToVideo", "inputs": {"clip": ["2", 0], "vae": ["3", 0], "prompt": prompt, "width": width, "height": height, "length": length}},
        "8": {"class_type": "RandomNoise", "inputs": {"noise_seed": int.from_bytes(os.urandom(4), "big")}},
        "9": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "res_multistep"}},
        "10": {"class_type": "BasicScheduler", "inputs": {"model": ["1b", 0], "scheduler": "simple", "steps": STEPS, "denoise": 1}},
        "11": {"class_type": "BasicGuider", "inputs": {"model": ["1b", 0], "conditioning": ["7", 0]}},
        "12": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["8", 0], "guider": ["11", 0], "sampler": ["9", 0], "sigmas": ["10", 0], "latent_image": ["7", 1]}},
        "13": {"class_type": "VAEDecode", "inputs": {"samples": ["12", 0], "vae": ["3", 0]}},
        "14": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["12", 0], "vae": ["4", 0]}},
        "15": {"class_type": "CreateVideo", "inputs": {"images": ["13", 0], "audio": ["14", 0], "fps": 24}},
        "16": {"class_type": "SaveVideo", "inputs": {"video": ["15", 0], "filename_prefix": f"video/{tag}", "format": "auto", "codec": "auto"}},
    }


def load_workflow(path):
    """스킬 폴더의 workflow_api.json 을 읽는다. 없으면 build_workflow() 코드로 조립."""
    f = Path(path)
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def fill_workflow(base, prompt, tag, width, height, length, low_vram):
    """클래스 이름으로 노드를 찾아 프롬프트·시드·크기·길이·저장 이름만 채운다(그래프 구조는 그대로)."""
    wf = json.loads(json.dumps(base)); hit = 0
    for n in wf.values():
        ct, inp = n.get("class_type"), n.get("inputs", {})
        if ct == "MiniMaxH3ImageToVideo": inp.update(prompt=prompt, width=width, height=height, length=length); inp.pop("first_frame", None); inp.pop("last_frame", None); hit += 1
        elif ct == "RandomNoise": inp["noise_seed"] = int.from_bytes(os.urandom(4), "big")
        elif ct == "KSampler": inp["seed"] = int.from_bytes(os.urandom(4), "big")
        elif ct == "SaveVideo": inp["filename_prefix"] = f"video/{tag}"
        elif ct == "MiniMaxH3TurboLoRA": inp["low_vram"] = low_vram
    if not hit: raise SystemExit("워크플로에 MiniMaxH3ImageToVideo 노드가 없습니다.")
    return wf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8188"); ap.add_argument("--prompts", default="prompts"); ap.add_argument("--out", default="clips")
    ap.add_argument("--only", nargs="*"); ap.add_argument("--mode", choices=["turbo", "20step"], default="turbo"); ap.add_argument("--workflow", default=None); ap.add_argument("--width", type=int, default=WIDTH); ap.add_argument("--height", type=int, default=HEIGHT)
    ap.add_argument("--length", type=int, default=None); ap.add_argument("--low-vram", action="store_true")
    a = ap.parse_args()
    root = Path(__file__).resolve().parent.parent
    if a.length is None: a.length = LENGTH if a.mode == "turbo" else 192   # turbo 175프레임≈7초, 20step 192프레임=8초
    if a.workflow is None: a.workflow = str(root / f"workflow_api_{a.mode}.json")
    if a.mode == "20step" and not Path(a.workflow).exists(): raise SystemExit("20step 워크플로 파일이 없습니다: " + a.workflow)
    files = sorted(Path(a.prompts).glob("*.txt")); out = Path(a.out); out.mkdir(exist_ok=True)
    todo = [p for p in files if (not a.only or any(p.stem == o or p.stem.startswith(o + "_") for o in a.only)) and not (out / (p.stem + ".mp4")).exists()]
    print(f"프롬프트 {len(files)}개 중 만들 것 {len(todo)}개 (모드 {a.mode}: 클립 1개당 5080 약 {14 if a.mode == "turbo" else 46}분 → 예상 {len(todo)*(14 if a.mode == "turbo" else 46)}분)", flush=True)
    import requests
    try: requests.get(a.server + "/object_info/MiniMaxH3TurboLoRA", timeout=10).raise_for_status()
    except Exception as e: print("ComfyUI 서버/노드 확인 실패:", e, "\nComfyUI 를 켜고, 영상 노드·모델이 설치돼 있는지 확인하세요(longform-free-1-preflight 안내)."); return 3
    base = load_workflow(a.workflow); failed = []
    for p in todo:
        n = p.stem; text = p.read_text(encoding="utf-8").strip()
        if not text: print(n, "프롬프트가 비어 있음"); failed.append(n); continue
        wf = fill_workflow(base, text, n, a.width, a.height, a.length, a.low_vram) if base or a.mode == "20step" else build_workflow(text, n, a.width, a.height, a.length, a.low_vram); t0 = time.time()
        r = requests.post(a.server + "/prompt", json={"prompt": wf, "client_id": str(uuid.uuid4())}, timeout=30)
        if r.status_code != 200: print(n, "큐 등록 실패", r.status_code, r.text[:300]); failed.append(n); continue
        pid = r.json()["prompt_id"]; print(n, "생성 중...", flush=True)
        while True:
            time.sleep(10)
            try: h = requests.get(f"{a.server}/history/{pid}", timeout=15).json()   # websocket 대신 HTTP 폴링(서버 불안정 대비)
            except Exception: continue
            if pid in h: break
        st = h[pid].get("status", {})
        if st.get("status_str") == "error": print(n, "실행 오류:", json.dumps(st, ensure_ascii=False)[:400]); failed.append(n); continue
        got = None
        for node in h[pid].get("outputs", {}).values():
            for k in ("images", "videos", "gifs"):
                for it in node.get(k, []):
                    if str(it.get("filename", "")).lower().endswith((".mp4", ".webm")): got = it
        if not got: print(n, "결과 파일을 찾지 못함"); failed.append(n); continue
        v = requests.get(a.server + "/view", params={"filename": got["filename"], "subfolder": got.get("subfolder", ""), "type": got.get("type", "output")}, timeout=120); v.raise_for_status()
        (out / f"{n}.mp4").write_bytes(v.content); print(n, f"완료 {time.time()-t0:.0f}초", flush=True)
    print("실패:", failed if failed else "없음")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
