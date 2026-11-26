# -*- coding: utf-8 -*-
"""scenes.json 한 장으로 실사 t2v 프롬프트(영어)를 조립한다.
- 고정 문단(스타일·시대 고증·무언·무글자·음향·카메라·렌즈 히트)은 이 스크립트가 붙이고, 장면마다 달라지는 부분만 scenes.json 에 쓴다.
- 출력: prompts.txt ([C001] 블록, comfy_t2v.py 가 그대로 읽음) + prompts/<C번호>_<장면id>.txt (프롬프트 본문만) + narration_map.txt (나레이션 원문) + prompt_map.csv (C번호↔장면id)
사용: python build_t2v_prompts.py scenes.json [--out <폴더>]
scenes.json 형식은 references/scenes_template.json 참고."""
import argparse, csv, json, sys
from pathlib import Path

try: sys.stdout.reconfigure(errors="replace")
except Exception: pass

STYLES = {
    "photoreal": "Photorealistic cinematic live-action footage, shot on a large-format digital cinema camera with natural film grain, real skin and fabric and metal textures, shallow depth of field, grounded historical-epic color grade; not an illustration, not a cartoon, not a 3D render, not a painting.",
}
ORIENT = {"16:9": "Horizontal 16:9 composition, wide frame.", "9:16": "Vertical 9:16 composition, tall frame."}
SILENT = "Characters remain completely silent throughout - mouths closed or naturally at rest, no talking, no lip movement, no dialogue, no shouting with visible speech."
NO_TEXT = "No on-screen text of any kind - no captions, no subtitles, no logos, no watermark."


def need(d, key, where):
    if not d.get(key): raise SystemExit(f"[오류] {where} 에 '{key}' 가 없습니다.")
    return d[key]


def audio_line(p):
    mode = p.get("audio", "sfx_only")
    if mode == "silent": return "Audio: none."
    fx = p.get("audio_effects") or "wind, footsteps, armor and metal, cloth, distant crowd murmur"
    return f"Audio: ambient sound effects only - {fx}. NO music, NO score, NO soundtrack."


def build(p, c, s, idx):
    sid = need(s, "id", f"장면 {idx}")
    sec = p.get("clip_seconds", 8)
    mode = s.get("mode", "onetake")
    style = STYLES.get(p.get("style", "photoreal"), p.get("style"))
    out = []
    if mode == "multishot":
        shots = need(s, "shots", sid)
        out.append(f"A {sec}-second multi-shot sequence of {len(shots)} shots, hard cuts only between shots. {ORIENT[p['ratio']]} {style} {s.get('place_time', p.get('place_time', ''))}".strip())
    else:
        out.append(f"One single unbroken continuous camera take, {sec} seconds, no cuts, one shot only. {ORIENT[p['ratio']]} {style} {s.get('place_time', p.get('place_time', ''))}".strip())
    out.append("FROM THE VERY FIRST FRAME: " + need(s, "opening", sid))
    if mode == "multishot":
        lines = []
        for k, sh in enumerate(need(s, "shots", sid)):
            lines.append(f"[{sh['t']}] " + ("" if k == 0 else "Hard cut to ") + sh["text"])
        out.append("\n".join(lines))
    else:
        for para in s.get("development", []): out.append(para)
    used = s.get("cast", [])
    if used:
        miss = [k for k in used if k not in c]
        if miss: raise SystemExit(f"[오류] {sid}: casting 에 없는 인물 {miss}")
        out.append("CAST (identical in every shot): " + " ".join(c[k] for k in used))
    out.append("LIGHTING: " + need(s, "light", sid))
    out.append(p["era_lock"])
    out.append(SILENT + " " + NO_TEXT + (" " + s["text_exception"] if s.get("text_exception") else ""))
    out.append(audio_line(p))
    out.append("Camera: " + need(s, "camera", sid))
    hits = need(s, "lens_hits", sid)
    out.append("Lens-hit events in order: " + ", ".join(hits) + ".")
    return sid, "\n\n".join(out)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("scenes"); ap.add_argument("--out", default=".")
    a = ap.parse_args()
    data = json.loads(Path(a.scenes).read_text(encoding="utf-8"))
    p = data["project"]; c = data.get("casting", {})
    for k in ("ratio", "era_lock"): need(p, k, "project")
    if p["ratio"] not in ORIENT: raise SystemExit("[오류] ratio 는 16:9 또는 9:16")
    out = Path(a.out); (out / "prompts").mkdir(parents=True, exist_ok=True)
    blocks, rows, narr = [], [], []
    for i, s in enumerate(data["scenes"], 1):
        sid, text = build(p, c, s, i); cid = f"C{i:03d}"
        blocks.append(f"[{cid}] {text}"); rows.append((cid, sid, len(text)))
        (out / "prompts" / f"{cid}_{sid}.txt").write_text(text + "\n", encoding="utf-8")   # 본문만(머리말 없음): 생성 스킬이 파일 전체를 프롬프트로 읽는다
        narr.append(f"[{cid} / {sid}] {s.get('narration', '')}")
    (out / "prompts.txt").write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
    (out / "narration_map.txt").write_text("\n".join(narr) + "\n", encoding="utf-8")
    with open(out / "prompt_map.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["clip", "scene", "chars"]); w.writerows(rows)
    print(f"장면 {len(rows)}개 조립 -> {out / 'prompts.txt'}")
    for cid, sid, n in rows: print(f"  {cid} {sid}: {n}자" + ("  (3,500자 초과)" if n > 3500 else ""))
    print("다음: python lint_t2v_prompts.py prompts.txt")


if __name__ == "__main__":
    main()
