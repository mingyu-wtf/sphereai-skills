# -*- coding: utf-8 -*-
"""[무료] ComfyUI(MiniMax H3 터보)로 이미지 A → 다음 이미지 B 로 이어지는 7초 영상을 순차 생성. 이미 만든 컷은 건너뛰어 이어서 한다.
입력: images/ 폴더의 이미지(이름순). 각 컷은 '자기 이미지 → 다음 컷 이미지' 클립이 된다(마지막 컷은 자기 자신).
사용: python comfy_i2v.py --server http://127.0.0.1:8188 [--only 이름 ...]
주의: 7초 클립 1개에 RTX 5090 약 9분, RTX 5080 16GB 약 14분. 서버가 꺼지면 같은 명령을 다시 실행하면 이어진다."""
import argparse, json, os, time, uuid
from pathlib import Path

PROMPT = "Smooth, natural motion from the first image to the last image."


def load_workflow(path):
    """에이전트가 만든 ComfyUI API 형식 워크플로(.json)를 읽는다. 이 스킬은 워크플로를 제공하지 않는다."""
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"워크플로 파일이 없습니다: {path}\n에이전트가 ComfyUI 에 MiniMax H3 첫·끝 프레임 영상 워크플로를 구성해 API 형식(.json)으로 저장한 뒤 --workflow 로 지정하세요.")
    return json.loads(p.read_text(encoding="utf-8"))


def fill_workflow(wf, first_img, last_img, prompt, tag, low_vram=False):
    """클래스 이름으로 노드를 찾아 이미지·프롬프트·시드·저장 이름만 채운다(그래프 구조는 건드리지 않는다)."""
    wf = json.loads(json.dumps(wf)); loads = [n for n in wf.values() if n.get("class_type") == "LoadImage"]
    if len(loads) < 2: raise SystemExit("워크플로에 LoadImage 노드가 2개(첫·끝 프레임) 필요합니다.")
    loads[0]["inputs"]["image"], loads[1]["inputs"]["image"] = first_img, last_img
    hit = {"p": 0, "s": 0, "v": 0}
    for n in wf.values():
        ct, inp = n.get("class_type"), n.get("inputs", {})
        if ct == "MiniMaxH3ImageToVideo": inp["prompt"] = prompt; hit["p"] += 1
        elif ct == "RandomNoise": inp["noise_seed"] = int.from_bytes(os.urandom(4), "big"); hit["s"] += 1
        elif ct == "SaveVideo": inp["filename_prefix"] = f"video/{tag}"; hit["v"] += 1
        elif ct == "MiniMaxH3TurboLoRA" and "low_vram" in inp: inp["low_vram"] = low_vram
    if not (hit["p"] and hit["v"]): raise SystemExit("워크플로에 MiniMaxH3ImageToVideo / SaveVideo 노드가 있어야 합니다.")
    return wf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8188"); ap.add_argument("--workflow", default="workflow_api.json"); ap.add_argument("--images", default="images")
    ap.add_argument("--out", default="clips"); ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    imgs = sorted([p for p in Path(a.images).iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png")])
    out = Path(a.out); out.mkdir(exist_ok=True)
    names = [p.stem for p in imgs]; todo = [n for n in names if (not a.only or n in a.only) and not list(out.glob(n + ".mp4"))]
    print(f"컷 {len(names)}개 중 만들 것 {len(todo)}개 (7초 클립 1개당 약 9~14분 → 예상 {len(todo)*9}~{len(todo)*14}분)")
    base = load_workflow(a.workflow)
    import requests
    try: requests.get(a.server + "/object_info/MiniMaxH3TurboLoRA", timeout=10).raise_for_status()
    except Exception as e: print("ComfyUI 서버/노드 확인 실패:", e, "\nComfyUI 를 켜고, 영상 노드·모델이 설치돼 있는지 확인하세요(longform-free-1-preflight 안내)."); return 3

    def upload(p):
        with open(p, "rb") as f:
            r = requests.post(a.server + "/upload/image", files={"image": (p.name, f)}, data={"type": "input", "overwrite": "true"}, timeout=60); r.raise_for_status(); return r.json()["name"]
    failed = []
    for n in todo:
        i = names.index(n); first = imgs[i]; last = imgs[i + 1] if i + 1 < len(imgs) else imgs[i]
        wf = fill_workflow(base, upload(first), upload(last), PROMPT, n); t0 = time.time()
        r = requests.post(a.server + "/prompt", json={"prompt": wf, "client_id": str(uuid.uuid4())}, timeout=30)
        if r.status_code != 200: print(n, "큐 등록 실패", r.status_code, r.text[:200]); failed.append(n); continue
        pid = r.json()["prompt_id"]; print(n, "생성 중...", flush=True)
        while True:
            time.sleep(10)
            try: h = requests.get(f"{a.server}/history/{pid}", timeout=15).json()
            except Exception: continue
            if pid in h: break
        st = h[pid].get("status", {})
        if st.get("status_str") == "error": print(n, "실행 오류:", json.dumps(st, ensure_ascii=False)[:300]); failed.append(n); continue
        got = None
        for node in h[pid].get("outputs", {}).values():
            for k in ("images", "videos", "gifs"):
                for it in node.get(k, []):
                    if str(it.get("filename", "")).lower().endswith((".mp4", ".webm")): got = it
        if not got: print(n, "결과 파일을 찾지 못함"); failed.append(n); continue
        v = requests.get(a.server + "/view", params={"filename": got["filename"], "subfolder": got.get("subfolder", ""), "type": got.get("type", "output")}, timeout=120); v.raise_for_status()
        (out / f"{n}.mp4").write_bytes(v.content); print(n, f"완료 {time.time()-t0:.0f}초")
    print("실패:", failed if failed else "없음")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
