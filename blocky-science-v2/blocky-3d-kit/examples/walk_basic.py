# 기본 뼈대 컷(무료판): 노을 강변을 걸어와 하늘의 블록 혜성을 가리킨다 — 30fps, 150프레임 = 5초
#  새 컷을 만들 때 이 파일을 복사해서 내용만 바꾼다. 사용법은 이 키트의 SKILL.md.
#  아래 숏 목록은 "#  이름  시작~끝  설명" 형식을 지킨다.
#  S1    1~90   노을 강변: 낮은 데서 떠오르는 크레인. 보라가 걸어와 하늘의 블록 혜성을 가리킴
#  S2   91~150  인물 옆: 둘이 혜성을 올려다봄(천천히 밀고 들어감)
import bpy, sys, math, importlib, os
from mathutils import Vector

# ---------- ① 경로와 모듈(이 묶음은 그대로 복사) ----------
SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")   # 키트의 scripts 폴더(이 파일 위치 기준)
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
import lib_mc; importlib.reload(lib_mc)
import kit_base as D; importlib.reload(D)          # 기본 도우미(텍스처 등록·보이기 키·하늘·프레임 계산)
import char_rig2 as CR; importlib.reload(CR)        # 캐릭터 리그 v2
import sci_fx3 as X; importlib.reload(X)            # 물리 하늘(sky3)
import mc_world3 as W; importlib.reload(W)          # 블록 세계
import block_fx3 as BF; importlib.reload(BF)        # 블록 혜성 + 빛 번짐 + 색감
import cine3 as CN; importlib.reload(CN)            # 카메라 연출
A = D

# ---------- ② 장면과 프레임 범위 ----------
SC = lib_mc.wipe_scene("WALK_basic")                # 변수 이름은 반드시 SC
L = lib_mc.Lib(SC, seed=7, prefix="WB")
D.setup(L)
F0, F1 = 1, 150
SC.frame_start, SC.frame_end = F0, F1               # 세계를 만들기 전에 정한다

# ---------- ③ 하늘과 해 ----------
SD_DUSK = (-0.64, -0.77, 0.07)                      # 노을 해가 있는 방향. 카메라가 −Y를 볼 때 화면 오른쪽이 −X
X.sky3(L, [(F0, 2.5, 220, 0.27)])                   # (프레임, 해 고도°, 방위°, 세기)
d = bpy.data.lights.new(L.prefix + "SUN", 'SUN'); d.color = (1.0, 0.58, 0.36); d.energy = 1.2; d.angle = math.radians(1.0)
sun = bpy.data.objects.new("SUN", d); L.coll.objects.link(sun)
sun.rotation_euler = Vector((0, 0, -1)).rotation_difference(-Vector(SD_DUSK).normalized()).to_euler()
W.block_sun3(L, "BSUN", SD_DUSK, keys=[(F0, True)])  # 네모난 해

# ---------- ④ 블록 세계(도시는 y<0, 강은 y 20~400, 인물은 y≈404 강변) ----------
W.city_lights(L, [(F0, 3.0)])                       # 창·가로등·차 불빛: 낮 0, 노을 2~3, 밤 4
W.city3(L, "CITY", seed=21)
W.land3(L, "LAND")
W.land3(L, "LAND2", y_min=399.0, z=0.12)
W.river3(L, "RIVER", (0, 210), (4000, 380))
W.bridge3(L, "BR", -120.0, -6.0, 402.0)
W.traffic3(L, "TR", (-120, -30, 11), (-120, 430, 11), n=16, f0=F0, f1=F1)
W.riverside3(L, "BANK", (0, 396), width=600, tree=((14.0, 6.0, 5), (-14.0, 8.0, 4), (24.0, 15.0, 6)))
W.hills3(L, "HILL", (0, -520, 0), low_x=(-950, -450))

# ---------- ⑤ 하늘의 블록 혜성(가만히 떠서 꼬리만 흐름) ----------
CAM1_A, CAM1_B = Vector((4.6, 411.6, 0.55)), Vector((3.6, 408.3, 1.5))
hh = Vector((-60 - 3.6, 300 - 408.3, 0)).normalized(); right = hh.cross(Vector((0, 0, 1)))
dirH = (hh + right * 0.10).normalized() * math.cos(math.radians(23)) + Vector((0, 0, math.sin(math.radians(23))))
HEAD = CAM1_B + dirH * 1100                         # 카메라에서 본 방향 × 거리 1100m
sdn = Vector(SD_DUSK).normalized()
tdir = dirH - sdn; tdir = (tdir - dirH * tdir.dot(dirH)).normalized()     # 꼬리 = 화면에서 해 반대쪽
BF.block_comet3(L, "CMT", tuple(HEAD), sun_dir=tuple(-tdir), scale=40.0, tail_len=12, seed=8, flow=(F0, F1),
                side=tuple(right), N=6, glow=0.0, emit=1.5)
W.clouds3(L, "CLD", z=360, f0=F0, f1=F1, cover=0.26, keep_rays=[(CAM1_B, HEAD + tdir * k, 250) for k in (0, 200, 400, 600)])   # 구름은 맨 나중에

# ---------- ⑥ 인물(정면 = −Y, 원점 = 발바닥, 강변 윗면 z=0.2) ----------
bora = CR.build(L, "BORA", CR.HERO, loc=(1.8, 405.0, 0.2), rot_z=0)
dy = CR.build(L, "DOYUN", CR.BOY, loc=(-0.6, 403.8, 0.2), rot_z=-8)
for ch in (bora, dy):
    CR.rest(ch, F0); CR.face(ch, F0, "normal")
CR.walk_to(bora, [(1.8, 405.0), (0.6, 403.5)], 4, 60)                           # 1.9m를 56프레임(약 1m/s)
CR.pose(bora, 62, head=(-22, 0, 6), torso=(-3, 0, 0))                           # 걷기 뒤 포즈는 f1+2부터
CR.pose(bora, 74, head=(-30, 0, 8), armR=(-150, 0, -18), elbowR=(-15, 0, 0), torso=(-5, 0, 0))   # 하늘을 가리킴
CR.pose(bora, 120, head=(-30, 0, 8), armR=(-150, 0, -18), elbowR=(-15, 0, 0), torso=(-5, 0, 0))
CR.pose(bora, 132, head=(-28, 0, -6), armR=(-10, 0, -6), elbowR=(-8, 0, 0), torso=(-4, 0, 0))
CR.face(bora, 72, "shocked")
CR.pose(dy, F0, head=(-8, 0, -4), torso=(-1, 0, 0))
CR.pose(dy, 76, head=(-8, 0, -4), torso=(-1, 0, 0))
CR.pose(dy, 86, head=(-26, 0, -8), armL=(-20, 0, 10), torso=(-3, 0, 0))
CR.face(dy, 84, "scared")
CR.idle(dy, F0, F1)
for i, ch in enumerate((bora, dy)):
    CR.auto_blink(ch, F0, F1, seed=i + 3)                                       # 표정 키를 다 넣은 뒤 맨 마지막에

# ---------- ⑦ 카메라 ----------
c1 = L.camera("CAM_S1", 22, 0, CN.crane_keys(CAM1_A, CAM1_B, F0, 90), [(F0, (-60, 300, 26)), (90, (-60, 300, 33))])
CN.handheld(c1, F0, 90, 120, drift=0.25, jitter=0.05, seed=2)
c2 = L.camera("CAM_S2", 24, 0, [(91, (5.0, 409.6, 1.4)), (F1, (4.4, 408.6, 1.45))], [(91, (-40, 300, 18)), (F1, (-40, 300, 21))])   # 시선 약 8°: 어깨와 혜성(고도 23°)이 같이 들어옴
CN.handheld(c2, 91, F1, 110, drift=0.3, jitter=0.06, seed=7)
L.bind_cameras([(F0, c1), (91, c2)])

# ---------- ⑧ 렌더 설정(순서를 바꾸지 않는다) ----------
L.haze_keys = [(F0, 0.35)]
L.render_setup(samples=32, res=(1280, 720), motion_blur=0)    # 시험은 720p·32샘플. 본 렌더는 기본값(1080p·48샘플)
BF.look3(L)                                                   # 빛 번짐을 Bloom으로(빼면 십자 줄무늬가 생김)
BF.grade3(L)                                                  # 색감 AgX(빼면 밝은 곳이 하얗게 탐)
D.fps30(L, F0, F1)
SC.frame_set(F0)
