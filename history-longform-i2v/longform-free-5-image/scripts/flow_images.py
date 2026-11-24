# -*- coding: utf-8 -*-
"""prompts.txt 의 프롬프트를 어사이드(Aside) 브라우저로 구글 플로우에 넣어 이미지를 자동 생성·저장한다.
입력: prompts.txt  ("[C001] 프롬프트…" 블록을 빈 줄로 구분 — build_prompts.py 결과)
출력: images/C001.jpg …  이미 있는 컷은 건너뛰므로 중단돼도 같은 명령으로 이어진다.
사용: python flow_images.py [prompts.txt] [--out images] [--account u0] [--only C001 C005]
준비: 어사이드 설치·실행, 어사이드 브라우저에 구글 로그인(플로우가 열리는 계정). 계정 목록은 `aside account list`.
한도: 플로우 무료 플랜은 생성 횟수 제한이 있다 — 한도에 걸리면 멈추고 알려 주니, 나중에 같은 명령으로 이어서 한다."""
import argparse, json, re, shutil, subprocess, sys, time
from pathlib import Path

try: sys.stdout.reconfigure(errors="replace")
except Exception: pass

JS = r"""
const PROJECT = %(project)s, PROMPT = %(prompt)s, NAME = %(name)s;
await openTab(PROJECT); await sleep(3500);
try { await page.getByRole('button', {name: '나중에'}).click({timeout: 1500}); } catch (e) {}
const box = page.getByRole('textbox', {name: '무엇을 만들고 싶으신가요?'});
await box.fill(PROMPT);
await page.getByRole('button', {name: /설정 트리거/}).click();
for (const t of ['16:9', 'x1']) { try { await page.getByText(t, {exact: true}).click({timeout: 2000}); } catch (e) {} }
await page.keyboard.press('Escape');
const key = PROMPT.slice(0, 50);
// 화면의 이미지들은 새 것이 맨 앞. 각 이미지의 프롬프트 글에서 내 프롬프트가 몇 번째인지 찾는다.
const where = async () => { const t = (await snapshot(page, {interactive: true})).tree; const m = [...t.matchAll(/text: "([^"]*생성됨[^"]*)"/g)].map(x => x[1]); return m.map((x, i) => x.includes(key) ? i : -1).filter(i => i >= 0); };
const before = (await where()).length;
await page.getByRole('button', {name: '생성 시작'}).click();
let ok = false;
for (let k = 0; k < 22 && !ok; k++) {
  await sleep(5000);
  const w = await where();
  if (w.length > before) {
    await sleep(3000);
    try {
      const dp = page.waitForEvent('download', {timeout: 20000});
      await page.getByRole('button', {name: '다운로드'}).nth(w[0]).click();
      const d = await dp; await fs.mkdir('./artifacts', {recursive: true}); await d.saveAs('./artifacts/' + NAME); ok = true;
    } catch (e) {}
  }
}
console.log(ok ? 'RESULT:OK ' + String(pwd) + '|' + NAME : 'RESULT:TIMEOUT');
"""
NEW = r"""
await openTab('https://flow.google.com/'); await sleep(3500);
try { await page.getByRole('button', {name: '나중에'}).click({timeout: 1500}); } catch (e) {}
await page.getByRole('button', {name: '새 프로젝트'}).click(); await sleep(5000);
console.log('PROJECT:' + page.url());
"""


def aside(js, account):
    exe = shutil.which("aside")
    if not exe: sys.exit("어사이드(aside) 명령을 찾지 못했습니다. 어사이드를 설치하고 실행해 두세요.")
    cmd = [exe] + (["--account", account] if account else []) + ["repl", js]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompts", nargs="?", default="prompts.txt"); ap.add_argument("--out", default="images"); ap.add_argument("--account"); ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    blocks = [b.strip() for b in re.split(r"\n\s*\n", Path(a.prompts).read_text(encoding="utf-8")) if b.strip()]
    items = []
    for b in blocks:
        m = re.match(r"\[(C\d+)\]\s*(.*)", b, re.S)
        if m: items.append((m.group(1), " ".join(m.group(2).split())))
    out = Path(a.out); out.mkdir(exist_ok=True)
    todo = [(n, p) for n, p in items if (not a.only or n in a.only) and not (out / f"{n}.jpg").exists()]
    print(f"컷 {len(items)}개 중 만들 것 {len(todo)}개")
    if not todo: return 0
    pf = Path("flow_project.txt")
    if pf.exists(): project = pf.read_text(encoding="utf-8").strip()
    else:
        r = aside(NEW, a.account); m = re.search(r"PROJECT:(\S+)", r.stdout)
        if not m: print("플로우 새 프로젝트를 만들지 못했습니다. 어사이드에 구글 로그인이 돼 있는지 확인하세요.\n", r.stdout[-400:], r.stderr[-300:]); return 2
        project = m.group(1); pf.write_text(project, encoding="utf-8"); print("플로우 프로젝트:", project)
    failed = []
    for n, p in todo:
        t0 = time.time(); name = f"{n}.jpg"
        r = aside(JS % {"project": json.dumps(project), "prompt": json.dumps(p, ensure_ascii=False), "name": json.dumps(name)}, a.account)
        m = re.search(r"RESULT:OK (.+?)\|", r.stdout); src = None
        if m:  # 어사이드는 받은 파일을 자기 세션 폴더에 두므로 거기서 images/ 로 옮긴다
            for cand in (Path(m.group(1)) / "artifacts" / "artifacts" / name, Path(m.group(1)) / "artifacts" / name):
                if cand.exists(): src = cand; break
        if src: shutil.copy2(src, out / name); print(n, f"완료 {time.time()-t0:.0f}초")
        else:
            print(n, "실패(시간 초과·한도·화면 변경 가능):", (r.stdout + r.stderr)[-300:].replace("\n", " ")); failed.append(n)
            if "RESULT:TIMEOUT" in r.stdout: print("무료 한도에 걸렸을 수 있습니다. 잠시 뒤 같은 명령으로 이어서 하세요."); break
    print("실패:", failed if failed else "없음"); return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
