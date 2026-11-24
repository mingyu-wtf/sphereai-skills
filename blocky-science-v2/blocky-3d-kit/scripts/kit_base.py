# 블록 3D 키트 기본 도우미 — 텍스처 등록·보이기/숨기기 키·단색 하늘·태양등·점광원·별·평지·프레임 계산
#   import kit_base as D; A = D; D.setup(L)   (뼈대 컷 examples/cut_template.py 참고)
import bpy, math
import numpy as np
from mathutils import Vector

P = 1 / 16
CYAN = (0.30, 0.78, 1.00)
FPS = 30

def fr(sec):
    """나레이션 초 → 프레임(초 × 30 + 1)"""
    return int(round(sec * FPS)) + 1


def fps30(L, F0, F1):
    """30fps + 프레임 범위"""
    L.SC.render.fps = FPS
    L.SC.frame_start, L.SC.frame_end = F0, F1


def setup(L):
    T = L.ENV_TEX
    T["sun"] = lambda: _sun_tex(L)
    T["brass"] = lambda: L.noise(16, 16, (0.72, 0.55, 0.22), 0.08)
    T["wood"] = lambda: _wood(L)
    T["gold_foil"] = lambda: _foil(L)
    T["panel"] = lambda: _panel(L)
    T["sand"] = lambda: L.noise(16, 16, (0.86, 0.78, 0.55), 0.08)
    T["water"] = lambda: L.noise(16, 16, (0.15, 0.45, 0.80), 0.06)
    T["field"] = lambda: L.noise(2, 2, CYAN, 0.0)
    T["wind"] = lambda: L.noise(2, 2, (1.0, 0.85, 0.30), 0.0)
    T["white"] = lambda: L.noise(4, 4, (0.95, 0.95, 0.95), 0.02)
    T["snow"] = lambda: L.noise(16, 16, (0.80, 0.85, 0.92), 0.04)   # 화질 v3: 하얗게 날아가지 않게 살짝 푸르게
    T["dirt"] = lambda: L.noise(16, 16, (0.48, 0.34, 0.22), 0.10)
    T["metal"] = lambda: L.noise(8, 8, (0.62, 0.64, 0.68), 0.06)
    T["air"] = lambda: L.noise(2, 2, (0.70, 0.88, 1.0), 0.0)
    T["red_light"] = lambda: L.noise(2, 2, (1.0, 0.15, 0.10), 0.0)


def _sun_tex(L):
    a = L.noise(16, 16, (1.0, 0.72, 0.12), 0.10)
    rng = L.nrng
    for _ in range(40):
        L.put(a, rng.integers(16), rng.integers(16), (1.0, 0.90, 0.35))
    for _ in range(14):
        L.put(a, rng.integers(16), rng.integers(16), (0.95, 0.45, 0.05))
    return a


def _wood(L):
    a = L.noise(16, 16, (0.55, 0.38, 0.22), 0.06)
    for r in range(0, 16, 4):
        a[r, :, :3] *= 0.82
    return a


def _foil(L):
    a = L.noise(16, 16, (0.85, 0.65, 0.20), 0.18)
    for _ in range(20):
        L.put(a, L.nrng.integers(16), L.nrng.integers(16), (1.0, 0.88, 0.45))
    return a


def _panel(L):
    a = np.ones((16, 16, 4)); a[..., :3] = (0.10, 0.18, 0.42)
    for i in range(16):
        if i % 4 == 0:
            a[i, :, :3] = (0.75, 0.75, 0.78); a[:, i, :3] = (0.75, 0.75, 0.78)
    for r in range(16):
        for c in range(16):
            if r % 4 == 1 and c % 4 == 1:
                a[r, c, :3] = (0.25, 0.40, 0.75)
    return a


def link(L, ob, coll=None):
    (coll or L.coll).objects.link(ob)
    return ob


def empty(L, name, loc=(0, 0, 0), coll=None):
    e = bpy.data.objects.new(name, None)
    link(L, e, coll); e.location = loc
    return e


def set_interp_id(idb, kind='CONSTANT', only=None):
    ad = idb.animation_data
    if not ad or not ad.action:
        return
    act = ad.action
    fcs = []
    try:
        fcs = list(act.fcurves)
    except AttributeError:
        for layer in getattr(act, "layers", []):
            for strip in layer.strips:
                for cb in strip.channelbags:
                    fcs.extend(cb.fcurves)
    for fc in fcs:
        if only and only not in fc.data_path:
            continue
        for kp in fc.keyframe_points:
            kp.interpolation = kind


def show_between(ob, f_on, f_off=None, f_scene0=1):
    """f_on 전에는 숨김, f_off부터 숨김 (hide_render + hide_viewport, CONSTANT)."""
    for f, hid in ((f_scene0, f_on > f_scene0), (f_on, False)) + (((f_off, True),) if f_off else ()):
        ob.hide_render = hid; ob.hide_viewport = hid
        ob.keyframe_insert("hide_render", frame=f); ob.keyframe_insert("hide_viewport", frame=f)
    set_interp_id(ob, 'CONSTANT', 'hide')


def vis_keys(ob, keys):
    """keys: [(frame, visible)] CONSTANT. 자식까지 같이(부모를 숨겨도 자식은 안 숨으므로)."""
    for o in [ob] + list(ob.children_recursive):
        for f, v in keys:
            o.hide_render = not v; o.hide_viewport = not v
            o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)
        set_interp_id(o, 'CONSTANT', 'hide')


def world_keys(L, keys):
    """keys: [(frame, (r,g,b), strength)] — 숏별 월드 색 CONSTANT."""
    w = bpy.data.worlds.new(L.prefix + "world"); L.SC.world = w
    w.use_nodes = True
    nt = w.node_tree; N = nt.nodes; Lk = nt.links.new
    bg = N["Background"]
    # 화질 v3: 단색 대신 하늘 그라디언트(지평선이 밝고 위로 갈수록 진함) + 낮 숏만 옅은 공기 원근(볼륨 안개)
    rgb = N.new("ShaderNodeRGB")
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ")
    Lk(tc.outputs["Generated"], sep.inputs[0])
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -0.05; mr.inputs["From Max"].default_value = 0.55
    Lk(sep.outputs["Z"], mr.inputs["Value"])
    hor = N.new("ShaderNodeMix"); hor.data_type = 'RGBA'; hor.blend_type = 'MULTIPLY'
    hor.inputs["Factor"].default_value = 1.0; hor.inputs["B"].default_value = (1.28, 1.22, 1.12, 1)
    Lk(rgb.outputs[0], hor.inputs["A"])
    hz = N.new("ShaderNodeMix"); hz.data_type = 'RGBA'; hz.blend_type = 'ADD'
    hz.inputs["B"].default_value = (0.03, 0.03, 0.03, 1)
    Lk(hor.outputs["Result"], hz.inputs["A"])
    grad = N.new("ShaderNodeMix"); grad.data_type = 'RGBA'
    Lk(mr.outputs["Result"], grad.inputs["Factor"]); Lk(hz.outputs["Result"], grad.inputs["A"]); Lk(rgb.outputs[0], grad.inputs["B"])
    Lk(grad.outputs["Result"], bg.inputs[0])
    # 우주·밤이 순흑이면 어두운 쪽 윤곽이 배경에 묻힘(Gemini 2차 지적) → 짙은 남색 바닥값
    keys = [(f, tuple(max(c, m) for c, m in zip(col, (0.006, 0.009, 0.022))), s) for f, col, s in keys]
    for f, col, s in keys:
        day = max(col) > 0.2
        hz.inputs["Factor"].default_value = 1.0 if day else 0.0
        hz.inputs["Factor"].keyframe_insert("default_value", frame=f)
        rgb.outputs[0].default_value = (*col, 1); rgb.outputs[0].keyframe_insert("default_value", frame=f)
        bg.inputs[1].default_value = s; bg.inputs[1].keyframe_insert("default_value", frame=f)
    set_interp_id(w.node_tree, 'CONSTANT')
    # 낮 숏에만 공기 원근(멀리 있는 블록이 하늘색으로 옅어짐) — 컴포지터 미스트(lib_mc.look_v3)가 이 키를 읽는다
    # (월드 볼륨 안개는 EEVEE에서 화면 전체가 까맣게 나와서 쓰지 않음, 2026-10-20)
    L.haze_keys = [(f, 1.0 if max(col) > 0.2 else 0.0) for f, col, s in keys]
    return w


def sun_lamp(L, name, rot, keys, color=(1.0, 0.96, 0.9)):
    """keys: [(frame, energy)] CONSTANT."""
    d = bpy.data.lights.new(L.prefix + name, 'SUN'); d.color = color; d.angle = math.radians(1.5)
    ob = bpy.data.objects.new(name, d); link(L, ob); ob.rotation_euler = rot
    for f, e in keys:
        d.energy = e; d.keyframe_insert("energy", frame=f)
    set_interp_id(d, 'CONSTANT')
    return ob


def point(L, name, loc, energy, color=(1, 1, 1), radius=0.3):
    d = bpy.data.lights.new(L.prefix + name, 'POINT'); d.energy = energy; d.color = color
    d.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, d); link(L, ob); ob.location = loc
    return ob


def stars(L, n=600, R=1800, seed=7, size=2.4, center=(0, 0, 0), emit=6.0):
    """별 = 한 메쉬(숏별로 통째로 숨기기 쉽게).
    04화부터 카메라 클립이 6000이라 별이 실제로 보임 → emit 6이면 빛 번짐 십자가 커서 피사체를 가림(Gemini 2차): size 3.5·emit 2 권장."""
    rng = np.random.default_rng(seed)
    vox = {}
    for i in range(n):
        v = rng.normal(size=3); v = v / np.linalg.norm(v) * R
        col = (1, 1, 0.95) if rng.random() > 0.2 else (0.75, 0.85, 1.0)
        vox[tuple(int(c // size) for c in v)] = col
    ob = L.voxel_mesh("SKY_stars", vox, size, emit=emit)
    ob.location = center
    ob.visible_shadow = False
    return ob


def ground(L, name, center, size=(200, 200), tex="grass_top", z=0.0):
    return L.box(name, (size[0], size[1], 1), offset=(center[0], center[1], z - 0.5), tex=tex, tile=1)

