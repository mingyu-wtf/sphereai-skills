# -*- coding: utf-8 -*-
"""[무료] T2V 클립 + 나레이션 + 대본 -> 자막 입힌 가편집 mp4 (ffmpeg 만 필요).
- clips/ 의 mp4(이름순) = 대본 블록 순서. 블록마다 클립 길이를 나레이션 길이(timing.json)에 맞춘다
  (속도 0.8~1.25배 범위 안에서 늘리거나 줄이고, 모자라면 마지막 장면을 잠깐 멈춘다).
- 클립 자체 효과음은 낮춰서 나레이션 밑에 깐다. 대본을 24자 안팎 한 줄 자막으로 나눠 입힌다.
- 썸네일용으로 첫 클립에서 프레임 1장을 images/C001.jpg 로 뽑는다(longform-free-8-finish 가 쓴다).
사용: python t2v_edit.py [--clips clips] [--timing narration/timing.json] [--audio narration/narration.mp3]
                          [--script script.txt] [--out draft.mp4] [--sfx 0.25] [--no-subs] [--font "Malgun Gothic"]"""
import argparse, json, re, subprocess, sys, tempfile
from pathlib import Path

try: sys.stdout.reconfigure(errors="replace")
except Exception: pass


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode: raise SystemExit("ffmpeg 오류: " + r.stderr[-600:])
    return r.stdout


def probe(p, what):
    out = run(["ffprobe", "-v", "error", "-select_streams", what[0], "-show_entries", what[1], "-of", "csv=p=0", str(p)]).strip()
    return out


def duration(p):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).strip())


def srt_time(t):
    h, m = int(t // 3600), int(t % 3600 // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}".replace(",1000", ",999")


def split_text(text, width=24):
    """공백 기준으로 width 글자 안팎의 줄로 나눈다."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width: lines.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    if cur: lines.append(cur)
    return lines or [text]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clips", default="clips"); ap.add_argument("--timing", default="narration/timing.json")
    ap.add_argument("--audio", default="narration/narration.mp3"); ap.add_argument("--script", default="script.txt")
    ap.add_argument("--out", default="draft.mp4"); ap.add_argument("--sfx", type=float, default=0.25)
    ap.add_argument("--no-subs", action="store_true"); ap.add_argument("--font", default="Malgun Gothic")
    ap.add_argument("--size", default="1920x1080"); ap.add_argument("--fps", type=int, default=24)
    a = ap.parse_args()
    clips = sorted(Path(a.clips).glob("*.mp4")); timing = json.loads(Path(a.timing).read_text(encoding="utf-8"))
    blocks = [" ".join(b.split()) for b in re.split(r"\n\s*\n", Path(a.script).read_text(encoding="utf-8")) if b.strip()]
    n = min(len(clips), len(timing))
    if len(clips) != len(timing): print(f"[주의] 클립 {len(clips)}개, 나레이션 블록 {len(timing)}개 - 앞의 {n}개만 조립합니다.")
    if not n: raise SystemExit("조립할 클립이 없습니다.")
    W, H = a.size.split("x"); work = Path(tempfile.mkdtemp(prefix="t2vedit_")); parts, notes = [], []
    for i in range(n):
        cd, td = duration(clips[i]), float(timing[i]["dur"]) + 0.25   # 블록 끝에 숨 쉴 틈 0.25초
        r = min(1.25, max(0.8, td / cd)); has_a = bool(probe(clips[i], ("a", "stream=codec_type")))
        vf = f"setpts=PTS*{r:.5f},scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,fps={a.fps},tpad=stop_mode=clone:stop_duration=30,trim=duration={td:.3f},format=yuv420p"
        o = work / f"{i:03d}.mp4"; cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(clips[i])]
        if has_a:
            af = f"atempo={1 / r:.5f},volume={a.sfx},apad,atrim=duration={td:.3f},aresample=48000"
            cmd += ["-vf", vf, "-af", af]
        else:
            cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-vf", vf, "-t", f"{td:.3f}", "-map", "0:v", "-map", "1:a"]
        cmd += ["-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-ac", "2", "-ar", "48000", str(o)]
        run(cmd); parts.append(o); notes.append((clips[i].name, cd, td, r))
        if r in (0.8, 1.25) and abs(td / cd - r) > 0.02: print(f"[주의] {clips[i].name}: 클립 {cd:.1f}초 vs 나레이션 {td:.1f}초 - 속도 한계에 걸려 {'마지막 장면을 멈춤' if td > cd * r else '끝을 자름'}. 대본이나 클립을 손보세요.")
    lst = work / "l.txt"; lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
    cat = work / "cat.mp4"; run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(cat)])
    vf_final = "null"
    if not a.no_subs:
        srt, t = [], 0.0
        for i in range(n):
            td = float(timing[i]["dur"]); lines = split_text(blocks[i] if i < len(blocks) else "")
            tot = sum(len(x) for x in lines) or 1; s0 = t
            for ln in lines:
                d = td * len(ln) / tot; srt.append((s0, s0 + d, ln)); s0 += d
            t += float(timing[i]["dur"]) + 0.25
        (work / "subs.srt").write_text("".join(f"{k}\n{srt_time(x)} --> {srt_time(y)}\n{z}\n\n" for k, (x, y, z) in enumerate(srt, 1)), encoding="utf-8")
        vf_final = f"subtitles=subs.srt:force_style='FontName={a.font},FontSize=22,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,Outline=2,Shadow=0,MarginV=40'"
    out = Path(a.out).resolve()
    run(["ffmpeg", "-v", "error", "-y", "-i", "cat.mp4", "-i", str(Path(a.audio).resolve()), "-filter_complex",
         f"[0:v]{vf_final}[v];[0:a][1:a]amix=inputs=2:duration=first:normalize=0[a]", "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-crf", "18", "-c:a", "aac", "-shortest", str(out)], cwd=str(work))
    img = Path("images"); img.mkdir(exist_ok=True)
    if not (img / "C001.jpg").exists(): run(["ffmpeg", "-v", "error", "-y", "-ss", "2", "-i", str(clips[0]), "-frames:v", "1", "-q:v", "2", str(img / "C001.jpg")])
    print(f"완료: {out} (클립 {n}개, {duration(out):.1f}초). 썸네일용 프레임: images/C001.jpg")
    print("임시 폴더:", work)


if __name__ == "__main__":
    main()
