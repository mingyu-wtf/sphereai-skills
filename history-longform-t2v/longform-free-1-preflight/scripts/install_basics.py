# -*- coding: utf-8 -*-
"""기본 도구 설치(ffmpeg + 파이썬 패키지). 인자 없이 실행하면 '무엇을 설치할지'만 보여 준다.
사용: python install_basics.py          # 계획만 출력
      python install_basics.py --yes    # 실제 설치 (이미 있는 것은 건너뜀)
비용: 모두 무료. 용량: 합쳐서 수백 MB 안팎."""
import importlib.util, shutil, subprocess, sys

PKGS = {"edge_tts": "edge-tts", "cv2": "opencv-python-headless", "numpy": "numpy", "PIL": "pillow", "requests": "requests"}


def have_mod(m): return importlib.util.find_spec(m) is not None


def edge_old():
    """edge-tts 7.3 미만이면 마이크로소프트 서버가 403 으로 거부한다(실제로 겪음) → 올려야 함."""
    try:
        from importlib.metadata import version
        v = tuple(int(x) for x in version("edge-tts").split(".")[:2]); return v < (7, 3)
    except Exception:
        return False


def ffmpeg_cmd():
    if sys.platform.startswith("win"): return ["winget", "install", "--id", "Gyan.FFmpeg", "-e", "--accept-source-agreements", "--accept-package-agreements"]
    if sys.platform == "darwin": return ["brew", "install", "ffmpeg"]
    return ["sudo", "apt-get", "install", "-y", "ffmpeg"]


def main():
    yes = "--yes" in sys.argv
    todo_py = [p for m, p in PKGS.items() if not have_mod(m)]
    if edge_old(): todo_py.append("edge-tts>=7.3")
    need_ff = not shutil.which("ffmpeg")
    if not todo_py and not need_ff:
        print("필요한 기본 도구가 모두 설치돼 있습니다."); return 0
    print("설치 계획(무료):")
    if need_ff: print(" - ffmpeg:", " ".join(ffmpeg_cmd()))
    if todo_py: print(" - 파이썬 패키지:", " ".join(todo_py))
    if not yes:
        print("\n실제로 설치하려면 --yes 를 붙여 다시 실행하세요."); return 0
    rc = 0
    if todo_py:
        rc |= subprocess.call([sys.executable, "-m", "pip", "install", "-U", *todo_py])
    if need_ff:
        rc |= subprocess.call(ffmpeg_cmd())
        print("ffmpeg 설치 후에는 터미널을 새로 열어야 PATH 에 잡힙니다.")
    print("설치 끝. python preflight.py 로 다시 점검하세요." if rc == 0 else "일부 설치가 실패했습니다. 위 오류를 확인하세요.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
