# -*- coding: utf-8 -*-
"""[Pro] 컷 이미지(+영상 클립)·나레이션·대본으로 리모션이 자동 편집·자막·렌더까지 한다.
같은 폴더의 remotion_template/ 을 작업 폴더로 복사해 쓰는 '새로 만든 최소 템플릿'이다(특정 채널 브랜딩 없음).

준비물(현재 폴더 기준):  images/C001.jpg…   narration/timing.json   narration/narration.mp3   script.txt(블록은 빈 줄로 구분)
                         (선택) clips/C001.mp4…   bgm.mp3   image_blocks.json {"C001": 1, ...}
사용:  python auto_edit.py            # 타임라인만 만들고 필요한 설치·용량을 알려 준다(아무것도 설치하지 않음)
       python auto_edit.py --yes      # 필요하면 npm install 까지 하고 렌더한다
필요: Node.js 18 이상, ffmpeg(ffprobe). 첫 설치/첫 렌더는 수백 MB(리모션 + 렌더용 브라우저)를 받는다 — 무료."""
import argparse, json, math, re, shutil, subprocess, sys, time
from pathlib import Path

FPS = 24
HERE = Path(__file__).resolve().parent


def vdur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout.strip())


def split_caption(text, limit=24):
    words, lines, cur = text.split(), [], ""
    for w in words:
        while len(w) > limit:
            if cur: lines.append(cur); cur = ""
            lines.append(w[:limit]); w = w[limit:]
        if len(cur) + len(w) + (1 if cur else 0) <= limit: cur = (cur + " " + w).strip()
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def main():
    ap = argparse.ArgumentParser()
    for k, d in (("images", "images"), ("clips", "clips"), ("timing", "narration/timing.json"), ("audio", "narration/narration.mp3"), ("script", "script.txt"), ("work", "remotion_edit"), ("out", "final.mp4")): ap.add_argument("--" + k, default=d)
    ap.add_argument("--bgm"); ap.add_argument("--blocks"); ap.add_argument("--bgm-volume", type=float, default=0.12); ap.add_argument("--yes", action="store_true"); ap.add_argument("--images-only", action="store_true", help="이미지+자막+나레이션만(영상 클립·BGM 무시) — 무료판 기본"); a = ap.parse_args()
    if a.images_only: a.bgm = None

    imgs = sorted(p for p in Path(a.images).iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    timing = json.loads(Path(a.timing).read_text(encoding="utf-8"))
    blocks = [" ".join(b.split()) for b in re.split(r"\n\s*\n", Path(a.script).read_text(encoding="utf-8")) if b.strip()]
    if len(blocks) != len(timing): print(f"대본 블록 {len(blocks)}개 ≠ timing.json {len(timing)}개 — 나레이션을 만든 대본과 같은 파일인지 확인하세요."); return 2
    bmap = json.loads(Path(a.blocks).read_text(encoding="utf-8")) if a.blocks else {p.stem: min(i * len(timing) // len(imgs) + 1, len(timing)) for i, p in enumerate(imgs)}
    per = {}
    for p in imgs: per.setdefault(bmap[p.stem], []).append(p)

    work = Path(a.work)
    if not work.exists(): shutil.copytree(HERE / "remotion_template", work)
    pub = work / "public"; (pub / "images").mkdir(parents=True, exist_ok=True); (pub / "clips").mkdir(exist_ok=True)

    cuts, caps, k = [], [], 0
    for t in timing:
        b0 = round(t["start"] * FPS); b1 = round((t["start"] + t["dur"]) * FPS); group = per.get(t["block"], [])
        if group:
            for i, p in enumerate(group):
                f0 = b0 + (b1 - b0) * i // len(group); f1 = b0 + (b1 - b0) * (i + 1) // len(group)
                shutil.copy2(p, pub / "images" / p.name); cut = {"id": p.stem, "from": f0, "frames": max(f1 - f0, 2), "mode": k % 4}
                clip = Path(a.clips) / (p.stem + ".mp4")
                if clip.exists() and not a.images_only: shutil.copy2(clip, pub / "clips" / clip.name); cut["clip"] = f"clips/{clip.name}"; cut["clipSec"] = round(vdur(clip), 3)
                else: cut["image"] = f"images/{p.name}"
                cuts.append(cut); k += 1
        lines = split_caption(blocks[t["block"] - 1]); total = sum(len(l) for l in lines) or 1; f = b0
        for i, l in enumerate(lines):
            n = (b1 - f) if i == len(lines) - 1 else max(int(round((b1 - b0) * len(l) / total)), 2); caps.append({"from": f, "frames": max(n, 2), "text": l}); f += n
    total_frames = round((timing[-1]["start"] + timing[-1]["dur"]) * FPS)
    shutil.copy2(a.audio, pub / "narration.mp3")
    tl = {"width": 1920, "height": 1080, "fps": FPS, "totalFrames": total_frames, "narration": "narration.mp3", "bgmVolume": a.bgm_volume, "cuts": cuts, "captions": caps}
    if a.bgm: shutil.copy2(a.bgm, pub / "bgm.mp3"); tl["bgm"] = "bgm.mp3"
    (work / "src" / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
    nclip = sum(1 for c in cuts if "clip" in c)
    print(f"타임라인 완료: 컷 {len(cuts)}개(영상 클립 {nclip}개), 자막 {len(caps)}줄, 길이 {total_frames/FPS:.1f}초 → {work/'src'/'timeline.json'}")

    node, npx, npm = shutil.which("node"), shutil.which("npx"), shutil.which("npm")
    if not node or not npx or not npm: print("Node.js 가 없습니다. https://nodejs.org 에서 LTS 를 설치한 뒤 다시 실행하세요."); return 3
    chrome_tail = r"\node_modules\.remotion\chrome-headless-shell\win64\chrome-headless-shell-win64\chrome-headless-shell.exe"
    if sys.platform.startswith("win") and len(str(work.resolve())) + len(chrome_tail) > 250:
        print(f"작업 폴더 경로가 너무 깁니다({len(str(work.resolve())) + len(chrome_tail)}자 > 윈도우 한도 260자). 렌더용 브라우저를 실행하지 못합니다.\n짧은 경로를 지정해 다시 실행하세요. 예) python auto_edit.py --work C:\\lf_edit --yes"); return 6
    need_install = not (work / "node_modules").exists()
    if not a.yes:
        print("\n다음 단계(--yes 를 붙이면 실행):")
        if need_install: print(" - npm install: 리모션 패키지 다운로드(수십~수백 MB). 첫 렌더 때 렌더용 브라우저(약 100MB)도 받음. 모두 무료.")
        print(f" - 렌더: {a.out}"); return 0
    if need_install:
        print("npm install 중..."); rc = subprocess.call([npm, "install", "--no-audit", "--no-fund"], cwd=work)
        if rc: print("npm install 실패. 위 오류를 확인하세요."); return rc
    out = Path(a.out).resolve(); t0 = time.time()
    print("렌더 중... (길이에 따라 수 분~수십 분)")
    rc = subprocess.call([npx, "remotion", "render", "src/index.ts", "Episode", str(out), "--timeout=120000"], cwd=work)
    if rc or not out.exists() or out.stat().st_mtime < t0: print("렌더 실패(또는 파일이 새로 만들어지지 않음). 이전 파일이 남아 있어도 믿지 마세요."); return rc or 4
    d = vdur(out); print(f"완료: {out}  길이 {d:.1f}초 (예상 {total_frames/FPS:.1f}초)  {out.stat().st_size/1e6:.0f}MB")
    return 0 if abs(d - total_frames / FPS) < 1.0 else 5


if __name__ == "__main__":
    sys.exit(main())
