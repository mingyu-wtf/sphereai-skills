# 블록 입자 이펙트 v1 (2026-11-05, 사용자 "혜성도 이런 식으로(정육면체 + 빛줄기) / 다양한 이펙트")
#  지오메트리 노드로 "점 → 큐브"를 찍되 위치·크기를 수식으로 계산한다(시뮬레이션·베이크 없음 → 아무 프레임이나 바로 렌더).
#    위치 = p + v·(1−e^(−k·τ))/k + ½·a·τ²   (τ = 태어난 뒤 흐른 초, k = 공기 저항)
#    크기 = size × 나타남 × 사라짐 × (1 + grow·나이)     나이(0~1)는 "age" 속성으로 재질에 전달 → 색·발광이 나이를 따라 변함
#  입자 하나하나의 출발점·속도·태어나는 때·수명은 파이썬에서 정한다 → 같은 노드 하나로 꼬리·불똥·연기·파편·충격파를 다 만든다.
#    block_particles : 기본 입자 / particle_mat : 나이별 색·발광 재질
#    block_comet3    : 블록 혜성(얼음 정육면체 머리 + 사방 빛줄기 + 흐르는 블록 꼬리 2개 + 밑에 깔리는 볼륨 빛)
#    entry_blocks3   : 진입 — 지나간 자리에 남는 블록 연기 + 불똥 (sci_fx3.entry3와 같이)
#    block_burst3    : 블록 폭발 — 불 블록·블록 연기·날아가는 파편·수평 고리 (sci_fx3.airburst3와 같이)
#    shock_front3    : 충격파가 물·땅을 훑고 지나가는 자국(거리만큼 늦게 도착)
#    glass_burst3    : 충격파가 닿은 건물에서 유리 조각이 쏟아짐
#    impact_comp     : 폭발 프레임에 노출 번쩍 + 색수차(컴포지터)
# 쓰는 법은 config/04_blender_upgrade_guide.md 4장
import bpy, math, random
from mathutils import Vector, Matrix
import sci_fx3 as X

G = X.G


def particle_mat(L, name, cols, emits=None, rough=0.9, var=0.18, unlit=False):
    """나이(0~1)에 따라 색·발광이 변하는 블록 입자 재질. cols=[(나이,(r,g,b))], emits=[(나이,세기)].
    unlit=True면 햇빛을 받지 않고 제 빛만 낸다(빛나는 꼬리·불똥: 햇빛을 받으면 전부 하얗게 날아가 색이 사라짐)."""
    m = bpy.data.materials.new(L.prefix + name); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes["Principled BSDF"]; g = G(nt)
    age = g.node("ShaderNodeAttribute", attribute_name="age").outputs["Fac"]
    rnd = g.node("ShaderNodeAttribute", attribute_name="rnd").outputs["Fac"]
    c = g.ramp(age, cols)
    k = g.m('ADD', 1.0 - var / 2, g.m('MULTIPLY', rnd, var))
    sc = g.node("ShaderNodeVectorMath", operation='SCALE'); g.link(c, sc.inputs[0]); g.link(k, sc.inputs["Scale"])
    if unlit:
        bs.inputs["Base Color"].default_value = (0, 0, 0, 1)
        if "Specular IOR Level" in bs.inputs:
            bs.inputs["Specular IOR Level"].default_value = 0.0
    else:
        g.link(sc.outputs["Vector"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = rough
    if emits:
        mx = max(e for _, e in emits) or 1.0
        e = g.ramp(age, [(a, (v / mx,) * 3) for a, v in emits])
        g.link(sc.outputs["Vector"], bs.inputs["Emission Color"])
        g.link(g.m('MULTIPLY', e, mx), bs.inputs["Emission Strength"])
    return m


def block_particles(L, name, pts, mat, acc=(0, 0, 0), drag=0.0, loop=False, spin=0.0, parent=None,
                    fade_in=0.06, fade_out=0.6, grow=0.0, fps=30, step=1, shadow=False, stretch=1.0):
    """pts = [dict(p=(x,y,z), v=(vx,vy,vz), birth=초, life=초, size=m, rnd=0~1)].
    stretch>1이면 날아가는 방향으로 길쭉한 막대(빛줄기·속도선·불똥 꼬리)가 된다.
    loop=True면 수명마다 되풀이(꼬리처럼 끊임없이 흐르는 것). spin>0이면 구르며 날아감(0 = 격자에 맞춘 블록).
    step>1이면 그 프레임 수마다 뚝뚝 움직임. 좌표는 오브젝트 로컬(parent에 붙이면 같이 움직이고 커짐)."""
    rng = random.Random(len(pts) * 7 + 1)
    me = bpy.data.meshes.new(L.prefix + name)
    me.from_pydata([tuple(p["p"]) for p in pts], [], [])
    at = me.attributes.new("v0", 'FLOAT_VECTOR', 'POINT')
    at.data.foreach_set("vector", [float(c) for p in pts for c in p.get("v", (0, 0, 0))])
    for key, dflt in (("birth", 0.0), ("life", 1.0), ("size", 1.0), ("rnd", None)):
        at = me.attributes.new(key, 'FLOAT', 'POINT')
        at.data.foreach_set("value", [float(p[key]) if key in p else (rng.random() if dflt is None else dflt) for p in pts])
    ob = bpy.data.objects.new(name, me); L.coll.objects.link(ob)
    if parent:
        ob.parent = parent
    ob.visible_shadow = shadow
    ng = bpy.data.node_groups.new(L.prefix + name + "_gn", 'GeometryNodeTree')
    ng.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    g = G(ng)
    gi = g.node("NodeGroupInput"); go = g.node("NodeGroupOutput")

    def attr(nm, typ='FLOAT'):
        n = g.node("GeometryNodeInputNamedAttribute", data_type=typ); n.inputs["Name"].default_value = nm
        return n.outputs["Attribute"]

    fr = g.node("GeometryNodeInputSceneTime").outputs["Frame"]
    if step > 1:
        fr = g.m('MULTIPLY', g.m('FLOOR', g.m('DIVIDE', fr, float(step))), float(step))
    t = g.m('DIVIDE', fr, float(fps))
    birth, life, size, rnd, v0 = attr("birth"), attr("life"), attr("size"), attr("rnd"), attr("v0", 'FLOAT_VECTOR')
    a_raw = g.m('DIVIDE', g.m('SUBTRACT', t, birth), life)
    alive = g.m('GREATER_THAN', a_raw, 0.0)
    if loop:
        a = g.m('FRACT', a_raw)
    else:
        a = a_raw
        alive = g.m('MULTIPLY', alive, g.m('LESS_THAN', a_raw, 1.0))
    tau = g.m('MULTIPLY', a, life)
    fd = tau if not drag else g.m('DIVIDE', g.m('SUBTRACT', 1.0, g.m('EXPONENT', g.m('MULTIPLY', tau, -drag))), drag)
    d1 = g.node("ShaderNodeVectorMath", operation='SCALE'); g.link(v0, d1.inputs[0]); g.link(fd, d1.inputs["Scale"])
    d2 = g.node("ShaderNodeVectorMath", operation='SCALE'); d2.inputs[0].default_value = tuple(acc)
    g.link(g.m('MULTIPLY', g.m('MULTIPLY', tau, tau), 0.5), d2.inputs["Scale"])
    pos = g.node("GeometryNodeInputPosition").outputs[0]
    s1 = g.node("ShaderNodeVectorMath", operation='ADD'); g.link(pos, s1.inputs[0]); g.link(d1.outputs["Vector"], s1.inputs[1])
    s2 = g.node("ShaderNodeVectorMath", operation='ADD'); g.link(s1.outputs["Vector"], s2.inputs[0]); g.link(d2.outputs["Vector"], s2.inputs[1])
    dl = g.node("GeometryNodeDeleteGeometry")           # 아직 안 태어났거나 수명이 끝난 점은 지움
    g.link(gi.outputs[0], dl.inputs["Geometry"]); g.link(g.m('SUBTRACT', 1.0, alive), dl.inputs["Selection"])
    sp = g.node("GeometryNodeSetPosition")
    g.link(dl.outputs[0], sp.inputs["Geometry"]); g.link(s2.outputs["Vector"], sp.inputs["Position"])
    sa = g.node("GeometryNodeStoreNamedAttribute", data_type='FLOAT', domain='POINT')
    sa.inputs["Name"].default_value = "age"
    g.link(sp.outputs[0], sa.inputs["Geometry"]); g.link(g.m('MINIMUM', g.m('MAXIMUM', a, 0.0), 1.0), sa.inputs["Value"])
    sz = g.m('MULTIPLY', size, g.smooth(a, 0.0, max(1e-4, fade_in)))
    sz = g.m('MULTIPLY', sz, g.smooth(a, 1.0, fade_out))
    if grow:
        sz = g.m('MULTIPLY', sz, g.m('ADD', 1.0, g.m('MULTIPLY', a, grow)))
    cube = g.node("GeometryNodeMeshCube")
    ip = g.node("GeometryNodeInstanceOnPoints")
    g.link(sa.outputs[0], ip.inputs["Points"]); g.link(cube.outputs[0], ip.inputs["Instance"])
    if stretch != 1.0:                                   # 속도 방향(로컬 X)으로 늘인 막대
        g.link(g.comb(g.m('MULTIPLY', sz, stretch), sz, sz), ip.inputs["Scale"])
        al = g.node("FunctionNodeAlignRotationToVector")
        try:
            al.axis = 'X'
        except Exception:
            pass
        g.link(v0, al.inputs["Vector"]); g.link(al.outputs[0], ip.inputs["Rotation"])
    else:
        g.link(sz, ip.inputs["Scale"])
    if spin and stretch == 1.0:
        r2 = g.m('FRACT', g.m('MULTIPLY', rnd, 7.31)); r3 = g.m('FRACT', g.m('MULTIPLY', rnd, 3.17))
        e = [g.m('ADD', g.m('MULTIPLY', r, 6.283), g.m('MULTIPLY', g.m('MULTIPLY', g.m('SUBTRACT', r, 0.5), 2.0 * spin), tau)) for r in (rnd, r2, r3)]
        g.link(g.comb(*e), ip.inputs["Rotation"])
    rl = g.node("GeometryNodeRealizeInstances"); g.link(ip.outputs[0], rl.inputs[0])
    sm = g.node("GeometryNodeSetMaterial"); sm.inputs["Material"].default_value = mat
    g.link(rl.outputs[0], sm.inputs["Geometry"]); g.link(sm.outputs[0], go.inputs[0])
    md = ob.modifiers.new("blocks", 'NODES'); md.node_group = ng
    return ob


def _unit(rng):
    while True:
        v = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1)))
        if v.length > 1e-3:
            return v.normalized()


FIRE = dict(cols=[(0.0, (1.0, 1.0, 0.9)), (0.15, (1.0, 0.85, 0.4)), (0.4, (1.0, 0.45, 0.1)), (0.7, (0.6, 0.12, 0.04)), (1.0, (0.15, 0.1, 0.1))],
            emits=[(0.0, 6.0), (0.2, 3.6), (0.6, 2.0), (1.0, 0.0)])     # AgX 기준(grade3). Standard 보기에서는 2를 넘으면 색이 날아가 흰 블록이 된다
SMOKE = dict(cols=[(0.0, (1.0, 0.45, 0.10)), (0.02, (0.6, 0.2, 0.06)), (0.05, (0.05, 0.045, 0.04)), (0.4, (0.10, 0.095, 0.09)), (1.0, (0.18, 0.175, 0.17))],   # 낮 햇빛(세기 3)에서 회색으로 보이는 값
             emits=[(0.0, 3.0), (0.02, 1.5), (0.05, 0.0), (1.0, 0.0)])
EMBER = dict(cols=[(0.0, (1.0, 0.95, 0.7)), (0.4, (1.0, 0.6, 0.2)), (1.0, (0.8, 0.2, 0.05))], emits=[(0.0, 2.6), (0.6, 1.6), (1.0, 0.9)])


# ---------------- 블록 혜성 ----------------
def block_comet3(L, name, head, sun_dir=(1, 0, 0), scale=1.0, tail_len=160.0, seed=4, flow=(1, 600), side=(0, 0, 1),
                 N=6, bsize=0.5, emit=1.0, glow=0.5, rays=14, n_ion=240, n_dust=320, jets=0, spin=0.35, fps=30):
    """블록 혜성(사용자 스케치: 정육면체 머리 + 사방 빛줄기 + 블록 꼬리).
    머리 = 모서리가 깨진 얼음 블록 덩어리(N×N×N, 천천히 구름), 빛줄기 = 바깥으로 흘러 나가며 작아지는 블록 점선,
    꼬리 = 파란 이온 블록(곧게) + 노란 먼지 블록(휘어서)이 끝없이 흐름. glow = 밑에 깔리는 볼륨 빛(코마·꼬리)의 세기 배율(0이면 블록만).
    반환 dict(root, head, ion, dust, rays, jets?, coma?)."""
    rng = random.Random(seed)
    root = X._empty(L, name, head); root.scale = (scale,) * 3
    sd = Vector(sun_dir).normalized(); anti = -sd
    sv = Vector(side); sv = (sv - anti * sv.dot(anti)).normalized()
    Rn = N * bsize / 2
    out = {"root": root}
    vox = {}
    h = (N - 1) / 2
    for i in range(N):
        for j in range(N):
            for k in range(N):
                x, y, z = abs(i - h) / h, abs(j - h) / h, abs(k - h) / h
                corner = x + y + z
                if corner > 2.55 or (corner > 2.05 and rng.random() < 0.55) or (max(x, y, z) == 1 and rng.random() < 0.07):
                    continue
                r = rng.random()
                col = (0.75, 0.90, 1.0) if r < 0.58 else (1.0, 1.0, 1.0) if r < 0.74 else (0.35, 0.62, 0.98) if r < 0.90 else (0.16, 0.20, 0.30)
                vox[(i, j, k)] = col
    hd = L.voxel_mesh(f"{name}_head", vox, bsize, center=(N / 2, N / 2, N / 2), emit=0.75 * emit)   # 낮게: 발광이 세면 면 구분이 사라져 흰 덩어리가 된다
    hd.parent = root; hd.visible_shadow = False
    hd.rotation_euler = (0.5, 0.35, 0.2); hd.keyframe_insert("rotation_euler", frame=flow[0])
    T = (flow[1] - flow[0]) / fps
    hd.rotation_euler = (0.5 + spin * T * 0.6, 0.35 + spin * T, 0.2 + spin * T * 0.3); hd.keyframe_insert("rotation_euler", frame=flow[1])
    X._linear(hd)
    out["head"] = hd
    dd = (anti * 0.93 + sv * 0.37).normalized()
    if glow > 0:
        out["coma"] = X.coma3(L, f"{name}_coma", Rn * 5.0, parent=root, col=(0.7, 0.95, 1.0), emit=0.5 * glow, density=0.05, seed=seed, flow=flow)
        out["ion_glow"] = X.tail3(L, f"{name}_iong", (0, 0, 0), tuple(anti), tail_len, Rn * 3.0, parent=root, kind='ion',
                                  emit=1.8 * glow, density=0.02, seed=seed + 7, flow=flow, speed=6.0, head_w=0.25, fade=1.1)
        dg = X.tail3(L, f"{name}_dustg", (0, 0, 0), tuple(dd), tail_len * 0.75, Rn * 8.0, parent=root, kind='dust', curve=0.55,
                     emit=2.2 * glow, density=0.04, seed=seed + 8, flow=flow, speed=1.0, head_w=0.12, fade=1.6, zscale=2.6,
                     col=(1.0, 0.95, 0.82), col_end=(1.0, 0.82, 0.55))
        M = dg.rotation_euler.to_matrix(); yl = M.col[1]
        target = (sv - dd * sv.dot(dd)).normalized()
        ang = math.atan2(yl.cross(target).dot(dd), yl.dot(target))
        dg.rotation_mode = 'QUATERNION'; dg.rotation_quaternion = (Matrix.Rotation(ang, 3, dd) @ M).to_quaternion()
        out["dust_glow"] = dg
    t0 = flow[0] / fps

    def perp(d):
        v = _unit(rng)
        return v - d * v.dot(d)

    # 이온 꼬리 블록(곧게, 빠르게)
    pts = []
    for _ in range(n_ion):
        life = rng.uniform(2.2, 4.0)
        pts.append(dict(p=tuple(_unit(rng) * Rn * rng.uniform(0.2, 1.0)), v=tuple((anti + perp(anti) * 0.035) * tail_len / life * rng.uniform(0.6, 1.0)),
                        birth=t0 - rng.uniform(0, life), life=life, size=bsize * rng.uniform(0.45, 1.2)))
    out["ion"] = block_particles(L, f"{name}_ion", pts, particle_mat(L, f"{name}_ionm", [(0.0, (0.72, 0.90, 1.0)), (0.3, (0.30, 0.60, 1.0)), (1.0, (0.15, 0.30, 0.95))],
                                 [(0.0, 1.2 * emit), (0.5, 1.0 * emit), (1.0, 0.7 * emit)], unlit=True), loop=True, parent=root, fade_in=0.04, fade_out=0.3, fps=fps)
    # 먼지 꼬리 블록(넓게 퍼지며 side 쪽으로 휨)
    pts = []
    for _ in range(n_dust):
        life = rng.uniform(3.0, 6.0)
        pts.append(dict(p=tuple(_unit(rng) * Rn * rng.uniform(0.2, 1.2)), v=tuple((dd + perp(dd) * 0.13) * tail_len * 0.6 / life * rng.uniform(0.5, 1.0)),
                        birth=t0 - rng.uniform(0, life), life=life, size=bsize * rng.uniform(0.5, 1.6)))
    out["dust"] = block_particles(L, f"{name}_dust", pts, particle_mat(L, f"{name}_dustm", [(0.0, (1.0, 0.95, 0.70)), (0.35, (1.0, 0.80, 0.40)), (1.0, (1.0, 0.50, 0.20))],
                                  [(0.0, 1.15 * emit), (0.5, 1.0 * emit), (1.0, 0.6 * emit)], unlit=True), acc=tuple(sv * tail_len * 0.022), loop=True, parent=root, fade_in=0.04, fade_out=0.35, fps=fps)
    # 사방 빛줄기(블록 점선이 바깥으로 흘러 나가며 작아짐)
    if rays:
        pts = []
        for r in range(rays):
            d = _unit(rng); life = rng.uniform(0.9, 1.5); ph = rng.uniform(0, life)
            sp_ = rng.uniform(7.0, 10.0)
            for q in range(3):
                pts.append(dict(p=tuple(d * Rn * 1.9), v=tuple(d * Rn * sp_), birth=t0 - ph - q * life / 3 - life, life=life,
                                size=bsize * 0.42))
        out["rays"] = block_particles(L, f"{name}_rays", pts, particle_mat(L, f"{name}_raym", [(0.0, (1.0, 1.0, 0.95)), (1.0, (0.6, 0.85, 1.0))],
                                      [(0.0, 2.0 * emit), (1.0, 0.9 * emit)], var=0.05, unlit=True), drag=2.0, loop=True, parent=root, fade_in=0.1, fade_out=0.25, fps=fps, stretch=5.0)
    # 해 받는 쪽 분출(우주 클로즈업용): 얼음 조각이 뿜어져 나옴
    if jets:
        pts = []
        for j in range(jets):
            jd = (sd + _unit(rng) * 0.6).normalized()
            for _ in range(46):
                d = (jd + _unit(rng) * 0.16).normalized(); life = rng.uniform(1.4, 3.0)
                pts.append(dict(p=tuple(jd * Rn * 0.9), v=tuple(d * Rn * rng.uniform(4.0, 9.0)), birth=t0 - rng.uniform(0, life), life=life,
                                size=bsize * rng.uniform(0.18, 0.5)))
        out["jets"] = block_particles(L, f"{name}_jets", pts, particle_mat(L, f"{name}_jetm", [(0.0, (1.0, 1.0, 1.0)), (1.0, (0.6, 0.85, 1.0))],
                                      [(0.0, 1.5 * emit), (1.0, 0.6 * emit)], unlit=True), drag=1.1, loop=True, spin=3.0, parent=root, fade_in=0.05, fade_out=0.4, fps=fps)
    return out


# ---------------- 진입: 블록 연기 줄기 + 불똥 ----------------
def entry_blocks3(L, name, p0, p1, f0, f1, size=6.0, seed=6, n_smoke=340, n_ember=180, fps=30, smoke_life=(5.0, 9.0), smoke_size=1.0):
    """sci_fx3.entry3와 같이 쓴다. 지나간 자리에 블록 연기가 남아 부풀고(주황 → 검정 → 회색), 뒤로 불똥 블록이 튄다."""
    rng = random.Random(seed)
    p0, p1 = Vector(p0), Vector(p1)
    dv = (p1 - p0).normalized()
    pts = []
    for i in range(n_smoke):
        tt = (i + rng.random()) / n_smoke
        f = f0 + tt * (f1 - f0)
        pts.append(dict(p=tuple(p0.lerp(p1, tt) - dv * size * 1.6 + _unit(rng) * size * rng.uniform(0, 0.9)), v=tuple(-dv * size * rng.uniform(0.2, 1.2) + _unit(rng) * size * 0.5),   # 바위 뒤에서 태어남(바위를 가리지 않게)
                        birth=f / fps, life=rng.uniform(*smoke_life), size=size * smoke_size * rng.uniform(0.7, 1.5)))
    out = {"smoke": block_particles(L, f"{name}_bsmoke", pts, particle_mat(L, f"{name}_bsmokem", var=0.5, **SMOKE), drag=1.5, grow=1.3,
                                    fade_in=0.01, fade_out=0.55, fps=fps)}
    pts = []
    for i in range(n_ember):
        tt = rng.random(); f = f0 + tt * (f1 - f0)
        pts.append(dict(p=tuple(p0.lerp(p1, tt) + _unit(rng) * size * 0.6), v=tuple(-dv * size * rng.uniform(2.0, 6.0) + _unit(rng) * size * 3.0),
                        birth=f / fps, life=rng.uniform(0.7, 1.6), size=size * rng.uniform(0.07, 0.2)))
    out["embers"] = block_particles(L, f"{name}_bember", pts, particle_mat(L, f"{name}_bemberm", unlit=True, **EMBER), acc=(0, 0, -size * 1.2), drag=1.0, spin=6.0,
                                    fade_in=0.02, fade_out=0.5, fps=fps)
    return out


# ---------------- 블록 폭발 ----------------
def block_burst3(L, name, center, f, R=50.0, seed=3, fps=30, n_fire=170, n_smoke=420, n_chunk=40, n_ring=120, smoke_life=(5.0, 9.0)):
    """블록 폭발(sci_fx3.airburst3 볼륨과 같이 쓴다): 불 블록이 터져 나갔다 식고 → 블록 연기가 몽글몽글 떠오르고 →
    달아오른 파편이 포물선으로 날아가고 → 흰 블록 고리가 수평으로 퍼진다. R = 불덩이 반지름(m)."""
    rng = random.Random(seed)
    c = Vector(center); t0 = f / fps
    out = {}
    pts = [dict(p=tuple(c + _unit(rng) * R * 0.05), v=tuple(_unit(rng) * R * rng.uniform(1.5, 4.2)), birth=t0 + rng.uniform(0, 0.1),
                life=rng.uniform(1.0, 2.3), size=R * rng.uniform(0.07, 0.17)) for _ in range(n_fire)]
    out["fire"] = block_particles(L, f"{name}_fire", pts, particle_mat(L, f"{name}_firem", unlit=True, **FIRE), drag=4.0, fade_in=0.03, fade_out=0.5, fps=fps)
    pts = [dict(p=tuple(c + _unit(rng) * R * 0.08), v=tuple(_unit(rng) * R * rng.uniform(0.8, 3.3)), birth=t0 + rng.uniform(0.04, 0.5),
                life=rng.uniform(*smoke_life), size=R * rng.choice((0.07, 0.10, 0.14, 0.19, 0.25)) * rng.uniform(0.85, 1.15)) for _ in range(n_smoke)]
    out["smoke"] = block_particles(L, f"{name}_smoke", pts, particle_mat(L, f"{name}_smokem", var=0.55, **SMOKE), acc=(0, 0, R * 0.012), drag=3.5, grow=0.8,
                                   fade_in=0.02, fade_out=0.6, fps=fps)
    # 연기 속에 오래 남는 불씨(구름 안쪽이 한동안 벌겋게 빛남)
    pts = [dict(p=tuple(c + _unit(rng) * R * 0.08), v=tuple(_unit(rng) * R * rng.uniform(0.5, 2.2)), birth=t0 + rng.uniform(0.1, 0.8),
                life=rng.uniform(3.0, 6.5), size=R * rng.uniform(0.05, 0.12)) for _ in range(70)]
    out["core"] = block_particles(L, f"{name}_core", pts, particle_mat(L, f"{name}_corem", [(0.0, (1.0, 0.8, 0.35)), (0.4, (1.0, 0.4, 0.1)), (1.0, (0.5, 0.08, 0.03))],
                                  [(0.0, 2.2), (0.5, 1.5), (1.0, 0.7)], unlit=True), acc=(0, 0, R * 0.012), drag=3.5, fade_in=0.03, fade_out=0.5, fps=fps)
    pts = []
    for _ in range(n_chunk):
        d = _unit(rng); d.z = abs(d.z) * 0.6 + 0.1; d.normalize()
        pts.append(dict(p=tuple(c), v=tuple(d * R * rng.uniform(1.4, 3.0)), birth=t0 + rng.uniform(0, 0.08), life=rng.uniform(2.0, 3.6), size=R * rng.uniform(0.04, 0.09)))
    out["chunks"] = block_particles(L, f"{name}_chunk", pts, particle_mat(L, f"{name}_chunkm", unlit=True, **EMBER), acc=(0, 0, -R * 0.55), drag=0.4, spin=5.0,
                                    fade_in=0.02, fade_out=0.7, fps=fps)
    pts = []
    for i in range(n_ring):
        th = 6.2832 * (i + rng.random() * 0.5) / n_ring
        d = Vector((math.cos(th), math.sin(th), rng.uniform(-0.04, 0.04)))
        pts.append(dict(p=tuple(c + d * R * 0.3), v=tuple(d * R * rng.uniform(4.6, 5.4)), birth=t0 + 0.03, life=rng.uniform(1.0, 1.5), size=R * rng.uniform(0.06, 0.11)))
    out["ring"] = block_particles(L, f"{name}_bring", pts, particle_mat(L, f"{name}_bringm", [(0.0, (1.0, 1.0, 1.0)), (1.0, (0.8, 0.9, 1.0))], [(0.0, 3.0), (0.6, 1.0), (1.0, 0.0)]),
                                  drag=0.8, fade_in=0.03, fade_out=0.3, fps=fps)
    return out


# ---------------- 충격파가 땅·물을 훑고 지나감 ----------------
def shock_front3(L, name, epicenter, f, speed=420.0, r0=60.0, r1=900.0, sector=(0.0, 360.0), z=0.0, n=420, kind="water",
                 size=(1.5, 4.0), fps=30, seed=9, height=3.0, life=(0.4, 0.8)):
    """폭발 바로 아래(epicenter x,y)에서 퍼져 나가는 충격파 자국. 거리 ÷ speed 만큼 늦게 도착한다(먼 곳일수록 나중에).
    kind = 'water'(흰 물보라) / 'dust'(흙먼지) / 'leaf'(잎). sector = 퍼지는 방위 범위(도, +X 기준 반시계) — 카메라 쪽만 뿌려 개수 절약."""
    rng = random.Random(seed)
    ex, ey = epicenter[0], epicenter[1]
    t0 = f / fps
    pts = []
    for _ in range(n):
        r = math.sqrt(rng.uniform(r0 * r0, r1 * r1)); th = math.radians(rng.uniform(*sector))
        d = Vector((math.cos(th), math.sin(th), 0))
        s = rng.uniform(*size)
        pts.append(dict(p=(ex + d.x * r, ey + d.y * r, z), v=tuple(d * speed * 0.035 + Vector((0, 0, height * rng.uniform(1.5, 4.0)))),
                        birth=t0 + r / speed + rng.uniform(-0.04, 0.04), life=rng.uniform(*life), size=s))
    cols = {"water": [(0.0, (1.0, 1.0, 1.0)), (1.0, (0.75, 0.88, 1.0))], "dust": [(0.0, (0.80, 0.74, 0.62)), (1.0, (0.62, 0.60, 0.56))],
            "leaf": [(0.0, (0.30, 0.60, 0.20)), (1.0, (0.22, 0.45, 0.16))]}[kind]
    m = particle_mat(L, f"{name}_m", cols, [(0.0, 0.5), (1.0, 0.0)] if kind == "water" else None)
    return block_particles(L, name, pts, m, acc=(0, 0, -height * 3.0), drag=1.5, spin=4.0 if kind == "leaf" else 0.0, grow=0.6, fade_in=0.05, fade_out=0.45, fps=fps)


def glass_burst3(L, name, tops, epicenter, f, speed=420.0, per=7, fps=30, seed=11, size=(0.8, 1.8), drop=30.0):
    """충격파가 닿는 순간 건물 꼭대기 층 유리가 반짝이며 쏟아진다. tops = [(x,y,z)] (mc_world3.city3가 돌려줌)."""
    rng = random.Random(seed)
    e = Vector(epicenter); t0 = f / fps
    pts = []
    for (x, y, z) in tops:
        p = Vector((x, y, z))
        away = (p - e); dist = away.length; away.z = 0
        if away.length < 1e-3:
            away = Vector((1, 0, 0))
        away.normalize()
        for _ in range(per):
            q = p + Vector((rng.uniform(-8, 8), rng.uniform(-8, 8), -rng.uniform(2, drop)))
            pts.append(dict(p=tuple(q), v=tuple(away * rng.uniform(6, 16) + _unit(rng) * 4.0), birth=t0 + dist / speed + rng.uniform(0, 0.15),
                            life=rng.uniform(1.6, 2.8), size=rng.uniform(*size)))
    m = particle_mat(L, f"{name}_m", [(0.0, (0.85, 0.95, 1.0)), (1.0, (0.55, 0.75, 0.9))], [(0.0, 2.5), (0.3, 0.8), (1.0, 0.3)], rough=0.1)
    return block_particles(L, name, pts, m, acc=(0, 0, -22.0), drag=0.3, spin=9.0, fade_in=0.02, fade_out=0.7, fps=fps)


# ---------------- 임팩트 프레임(컴포지터) ----------------
def impact_comp(L, f, exposure=1.6, dispersion=0.07, invert=False, base_dispersion=0.0, hold=10):
    """render_setup(look='v3') 다음에 호출. 폭발 프레임 f에 노출 번쩍 + 색수차(렌즈 분산)가 튀었다가 hold 프레임 동안 가라앉는다.
    invert=True면 f+1 한 프레임을 반전(애니메이션 임팩트 프레임)."""
    ng = L.SC.compositing_node_group
    if ng is None:
        return None
    N = ng.nodes
    out = [n for n in N if n.bl_idname == "NodeGroupOutput"][0]
    src = out.inputs[0].links[0].from_socket
    done = {}

    def sock(node, *names):
        for nm in names:
            if nm in node.inputs:
                return node.inputs[nm]
        return None

    try:
        ld = N.new("CompositorNodeLensdist")
        ds = sock(ld, "Dispersion")
        if ds is not None:
            X.key_value(ds, [(1, base_dispersion), (f - 1, base_dispersion), (f, dispersion), (f + hold, base_dispersion)])
            ng.links.new(src, ld.inputs["Image"]); src = ld.outputs["Image"]; done["dispersion"] = True
        else:
            N.remove(ld)
    except Exception as ex:
        print("impact_comp lens:", ex)
    try:
        exn = N.new("CompositorNodeExposure")
        es = sock(exn, "Exposure")
        X.key_value(es, [(1, 0.0), (f - 1, 0.0), (f, exposure), (f + 2, exposure * 0.4), (f + hold, 0.0)])
        ng.links.new(src, exn.inputs["Image"]); src = exn.outputs["Image"]; done["exposure"] = True
    except Exception as ex:
        print("impact_comp exposure:", ex)
    inv_path = None
    if invert:
        try:
            iv = N.new("CompositorNodeInvert")
            fs = sock(iv, "Factor", "Fac")
            ng.links.new(src, iv.inputs["Color"] if "Color" in iv.inputs else iv.inputs["Image"])
            for ff, v in ((1, 0.0), (f + 1, 1.0), (f + 2, 0.0)):
                fs.default_value = v; fs.keyframe_insert("default_value", frame=ff)
            src = iv.outputs[0]; inv_path = fs.path_from_id(); done["invert"] = True
        except Exception as ex:
            print("impact_comp invert:", ex)
    ng.links.new(src, out.inputs[0])
    ad = ng.animation_data
    if ad and ad.action:        # 미스트(낮 안개) 키와 반전 키는 CONSTANT로 되돌림(key_value가 그룹 전체를 LINEAR로 바꿈)
        try:
            fcs = list(ad.action.fcurves)
        except AttributeError:
            fcs = [fc for ly in ad.action.layers for st in ly.strips for cb in st.channelbags for fc in cb.fcurves]
        for fc in fcs:
            keep_linear = ("Dispersion" in fc.data_path or "Exposure" in fc.data_path) and not (inv_path and fc.data_path.startswith(inv_path))
            lin = False
            try:
                node_name = fc.data_path.split('"')[1]
                lin = N[node_name].bl_idname in ("CompositorNodeLensdist", "CompositorNodeExposure")
            except Exception:
                lin = keep_linear
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR' if lin else 'CONSTANT'
    print("IMPACT_COMP", done)
    return done


# ---------------- 화면 마무리(빛 번짐 종류 바로잡기) ----------------
def look3(L, glare="Bloom", strength=0.22, threshold=1.6, size=0.4):
    """render_setup(look='v3') 다음에 호출. 블렌더 5.x에서는 빛 번짐 종류가 노드 입력("Type")으로 바뀌어
    lib_mc의 glare_type 설정이 조용히 무시되고 기본값 Streaks(십자 줄무늬)로 렌더된다 → 여기서 Bloom(부드러운 번짐)으로 바로잡는다.
    glare = 'Bloom' / 'Fog Glow'(더 곱지만 느림) / 'Streaks'(십자 반짝임)."""
    ng = L.SC.compositing_node_group
    if ng is None:
        return
    for n in ng.nodes:
        if n.bl_idname == "CompositorNodeGlare":
            for k, v in (("Type", glare), ("Quality", "High"), ("Threshold", threshold), ("Strength", strength), ("Size", size)):
                try:
                    n.inputs[k].default_value = v
                except Exception as ex:
                    print("look3", k, ex)


# ---------------- 색감(색 관리) ----------------
def grade3(L, view="AgX", look="AgX - Punchy", exposure=0.0, saturation=1.3):
    """render_setup(look='v3') 다음에 호출. 사용자 지적(2026-11-05): "노출이 높은 사진 같아", "타는 느낌은 없애줘".
    lib_mc 기본값인 Standard 보기는 1을 넘는 밝기를 그대로 잘라 버려서 노을 지평선·물 반사·켜진 창이 노랗게/하얗게 타 보인다.
    AgX는 밝은 곳을 부드럽게 눌러 담는다(사진기의 넓은 관용도). 대신 채도가 조금 빠지므로 Punchy 룩 + 컴포지터 채도 1.3으로 블록 색을 되살린다.
    exposure = 전체 노출(스톱). 완성 편(1~6화)은 Standard 그대로 둔다."""
    vs = L.SC.view_settings
    vs.view_transform = view
    try:
        vs.look = look
    except Exception as ex:
        print("grade3 look:", ex)
    vs.exposure = exposure
    ng = L.SC.compositing_node_group
    if ng is not None:
        for n in ng.nodes:
            if n.bl_idname == "CompositorNodeColorCorrection" and "Saturation" in n.inputs:
                n.inputs["Saturation"].default_value = saturation


# ---------------- 블록만으로 만든 진입(볼륨 없음) ----------------
def _vis(objs, keys):
    for o in objs:
        for f, v in keys:
            o.hide_render = not v; o.hide_viewport = not v
            o.keyframe_insert("hide_render", frame=f); o.keyframe_insert("hide_viewport", frame=f)
        ad = o.animation_data
        try:
            fcs = list(ad.action.fcurves)
        except AttributeError:
            fcs = [fc for ly in ad.action.layers for st in ly.strips for cb in st.channelbags for fc in cb.fcurves]
        for fc in fcs:
            if "hide" in fc.data_path:
                for kp in fc.keyframe_points:
                    kp.interpolation = 'CONSTANT'


def block_entry3(L, name, p0, p1, f0, f1, size=6.0, seed=6, split_at=None, n_pieces=4, burst_R=None, n_smoke=340, n_ember=180,
                 smoke_life=(5.0, 9.0), smoke_size=1.0, light=True, fps=30, lines=28, hot=(2.0, 4.0)):
    """볼륨 없이 블록만으로 만든 대기권 진입: 달아오른 복셀 바위 + 뒤로 뻗는 속도선 + 남는 블록 연기 + 불똥
    (+ split_at에 쪼개짐, burst_R을 주면 f1에 블록 폭발과 섬광). size = 바위 반지름(m).
    볼륨이 없어서 숏별 볼륨 깊이(vol_shots)를 맞출 필요가 없다 → 실내 창밖·먼 하늘·짧은 별똥별 숏에 쓴다."""
    rng = random.Random(seed)
    p0, p1 = Vector(p0), Vector(p1)
    dv = (p1 - p0).normalized()
    root = X._empty(L, name, tuple(p0))
    out = {"root": root}
    rock = X.nucleus3(L, f"{name}_rock", R=6, size=size / 6.0, seed=seed, lobes=False, craters=2)
    rock.parent = root; rock.visible_shadow = False
    rock.data.materials.clear()
    rock.data.materials.append(X._hot_mat(L, f"{name}_rockm", [(f0, hot[0]), (f1, hot[1])], col=(1.0, 0.42, 0.10)))
    rock.rotation_euler = (0, 0, 0); rock.keyframe_insert("rotation_euler", frame=f0)
    rock.rotation_euler = (2.0, 1.2, 0.6); rock.keyframe_insert("rotation_euler", frame=f1); X._linear(rock)
    out["rock"] = rock
    if lines:                      # 속도선: 바위 둘레에서 뒤로 뻗는 막대
        pts = []
        for _ in range(lines):
            d = _unit(rng); d = (d - dv * d.dot(dv))
            d = d.normalized() if d.length > 1e-3 else Vector((0, 0, 1))
            life = rng.uniform(0.25, 0.5)
            pts.append(dict(p=tuple(d * size * rng.uniform(0.9, 1.5) + dv * size * 0.5), v=tuple(-dv * size * rng.uniform(8.0, 14.0)),
                            birth=f0 / fps - rng.uniform(0, life), life=life, size=size * 0.11))
        out["lines"] = block_particles(L, f"{name}_lines", pts, particle_mat(L, f"{name}_linem", [(0.0, (1.0, 0.95, 0.8)), (1.0, (1.0, 0.5, 0.15))],
                                       [(0.0, 4.0), (1.0, 1.5)], var=0.05, unlit=True), loop=True, parent=root, fade_in=0.1, fade_out=0.3, fps=fps, stretch=6.0)
    if light:
        lt = bpy.data.lights.new(L.prefix + name + "_L", 'POINT'); lt.color = (1.0, 0.7, 0.4); lt.shadow_soft_size = size * 2
        lt.volume_factor = 0.0
        lo = bpy.data.objects.new(name + "_L", lt); L.coll.objects.link(lo); lo.parent = root
        e = 3e3 * size * size
        for ff, ee in ((f0 - 1, 0), (f0, e), (f1, e * 4), (f1 + 1, 0)):
            lt.energy = ee; lt.keyframe_insert("energy", frame=ff)
    root.location = p0; root.keyframe_insert("location", frame=f0)
    root.location = p1; root.keyframe_insert("location", frame=f1)
    X._linear(root, "location")
    _vis([root] + list(root.children_recursive), [(f0 - 1, False), (f0, True), (f1 + 1, False)])
    if n_smoke > 0 or n_ember > 0:
        out.update(entry_blocks3(L, name, tuple(p0), tuple(p1), f0, f1, size=size, seed=seed, n_smoke=max(1, n_smoke), n_ember=max(1, n_ember),
                                 fps=fps, smoke_life=smoke_life, smoke_size=smoke_size))
    if split_at:
        _vis([rock], [(f0 - 1, False), (f0, True), (split_at, False)])
        out["pieces"] = []
        for k in range(n_pieces):
            pc = X.nucleus3(L, f"{name}_pc{k}", R=4, size=size * 0.55 / 4.0, seed=seed + 10 + k, lobes=False, craters=1)
            pc.visible_shadow = False
            pc.data.materials.clear(); pc.data.materials.append(X._hot_mat(L, f"{name}_pcm{k}", [(1, hot[1])], col=(1.0, 0.5, 0.15)))
            off = _unit(rng); off = (off - dv * off.dot(dv)).normalized()
            for ff in range(split_at, f1 + 1, 2):
                tt = (ff - f0) / max(1, f1 - f0); ts = (ff - split_at) / max(1, f1 - split_at)
                pc.location = p0.lerp(p1, tt) + off * size * (0.6 + 3.5 * ts * ts) - dv * size * 1.5 * ts * k / n_pieces
                pc.keyframe_insert("location", frame=ff)
            _vis([pc], [(split_at - 1, False), (split_at, True), (f1 + 1, False)])
            out["pieces"].append(pc)
    if burst_R:
        out["burst"] = block_burst3(L, f"{name}_bb", tuple(p1), f1, R=burst_R, seed=seed, fps=fps)
        lt = bpy.data.lights.new(L.prefix + name + "_FL", 'POINT'); lt.color = (1.0, 0.92, 0.8); lt.shadow_soft_size = burst_R * 0.3
        lt.volume_factor = 0.0
        lo = bpy.data.objects.new(name + "_FL", lt); L.coll.objects.link(lo); lo.location = p1
        fl = 6e7 * (burst_R / 170.0) ** 2
        for ff, ee in ((f1 - 1, 0), (f1, fl), (f1 + 4, fl * 0.45), (f1 + 20, fl * 0.1), (f1 + 60, 0)):
            lt.energy = ee; lt.keyframe_insert("energy", frame=ff)
        out["flash"] = lo
    return out
