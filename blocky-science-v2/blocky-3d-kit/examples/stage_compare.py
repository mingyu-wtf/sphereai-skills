# 설명 컷 뼈대: 하늘에 뜬 잔디 섬 무대 위 크기 비교 — 30fps, 180프레임 = 6초
#  설명·비교·도표 컷을 만들 때 이 파일을 복사한다. 회색 바닥판 + 단색 하늘 대신 이 무대를 쓴다(크기감이 생긴다).
#  C1    1~180  섬 둘레를 천천히 돌며 다가감. 사람 → 버스 → 나무 → 6층 건물이 차례로 튀어나옴(크기 비교), 섬 아래 블록 구름
import bpy, sys, math, importlib, os
from mathutils import Vector

SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
import lib_mc; importlib.reload(lib_mc)
import kit_base as D; importlib.reload(D)
import char_rig2 as CR; importlib.reload(CR)
import mc_world3 as W; importlib.reload(W)
import block_fx3 as BF; importlib.reload(BF)
import cine3 as CN; importlib.reload(CN)
import sets3 as ST; importlib.reload(ST)
A = D

SC = lib_mc.wipe_scene("STAGE_compare")
L = lib_mc.Lib(SC, seed=5, prefix="SG")
D.setup(L)
F0, F1 = 1, 180
SC.frame_start, SC.frame_end = F0, F1

# 하늘색 배경 + 태양등(설명 컷은 물리 하늘 대신 단색). 단색 하늘 + 태양등 장면은 grade3 노출 +0.5
A.world_keys(L, [(F0, (0.34, 0.50, 0.80), 1.0)])
sd = Vector((0.45, 0.55, 0.70)).normalized()
d = bpy.data.lights.new(L.prefix + "SUN", 'SUN'); d.energy = 3.2; d.angle = math.radians(1.0)
sun = bpy.data.objects.new("SUN", d); L.coll.objects.link(sun)
sun.rotation_euler = Vector((0, 0, -1)).rotation_difference(-sd).to_euler()

# 무대: 윗면 z=0, 90×90m, 10m 눈금 → 크기를 눈으로 잴 수 있다
ST.stage3(L, "STG", (0, 0, 0), size=(90.0, 90.0), seed=2)
W.clouds3(L, "CLD", center=(0, 0), z=-38, f0=F0, f1=F1, cover=0.42, cell=16.0, thick=6.0, extent=(900, 900), seed=4)


def pop(ob, f, s=1.0):
    """튀어나오기: 0 → 1.15 → 1 (BACK 보간 없이 키 3개)"""
    for fr, k in ((F0, 0.0), (f - 1, 0.0), (f + 4, 1.15 * s), (f + 9, s)):
        ob.scale = (k, k, k); ob.keyframe_insert("scale", frame=fr)


# 비교할 것들(1m 블록 기준). 원점은 바닥 → 크기 0에서 자라도 땅 밑에서 올라오지 않는다
person = CR.build(L, "BORA", CR.HERO, loc=(-24, -26, 0), rot_z=-20)
CR.rest(person, F0); CR.face(person, F0, "normal"); CR.idle(person, F0, F1); CR.auto_blink(person, F0, F1, seed=3)
pop(person["root"], 20)                                   # CR.build는 dict를 돌려준다. 옮기기·크기는 ["root"]
L.ENV_TEX["bus_body"] = lambda: L.noise(8, 8, (0.95, 0.70, 0.14), 0.05)                      # 새 색 텍스처 = ENV_TEX에 키 하나
L.ENV_TEX["bus_glass"] = lambda: L.noise(4, 4, (0.20, 0.30, 0.40), 0.05)
bus = L.box("BUS", (12.0, 2.6, 3.2), offset=(0, 0, 1.6), tex="bus_body", loc=(-8, -26, 0))     # 버스 12m
win = L.box("BUS_w", (11.2, 2.7, 0.9), offset=(0, 0, 0), tex="bus_glass", loc=(0, 0, 2.3))      # 창 띠(살짝 튀어나오게 2.7 > 2.6)
win.parent = bus
for wx in (-3.6, 3.6):
    for wy in (-1.35, 1.35):
        wh = L.box(f"BUS_wh{wx}{wy}", (1.2, 0.3, 1.2), offset=(0, 0, 0), tex="stone", loc=(wx, wy, 0.55)); wh.parent = bus
pop(bus, 55)
trunk = L.box("TREE_t", (1.0, 1.0, 6.0), offset=(0, 0, 3.0), tex="log", loc=(8, -26, 0))      # 나무 9m
leaf = L.box("TREE_l", (5.0, 5.0, 4.0), offset=(0, 0, 0), tex="leaves", loc=(0, 0, 7.0))
leaf.parent = trunk
pop(trunk, 85)
bld = L.box("BLD", (10.0, 10.0, 18.0), offset=(0, 0, 9.0), tex="stone", loc=(24, -26, 0))      # 6층 건물 18m
pop(bld, 115)

# 카메라: 섬 둘레를 돌며 다가감(orbit_keys) + 얇은 손떨림
cam = L.camera("CAM", 26, 0, CN.orbit_keys((0, -26, 0), r0=70, a0=-104, a1=-80, z0=30, f0=F0, f1=F1, r1=52, z1=16),
               [(F0, (0, -26, 2)), (F1, (2, -26, 6))])   # 섬 가장자리와 아래 구름이 보이게 위에서. 타깃은 물체들 가운데
CN.handheld(cam, F0, F1, 75, drift=0.25, jitter=0.05, seed=2)
L.bind_cameras([(F0, cam)])

L.render_setup(samples=32, res=(1280, 720), motion_blur=0)
BF.look3(L)
BF.grade3(L, exposure=0.5, saturation=1.45)
D.fps30(L, F0, F1)
SC.frame_set(F0)
