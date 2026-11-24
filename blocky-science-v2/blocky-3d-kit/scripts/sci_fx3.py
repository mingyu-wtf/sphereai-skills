# 과학 연출 v3 (2026-11-05, 사용자 "혜성도 따로 모델링 해서 더 리얼하게 / 전반적으로 퀄리티를 올려줘")
#  블록 세계는 유지(핵·건물·캐릭터 = 블록), "빛과 기체"만 진짜처럼 → Eevee 볼륨 셰이더
#    nucleus3     : 복셀 핵(작은 블록, 크레이터, 얼음 노출, 아주 어두운 탄소 표면)
#    comet3       : 핵 + 제트 + 코마(초록빛 C2 발광) + 이온 꼬리(곧은 파랑 줄무늬) + 먼지 꼬리(휜 노랑-흰색)
#    entry3       : 대기권 진입 — 달아오른 핵 + 플라스마 껍질 + 뒤쪽 불꽃 꼬리 + 남아서 부푸는 연기 기둥 + 불똥 + 쪼개짐
#    airburst3    : 공중 폭발 — 흑체 온도(6500K→식음)로 색이 변하는 불덩이 → 떠오르는 연기, 충격파 고리, 섬광
#    sky3         : 물리 하늘(대기 산란) + 해 고도 키 / cloud_bank3: 볼륨 적운
#    volume_setup : Eevee 볼륨 품질 설정(render_setup 뒤에 호출)
# 쓰는 법은 config/04_blender_upgrade_guide.md 2장
import bpy, bmesh, math, random
from mathutils import Vector, Matrix

P = 1 / 16


# ---------------- 노드 도우미 ----------------
class G:
    def __init__(self, nt):
        self.nt, self.N = nt, nt.nodes

    def node(self, typ, **kw):
        n = self.N.new(typ)
        for k, v in kw.items():
            setattr(n, k, v)
        return n

    def link(self, out, inp):
        self.nt.links.new(out, inp)

    def _in(self, sock, v):
        if isinstance(v, (int, float)):
            sock.default_value = v
        else:
            self.link(v, sock)

    def m(self, op, a, b=None, c=None, clamp=False):
        n = self.node("ShaderNodeMath", operation=op, use_clamp=clamp)
        self._in(n.inputs[0], a)
        if b is not None:
            self._in(n.inputs[1], b)
        if c is not None:
            self._in(n.inputs[2], c)
        return n.outputs[0]

    def smooth(self, x, a, b, lo=0.0, hi=1.0):
        n = self.node("ShaderNodeMapRange", interpolation_type='SMOOTHSTEP')
        self._in(n.inputs["Value"], x)
        n.inputs["From Min"].default_value = a; n.inputs["From Max"].default_value = b
        n.inputs["To Min"].default_value = lo; n.inputs["To Max"].default_value = hi
        return n.outputs["Result"]

    def xyz(self, vec):
        s = self.node("ShaderNodeSeparateXYZ"); self.link(vec, s.inputs[0])
        return s.outputs[0], s.outputs[1], s.outputs[2]

    def comb(self, x, y, z):
        c = self.node("ShaderNodeCombineXYZ")
        for i, v in enumerate((x, y, z)):
            self._in(c.inputs[i], v)
        return c.outputs[0]

    def noise(self, vec, scale=3.0, detail=6.0, rough=0.55, w=None, distort=0.0):
        n = self.node("ShaderNodeTexNoise")
        if w is not None:
            n.noise_dimensions = '4D'; self._in(n.inputs["W"], w)
        self.link(vec, n.inputs["Vector"])
        n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = rough
        if "Distortion" in n.inputs:
            n.inputs["Distortion"].default_value = distort
        return n.outputs["Fac"]

    def value(self, v=0.0):
        n = self.node("ShaderNodeValue"); n.outputs[0].default_value = v
        return n.outputs[0]

    def ramp(self, x, stops):
        r = self.node("ShaderNodeValToRGB"); self._in(r.inputs[0], x)
        el = r.color_ramp.elements
        while len(el) > 2:
            el.remove(el[-1])
        for i, (pos, col) in enumerate(stops):
            e = el[i] if i < 2 else el.new(pos)
            e.position = pos; e.color = tuple(col) + ((1.0,) if len(col) == 3 else ())
        return r.outputs["Color"]


def key_value(sock, keys, interp='LINEAR'):
    """노드 소켓 값 키 [(frame, v)]."""
    for f, v in keys:
        sock.default_value = v; sock.keyframe_insert("default_value", frame=f)
    nt = sock.id_data
    ad = nt.animation_data
    if not ad or not ad.action:
        return
    fcs = []
    try:
        fcs = list(ad.action.fcurves)
    except AttributeError:
        for ly in ad.action.layers:
            for st in ly.strips:
                for cb in st.channelbags:
                    fcs.extend(cb.fcurves)
    for fc in fcs:
        for kp in fc.keyframe_points:
            kp.interpolation = interp


def _linear(ob, path=None):
    ad = ob.animation_data
    if not ad or not ad.action:
        return
    fcs = []
    try:
        fcs = list(ad.action.fcurves)
    except AttributeError:
        for ly in ad.action.layers:
            for st in ly.strips:
                for cb in st.channelbags:
                    fcs.extend(cb.fcurves)
    for fc in fcs:
        if path is None or fc.data_path == path:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'


def vol_mat(L, name):
    """빈 볼륨 재질(표면 없음). (mat, G, principled_volume) 반환."""
    m = bpy.data.materials.new(L.prefix + name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            nt.nodes.remove(n)
    out = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    g = G(nt)
    pv = g.node("ShaderNodeVolumePrincipled")
    g.link(pv.outputs[0], out.inputs["Volume"])
    return m, g, pv


def obj_coords(g):
    tc = g.node("ShaderNodeTexCoord")
    return tc.outputs["Object"]


# ---------------- 볼륨 그릇(메쉬) ----------------
def _mesh_ob(L, name, bm, parent=None):
    me = bpy.data.meshes.new(L.prefix + name)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); L.coll.objects.link(ob)
    if parent:
        ob.parent = parent
    ob.visible_shadow = False
    return ob


def sphere_domain(L, name, radius=1.0, subdiv=3, parent=None):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=radius)
    return _mesh_ob(L, name, bm, parent)


def box_domain(L, name, x=(0, 1), y=(-1, 1), z=(-1, 1), parent=None):
    """로컬 좌표 상자(볼륨 셰이더가 오브젝트 좌표를 그대로 씀 → 꼬리는 x 0~1 = 머리~끝)."""
    bm = bmesh.new()
    vs = [bm.verts.new((xx, yy, zz)) for xx in x for yy in y for zz in z]
    idx = lambda i, j, k: vs[i * 4 + j * 2 + k]
    for f in ((0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)), ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)), \
             ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)), ((0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)), \
             ((0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)), ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)):
        bm.faces.new([idx(*c) for c in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _mesh_ob(L, name, bm, parent)


def aim(ob, direction, up=(0, 0, 1)):
    """로컬 +X를 direction으로."""
    d = Vector(direction).normalized()
    u = Vector(up)
    if abs(d.dot(u.normalized())) > 0.98:
        u = Vector((0, 1, 0))
    yv = u.cross(d).normalized()          # 오른손 좌표: x=d, y=up×d, z=x×y(≈up)
    zv = d.cross(yv).normalized()
    M = Matrix((d, yv, zv)).transposed()
    ob.rotation_euler = M.to_euler()


# ---------------- 핵 ----------------
def _n3(x, y, z, s):
    return (math.sin(x * 1.7 + s) * math.cos(y * 1.3 - s * 0.7) + math.sin(z * 2.1 + y * 0.9 + s * 1.3) * 0.6
            + math.sin((x + y + z) * 3.3 + s * 2.1) * 0.25 + math.sin(x * 5.1 - z * 4.3 + s) * 0.12)


def nucleus3(L, name, R=14, size=0.25, seed=3, lobes=True, ice=0.10, craters=7, hot=0.0):
    """감자·오리 모양(두 덩어리) 핵. R = 블록 반지름. hot>0이면 달아오른 진입 조각(표면 발광)."""
    rng = random.Random(seed)
    cr = []
    for _ in range(craters):
        v = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))).normalized() * R * 0.95
        cr.append((v, R * rng.uniform(0.18, 0.38)))
    vox = {}
    rng2 = random.Random(seed + 1)
    for i in range(-R - 3, R + 4):
        for j in range(-R - 3, R + 4):
            for k in range(-R - 3, R + 4):
                p = Vector((i, j, k))
                # 큰 몸통 + (lobes) 작은 머리가 붙은 67P 같은 모양
                d1 = math.sqrt((i / 1.0) ** 2 + (j / 0.78) ** 2 + (k / 0.70) ** 2)
                r1 = R * 0.78 * (1 + 0.16 * _n3(i * 0.22, j * 0.22, k * 0.22, seed))
                inside = d1 < r1
                if lobes:
                    q = p - Vector((R * 0.55, 0, R * 0.42))
                    d2 = math.sqrt((q.x / 0.8) ** 2 + (q.y / 0.7) ** 2 + (q.z / 0.66) ** 2)
                    r2 = R * 0.48 * (1 + 0.18 * _n3(i * 0.3, j * 0.3, k * 0.3, seed + 5))
                    inside = inside or d2 < r2
                if not inside:
                    continue
                if any((p - c).length < rad for c, rad in cr):
                    continue
                # 겉껍질만(속은 비움) — 6이웃 중 하나라도 바깥이면 표면
                vox[(i, j, k)] = None
    keys = set(vox)
    out = {}
    for (i, j, k) in keys:
        if all((i + a, j + b, k + c) in keys for a, b, c in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))):
            continue
        if hot > 0:
            t = rng2.random()
            col = (1.0, 0.55 + 0.3 * t, 0.22 + 0.25 * t) if t > 0.35 else (0.35, 0.16, 0.08)
        elif rng2.random() < ice and _n3(i * 0.5, j * 0.5, k * 0.5, seed + 9) > 0.35:
            col = (0.80, 0.86, 0.92)                 # 드러난 얼음
        else:
            g = rng2.uniform(0.055, 0.11) * (1 + 0.35 * _n3(i * 0.4, j * 0.4, k * 0.4, seed + 3))
            col = (g, g * 0.96, g * 0.92)            # 실제 혜성 핵은 숯처럼 어둡다(반사율 4%)
        out[(i, j, k)] = col
    ob = L.voxel_mesh(name, out, size, center=(0, 0, 0), emit=hot)
    bs = ob.data.materials[0].node_tree.nodes["Principled BSDF"]
    bs.inputs["Roughness"].default_value = 0.92
    return ob


# ---------------- 코마·꼬리·제트 ----------------
def coma3(L, name, radius, parent=None, col=(0.62, 1.0, 0.78), emit=6.0, density=0.15, seed=1, flow=(1, 600)):
    """핵 둘레 빛 구름. 안쪽이 아주 밝고 바깥으로 갈수록 옅어짐. 실제 혜성 코마는 C2 분자 때문에 초록빛."""
    ob = sphere_domain(L, name, 1.0, 3, parent)
    ob.scale = (radius,) * 3
    m, g, pv = vol_mat(L, name)
    co = obj_coords(g)
    t = g.value(0.0); key_value(t, [(flow[0], 0.0), (flow[1], (flow[1] - flow[0]) / 300.0)])
    r = g.node("ShaderNodeVectorMath", operation='LENGTH'); g.link(co, r.inputs[0]); r = r.outputs["Value"]
    halo = g.m('POWER', g.m('SUBTRACT', 1.0, r, clamp=True), 2.2)
    core = g.m('EXPONENT', g.m('MULTIPLY', g.m('MULTIPLY', r, r), -60.0))
    nz = g.smooth(g.noise(co, 2.2, 5, 0.6, w=t), 0.3, 0.75, 0.55, 1.15)
    field = g.m('ADD', g.m('MULTIPLY', halo, nz), g.m('MULTIPLY', core, 2.5))
    wr = radius * _wscale(parent)
    g.link(g.m('MULTIPLY', field, density / wr), pv.inputs["Density"])
    pv.inputs["Color"].default_value = tuple(col) + (1,)
    pv.inputs["Emission Color"].default_value = tuple(col) + (1,)
    g.link(g.m('MULTIPLY', field, emit / wr), pv.inputs["Emission Strength"])
    ob.data.materials.append(m)
    return ob


def tail3(L, name, head, direction, length, width, parent=None, kind="dust", curve=0.0, emit=3.0, density=0.05,
          col=None, col_end=None, seed=2, flow=(1, 600), speed=1.0, head_w=0.08, zscale=1.0, fade=1.4):
    """꼬리 볼륨. kind = 'ion'(곧고 가는 줄무늬) / 'dust'(넓고 부드럽게 휨) / 'jet'(짧은 분출) / 'wake'(진입 불꽃).
    오브젝트 좌표 x 0(머리)~1(끝), y·z = ±1 × width. curve>0이면 +y 쪽으로 휜다."""
    ob = box_domain(L, name, x=(0, 1), y=(-1, 1 + curve * 1.2), z=(-1, 1), parent=parent)
    ob.location = head
    ob.scale = (length, width, width)
    aim(ob, direction)
    m, g, pv = vol_mat(L, name)
    co = obj_coords(g)
    x, y, z = g.xyz(co)
    u = g.m('MAXIMUM', g.m('MINIMUM', x, 1.0), 0.0)
    yc = g.m('SUBTRACT', y, g.m('MULTIPLY', g.m('MULTIPLY', u, u), curve))
    w = g.m('ADD', head_w, g.m('MULTIPLY', 1.0 - head_w, g.m('POWER', u, 0.65 if kind != 'ion' else 0.9)))
    rr = g.m('DIVIDE', g.m('ADD', g.m('MULTIPLY', yc, yc), g.m('MULTIPLY', g.m('MULTIPLY', z, z), zscale * zscale)), g.m('MULTIPLY', w, w))
    radial = g.m('EXPONENT', g.m('MULTIPLY', rr, -3.2 if kind != 'ion' else -5.0))
    along = g.m('MULTIPLY', g.m('POWER', g.m('SUBTRACT', 1.0, u, clamp=True), fade), g.smooth(u, 0.0, 0.025))
    t = g.value(0.0); key_value(t, [(flow[0], 0.0), (flow[1], speed * (flow[1] - flow[0]) / 30.0)])
    # 흘러가는 좌표(꼬리 방향으로 물질이 밀려남)
    flowx = g.m('SUBTRACT', g.m('MULTIPLY', u, 1.0), g.m('MULTIPLY', t, 0.08))
    if kind == 'ion':
        nv = g.comb(g.m('MULTIPLY', flowx, 1.2), g.m('MULTIPLY', g.m('DIVIDE', yc, w), 7.0), g.m('MULTIPLY', g.m('DIVIDE', z, w), 7.0))
        st = g.smooth(g.noise(nv, 1.0, 4, 0.5, w=g.m('MULTIPLY', t, 0.05)), 0.38, 0.72, 0.15, 1.3)
        nv2 = g.comb(g.m('MULTIPLY', flowx, 9.0), g.m('MULTIPLY', yc, 3.0), g.m('MULTIPLY', z, 3.0))
        knot = g.smooth(g.noise(nv2, 1.0, 3, 0.5), 0.45, 0.8, 0.7, 1.4)
        streak = g.m('MULTIPLY', st, knot)
    elif kind in ('jet', 'wake'):
        nv = g.comb(g.m('MULTIPLY', flowx, 6.0), g.m('MULTIPLY', yc, 2.5), g.m('MULTIPLY', z, 2.5))
        streak = g.smooth(g.noise(nv, 1.0, 6, 0.6, w=g.m('MULTIPLY', t, 0.3)), 0.3, 0.75, 0.2, 1.3)
    else:
        nv = g.comb(g.m('MULTIPLY', flowx, 2.2), g.m('MULTIPLY', yc, 1.4), g.m('MULTIPLY', z, 1.4))
        nv3 = g.comb(g.m('MULTIPLY', flowx, 0.6), g.m('MULTIPLY', yc, 6.0), z)  # 먼지 꼬리 결(싱크로나 줄)
        streak = g.m('MULTIPLY', g.smooth(g.noise(nv, 1.0, 5, 0.55, w=g.m('MULTIPLY', t, 0.04)), 0.3, 0.75, 0.55, 1.15),
                     g.smooth(g.noise(nv3, 1.0, 2, 0.4), 0.35, 0.7, 0.75, 1.15))
    field = g.m('MULTIPLY', g.m('MULTIPLY', radial, along), streak)
    if col is None:
        col = {'ion': (0.30, 0.55, 1.0), 'dust': (1.0, 0.93, 0.78), 'jet': (0.85, 0.95, 1.0), 'wake': (1.0, 0.85, 0.55)}[kind]
    if col_end is not None:
        c = g.ramp(u, [(0.0, col), (1.0, col_end)])
        g.link(c, pv.inputs["Emission Color"]); g.link(c, pv.inputs["Color"])
    else:
        pv.inputs["Emission Color"].default_value = tuple(col) + (1,)
        pv.inputs["Color"].default_value = tuple(col) + (1,)
    ww = width * _wscale(parent)          # 세기 = 가운데를 지나는 빛 한 줄의 밝기(크기와 무관)
    g.link(g.m('MULTIPLY', field, density / ww), pv.inputs["Density"])
    g.link(g.m('MULTIPLY', field, emit / ww), pv.inputs["Emission Strength"])
    ob.data.materials.append(m)
    return ob


def _wscale(parent):
    s = 1.0
    while parent is not None:
        s *= max(parent.scale)
        parent = parent.parent
    return s


def _empty(L, name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None); L.coll.objects.link(e)
    e.location = loc
    if parent:
        e.parent = parent
    return e


def comet3(L, name, head, sun_dir=(1, 0, 0), scale=1.0, tail_len=160.0, seed=4, flow=(1, 600), emit=1.0,
           nucleus=True, jets=4, nuc_R=14, nuc_size=0.25, spin=0.25, side=(0, 0, 1)):
    """완성 혜성. scale = 전체 크기 배율(핵 반지름 ≈ nuc_R*nuc_size*scale).
    sun_dir = 태양 쪽 방향 → 이온 꼬리는 정반대로 곧게, 먼지 꼬리는 궤도 뒤쪽(side 쪽)으로 휜다.
    반환 dict(root, nuc, coma, ion, dust, jets)."""
    rng = random.Random(seed)
    root = _empty(L, name, head)
    root.scale = (scale,) * 3
    sd = Vector(sun_dir).normalized()
    anti = -sd
    out = {"root": root, "jets": []}
    Rn = nuc_R * nuc_size
    if nucleus:
        nuc = nucleus3(L, f"{name}_nuc", R=nuc_R, size=nuc_size, seed=seed)
        nuc.parent = root
        nuc.rotation_euler = (0.4, 0.2, 0.0); nuc.keyframe_insert("rotation_euler", frame=flow[0])
        nuc.rotation_euler = (0.4, 0.2, spin * (flow[1] - flow[0]) / 30.0); nuc.keyframe_insert("rotation_euler", frame=flow[1])
        _linear(nuc)
        out["nuc"] = nuc
        for j in range(jets):        # 해를 받는 쪽에서 가스가 뿜어져 나옴
            v = (sd + Vector((rng.gauss(0, 0.55), rng.gauss(0, 0.55), rng.gauss(0, 0.55)))).normalized()
            jt = tail3(L, f"{name}_jet{j}", tuple(v * Rn * 0.8), tuple(v), Rn * rng.uniform(3.0, 5.0), Rn * 0.9,
                       parent=root, kind='jet', emit=2.2 * emit, density=0.4, seed=seed + j, flow=flow, speed=3.0, head_w=0.12, fade=1.8)
            out["jets"].append(jt)
    out["coma"] = coma3(L, f"{name}_coma", Rn * 7.0, parent=root, emit=0.45 * emit, density=0.06, seed=seed, flow=flow)
    out["coma_in"] = coma3(L, f"{name}_coma2", Rn * 2.6, parent=root, col=(0.85, 1.0, 0.92), emit=0.9 * emit, density=0.25, seed=seed + 1, flow=flow)
    # 꼬리 평면: anti와 side로 만든 면 안에서 휨
    sv = Vector(side)
    sv = (sv - anti * sv.dot(anti)).normalized()
    ion = tail3(L, f"{name}_ion", (0, 0, 0), tuple(anti), tail_len, Rn * 3.2, parent=root, kind='ion',
                emit=1.8 * emit, density=0.02, seed=seed + 7, flow=flow, speed=6.0, head_w=0.25, fade=1.1, zscale=1.0)
    dust_dir = (anti * 0.93 + sv * 0.37).normalized()
    dust = tail3(L, f"{name}_dust", (0, 0, 0), tuple(dust_dir), tail_len * 0.75, Rn * 9.0, parent=root, kind='dust', curve=0.55,
                 emit=2.6 * emit, density=0.05, seed=seed + 8, flow=flow, speed=1.0, head_w=0.12, fade=1.6, zscale=2.6,
                 col=(1.0, 0.95, 0.82), col_end=(1.0, 0.82, 0.55))
    # 먼지 꼬리 휨 방향(+y)을 side 쪽으로 돌림
    M = dust.rotation_euler.to_matrix()
    yl = M.col[1]
    target = (sv - dust_dir * sv.dot(dust_dir)).normalized()
    ang = math.atan2(yl.cross(target).dot(dust_dir), yl.dot(target))
    rot = Matrix.Rotation(ang, 3, dust_dir) @ M
    dust.rotation_mode = 'QUATERNION'
    dust.rotation_quaternion = rot.to_quaternion()
    out["ion"], out["dust"] = ion, dust
    return out


# ---------------- 대기권 진입 ----------------
def _hot_mat(L, name, emit_keys, col=(1.0, 0.75, 0.45)):
    m = bpy.data.materials.new(L.prefix + name); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (0.12, 0.07, 0.05, 1)
    bs.inputs["Emission Color"].default_value = tuple(col) + (1,)
    key_value(bs.inputs["Emission Strength"], emit_keys)
    return m


def entry3(L, name, p0, p1, f0, f1, size=6.0, seed=6, split_at=None, n_pieces=4, smoke_w=(0.6, 9.0),
           wake_len=14.0, sparks=60, burst=True, burst_R=None, sheath=1.0, wake=1.0, trail=1.0):
    """p0→p1(f0~f1) 진입. size = 조각 반지름(m). 지나간 자리에 연기 기둥이 남아 천천히 부푼다.
    sheath·wake = 플라스마 껍질·불꽃 꼬리 밝기 배율(가까이서 찍는 숏은 0.4~0.6: 1이면 블록 바위가 빛에 묻힘).
    trail = 볼륨 연기 기둥 짙기 배율. 블록 연기(block_fx3.entry_blocks3)를 같이 쓰면 0.1~0.2로 — 머리 바로 뒤 연기가
    아주 짙어서(폭이 좁을 때) 햇빛을 받으면 새하얀 덩어리가 되어 바위를 가린다.
    반환 dict(root, trail, light, burst?)."""
    rng = random.Random(seed)
    p0, p1 = Vector(p0), Vector(p1)
    dv = (p1 - p0); path_len = dv.length; dv.normalize()
    root = _empty(L, name, tuple(p0))
    out = {"root": root}
    # 조각(복셀 바위, 달아오름)
    rock = nucleus3(L, f"{name}_rock", R=9, size=size / 9.0, seed=seed, lobes=False, craters=3, hot=0.0)
    rock.parent = root
    rock.data.materials.clear()
    rock.data.materials.append(_hot_mat(L, f"{name}_rockmat", [(f0, 0.45), (f1, 1.3)]))   # 1.6 넘으면 빛 번짐이 바위 전체를 하얀 공으로 덮음
    rock.rotation_euler = (0, 0, 0); rock.keyframe_insert("rotation_euler", frame=f0)
    rock.rotation_euler = (2.0, 1.2, 0.6); rock.keyframe_insert("rotation_euler", frame=f1); _linear(rock)
    # 플라스마 껍질(앞쪽이 가장 밝은 달걀 모양)
    sh = sphere_domain(L, f"{name}_sheath", 1.0, 3, root)
    sh.scale = (size * 1.9, size * 1.9, size * 1.9)
    m, g, pv = vol_mat(L, f"{name}_sheath")
    co = obj_coords(g)
    r = g.node("ShaderNodeVectorMath", operation='LENGTH'); g.link(co, r.inputs[0]); r = r.outputs["Value"]
    shell = g.m('EXPONENT', g.m('MULTIPLY', g.m('MULTIPLY', g.m('SUBTRACT', r, 0.55), g.m('SUBTRACT', r, 0.55)), -30.0))
    loc_dir = g.node("ShaderNodeVectorMath", operation='DOT_PRODUCT'); g.link(co, loc_dir.inputs[0])
    loc_dir.inputs[1].default_value = (0, 0, 0)
    front = g.smooth(loc_dir.outputs["Value"], -0.3, 0.6, 0.35, 1.6)
    field = g.m('MULTIPLY', g.m('MULTIPLY', shell, front), g.smooth(r, 1.0, 0.8))
    pv.inputs["Emission Color"].default_value = (1.0, 0.62, 0.30, 1)
    pv.inputs["Density"].default_value = 0.0
    E = g.value(0.0); key_value(E, [(f0, 0.5 * sheath / (size * 1.9)), (f1, 1.4 * sheath / (size * 1.9))])
    g.link(g.m('MULTIPLY', field, E), pv.inputs["Emission Strength"])
    sh.data.materials.append(m)
    # 진행 방향 단위벡터를 껍질 로컬로(루트는 회전 없음 → 월드 = 로컬)
    loc_dir.inputs[1].default_value = tuple(dv)
    # 뒤쪽 불꽃 꼬리(흰색 → 주황 → 빨강)
    wk0 = tail3(L, f"{name}_wake", (0, 0, 0), tuple(-dv), size * wake_len, size * 1.6, parent=root, kind='wake',
                 emit=1.1 * wake, density=0.15, flow=(f0, f1 + 200), speed=8.0, head_w=0.55, fade=1.3,
                 col=(1.0, 0.92, 0.75), col_end=(0.9, 0.25, 0.08))
    out["wake"] = wk0
    # 빛
    lt = bpy.data.lights.new(L.prefix + name + "_L", 'POINT'); lt.color = (1.0, 0.78, 0.5); lt.shadow_soft_size = size * 2
    lt.volume_factor = 0.0      # 바로 옆 연기를 수천 배로 비춰 하얀 덩어리가 됨(2026-11-05) → 땅·건물만 비춘다
    lo = bpy.data.objects.new(name + "_L", lt); L.coll.objects.link(lo); lo.parent = root
    for ff, e in ((f0 - 1, 0), (f0, 3e5), (f1, 4e6)):
        lt.energy = e; lt.keyframe_insert("energy", frame=ff)
    out["light"] = lo
    # 이동(선형) + 등장/퇴장
    root.location = p0; root.keyframe_insert("location", frame=f0)
    root.location = p1; root.keyframe_insert("location", frame=f1)
    _linear(root, "location")
    for o in [root] + list(root.children_recursive):
        for f, v in ((1, False), (f0, True), (f1 + 1, False)):
            o.hide_render = not v; o.keyframe_insert("hide_render", frame=f)
    # 남는 연기 기둥(경로 전체 그릇, 진행도 prog 만큼만 보임 → 지나간 시간(age)만큼 넓고 옅어짐)
    tr = box_domain(L, f"{name}_trail", x=(0, 1), y=(-1, 1), z=(-1, 1))
    tr.location = p0
    tr.scale = (path_len, smoke_w[1], smoke_w[1])
    aim(tr, dv)
    m, g, pv = vol_mat(L, f"{name}_trail")
    co = obj_coords(g)
    x, y, z = g.xyz(co)
    prog = g.value(0.0); key_value(prog, [(f0, 0.0), (f1, 1.0)])
    clock = g.value(0.0); key_value(clock, [(f0, 0.0), (f0 + 900, 30.0)])
    age_s = g.m('SUBTRACT', prog, x)                         # 경로 비율 단위
    age = g.m('MAXIMUM', g.m('MULTIPLY', age_s, (f1 - f0) / 30.0), 0.0)   # 지난 초(진입 중) — 폭발 뒤엔 clock이 이어받음
    age = g.m('ADD', age, g.m('MAXIMUM', g.m('SUBTRACT', clock, (f1 - f0) / 30.0), 0.0))
    mask = g.m('MULTIPLY', g.smooth(age_s, -0.002, 0.004), g.smooth(x, 0.0, 0.03))
    w = g.m('MINIMUM', g.m('ADD', smoke_w[0] / smoke_w[1], g.m('MULTIPLY', age, 0.12)), 1.0)
    wob = g.m('MULTIPLY', g.m('SUBTRACT', g.noise(g.comb(g.m('MULTIPLY', x, 3.0), 0, 0), 1.0, 2, 0.5), 0.5), 0.5)
    yy = g.m('SUBTRACT', y, g.m('MULTIPLY', wob, g.m('MINIMUM', g.m('MULTIPLY', age, 0.2), 1.0)))
    rr = g.m('DIVIDE', g.m('ADD', g.m('MULTIPLY', yy, yy), g.m('MULTIPLY', z, z)), g.m('MULTIPLY', w, w))
    radial = g.m('EXPONENT', g.m('MULTIPLY', rr, -2.5))
    nv = g.comb(g.m('MULTIPLY', x, path_len / (smoke_w[1] * 1.5)), g.m('MULTIPLY', y, 1.6), g.m('MULTIPLY', z, 1.6))
    puff = g.smooth(g.noise(nv, 1.0, 7, 0.6, w=g.m('MULTIPLY', clock, 0.05), distort=0.3), 0.32, 0.72, 0.1, 1.25)
    thick = g.m('ADD', 0.35, g.m('MULTIPLY', x, 0.9))          # 아래(공기 짙은 곳)로 갈수록 연기 많음
    field = g.m('MULTIPLY', g.m('MULTIPLY', g.m('MULTIPLY', radial, mask), puff), thick)
    dens_scale = g.m('DIVIDE', 1.0, g.m('ADD', 1.0, g.m('MULTIPLY', age, 0.08)))
    wworld = g.m('MULTIPLY', w, smoke_w[1])                 # 넓어져도 두께감(광학 깊이)은 일정 → dens_scale로만 옅어짐
    g.link(g.m('DIVIDE', g.m('MULTIPLY', g.m('MULTIPLY', field, dens_scale), 10.0 * trail), wworld), pv.inputs["Density"])
    pv.inputs["Color"].default_value = (0.93, 0.92, 0.90, 1)    # 해를 받은 쪽은 하얗게, 반대쪽은 자기 그림자로 어둡게
    pv.inputs["Anisotropy"].default_value = 0.3
    hot = g.m('EXPONENT', g.m('MULTIPLY', age, -2.2))      # 막 지나간 곳은 주황빛으로 달아오름
    pv.inputs["Emission Color"].default_value = (1.0, 0.45, 0.15, 1)
    g.link(g.m('DIVIDE', g.m('MULTIPLY', g.m('MULTIPLY', field, hot), 2.5), wworld), pv.inputs["Emission Strength"])
    tr.data.materials.append(m)
    out["trail"] = tr
    # 불똥(블록 — 세계관 표시)
    sm = _hot_mat(L, f"{name}_spark", [(1, 3.0)], col=(1.0, 0.7, 0.35))
    for i in range(sparks):
        f = f0 + rng.randint(0, max(1, f1 - f0 - 4))
        tt = (f - f0) / max(1, f1 - f0)
        p = p0.lerp(p1, tt)
        s = size * rng.uniform(0.06, 0.16)
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=s)
        b = _mesh_ob(L, f"{name}_sp{i:03d}", bm); b.data.materials.append(sm)
        b.location = p; b.keyframe_insert("location", frame=f)
        v = -dv * rng.uniform(0.5, 2.0) * size + Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1) - 0.4)) * size * 0.9
        b.location = p + v * 2.5; b.keyframe_insert("location", frame=f + rng.randint(10, 22))
        b.scale = (0, 0, 0); b.keyframe_insert("scale", frame=f - 1)
        b.scale = (1, 1, 1); b.keyframe_insert("scale", frame=f)
        b.scale = (0, 0, 0); b.keyframe_insert("scale", frame=f + 22)
    # 쪼개짐
    if split_at:
        rock.hide_render = False; rock.keyframe_insert("hide_render", frame=f0)
        rock.hide_render = True; rock.keyframe_insert("hide_render", frame=split_at)
        out["pieces"] = []
        for k in range(n_pieces):
            pc = nucleus3(L, f"{name}_pc{k}", R=5, size=size * 0.6 / 5.0, seed=seed + 10 + k, lobes=False, craters=1)
            pc.data.materials.clear(); pc.data.materials.append(_hot_mat(L, f"{name}_pcmat{k}", [(1, 1.4)]))
            off = Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1)))
            off = (off - dv * off.dot(dv)).normalized()
            for ff in range(split_at, f1 + 1, 2):
                tt = (ff - f0) / max(1, f1 - f0); ts = (ff - split_at) / max(1, f1 - split_at)
                pc.location = p0.lerp(p1, tt) + off * size * (0.6 + 3.5 * ts * ts) - dv * size * 1.5 * ts * k / n_pieces
                pc.keyframe_insert("location", frame=ff)
            wk = tail3(L, f"{name}_pc{k}_wake", (0, 0, 0), tuple(-dv), size * wake_len * 0.45, size * 0.7, parent=pc, kind='wake',
                       emit=1.8 * wake, density=0.12, flow=(f0, f1 + 200), speed=8.0, head_w=0.5, fade=1.3,
                       col=(1.0, 0.9, 0.7), col_end=(0.9, 0.3, 0.1))
            for o in (pc, wk):
                for f, v in ((1, False), (split_at, True), (f1 + 1, False)):
                    o.hide_render = not v; o.keyframe_insert("hide_render", frame=f)
            out["pieces"].append(pc)
    for o in [root] + list(root.children_recursive) + [ob for ob in L.coll.objects if ob.name.startswith(f"{name}_sp")]:
        ad = o.animation_data
        if ad and ad.action:
            try: fcs = list(ad.action.fcurves)
            except AttributeError:
                fcs = [fc for ly in ad.action.layers for st in ly.strips for cb in st.channelbags for fc in cb.fcurves]
            for fc in fcs:
                if fc.data_path == "hide_render":
                    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
    if burst:
        out["burst"] = airburst3(L, f"{name}_burst", tuple(p1), f1, R=burst_R or size * 9.0, seed=seed)
    return out


def airburst3(L, name, center, f, R=50.0, seed=3, rise=0.6, ring=True, life=150, flash=6e7):
    """공중 폭발: f에 흰 섬광 → 흑체 온도로 노랑·주황·빨강으로 식으며 커짐 → 회색 연기로 떠오름. R = 최대 반지름(m)."""
    out = {}
    c = Vector(center)
    ob = sphere_domain(L, name, 1.0, 4)
    ob.location = c
    for ff, s in ((f - 1, 0.001), (f, R * 0.18), (f + 3, R * 0.5), (f + 10, R * 0.78), (f + 30, R * 0.95), (f + life, R * 1.25)):
        ob.scale = (s, s, s * 0.92); ob.keyframe_insert("scale", frame=ff)
    ob.location = c; ob.keyframe_insert("location", frame=f + 8)
    ob.location = c + Vector((0, 0, R * rise)); ob.keyframe_insert("location", frame=f + life)
    m, g, pv = vol_mat(L, name)
    co = obj_coords(g)
    tt = g.value(0.0); key_value(tt, [(f, 0.0), (f + life, 6.0)])
    r = g.node("ShaderNodeVectorMath", operation='LENGTH'); g.link(co, r.inputs[0]); r = r.outputs["Value"]
    big = g.noise(co, 1.3, 2, 0.5, w=g.m('ADD', g.m('MULTIPLY', tt, 0.08), float(seed)))          # 큰 덩어리(윤곽을 깨뜨림)
    nz = g.noise(co, 3.2, 7, 0.62, w=g.m('MULTIPLY', tt, 0.15), distort=0.4)
    rd = g.m('ADD', r, g.m('ADD', g.m('MULTIPLY', g.m('SUBTRACT', big, 0.5), 1.1), g.m('MULTIPLY', g.m('SUBTRACT', nz, 0.5), 0.55)))
    body = g.smooth(rd, 0.78, 0.42)       # 그릇(반지름 1)보다 안쪽에서 끝나야 공 모양 윤곽이 안 생김
    cauli = g.smooth(g.noise(co, 7.0, 4, 0.5, w=tt), 0.3, 0.7, 0.45, 1.3)   # 콜리플라워 결
    field = g.m('MULTIPLY', body, cauli)
    T = g.value(6500.0); key_value(T, [(f, 6500.0), (f + 6, 4500.0), (f + 20, 3000.0), (f + 50, 2000.0), (f + 90, 1500.0), (f + life, 1200.0)])
    inner = g.smooth(rd, 0.75, 0.15, 0.8, 1.15)                         # 안쪽이 더 뜨거움
    Tf = g.m('MULTIPLY', T, inner)
    bb = g.node("ShaderNodeBlackbody"); g.link(Tf, bb.inputs["Temperature"])
    g.link(bb.outputs["Color"], pv.inputs["Emission Color"])
    k = 1.0 / R
    E = g.value(0.0); key_value(E, [(f - 1, 0.0), (f, 40 * k), (f + 4, 22 * k), (f + 20, 5 * k), (f + 40, 0.8 * k), (f + 70, 0.12 * k), (f + life, 0.0)])
    g.link(g.m('MULTIPLY', g.m('MULTIPLY', field, inner), E), pv.inputs["Emission Strength"])
    D = g.value(0.0); key_value(D, [(f, 0.2 * k), (f + 15, 5.0 * k), (f + 45, 22.0 * k), (f + life, 14.0 * k)])   # 짙어야 스스로 그늘이 져서 입체로 보임
    g.link(g.m('MULTIPLY', field, D), pv.inputs["Density"])
    pv.inputs["Color"].default_value = (0.36, 0.33, 0.31, 1)    # 그을린 연기(살짝 갈색)
    pv.inputs["Anisotropy"].default_value = 0.25
    ob.data.materials.append(m)
    ob.hide_render = True; ob.keyframe_insert("hide_render", frame=1)
    ob.hide_render = False; ob.keyframe_insert("hide_render", frame=f)
    out["ball"] = ob
    # 섬광(점광원) — 도시 전체를 하얗게
    lt = bpy.data.lights.new(L.prefix + name + "_L", 'POINT'); lt.color = (1.0, 0.92, 0.8); lt.shadow_soft_size = R * 0.3
    lt.volume_factor = 0.05     # 자기 연기를 하얗게 태우지 않게
    lo = bpy.data.objects.new(name + "_L", lt); L.coll.objects.link(lo); lo.location = c
    for ff, e in ((f - 1, 0), (f, flash), (f + 4, flash * 0.45), (f + 20, flash * 0.1), (f + 60, flash * 0.015), (f + 100, 0)):
        lt.energy = e; lt.keyframe_insert("energy", frame=ff)
    out["light"] = lo
    if ring:                  # 충격파 고리(수증기 응결 고리처럼 하얗게 퍼졌다 사라짐)
        rg = sphere_domain(L, name + "_ring", 1.0, 4)
        rg.location = c
        for ff, s in ((f - 1, 0.001), (f + 2, R * 0.6), (f + 16, R * 3.2), (f + 34, R * 5.0)):
            rg.scale = (s, s, s * 0.35); rg.keyframe_insert("scale", frame=ff)
        m, g, pv = vol_mat(L, name + "_ring")
        co = obj_coords(g)
        r = g.node("ShaderNodeVectorMath", operation='LENGTH'); g.link(co, r.inputs[0]); r = r.outputs["Value"]
        shell = g.m('EXPONENT', g.m('MULTIPLY', g.m('MULTIPLY', g.m('SUBTRACT', r, 0.9), g.m('SUBTRACT', r, 0.9)), -400.0))
        shell = g.m('MULTIPLY', shell, g.smooth(g.noise(co, 5.0, 4, 0.5), 0.3, 0.7, 0.3, 1.2))
        A = g.value(0.0); key_value(A, [(f, 0.0), (f + 2, 1.0), (f + 20, 0.5), (f + 34, 0.0)])
        g.link(g.m('MULTIPLY', g.m('MULTIPLY', shell, A), 0.35 / R), pv.inputs["Density"])
        pv.inputs["Color"].default_value = (0.95, 0.95, 0.97, 1)
        pv.inputs["Emission Color"].default_value = (1.0, 0.95, 0.85, 1)
        g.link(g.m('MULTIPLY', g.m('MULTIPLY', shell, A), 0.5 / R), pv.inputs["Emission Strength"])
        rg.data.materials.append(m)
        rg.hide_render = True; rg.keyframe_insert("hide_render", frame=1)
        rg.hide_render = False; rg.keyframe_insert("hide_render", frame=f)
        rg.hide_render = True; rg.keyframe_insert("hide_render", frame=f + 35)
        out["ring"] = rg
    for o in [v for v in out.values()]:
        ad = o.animation_data
        if ad and ad.action:
            try: fcs = list(ad.action.fcurves)
            except AttributeError:
                fcs = [fc for ly in ad.action.layers for st in ly.strips for cb in st.channelbags for fc in cb.fcurves]
            for fc in fcs:
                if fc.data_path == "hide_render":
                    for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
    return out


# ---------------- 하늘·구름 ----------------
def sky3(L, keys, space_keys=None, stars_strength=0.0):
    """물리 하늘(대기 산란). keys = [(frame, 해 고도°, 해 방위°, 세기)] (CONSTANT).
    space_keys = [(frame, 0~1)] — 1이면 우주(검정+별 배경). 반환 world."""
    w = bpy.data.worlds.new(L.prefix + "sky3"); L.SC.world = w
    w.use_nodes = True
    nt = w.node_tree; g = G(nt)
    for n in list(nt.nodes):
        if n.type != 'OUTPUT_WORLD':
            nt.nodes.remove(n)
    out = [n for n in nt.nodes if n.type == 'OUTPUT_WORLD'][0]
    sky = g.node("ShaderNodeTexSky")
    try:
        sky.sky_type = 'MULTIPLE_SCATTERING'
    except Exception:
        sky.sky_type = 'SINGLE_SCATTERING'
    sky.sun_disc = False                 # 해는 태양등으로(원반이 빛 번짐 필터에서 화면을 덮음)
    sky.air_density = 1.1; sky.aerosol_density = 0.9      # 1.6이면 해 둘레가 하얗게 번져 화면 절반을 덮음
    bg = g.node("ShaderNodeBackground")
    g.link(sky.outputs["Color"], bg.inputs["Color"])
    sp = g.node("ShaderNodeBackground"); sp.inputs["Color"].default_value = (0.002, 0.003, 0.008, 1)
    mix = g.node("ShaderNodeMixShader")
    g.link(bg.outputs[0], mix.inputs[1]); g.link(sp.outputs[0], mix.inputs[2])
    g.link(mix.outputs[0], out.inputs["Surface"])
    for f, el, az, s in keys:
        sky.sun_elevation = math.radians(el); sky.keyframe_insert("sun_elevation", frame=f)
        sky.sun_rotation = math.radians(az); sky.keyframe_insert("sun_rotation", frame=f)
        bg.inputs["Strength"].default_value = s; bg.inputs["Strength"].keyframe_insert("default_value", frame=f)
    key_value(mix.inputs[0], space_keys or [(1, 0.0)], interp='CONSTANT')
    # 해 고도·방위 키도 CONSTANT
    ad = nt.animation_data
    fcs = []
    try: fcs = list(ad.action.fcurves)
    except AttributeError:
        fcs = [fc for ly in ad.action.layers for st in ly.strips for cb in st.channelbags for fc in cb.fcurves]
    for fc in fcs:
        for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
    return w


def sun_for(el, az):
    """sky3와 같은 고도·방위의 태양등 회전(euler)."""
    return (math.radians(90 - el), 0.0, math.radians(az + 90))


def cloud_bank3(L, name, center, size=(600, 600, 60), seed=5, cover=0.45, density=0.35, scale=2.2, aniso=0.45):
    """aniso: 역광(노을) 구름은 0.7~0.8 → 가장자리가 빛남."""
    """납작한 볼륨 적운 층(바닥은 평평, 위는 몽글몽글). 멀리 지평선에 깔면 공기가 생긴다."""
    ob = box_domain(L, name, x=(-1, 1), y=(-1, 1), z=(0, 1))
    ob.location = center; ob.scale = (size[0] / 2, size[1] / 2, size[2])
    m, g, pv = vol_mat(L, name)
    co = obj_coords(g)
    x, y, z = g.xyz(co)
    sx = size[0] / size[2] / 2
    nv = g.comb(g.m('MULTIPLY', x, sx / 2.5), g.m('MULTIPLY', y, sx / 2.5), g.m('MULTIPLY', z, 0.8))
    n1 = g.noise(nv, scale, 6, 0.55, w=float(seed))
    prof = g.m('MULTIPLY', g.smooth(z, 0.0, 0.12), g.smooth(z, 1.0, 0.35))   # 바닥 평평·위로 갈수록 줄어듦
    edge = g.m('MULTIPLY', g.smooth(g.m('ABSOLUTE', x), 1.0, 0.45), g.smooth(g.m('ABSOLUTE', y), 1.0, 0.2))   # 가장자리 직선이 보이지 않게 넓게 흐림
    thr = g.m('SUBTRACT', g.m('MULTIPLY', n1, 1.0), g.m('SUBTRACT', 1.0, g.m('MULTIPLY', prof, cover + 0.5)))
    field = g.m('MULTIPLY', g.smooth(thr, 0.0, 0.12), edge)
    g.link(g.m('MULTIPLY', field, density), pv.inputs["Density"])
    pv.inputs["Color"].default_value = (1, 1, 1, 1)
    pv.inputs["Anisotropy"].default_value = aniso
    ob.data.materials.append(m)
    return ob


def volume_setup(L, end=2500.0, tile='4', samples=96, shadows=True, start=0.5, dist=0.85):
    """Eevee 볼륨 품질. render_setup 다음에 호출. 볼륨이 먼 곳(수백 m)에 있으면 end를 그보다 크게."""
    e = L.SC.eevee
    e.volumetric_start = start; e.volumetric_end = end
    e.volumetric_tile_size = tile
    e.volumetric_samples = samples
    e.volumetric_sample_distribution = dist
    e.use_volumetric_shadows = shadows
    e.volumetric_shadow_samples = 32
    try:
        e.volumetric_light_clamp = 0.0
        e.clamp_volume_indirect = 0.0
    except Exception:
        pass


# ---------------- 숏별 볼륨 범위(키프레임이 안 되는 설정이라 렌더 때 핸들러로 바꿈) ----------------
#  Eevee 볼륨은 화면 깊이를 칸(volumetric_samples개)으로 나눠 계산한다. 칸 분포가 0.85(가까운 곳 촘촘)면
#  1~2km 떨어진 폭 10~20m 연기는 칸 하나(수십~수백 m) 안에서 묽어져 거의 사라진다(2026-11-05 테스트).
#  → 숏마다 (start, end, dist)를 그 숏 볼륨이 있는 거리에 맞춘다. 먼 하늘 숏: start 크게·dist 0.2~0.4.
def vol_shots(L, shots):
    """shots = [(frame, start, end, dist), ...] — 그 프레임부터 적용. render 때 scripts/vol_handler.py를 -P로 같이 넘긴다."""
    import json
    L.SC["vol_shots"] = json.dumps(sorted(shots))
    apply_vol_shot(L.SC)


def apply_vol_shot(sc, frame=None):
    import json
    raw = sc.get("vol_shots")
    if not raw:
        return
    f = sc.frame_current if frame is None else frame
    cur = None
    for row in json.loads(raw):
        if row[0] <= f:
            cur = row
    if cur:
        e = sc.eevee
        e.volumetric_start, e.volumetric_end, e.volumetric_sample_distribution = cur[1], cur[2], cur[3]


def install_vol_handler():
    def _h(sc, *a):
        apply_vol_shot(sc)
    for h in list(bpy.app.handlers.frame_change_pre):
        if getattr(h, "__name__", "") == "_h" and getattr(h, "__module__", "") == __name__:
            bpy.app.handlers.frame_change_pre.remove(h)
    bpy.app.handlers.frame_change_pre.append(_h)
    for sc in bpy.data.scenes:
        apply_vol_shot(sc)
