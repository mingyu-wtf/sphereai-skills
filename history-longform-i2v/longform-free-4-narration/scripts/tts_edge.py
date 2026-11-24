# -*- coding: utf-8 -*-
"""블록(빈 줄로 구분)별로 엣지 TTS 를 만들고, 블록 길이를 timing.json 에 기록한 뒤 이어 붙여 narration.mp3 를 만든다.
실패하면 블록별 3회 재시도. 이미 만든 블록은 건너뛴다(이어하기).
사용: python tts_edge.py script.txt outdir [--voice ko-KR-SunHiNeural] [--rate +0%]
결과: outdir/b01.mp3 ..., outdir/narration.mp3, outdir/timing.json  [{"block":1,"start":0.0,"dur":9.8}, ...]"""
import argparse, asyncio, json, re, subprocess
from pathlib import Path
import sys
try: sys.stdout.reconfigure(errors="replace")
except Exception: pass


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout.strip())


async def main():
    ap = argparse.ArgumentParser(); ap.add_argument("text"); ap.add_argument("outdir"); ap.add_argument("--voice", default="ko-KR-SunHiNeural"); ap.add_argument("--rate", default="+0%")
    a = ap.parse_args(); import edge_tts
    out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
    blocks = [" ".join(b.split()) for b in re.split(r"\n\s*\n", Path(a.text).read_text(encoding="utf-8")) if b.strip()]
    files = []
    for i, b in enumerate(blocks, 1):
        f = out / f"b{i:02d}.mp3"; files.append(f)
        if f.exists() and f.stat().st_size > 1000: continue
        for t in range(3):
            try: await edge_tts.Communicate(b, a.voice, rate=a.rate).save(str(f)); break
            except Exception as e: print(f"블록 {i} 재시도 {t+1}"); last = e; await asyncio.sleep(3)
        else:
            if "403" in str(last): print("엣지 TTS 서버가 접속을 거부했습니다(403). edge-tts 가 오래된 버전일 때 생깁니다 → python -m pip install -U edge-tts 후 다시 실행하세요.")
            print(f"블록 {i} 실패. 같은 명령을 다시 실행하면 이어서 합니다"); return 1
    timing, t = [], 0.0
    for i, f in enumerate(files, 1):
        d = dur(f); timing.append({"block": i, "start": round(t, 3), "dur": round(d, 3), "chars": len(blocks[i-1])}); t += d
    (out / "timing.json").write_text(json.dumps(timing, ensure_ascii=False, indent=1), encoding="utf-8")
    lst = out / "list.txt"; lst.write_text("".join(f"file '{f.name}'\n" for f in files), encoding="utf-8")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c:a", "libmp3lame", "-q:a", "3", str(out / "narration.mp3")], check=True)
    print(f"블록 {len(blocks)}개, 전체 {t:.1f}초 → {out/'narration.mp3'}")
    return 0


raise SystemExit(asyncio.run(main()))
