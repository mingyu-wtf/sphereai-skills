# 블록 세계 v3 (2026-11-05, 사용자 "이런 배경 모델링도 더 마인크래프트스럽게")
#  목표 = "셰이더 팩을 켠 마인크래프트": 모양·무늬는 전부 블록/픽셀, 빛·반사·공기만 진짜처럼.
#    city3        : 격자 도시(도로·인도·필지) + 계단식 블록 빌딩(픽셀 창문, 노을에 켜지는 창) + 옥상 소품 + 항공등 + 블록 나무
#    river3       : 픽셀 물(무늬가 뚝뚝 바뀜, 반사는 진짜)
#    bridge3      : 블록 다리(교각·난간·가로등) / traffic3 : 전조등·후미등 켠 블록 차
#    riverside3   : 인물이 서는 강변(잔디 블록·모래 단·울타리·가로등·나무·덤불)
#    hills3       : 먼 산(복셀 높이맵) + 산 위 탑
#    clouds3      : 납작한 블록 구름(천천히 흘러감)
#    block_sun3   : 네모난 해(지평선 뒤로 넘어가는 블록 해)
#    city_lights  : 도시 불빛 세기 키(창문·가로등·차 불빛이 한 값으로 같이 움직임)
# 쓰는 법은 config/04_blender_upgrade_guide.md 3장. 완성 편(1~6화)은 건드리지 않고 7화부터 쓴다.
import bpy, math, random
import numpy as np
from mathutils import Vector
import sci_fx3 as X

U = 6.0      # 도시 매크로 블록 한 칸(m). 한 층 = 한 블록 → 300~500m 밖에서도 "블록으로 쌓은 건물"로 읽힌다
PX = 8       # 블록 한 면의 픽셀 수
NB = 8       # 텍스처 한 장 = NB×NB 블록(임의 칸만큼 밀어서 반복이 안 보이게)
TV = 2.0     # 도시 나무 복셀 크기(m)

GLASS = [((0.14, 0.18, 0.24), (0.34, 0.54, 0.78)), ((0.12, 0.22, 0.24), (0.30, 0.62, 0.62)),
         ((0.10, 0.13, 0.20), (0.20, 0.30, 0.48)), ((0.20, 0.24, 0.26), (0.50, 0.68, 0.74))]
APT = [((0.90, 0.88, 0.82), (0.24, 0.32, 0.44)), ((0.80, 0.74, 0.66), (0.22, 0.28, 0.38)), ((0.72, 0.75, 0.80), (0.20, 0.28, 0.42))]
OFFICE = [((0.74, 0.74, 0.72), (0.26, 0.40, 0.56)), ((0.56, 0.52, 0.48), (0.22, 0.34, 0.46)), ((0.86, 0.84, 0.80), (0.20, 0.36, 0.40))]
BRICK = [((0.62, 0.30, 0.24), (0.22, 0.28, 0.36)), ((0.70, 0.52, 0.34), (0.20, 0.26, 0.34))]
GOLD = [((0.42, 0.30, 0.10), (0.96, 0.74, 0.28))]
WARM = [(1.0, 0.80, 0.46), (1.0, 0.90, 0.68), (0.82, 0.92, 1.0), (1.0, 0.72, 0.38)]


# ---------------- 도시 불빛(한 값으로 전체 조절) ----------------
def city_lights(L, keys=None):
    """keys = [(frame, 세기)] (CONSTANT). 낮 0, 노을 2~3, 밤 4. 여러 번 불러도 같은 그룹을 쓴다."""
    ng = getattr(L, "_clg", None)
    if ng is None:
        ng = bpy.data.node_groups.new(L.prefix + "citylight", 'ShaderNodeTree')
        ng.interface.new_socket("E", in_out='OUTPUT', socket_type='NodeSocketFloat')
        v = ng.nodes.new("ShaderNodeValue"); o = ng.nodes.new("NodeGroupOutput")
        ng.links.new(v.outputs[0], o.inputs[0])
        L._clg, L._clv = ng, v.outputs[0]
    if keys:
        X.key_value(L._clv, keys, interp='CONSTANT')
    return ng


def _light_node(L, nt):
    n = nt.nodes.new("ShaderNodeGroup"); n.node_tree = city_lights(L)
    return n.outputs[0]


def glow_mat(L, name, col, k=1.0, base=(0.05, 0.05, 0.05), always=0.0):
    """도시 불빛 그룹을 따르는 단색 발광 재질(가로등·전조등). always = 낮에도 남는 세기."""
    m = bpy.data.materials.new(L.prefix + name); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = tuple(base) + (1,)
    bs.inputs["Emission Color"].default_value = tuple(col) + (1,)
    g = X.G(nt)
    nt.links.new(g.m('ADD', g.m('MULTIPLY', _light_node(L, nt), k), always), bs.inputs["Emission Strength"])
    return m


# ---------------- 픽셀 텍스처 ----------------
def _facade(rng, style, pal, lit=0.4):
    """건물 벽 한 장(NB×NB 블록). (색, 불빛 마스크) 반환. 행 0 = 아래."""
    n = NB * PX
    wall, glass = pal
    col = np.ones((n, n, 4)); glow = np.zeros((n, n, 4)); glow[..., 3] = 1
    nz = 1 + np.array([[rng.uniform(-0.04, 0.04) for _ in range(n)] for _ in range(n)])
    col[..., :3] = np.array(wall)[None, None, :] * nz[..., None]
    for by in range(NB):
        for bx in range(NB):
            r, c = by * PX, bx * PX
            k = 1 + rng.uniform(-0.12, 0.12)
            g = np.array(glass) * k
            wins = []
            if style == 'glass':          # 유리 커튼월: 블록마다 유리 한 장, 왼쪽·아래 1픽셀이 틀
                col[r + 1:r + PX, c + 1:c + PX, :3] = g
                for d in range(3):
                    col[r + PX - 2 - d, c + 2 + d, :3] = np.minimum(1, g * 1.25 + 0.06)
                wins = [(r + 1, r + PX, c + 1, c + PX)]
            elif style == 'apt':          # 아파트: 창 두 개 + 발코니 줄
                col[r + 1, c:c + PX, :3] = np.minimum(1, np.array(wall) * 1.08)
                col[r + 3:r + 7, c + 1:c + 4, :3] = g
                col[r + 3:r + 7, c + 5:c + 7, :3] = g * 0.9
                wins = [(r + 3, r + 7, c + 1, c + 4)] if rng.random() < 0.7 else [(r + 3, r + 7, c + 5, c + 7)]
            elif style == 'office':       # 사무실: 가로 띠창
                col[r + 2:r + 6, c:c + PX, :3] = g
                col[r + 2:r + 6, c, :3] = np.array(wall) * 0.7
                col[r + 2:r + 6, c + 4, :3] = np.array(wall) * 0.7
                wins = [(r + 2, r + 6, c + 1, c + 4), (r + 2, r + 6, c + 5, c + PX)]
                if rng.random() < 0.5:
                    wins = wins[:1]
            else:                          # 벽돌: 줄눈 + 작은 창
                for rr in range(PX):
                    if rr % 2 == 0:
                        col[r + rr, c:c + PX, :3] *= 0.86
                col[r + 2:r + 6, c + 2:c + 6, :3] = g
                col[r + 1, c + 1:c + 7, :3] = (0.82, 0.80, 0.74)
                wins = [(r + 2, r + 6, c + 2, c + 6)]
            if rng.random() < lit:
                wc = rng.choice(WARM); kk = rng.uniform(0.55, 1.0)
                for (r0, r1, c0, c1) in wins:
                    glow[r0:r1, c0:c1, :3] = np.array(wc) * kk
    return col, glow


def _fac_mat(L, key, col, glow, rough):
    ci = L.make_img(key, col); gi = L.make_img(key + "_g", glow)
    m = bpy.data.materials.new(L.prefix + key); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    t1 = nt.nodes.new("ShaderNodeTexImage"); t1.image = ci; t1.interpolation = 'Closest'
    t2 = nt.nodes.new("ShaderNodeTexImage"); t2.image = gi; t2.interpolation = 'Closest'
    nt.links.new(t1.outputs["Color"], bs.inputs["Base Color"])
    nt.links.new(t2.outputs["Color"], bs.inputs["Emission Color"])
    nt.links.new(_light_node(L, nt), bs.inputs["Emission Strength"])
    bs.inputs["Roughness"].default_value = rough
    return m


def _img_mat(L, key, arr, rough=0.9):
    im = L.make_img(key, arr)
    m = bpy.data.materials.new(L.prefix + key); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = im; t.interpolation = 'Closest'
    nt.links.new(t.outputs["Color"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = rough
    return m


def _roof_tex(rng):
    n = NB * PX
    a = np.ones((n, n, 4))
    for r in range(n):
        for c in range(n):
            v = 0.30 + rng.uniform(-0.03, 0.03)
            if r % PX == 0 or c % PX == 0:
                v *= 0.8
            a[r, c, :3] = (v, v, v * 1.04)
    return a


# ---------------- 메쉬 모으기(상자 수백 개를 한 메쉬로) ----------------
class MB:
    def __init__(self):
        self.v, self.f, self.uv, self.mi, self.mats = [], [], [], [], []

    def slot(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def box(self, lo, hi, ms, mt=None, uvs=U * NB, uvo=(0.0, 0.0)):
        """lo/hi = 월드 좌표(m). 옆면 ms, 윗면 mt(없으면 ms). UV는 절대 좌표 기준 → 층·칸이 이웃 건물과 맞물린다."""
        x0, y0, z0 = lo; x1, y1, z1 = hi
        quads = [((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1), 0),
                 ((x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1), 0),
                 ((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1), 1),
                 ((x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1), 1),
                 ((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1), 2)]
        for *q, ax in quads:
            b = len(self.v)
            self.v.extend(q)
            self.f.append((b, b + 1, b + 2, b + 3))
            for p in q:
                if ax == 0:
                    uv = (p[0] / uvs + uvo[0], p[2] / uvs + uvo[1])
                elif ax == 1:
                    uv = (p[1] / uvs + uvo[0], p[2] / uvs + uvo[1])
                else:
                    uv = (p[0] / uvs, p[1] / uvs)
                self.uv.append(uv)
            self.mi.append(self.slot(mt if (ax == 2 and mt is not None) else ms))

    def finish(self, L, name, shadow=True):
        me = bpy.data.meshes.new(L.prefix + name)
        me.from_pydata(self.v, [], self.f)
        uvl = me.uv_layers.new()
        for i, uv in enumerate(self.uv):
            uvl.data[i].uv = uv
        for m in self.mats:
            me.materials.append(m)
        me.polygons.foreach_set("material_index", self.mi)
        ob = bpy.data.objects.new(name, me); L.coll.objects.link(ob)
        ob.visible_shadow = shadow
        return ob


def _tree(vox, i, j, k0, rng, big=False):
    h = rng.randint(2, 3) + (1 if big else 0)
    for k in range(h):
        vox[(i, j, k0 + k)] = (0.36, 0.25, 0.14)
    g = rng.choice(((0.22, 0.50, 0.16), (0.28, 0.58, 0.20), (0.18, 0.44, 0.18), (0.34, 0.60, 0.22)))
    R = 2 if big else 1
    for dz, r in ((0, R), (1, R), (2, max(0, R - 1))):
        for a in range(-r, r + 1):
            for b in range(-r, r + 1):
                if r > 1 and abs(a) == r and abs(b) == r and rng.random() < 0.7:
                    continue
                vox.setdefault((i + a, j + b, k0 + h + dz - 1), g)
    vox.setdefault((i, j, k0 + h + 2), g)


# ---------------- 격자 도시 ----------------
def city3(L, name, origin=(0, 0, 0), seed=21, bx=(-44, 44), by=(-30, -2), landmark=True, lit=0.42, hscale=1.0, trees=True,
          hmax=None, landmark_xy=None):
    """블록 격자 도시. 좌표 단위는 매크로 블록(U=6m). 강은 +Y 쪽(y>18m)에 둔다.
    hmax = 건물 높이 상한(m, 상징 고층은 예외). landmark_xy = 상징 고층을 세울 자리(블록 좌표, 가장 가까운 필지).
    반환 dict(towers=건물 메쉬, ground, trees, beacons, tops=[(x,y,z)] 옥상 좌표, O)."""
    O = Vector(origin)
    rng = random.Random(seed)
    city_lights(L)
    mats = {}

    def mat(style, i, v):
        key = f"fac_{style}_{i}_{v}"
        if key not in mats:
            pal = {'glass': GLASS, 'apt': APT, 'office': OFFICE, 'brick': BRICK, 'gold': GOLD}[style][i]
            col, glow = _facade(rng, 'glass' if style == 'gold' else style, pal, lit * (1.25 if style in ('glass', 'gold', 'office') else 0.8))
            mats[key] = _fac_mat(L, key, col, glow, 0.22 if style in ('glass', 'gold') else 0.7)
        return mats[key]

    roof = _img_mat(L, "roof3", _roof_tex(rng), 0.85)
    mb = MB(); props = MB()
    beacons, tops = [], []
    vox = {}
    X0, X1 = bx; Y0, Y1 = by
    road_x = [x for x in range(X0, X1 + 1) if (x - X0) % 11 in (0, 1)]
    road_y = [y for y in range(Y0, Y1 + 1) if (y - Y0) % 9 in (0, 1)]
    # ---- 바닥 지도(4픽셀 = 한 블록): 도로·차선·횡단보도·인도·광장·잔디
    PB = 4
    gx0, gx1, gy0, gy1 = X0 - 6, X1 + 8, Y0 - 6, Y1 + 5
    W, H = (gx1 - gx0) * PB, (gy1 - gy0) * PB
    gm = np.ones((H, W, 4))
    lots = {}

    def lot_of(x, y):
        if x in road_x or y in road_y or x < X0 or x > X1 + 1 or y < Y0 or y > Y1:
            return None
        return ((x - X0) // 11, (y - Y0) // 9)

    lot_kind = {}
    for r in range(H):
        for c in range(W):
            x = gx0 + c // PB; y = gy0 + r // PB
            sx, sy = c % PB, r % PB
            v = rng.uniform(-0.02, 0.02)
            inx, iny = x in road_x, y in road_y
            if y > Y1:                                       # 강변 공원(잔디 + 산책로)
                col = (0.30 + v, 0.56 + v, 0.20 + v)
                if y == Y1 + 2 and sy in (1, 2):
                    col = (0.74 + v, 0.70 + v, 0.60 + v)
            elif x < X0 or x > X1 + 1 or y < Y0:
                col = (0.33 + v, 0.52 + v, 0.24 + v)         # 도시 밖 잔디
            elif inx or iny:
                col = (0.20 + v, 0.20 + v, 0.22 + v)
                if inx and not iny:                           # 세로 도로 가운데 점선
                    first = (x - X0) % 11 == 0
                    if ((first and sx == PB - 1) or (not first and sx == 0)) and (r // 2) % 2 == 0:
                        col = (0.92, 0.82, 0.30)
                    nb = y + (1 if sy >= 2 else -1)           # 교차로 앞 횡단보도
                    if (y + 1 in road_y and y not in road_y) or (y - 1 in road_y and y not in road_y):
                        if c % 2 == 0:
                            col = (0.88, 0.88, 0.86)
                elif iny and not inx:
                    first = (y - Y0) % 9 == 0
                    if ((first and sy == PB - 1) or (not first and sy == 0)) and (c // 2) % 2 == 0:
                        col = (0.92, 0.82, 0.30)
                    if (x + 1 in road_x) or (x - 1 in road_x):
                        if r % 2 == 0:
                            col = (0.88, 0.88, 0.86)
            else:
                lk = lot_of(x, y)
                edge = any(lot_of(x + a, y + b) != lk for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if lk not in lot_kind:
                    lot_kind[lk] = rng.choices(("big", "two", "low", "park", "step"), (5, 4, 2, 1.3, 4))[0]
                if edge:
                    col = (0.62 + v, 0.62 + v, 0.64 + v)     # 인도
                elif lot_kind[lk] == "park":
                    col = (0.28 + v, 0.56 + v, 0.20 + v)
                else:
                    t = ((c // 2) + (r // 2)) % 2
                    col = (0.56 + 0.05 * t + v, 0.55 + 0.05 * t + v, 0.54 + 0.05 * t + v)   # 광장 타일
            gm[r, c, :3] = col
    gmat = _img_mat(L, f"{name}_groundmap", gm, 0.92)
    g = MB()
    g.v = [(gx0 * U, gy0 * U, 0), (gx1 * U, gy0 * U, 0), (gx1 * U, gy1 * U, 0), (gx0 * U, gy1 * U, 0)]
    g.f = [(0, 1, 2, 3)]; g.uv = [(0, 0), (1, 0), (1, 1), (0, 1)]; g.mi = [g.slot(gmat)]
    ground = g.finish(L, f"{name}_ground"); ground.location = O

    # ---- 건물
    def tower(x0, y0, w, d, h, style=None, pi=None):
        style = style or rng.choices(('glass', 'apt', 'office', 'brick'), (5, 3, 3, 1 if h < 10 else 0.2))[0]
        n_pal = {'glass': 4, 'apt': 3, 'office': 3, 'brick': 2, 'gold': 1}[style]
        ms = mat(style, rng.randrange(n_pal) if pi is None else pi, rng.randrange(2))
        uvo = (rng.randrange(NB) / NB, 0.0)
        tiers = [(x0, y0, w, d, 0, h)]
        kind = rng.choice(('slab', 'step', 'step', 'crown')) if (w >= 4 and d >= 4 and h >= 9) else 'slab'
        if kind == 'step':
            h1 = max(3, int(h * rng.uniform(0.5, 0.72))); h2 = max(h1 + 2, int(h * rng.uniform(0.82, 0.94)))
            tiers = [(x0, y0, w, d, 0, h1), (x0 + 1, y0 + 1, w - 2, d - 2, h1, h2)]
            if w >= 6 and d >= 6:
                tiers.append((x0 + 2, y0 + 2, w - 4, d - 4, h2, h))
            else:
                tiers[-1] = (x0 + 1, y0 + 1, w - 2, d - 2, h1, h)
        elif kind == 'crown':
            tiers = [(x0, y0, w, d, 0, h - 2), (x0 + 1, y0 + 1, w - 2, d - 2, h - 2, h)]
        for (tx, ty, tw, td, z0, z1) in tiers:
            mb.box((tx * U, ty * U, z0 * U), ((tx + tw) * U, (ty + td) * U, z1 * U), ms, roof, uvo=uvo)
        tx, ty, tw, td, z0, z1 = tiers[-1]
        top = z1 * U
        tops.append((O.x + (tx + tw / 2) * U, O.y + (ty + td / 2) * U, O.z + top))
        # 옥상: 난간 턱 + 실외기 + 물탱크 + 안테나(높은 건물엔 항공등)
        if tw >= 2 and td >= 2:
            props.box((tx * U + 1, ty * U + 1, top), ((tx + tw) * U - 1, (ty + td) * U - 1, top + 1.2), roof)
        for _ in range(rng.randint(1, 3)):
            ax = rng.uniform(tx * U + 2, (tx + tw) * U - 5); ay = rng.uniform(ty * U + 2, (ty + td) * U - 5)
            s = rng.choice((2.0, 3.0))
            props.box((ax, ay, top + 1.2), (ax + s, ay + s, top + 1.2 + s * 0.8), roof)
        if h >= 14 or rng.random() < 0.25:
            ax = (tx + tw / 2) * U + rng.uniform(-2, 2); ay = (ty + td / 2) * U + rng.uniform(-2, 2)
            ah = rng.choice((8, 12, 18)) if h >= 14 else 6
            props.box((ax - 0.5, ay - 0.5, top + 1.2), (ax + 0.5, ay + 0.5, top + 1.2 + ah), roof)
            if h >= 14:
                beacons.append((ax, ay, top + 1.2 + ah + 0.9))
        return top

    nlx = (X1 - X0) // 11; nly = (Y1 - Y0 + 1) // 9
    HM = max(2, int(hmax / U)) if hmax else 999
    lm_lot = (nlx // 2 - 1, max(0, nly - 2))
    if landmark_xy is not None:
        cand = [(a, b) for a in range(nlx + 1) for b in range(nly + 1) if X0 + a * 11 + 11 <= X1 + 2 and Y0 + b * 9 + 9 <= Y1 + 1]
        if cand:
            lm_lot = min(cand, key=lambda ab: (X0 + ab[0] * 11 + 6.5 - landmark_xy[0]) ** 2 + (Y0 + ab[1] * 9 + 5.5 - landmark_xy[1]) ** 2)
    for li in range(nlx + 1):
        for lj in range(nly + 1):
            lx = X0 + li * 11 + 2; ly = Y0 + lj * 9 + 2            # 필지 안쪽 시작(9×7)
            if lx + 9 > X1 + 2 or ly + 7 > Y1 + 1:
                continue
            kind = lot_kind.get((li, lj), "big")
            row = lj / max(1, nly - 1)                              # 0 = 뒤(먼 쪽), 1 = 강가
            cen = 1.3 if abs(lx + 4) < 16 else 1.0
            lo, hi = (14 - 8 * row) * cen * hscale, (30 - 15 * row) * cen * hscale
            hh = lambda: max(2, min(HM, int(rng.triangular(lo, hi, (lo + hi) / 2.2))))
            if landmark and (li, lj) == lm_lot:
                # 금빛 상징 고층(실제 건물 이름·로고 없음): 4단 계단 + 첨탑
                gm_ = mat('gold', 0, 0)
                zz = 0
                for k, (ins, hk) in enumerate(((0, 22), (1, 12), (2, 8), (3, 4))):
                    hk = int(hk * hscale)
                    mb.box(((lx + 1 + ins) * U, (ly + 1 + ins * 0.6) * U, zz * U), ((lx + 8 - ins) * U, (ly + 6 - ins * 0.6) * U, (zz + hk) * U), gm_, roof)
                    zz += hk
                cx_, cy_ = (lx + 4.5) * U, (ly + 3.5) * U
                props.box((cx_ - 1, cy_ - 1, zz * U), (cx_ + 1, cy_ + 1, zz * U + 30), roof)
                beacons.append((cx_, cy_, zz * U + 31))
                tops.append((O.x + cx_, O.y + cy_, O.z + zz * U))
                continue
            if kind == "park":
                if trees:
                    for _ in range(9):
                        _tree(vox, int((lx + rng.uniform(1, 8)) * U / TV), int((ly + rng.uniform(1, 6)) * U / TV), 0, rng, big=rng.random() < 0.4)
                continue
            if kind in ("big", "step"):
                w = rng.randint(5, 7); d = rng.randint(4, 5)
                tower(lx + rng.randint(1, 8 - w), ly + rng.randint(1, 6 - d), w, d, hh())
            elif kind == "two":
                d1, d2 = rng.randint(3, 5), rng.randint(3, 5)
                tower(lx + 1, ly + 1, 3, d1, hh()); tower(lx + 5, ly + 6 - d2, 3, d2, hh())
            else:                                                   # 낮은 건물 무리
                for a in range(3):
                    for b in range(2):
                        if rng.random() < 0.85:
                            tower(lx + 1 + a * 2.5, ly + 1 + b * 3, 2, 2, rng.randint(2, 5), style=rng.choice(('brick', 'apt', 'office')))
            if trees:                                               # 가로수
                for t in range(3):
                    if rng.random() < 0.7:
                        _tree(vox, int((lx + 0.3 + t * 4) * U / TV), int((ly + 0.25) * U / TV), 0, rng)
    towers = mb.finish(L, f"{name}_towers"); towers.location = O
    pr = props.finish(L, f"{name}_roofprops"); pr.location = O
    out = {"towers": towers, "ground": ground, "props": pr, "tops": tops, "O": O}
    # ---- 강변 공원 나무
    if trees:
        for x in range(X0 * 3, X1 * 3, 4):
            if rng.random() < 0.75:
                _tree(vox, x + rng.randint(-1, 1), int((Y1 + rng.choice((1.2, 2.8, 3.4))) * U / TV), 0, rng, big=rng.random() < 0.5)
        tr = L.voxel_mesh(f"{name}_trees", vox, TV)
        tr.location = O
        out["trees"] = tr
    # ---- 항공등(빨간 블록, 1초에 한 번 깜빡)
    if beacons:
        bm_ = MB()
        bmat = bpy.data.materials.new(L.prefix + name + "_beacon"); bmat.use_nodes = True
        bs = bmat.node_tree.nodes["Principled BSDF"]
        bs.inputs["Base Color"].default_value = (0.3, 0.02, 0.02, 1)
        bs.inputs["Emission Color"].default_value = (1.0, 0.08, 0.05, 1)
        ks = []
        for f in range(L.SC.frame_start, L.SC.frame_end + 60, 30):
            ks += [(f, 6.0), (f + 14, 0.4)]
        X.key_value(bs.inputs["Emission Strength"], ks, interp='CONSTANT')
        for (x, y, z) in beacons:
            bm_.box((x - 0.9, y - 0.9, z - 0.9), (x + 0.9, y + 0.9, z + 0.9), bmat)
        bo = bm_.finish(L, f"{name}_beacons", shadow=False); bo.location = O
        out["beacons"] = bo
    return out


# ---------------- 강(픽셀 물) ----------------
def _water_tex(L):
    rng = L.nrng
    a = np.ones((32, 32, 4))
    base = np.array((0.10, 0.26, 0.46))
    k = 1 + rng.uniform(-0.10, 0.10, (32, 32))
    a[..., :3] = base[None, None, :] * k[..., None]
    for _ in range(26):                      # 가로로 짧은 물결 픽셀
        r, c, n = rng.integers(32), rng.integers(32), rng.integers(2, 6)
        for d in range(n):
            a[r, (c + d) % 32, :3] = base * 1.45 + 0.04
    return a


def river3(L, name, center, size, z=-0.7, tile=24.0, step=6):
    """픽셀 물. 무늬가 step 프레임마다 뚝뚝 옮겨 가고(마인크래프트 물), 반사는 레이트레이싱."""
    L.ENV_TEX["water3"] = lambda: _water_tex(L)
    ob = L.box(name, (size[0], size[1], 2.0), offset=(center[0], center[1], z - 1.0), tex="water3", tile=tile)
    m = ob.data.materials[0]
    nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    bs.inputs["Roughness"].default_value = 0.07
    tx = [n for n in nt.nodes if n.type == 'TEX_IMAGE'][0]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], tx.inputs["Vector"])
    rng = random.Random(7)
    for f in range(L.SC.frame_start, L.SC.frame_end + step, step):
        mp.inputs["Location"].default_value = (rng.randrange(32) / 32.0, rng.randrange(32) / 32.0, 0)
        mp.inputs["Location"].keyframe_insert("default_value", frame=f)
    X.key_value(bs.inputs["Roughness"], [(1, 0.07)], interp='CONSTANT')     # 모든 키를 CONSTANT로(위 Location 포함)
    ob.visible_shadow = False
    return ob


# ---------------- 다리·차 ----------------
def bridge3(L, name, x, y0, y1, z=11.0, w=16.0, lamps=True, lamp_k=1.0):
    """Y 방향 블록 다리. 교각·난간·가로등(도시 불빛을 따름)."""
    L.ENV_TEX.setdefault("bridge_deck", lambda: L.noise(16, 16, (0.30, 0.30, 0.32), 0.06))
    L.ENV_TEX.setdefault("bridge_conc", lambda: L.noise(16, 16, (0.66, 0.65, 0.62), 0.07))
    ln = y1 - y0; cy = (y0 + y1) / 2
    L.box(f"{name}_deck", (w, ln, 2.0), offset=(x, cy, z - 1.0), tex="bridge_deck", tile=4)
    L.box(f"{name}_girder", (w - 4, ln, 2.0), offset=(x, cy, z - 3.0), tex="bridge_conc", tile=4)
    mb = MB()
    conc = L.mat_for("bridge_conc")
    for sx in (-1, 1):                                # 난간(기둥 + 가로대)
        mb.box((x + sx * (w / 2 - 0.5) - 0.3, y0, z + 1.0), (x + sx * (w / 2 - 0.5) + 0.3, y1, z + 1.5), conc, uvs=4)
        yy = y0
        while yy < y1:
            mb.box((x + sx * (w / 2 - 0.5) - 0.4, yy, z), (x + sx * (w / 2 - 0.5) + 0.4, yy + 0.8, z + 1.5), conc, uvs=4)
            yy += 6.0
    n = max(2, int(ln // 54))
    for k in range(n + 1):                            # 교각(아래가 넓은 2단)
        yy = y0 + ln * k / n
        mb.box((x - w / 2 + 2, yy - 3, z - 19), (x + w / 2 - 2, yy + 3, z - 4), conc, uvs=4)
        mb.box((x - w / 2 + 0.5, yy - 4.5, z - 5), (x + w / 2 - 0.5, yy + 4.5, z - 3.8), conc, uvs=4)
    rail = mb.finish(L, f"{name}_rail")
    out = {"rail": rail}
    if lamps:
        lm = MB()
        pole = L.mat_for("iron")
        gl = glow_mat(L, f"{name}_lamp", (1.0, 0.82, 0.5), k=lamp_k, base=(0.5, 0.45, 0.35))
        yy = y0 + 12
        i = 0
        while yy < y1:
            sx = -1 if i % 2 == 0 else 1
            px = x + sx * (w / 2 - 0.5)
            lm.box((px - 0.25, yy - 0.25, z + 1.5), (px + 0.25, yy + 0.25, z + 8.0), pole, uvs=4)
            lm.box((px - 0.25 - sx * 2.0, yy - 0.25, z + 7.5), (px + 0.25, yy + 0.25, z + 8.0), pole, uvs=4)
            lm.box((px - sx * 2.3 - 0.7, yy - 0.7, z + 6.6), (px - sx * 2.3 + 0.7, yy + 0.7, z + 7.5), gl, uvs=4)
            yy += 30.0; i += 1
        out["lamps"] = lm.finish(L, f"{name}_lamps", shadow=False)
    return out


CAR_COLS = [(0.80, 0.12, 0.10), (0.92, 0.92, 0.92), (0.16, 0.30, 0.66), (0.10, 0.10, 0.12), (0.95, 0.75, 0.15), (0.20, 0.55, 0.35), (0.55, 0.57, 0.60)]


def traffic3(L, name, p0, p1, n=10, f0=1, f1=600, speed=16.0, lane=3.4, scale=1.6, seed=5, fps=30):
    """p0→p1 직선 도로 위 블록 차 n대(양방향 2차선). 전조등·후미등은 도시 불빛을 따른다(낮에도 약하게).
    scale = 실제 차보다 키우는 배율(멀리서도 보이게)."""
    rng = random.Random(seed)
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1 - p0); ln = d.length; d.normalize()
    side = Vector((-d.y, d.x, 0))
    yaw = math.atan2(d.y, d.x)
    head = glow_mat(L, f"{name}_head", (1.0, 0.95, 0.8), k=3.0, base=(0.9, 0.9, 0.8), always=1.2)
    tail = glow_mat(L, f"{name}_tail", (1.0, 0.08, 0.05), k=2.5, base=(0.5, 0.05, 0.05), always=0.8)
    glassm = bpy.data.materials.new(L.prefix + name + "_glass"); glassm.use_nodes = True
    gb = glassm.node_tree.nodes["Principled BSDF"]; gb.inputs["Base Color"].default_value = (0.08, 0.12, 0.18, 1); gb.inputs["Roughness"].default_value = 0.15
    cars = []
    T = (f1 - f0) / fps
    for i in range(n):
        fwd = i % 2 == 0
        dirv = d if fwd else -d
        col = rng.choice(CAR_COLS)
        bm_ = bpy.data.materials.new(L.prefix + f"{name}_c{i}"); bm_.use_nodes = True
        b = bm_.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = tuple(col) + (1,); b.inputs["Roughness"].default_value = 0.45
        bus = rng.random() < 0.18
        Lc, Wc, Hc = (9.0, 2.5, 2.9) if bus else (4.4, 1.9, 0.8)
        mb = MB()
        mb.box((-Lc / 2, -Wc / 2, 0.35), (Lc / 2, Wc / 2, 0.35 + Hc), bm_, uvs=4)
        if not bus:
            mb.box((-Lc * 0.28, -Wc / 2 + 0.1, 0.35 + Hc), (Lc * 0.2, Wc / 2 - 0.1, 0.35 + Hc + 0.65), glassm, uvs=4)
        else:
            mb.box((-Lc / 2 + 0.3, -Wc / 2 - 0.02, 1.6), (Lc / 2 - 0.3, Wc / 2 + 0.02, 2.6), glassm, uvs=4)
        for sy in (-1, 1):
            mb.box((Lc / 2, sy * Wc * 0.3 - 0.25, 0.6), (Lc / 2 + 0.08, sy * Wc * 0.3 + 0.25, 1.0), head, uvs=4)
            mb.box((-Lc / 2 - 0.08, sy * Wc * 0.3 - 0.25, 0.6), (-Lc / 2, sy * Wc * 0.3 + 0.25, 1.0), tail, uvs=4)
        ob = mb.finish(L, f"{name}_car{i}", shadow=False)
        ob.scale = (scale,) * 3
        ob.rotation_euler = (0, 0, yaw if fwd else yaw + math.pi)
        v = speed * rng.uniform(0.8, 1.2)
        s0 = rng.uniform(0, ln)
        base = p0 + side * (lane * scale * 0.5 * (-1 if fwd else 1))
        # 길 위를 돌고 돈다: 끝에 닿으면 처음으로(그 순간만 CONSTANT)
        s = s0 if fwd else ln - s0
        f = f0
        keys = []
        while f < f1:
            remain = (ln - s) if fwd else s
            df = max(1, int(round(remain / v * fps)))
            fe = min(f1, f + df)
            s_end = s + (v * (fe - f) / fps) * (1 if fwd else -1)
            keys.append((f, s)); keys.append((fe, s_end))
            f = fe + 1; s = 0.0 if fwd else ln
        for ff, ss in keys:
            ob.location = base + d * ss + Vector((0, 0, 0)); ob.keyframe_insert("location", frame=ff)
        X._linear(ob)
        cars.append(ob)
    return cars


# ---------------- 인물이 서는 강변 ----------------
def riverside3(L, name, origin, width=120.0, depth=60.0, top=0.2, water_z=-0.7, lamp=True, tree=((8.0, 9.0, 5), (-14.0, 8.0, 4), (24.0, 15.0, 6)), seed=4, lamp_k=0.9):
    """origin = 물가 가운데(x, y). 강은 -Y 쪽, 잔디는 +Y 쪽으로 depth만큼. 1m 블록·16픽셀 텍스처(인물 눈높이용)."""
    rng = random.Random(seed)
    ox, oy = origin
    L.ENV_TEX.setdefault("sand3", lambda: L.noise(16, 16, (0.82, 0.76, 0.56), 0.07))
    L.ENV_TEX.setdefault("gravel3", lambda: L.noise(16, 16, (0.60, 0.58, 0.55), 0.12))
    L.ENV_TEX.setdefault("plank3", lambda: L.noise(16, 16, (0.55, 0.40, 0.24), 0.08))
    grass = {"pz": "grass_top", "all": "grass_side"}
    L.box(f"{name}_grass", (width, depth, 3.0), offset=(ox, oy + 4 + depth / 2, top - 1.5), tex=grass, tile=1)
    L.box(f"{name}_step1", (width, 2.0, 3.0), offset=(ox, oy + 3, top - 1.5 - 0.5), tex=grass, tile=1)
    L.box(f"{name}_sand", (width, 3.0, 3.0), offset=(ox, oy + 0.5, water_z + 0.25 - 1.5), tex="sand3", tile=1)
    L.box(f"{name}_path", (width, 2.0, 0.1), offset=(ox, oy + 12.0, top + 0.02), tex="gravel3", tile=1)
    # 군데군데 솟은 잔디 블록(평평한 판으로 안 보이게)
    for _ in range(26):
        x = ox + rng.uniform(-width / 2 + 2, width / 2 - 2); y = oy + rng.uniform(16, depth - 2)
        s = rng.choice((1, 1, 2, 3))
        L.box(f"{name}_bump", (s, rng.choice((1, 2, 3)), 1.0), offset=(round(x), round(y), top + 0.5), tex=grass, tile=1)
    # 울타리(기둥 + 가로대 두 줄)
    mb = MB(); wood = L.mat_for("plank3")
    fy = oy + 5.2
    xx = ox - width / 2 + 1
    while xx < ox + width / 2 - 1:
        mb.box((xx - 0.12, fy - 0.12, top), (xx + 0.12, fy + 0.12, top + 1.05), wood, uvs=1)
        xx += 2.0
    for zz in (0.45, 0.85):
        mb.box((ox - width / 2 + 1, fy - 0.06, top + zz - 0.07), (ox + width / 2 - 1, fy + 0.06, top + zz + 0.07), wood, uvs=1)
    out = {"fence": mb.finish(L, f"{name}_fence")}
    if lamp:                # 가로등(블록 등불)
        for i, lx in enumerate((ox - 9.0, ox + 15.0, ox - 33.0, ox + 39.0)):
            lm = MB()
            lm.box((lx - 0.12, fy + 0.6, top), (lx + 0.12, fy + 0.84, top + 3.4), L.mat_for("iron"), uvs=1)
            lm.box((lx - 0.3, fy + 0.42, top + 3.4), (lx + 0.3, fy + 1.02, top + 4.0), glow_mat(L, f"{name}_lamp{i}", (1.0, 0.80, 0.45), k=lamp_k, base=(0.6, 0.5, 0.3)), uvs=1)
            lm.finish(L, f"{name}_lamp{i}", shadow=False)
    if tree:                # 화면 틀이 되는 나무(통나무 + 잎 블록)
        for (dx_, dy_, th) in tree:
            tx, ty = ox + dx_, oy + dy_
            L.box(f"{name}_log", (1, 1, th), offset=(tx, ty, top + th / 2), tex="log", tile=1)
            for dz, r in ((0, 2), (1, 2), (2, 1), (3, 1)):
                s = 2 * r + 1
                L.box(f"{name}_leaf", (s, s, 1), offset=(tx, ty, top + th - 0.5 + dz), tex="leaves", tile=1)
        for _ in range(8):  # 덤불
            x = ox + rng.uniform(-width / 2 + 2, width / 2 - 2)
            L.box(f"{name}_bush", (rng.choice((1, 2)), 1, 1), offset=(round(x) + 0.5, oy + 6.5, top + 0.5), tex="leaves", tile=1)
    return out


# ---------------- 먼 산 ----------------
def hills3(L, name, center, half=(900, 160), block=14.0, hmax=11, seed=6, tower=True, low_x=None):
    """복셀 높이맵 산줄기(도시 뒤 배경). low_x=(x0,x1) 구간은 낮게(해가 넘어가는 자리)."""
    rng = random.Random(seed)
    cx, cy, cz = center
    nx, ny = int(half[0] / block), int(half[1] / block)
    ph = [rng.uniform(0, 6.28) for _ in range(6)]

    def hgt(i, j):
        x = i / nx
        ridge = (math.sin(x * 4.1 + ph[0]) * 0.5 + math.sin(x * 9.3 + ph[1]) * 0.28 + math.sin(x * 17.0 + ph[2]) * 0.14 + 1.0) / 1.9
        prof = max(0.0, 1.0 - (j / ny) ** 2)
        h = hmax * ridge * prof * (1 - 0.35 * abs(x) ** 2)
        h += math.sin(i * 0.9 + j * 1.3 + ph[3]) * 0.6
        if low_x and low_x[0] < cx + i * block < low_x[1]:
            h *= 0.35
        return max(0, int(round(h)))

    vox = {}
    peak = (0, 0, 0)
    for i in range(-nx, nx + 1):
        for j in range(-ny, ny + 1):
            h = hgt(i, j)
            if h <= 0:
                continue
            if h > peak[2] and abs(i) < nx * 0.5:
                peak = (i, j, h)
            for k in range(max(0, h - 3), h):
                t = rng.uniform(-0.03, 0.03)
                if k == h - 1:
                    col = (0.08 + t, 0.24 + t, 0.07 + t) if h < hmax * 0.8 else (0.20 + t, 0.28 + t, 0.18 + t)
                else:
                    col = (0.22 + t, 0.24 + t, 0.20 + t)
                vox[(i, j, k)] = col
    if tower:                 # 산 위 탑(이름·로고 없는 일반 전망탑)
        i, j, h = peak
        for k in range(h, h + 7):
            vox[(i, j, k)] = (0.85, 0.85, 0.86)
        for a in (-1, 0, 1):
            for b in (-1, 0, 1):
                vox[(i + a, j + b, h + 4)] = (0.75, 0.78, 0.82)
    ob = L.voxel_mesh(name, vox, block)
    ob.location = (cx, cy, cz)
    ob.visible_shadow = False
    bs = ob.data.materials[0].node_tree.nodes["Principled BSDF"]     # 먼 산이 하늘 반사로 허옇게 뜨지 않게
    bs.inputs["Roughness"].default_value = 1.0
    if "Specular IOR Level" in bs.inputs:
        bs.inputs["Specular IOR Level"].default_value = 0.0
    return ob


# ---------------- 블록 구름 ----------------
def clouds3(L, name, center=(0, 0), z=340.0, cell=30.0, thick=11.0, extent=(2400, 2400), cover=0.34, seed=8,
            drift=(3.0, 0.0), f0=1, f1=600, fps=30, emit=0.22, layers=1, keep_out=(), keep_rays=()):
    """납작한 블록 구름 층. 큰 덩어리 무늬 + 가장자리 칸 단위 들쭉날쭉. drift = 초당 이동(m)."""
    rng = random.Random(seed)
    nx, ny = int(extent[0] / cell / 2), int(extent[1] / cell / 2)
    C = 5                                                   # 거친 격자 한 칸 = 구름 5칸
    coarse = {}
    cg = lambda a, b: coarse.setdefault((a, b), rng.random())

    def val(i, j):
        a, b = i / C, j / C
        ia, ib = math.floor(a), math.floor(b)
        fa, fb = a - ia, b - ib
        v = (cg(ia, ib) * (1 - fa) + cg(ia + 1, ib) * fa) * (1 - fb) + (cg(ia, ib + 1) * (1 - fa) + cg(ia + 1, ib + 1) * fa) * fb
        return v

    holes = list(keep_out)                      # keep_out=[(x,y,반지름)] 구름을 비울 자리
    for (cam, pt, rad) in keep_rays:            # keep_rays=[(카메라 위치, 보여야 할 점, 반지름)] → 그 시선이 구름 층을 지나는 자리를 비움
        cam, pt = Vector(cam), Vector(pt)
        if abs(pt.z - cam.z) > 1e-3 and (z - cam.z) / (pt.z - cam.z) > 0:
            q = cam + (pt - cam) * ((z - cam.z) / (pt.z - cam.z))
            holes.append((q.x, q.y, rad))
    vox = {}
    for i in range(-nx, nx + 1):
        for j in range(-ny, ny + 1):
            v = val(i, j) + rng.uniform(-0.05, 0.05)
            wx, wy = center[0] + i * cell, center[1] + j * cell
            if any((wx - hx) ** 2 + (wy - hy) ** 2 < hr * hr for hx, hy, hr in holes):
                continue
            if v > 1 - cover:
                vox[(i, j, 0)] = (0.97, 0.97, 0.98)
                if layers > 1 and v > 1 - cover + 0.12:
                    vox[(i, j, 1)] = (0.99, 0.99, 1.0)
    ob = L.voxel_mesh(name, vox, cell, emit=emit)
    ob.scale = (1, 1, thick / cell)
    bs = ob.data.materials[0].node_tree.nodes["Principled BSDF"]
    bs.inputs["Roughness"].default_value = 1.0
    T = (f1 - f0) / fps
    ob.location = (center[0], center[1], z); ob.keyframe_insert("location", frame=f0)
    ob.location = (center[0] + drift[0] * T, center[1] + drift[1] * T, z); ob.keyframe_insert("location", frame=f1)
    X._linear(ob)
    ob.visible_shadow = False
    return ob


# ---------------- 네모난 해·달 ----------------
def block_sun3(L, name, sun_dir, size_deg=8.0, dist=4200.0, col=(1.0, 0.72, 0.35), emit=5.0, center=(0, 0, 0), keys=None, rim=True):
    """sun_dir = 해 쪽 방향. 멀리 세운 네모 발광판(가운데 밝고 테두리 한 칸 어둡게 = 픽셀 해). keys=[(frame, 보임)]."""
    sd = Vector(sun_dir).normalized()
    c = Vector(center) + sd * dist
    s = dist * math.tan(math.radians(size_deg) / 2)
    a = np.ones((8, 8, 4))
    for r in range(8):
        for q in range(8):
            edge = r in (0, 7) or q in (0, 7)
            a[r, q, :3] = np.array(col) * (0.72 if edge and rim else 1.0)
    im = L.make_img(name + "_tex", a)
    m = bpy.data.materials.new(L.prefix + name); m.use_nodes = True
    nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = im; t.interpolation = 'Closest'
    nt.links.new(t.outputs["Color"], bs.inputs["Emission Color"])
    bs.inputs["Base Color"].default_value = (0, 0, 0, 1)
    bs.inputs["Emission Strength"].default_value = emit
    me = bpy.data.meshes.new(L.prefix + name)
    me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
    uvl = me.uv_layers.new()
    for i, uv in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        uvl.data[i].uv = uv
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me); L.coll.objects.link(ob)
    ob.location = c
    nrm = -sd                                   # 네모가 기울지 않게: 가로변은 수평, 세로변은 위쪽
    rt = Vector((0, 0, 1)).cross(nrm).normalized(); up = nrm.cross(rt).normalized()
    from mathutils import Matrix
    ob.rotation_euler = Matrix((rt, up, nrm)).transposed().to_euler()
    ob.visible_shadow = False
    if keys:
        for f, v in keys:
            ob.hide_render = not v; ob.keyframe_insert("hide_render", frame=f)
        try:
            fcs = list(ob.animation_data.action.fcurves)
        except AttributeError:
            fcs = [fc for ly in ob.animation_data.action.layers for st in ly.strips for cb in st.channelbags for fc in cb.fcurves]
        for fc in fcs:
            for kp in fc.keyframe_points:
                kp.interpolation = 'CONSTANT'
    return ob


def land3(L, name, y_max=24.0, extent=4000.0, z=-0.06, col=(0.30, 0.50, 0.22), y_min=None):
    """도시 바깥 넓은 땅(공중 숏에서 세상 끝이 안 보이게). y_max보다 -Y 쪽 전부. y_min을 주면 그보다 +Y 쪽 전부(강 건너 이쪽 땅)."""
    if y_min is not None:
        L.ENV_TEX.setdefault("land3", lambda: L.noise(16, 16, col, 0.06))
        ob = L.box(name, (extent * 2, extent, 2.0), offset=(0, y_min + extent / 2, z - 1.0), tex="land3", tile=U * 4)
        ob.visible_shadow = False
        return ob
    L.ENV_TEX.setdefault("land3", lambda: L.noise(16, 16, col, 0.06))
    ob = L.box(name, (extent * 2, extent, 2.0), offset=(0, y_max - extent / 2, z - 1.0), tex="land3", tile=U * 4)
    ob.visible_shadow = False
    return ob
