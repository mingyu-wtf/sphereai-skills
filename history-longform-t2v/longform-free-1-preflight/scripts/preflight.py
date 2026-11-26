# -*- coding: utf-8 -*-
"""내 PC가 롱폼 자동 제작에 필요한 것을 갖췄는지 읽기 전용으로 점검한다. 아무것도 설치·변경하지 않는다.
사용: python preflight.py [--out preflight.json]"""
import json, os, platform, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REQ = json.loads((HERE / "requirements.json").read_text(encoding="utf-8"))


def run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return (r.stdout or "") + (r.stderr or "")
    except Exception:
        return ""


def ram_gb():
    try:
        if os.name == "nt":
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [("l", ctypes.c_ulong), ("m", ctypes.c_ulong)] + [(n, ctypes.c_ulonglong) for n in ("tp", "ap", "tpf", "apf", "tv", "av", "ae")]
            s = MS(); s.l = ctypes.sizeof(MS); ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s))
            return round(s.tp / 1024**3, 1)
        if sys.platform == "darwin":
            return round(int(run(["sysctl", "-n", "hw.memsize"]).strip()) / 1024**3, 1)
        for ln in open("/proc/meminfo"):
            if ln.startswith("MemTotal"):
                return round(int(ln.split()[1]) / 1024**2, 1)
    except Exception:
        pass
    return None


def gpu():
    o = run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"]).strip()
    if not o or "not found" in o.lower() or "failed" in o.lower():
        return None
    name, mem = [x.strip() for x in o.splitlines()[0].split(",")]
    return {"name": name, "vram_gb": round(int(mem) / 1024, 1)}


def tool_ver(cmd, flag="-version"):
    p = shutil.which(cmd)
    if not p:
        return None
    return (run([cmd, flag]).strip().splitlines() or [""])[0][:80]


def edge_ok():
    try:
        from importlib.metadata import version
        return tuple(int(x) for x in version("edge-tts").split(".")[:2]) >= (7, 3)
    except Exception:
        return False


def pymod(name):
    try:
        __import__(name); return True
    except Exception:
        return False


def main():
    out = Path("preflight.json")
    if "--out" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--out") + 1])
    g = gpu(); ram = ram_gb(); free = round(shutil.disk_usage(Path.cwd()).free / 1024**3, 1)
    r = {
        "os": platform.platform(), "python": platform.python_version(), "gpu": g, "ram_gb": ram, "disk_free_gb": free,
        "ffmpeg": tool_ver("ffmpeg"), "ffprobe": tool_ver("ffprobe"), "git": tool_ver("git", "--version"),
        "node": tool_ver("node", "--version"), "aside": bool(shutil.which("aside") or shutil.which("aside.exe")),
        "py_edge_tts": pymod("edge_tts") and edge_ok(), "py_cv2": pymod("cv2"), "py_numpy": pymod("numpy"), "py_pillow": pymod("PIL"), "py_requests": pymod("requests"),
    }
    cv = REQ["comfyui_video"]
    if not g:
        route = "manual"; why = "NVIDIA GPU를 찾지 못함 → 영상 변환은 수동 경로(정지 이미지 켄번즈로 진행)"
    elif g["vram_gb"] >= cv["verified_gpu_vram_gb"] - 0.5:
        sec = cv["seconds_per_7s_clip"]
        ref = next((v for k, v in sec.items() if any(t in g["name"] for t in k.split()[1:2])), None)
        est = f"약 {round(ref/60)}분" if ref else "약 9~14분(5090~5080 실측 범위)"
        route = "comfyui"; why = f"VRAM {g['vram_gb']}GB → ComfyUI 로컬 생성 가능(확인된 사양). 7초 클립 1개 {est}"
    else:
        route = "manual_or_try"; why = f"VRAM {g['vram_gb']}GB는 확인된 적 없는 사양(검증 16GB 이상). 수동 경로 권장, 시험해 볼 수는 있음"
    r["video_route"] = route; r["video_route_reason"] = why
    warns = []
    if free < REQ["min_disk_free_gb"]: warns.append(f"디스크 여유 {free}GB < 권장 {REQ['min_disk_free_gb']}GB (모델 약 {cv['disk_gb_models']}GB + 작업 파일)")
    if ram and ram < REQ["min_ram_gb"]: warns.append(f"RAM {ram}GB < 권장 {REQ['min_ram_gb']}GB")
    r["warnings"] = warns

    def mark(ok): return "[OK]  " if ok else "[없음]"
    print("== 내 PC 점검 ==")
    print(f"OS        {r['os']}\nGPU       {g['name'] + ' ' + str(g['vram_gb']) + 'GB' if g else '없음(NVIDIA 아님)'}\nRAM       {ram} GB\n디스크 여유 {free} GB (현재 폴더 기준)\n")
    print("== 필요한 도구 ==")
    for k, label, hint in [("ffmpeg", "ffmpeg", "install_basics.py 가 설치"), ("python", "Python", ""), ("py_edge_tts", "edge-tts 7.3 이상(무료 TTS, 낮은 버전은 403 오류)", "install_basics.py"), ("py_cv2", "opencv(부드러운 줌)", "install_basics.py"),
                           ("py_numpy", "numpy", "install_basics.py"), ("py_pillow", "Pillow(썸네일)", "install_basics.py"), ("py_requests", "requests(ComfyUI 연결)", "install_basics.py"),
                           ("git", "git(ComfyUI 노드 설치)", "https://git-scm.com"), ("aside", "어사이드(브라우저 자동화, Pro·구글 플로우 자동 배치용)", "직접 설치·로그인")]:
        print(mark(bool(r.get(k))), label, "" if r.get(k) else "→ " + hint)
    print("\n== 영상 변환 경로 ==\n" + why)
    for w in warns: print("주의:", w)
    out.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n점검 결과 저장: {out}")


if __name__ == "__main__":
    main()
