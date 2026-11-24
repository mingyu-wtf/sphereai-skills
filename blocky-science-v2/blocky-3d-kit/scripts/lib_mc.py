# 스타일 v2(마인크래프트 애니메이션) 공용 라이브러리
# build_style_v2_mc_anim.py에서 텍스처·상자·모기·거리 빌더를 떼어 왔다. 컷 스크립트에서:
#   import importlib, sys; sys.path.insert(0, SCRIPTS); import lib_mc; importlib.reload(lib_mc)
#   L = lib_mc.Lib(scene)
import bpy, math, random
import numpy as np
from mathutils import Euler, Vector

P = 1 / 16  # 픽셀 한 칸 = 1/16 m

# ---------------- 팔레트 ----------------
DARK = (0.20, 0.18, 0.17); BLACK = (0.08, 0.075, 0.075); WHITE = (0.95, 0.95, 0.92)
RED = (0.80, 0.10, 0.10); RED_D = (0.45, 0.04, 0.04)

# 화질 v3 재질 거칠기(텍스처 키에 이 단어가 들어 있으면 적용, 위에서부터 먼저 맞는 것)
ROUGH_DEFAULT = {"water": 0.06, "sea": 0.08, "salt": 0.1, "fresh": 0.06, "glass": 0.05, "ice_side": 0.35, "ice": 0.3,
                 "snow": 0.55, "window": 0.15, "metal": 0.35, "iron": 0.4, "panel": 0.25, "gold_foil": 0.3}

FACES = {
    "px": ((1,0,0), (0,1,0), (0,0,1)),
    "nx": ((-1,0,0), (0,-1,0), (0,0,1)),
    "py": ((0,1,0), (-1,0,0), (0,0,1)),
    "ny": ((0,-1,0), (1,0,0), (0,0,1)),
    "pz": ((0,0,1), (0,-1,0), (1,0,0)),
    "nz": ((0,0,-1), (0,1,0), (1,0,0)),
}


def wipe_scene(name):
    """같은 이름 씬이 있으면 그 씬의 오브젝트와 씬만 지운다(다른 씬은 건드리지 않음)."""
    old = bpy.data.scenes.get(name)
    if old:
        for ob in list(old.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        for c in list(old.collection.children_recursive):
            bpy.data.collections.remove(c)
        bpy.data.scenes.remove(old)
    sc = bpy.data.scenes.new(name)
    try:
        for w in bpy.context.window_manager.windows:
            w.scene = sc
    except Exception:
        pass
    return sc


class Lib:
    def __init__(self, scene, seed=11, prefix="V2"):
        self.SC = scene
        self.rng = random.Random(seed)
        self.nrng = np.random.default_rng(seed)
        self.prefix = prefix + "_"
        self.IMG, self.MAT = {}, {}
        self.coll = scene.collection
        self.ENV_TEX = {
            "asphalt": self.t_asphalt, "lane": self.t_lane, "stone": self.t_stone,
            "grass_top": self.t_grass_top, "grass_side": self.t_grass_side, "log": self.t_log,
            "leaves": self.t_leaves, "brick": self.t_brick,
            "plaster_yellow": lambda: self.noise(16, 16, (0.93, 0.78, 0.30), 0.05),
            "plaster_white": lambda: self.noise(16, 16, (0.92, 0.90, 0.85), 0.05),
            "plaster_gray": lambda: self.noise(16, 16, (0.62, 0.62, 0.64), 0.05),
            "window": lambda: self.t_window((0.55, 0.75, 0.92)),
            "window_dark": lambda: self.t_window((0.10, 0.13, 0.22)),
            "window_lit": lambda: self.t_window((1.0, 0.80, 0.45)),
            "window_lit_glow": lambda: self.t_window((1.0, 0.80, 0.45), glow=True),
            "lantern_glow": lambda: self.t_lantern(glow=True),
            "door": self.t_door, "cloud": lambda: self.noise(4, 4, (0.97, 0.97, 0.97), 0.01),
            "iron": lambda: self.noise(8, 8, (0.18, 0.18, 0.20), 0.08),
            "lantern": self.t_lantern, "moon": self.t_moon, "star": lambda: self.noise(2, 2, (1, 1, 0.95), 0),
            "puff": lambda: self.noise(4, 4, (0.92, 0.92, 0.92), 0.06),
        }

    # ---------------- 텍스처 ----------------
    def make_img(self, key, arr):
        if key in self.IMG:
            return self.IMG[key]
        h, w = arr.shape[:2]
        im = bpy.data.images.new(self.prefix + key, w, h, alpha=True)
        im.pixels.foreach_set(np.clip(arr, 0, 1).astype(np.float32).ravel())
        im.pack()
        self.IMG[key] = im
        return im

    def noise(self, w, h, base, var=0.08):
        a = np.ones((h, w, 4))
        k = 1 + self.nrng.uniform(-var, var, (h, w))
        a[..., :3] = np.array(base)[None, None, :] * k[..., None]
        return a

    @staticmethod
    def put(a, r, c, col, alpha=1.0):
        if 0 <= r < a.shape[0] and 0 <= c < a.shape[1]:
            a[r, c, :3] = col; a[r, c, 3] = alpha

    def t_asphalt(self):
        a = self.noise(16, 16, (0.33, 0.33, 0.35), 0.10)
        for _ in range(10):
            self.put(a, self.nrng.integers(16), self.nrng.integers(16), (0.24, 0.24, 0.26))
        return a
    def t_lane(self): return self.noise(4, 4, (0.92, 0.92, 0.90), 0.04)
    def t_stone(self):
        a = self.noise(16, 16, (0.62, 0.62, 0.62), 0.08)
        for i in range(16):
            self.put(a, 0, i, (0.48, 0.48, 0.48)); self.put(a, i, 0, (0.48, 0.48, 0.48))
        return a
    def t_grass_top(self): return self.noise(16, 16, (0.36, 0.66, 0.22), 0.14)
    def t_grass_side(self):
        a = self.noise(16, 16, (0.52, 0.36, 0.22), 0.10)
        for c in range(16):
            depth = 3 + self.nrng.integers(0, 3)
            for r in range(16 - depth, 16):
                a[r, c, :3] = np.array((0.36, 0.66, 0.22)) * (1 + self.nrng.uniform(-0.12, 0.12))
        return a
    def t_log(self):
        a = self.noise(16, 16, (0.42, 0.30, 0.18), 0.06)
        for c in range(0, 16, 3):
            a[:, c, :3] *= 0.75
        return a
    def t_leaves(self):
        a = self.noise(16, 16, (0.22, 0.50, 0.16), 0.20)
        for _ in range(28):
            self.put(a, self.nrng.integers(16), self.nrng.integers(16), (0.10, 0.28, 0.08))
        return a
    def t_brick(self):
        a = np.ones((16, 16, 4)); a[..., :3] = (0.72, 0.72, 0.68)
        for row in range(4):
            off = 0 if row % 2 == 0 else 4
            for r in range(row * 4 + 1, row * 4 + 4):
                for c in range(16):
                    if (c + off) % 8 != 0:
                        a[r, c, :3] = np.array((0.62, 0.26, 0.20)) * (1 + self.nrng.uniform(-0.10, 0.10))
        return a
    def t_window(self, glass, glow=False):
        """glow=True면 발광 마스크: 유리만 색, 틀은 검정."""
        frame = (0, 0, 0) if glow else (0.86, 0.78, 0.58)
        a = np.ones((16, 12, 4)); a[..., :3] = frame
        for r in range(2, 14):
            for c in range(2, 10):
                a[r, c, :3] = glass
        a[2:14, 6, :3] = frame
        a[8, 2:10, :3] = frame
        if not glow:
            hl = tuple(min(1, g * 1.25 + 0.1) for g in glass)
            for d in range(4):
                self.put(a, 11 - d, 3 + d, hl); self.put(a, 5 - d, 7 + d, hl)
        return a
    def t_door(self):
        a = self.noise(12, 20, (0.38, 0.25, 0.14), 0.06)
        a[:, 0, :3] *= 0.7; a[:, -1, :3] *= 0.7
        return a
    def t_lantern(self, glow=False):
        a = np.ones((8, 8, 4)); a[..., :3] = (0, 0, 0) if glow else (0.15, 0.15, 0.17)
        for r in range(2, 6):
            for c in range(2, 6):
                a[r, c, :3] = (1.0, 0.85, 0.45) if (r + c) % 3 else (1.0, 0.70, 0.30)
        return a
    def t_moon(self):
        a = self.noise(16, 16, (0.92, 0.93, 0.88), 0.04)
        for r, c in ((4, 4), (5, 4), (4, 5), (10, 9), (11, 10), (10, 10), (7, 12), (12, 3)):
            self.put(a, r, c, (0.72, 0.74, 0.70))
        return a

    # ---------------- 재질 ----------------
    def mat_for(self, key, alpha=False, emit=0.0, glow=None):
        """emit>0이면 발광. glow=마스크 텍스처 키(없으면 텍스처 색 전체가 빛남)."""
        mk = f"{key}|{int(alpha)}|{emit}|{glow}"
        if mk in self.MAT:
            return self.MAT[mk]
        for k in (key, glow):
            if k and k not in self.IMG:
                self.make_img(k, self.ENV_TEX[k]())
        m = bpy.data.materials.new(self.prefix + key + (f"_e{emit}" if emit else ""))
        m.use_nodes = True
        nt = m.node_tree
        bsdf = nt.nodes.get("Principled BSDF")
        tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = self.IMG[key]; tx.interpolation = 'Closest'
        nt.links.new(tx.outputs["Color"], bsdf.inputs["Base Color"])
        # 화질 v3: 재질마다 거칠기 다르게(물·얼음은 반짝, 바위·흙은 매트) — 키에 단어가 들어가면 적용
        rough = 0.8
        for word, r in getattr(self, "ROUGH", ROUGH_DEFAULT).items():
            if word in key:
                rough = r; break
        bsdf.inputs["Roughness"].default_value = rough
        if "Specular IOR Level" in bsdf.inputs:
            if "ice" in key or "snow" in key:       # 얼음·눈 윗면이 하얗게 날아가지 않게(Gemini 2차 지적)
                bsdf.inputs["Specular IOR Level"].default_value = 0.35
            elif rough < 0.3:
                bsdf.inputs["Specular IOR Level"].default_value = 0.7
        if alpha:
            nt.links.new(tx.outputs["Alpha"], bsdf.inputs["Alpha"])
        if emit:
            src = tx
            if glow:
                # 입력을 연결하지 않으면 활성 UV를 쓰므로 색 텍스처와 같은 좌표가 된다
                src = nt.nodes.new("ShaderNodeTexImage"); src.image = self.IMG[glow]; src.interpolation = 'Closest'
            nt.links.new(src.outputs["Color"], bsdf.inputs["Emission Color"])
            bsdf.inputs["Emission Strength"].default_value = emit
        self.MAT[mk] = m
        return m

    # ---------------- 상자 ----------------
    def box(self, name, size, offset=(0,0,0), tex="stone", tile=None, loc=(0,0,0), rot=(0,0,0),
            parent=None, alpha=False, emit=0.0, glow=None, coll=None):
        """tex: 문자열 / dict(면별, 'all' 기본) / 함수(face, w, h) -> (key, arr)."""
        h = [s / 2 for s in size]
        verts, faces, uvs, keys = [], [], [], []
        for fk, (n, r, u) in FACES.items():
            hn = sum(abs(n[i]) * h[i] for i in range(3))
            hr = sum(abs(r[i]) * h[i] for i in range(3))
            hu = sum(abs(u[i]) * h[i] for i in range(3))
            if callable(tex):
                key, arr = tex(fk, max(1, round(2 * hr / P)), max(1, round(2 * hu / P)))
                self.make_img(key, arr)
            elif isinstance(tex, dict):
                key = tex.get(fk, tex.get("all"))
            else:
                key = tex
            base = len(verts)
            for a, b in ((-1,-1), (1,-1), (1,1), (-1,1)):
                verts.append(tuple(offset[i] + n[i]*hn + r[i]*a*hr + u[i]*b*hu for i in range(3)))
                uvs.append(((a+1)/2 * 2*hr / tile, (b+1)/2 * 2*hu / tile) if tile else ((a+1)/2, (b+1)/2))
            faces.append((base, base+1, base+2, base+3))
            keys.append(key)
        me = bpy.data.meshes.new(self.prefix + name)
        me.from_pydata(verts, [], faces)
        uvl = me.uv_layers.new()
        for li, uv in enumerate(uvs):
            uvl.data[li].uv = uv
        slots = []
        for k in keys:
            if k not in slots:
                slots.append(k)
        for k in slots:
            me.materials.append(self.mat_for(k, alpha, emit, glow))
        for pi, k in enumerate(keys):
            me.polygons[pi].material_index = slots.index(k)
        ob = bpy.data.objects.new(name, me)
        (coll or self.coll).objects.link(ob)
        ob.location = loc; ob.rotation_euler = rot
        if parent:
            ob.parent = parent
        return ob

    # ---------------- 모기 (흰줄숲모기, 머리 +X) ----------------
    # 색 변형용 팔레트: base(머리·가슴), body(배·다리), band(흰 띠), eye
    PAL_AEDES = {"base": DARK, "body": BLACK, "band": WHITE, "eye": RED}
    PAL_VARIANTS = [
        {"base": (0.45, 0.32, 0.18), "body": (0.38, 0.26, 0.14), "band": (0.80, 0.66, 0.40), "eye": (0.15, 0.55, 0.20)},  # 갈색(집모기)
        {"base": (0.72, 0.56, 0.20), "body": (0.55, 0.40, 0.12), "band": (0.95, 0.85, 0.50), "eye": (0.80, 0.25, 0.10)},  # 금색
        {"base": (0.40, 0.40, 0.42), "body": (0.30, 0.30, 0.33), "band": (0.75, 0.75, 0.78), "eye": (0.20, 0.30, 0.80)},  # 회색
        {"base": (0.18, 0.28, 0.20), "body": (0.12, 0.20, 0.14), "band": (0.55, 0.80, 0.40), "eye": (0.85, 0.70, 0.10)},  # 초록
        {"base": (0.30, 0.16, 0.26), "body": (0.22, 0.10, 0.18), "band": (0.85, 0.55, 0.75), "eye": (0.95, 0.95, 0.30)},  # 보라
    ]

    def _pal(self):
        return getattr(self, "cur_pal", self.PAL_AEDES)

    def _tag(self):
        return getattr(self, "cur_tag", "")

    def head_tex(self, fk, w, h):
        p = self._pal()
        DARK, BLACK, WHITE, RED = p["base"], p["body"], p["band"], p["eye"]
        RED_D = tuple(c * 0.55 for c in RED)
        a = self.noise(w, h, DARK, 0.06)
        if fk == "px":
            for c0 in (1, 6):
                for r in range(3, 7):
                    for c in range(c0, c0 + 3):
                        self.put(a, r, c, RED_D if r == 6 else RED)
                self.put(a, 5, c0, (0.95, 0.95, 0.92)); self.put(a, 4, c0 + 2, tuple(c * 0.3 for c in RED))
            self.put(a, 8, 4, WHITE); self.put(a, 8, 5, WHITE)
            self.put(a, 1, 4, BLACK); self.put(a, 1, 5, BLACK)
        elif fk in ("py", "ny"):
            cols = (0, 1) if fk == "py" else (w - 2, w - 1)
            for r in range(3, 7):
                for c in cols:
                    self.put(a, r, c, RED_D if r == 6 else RED)
        elif fk == "pz":
            for r in range(h // 2, h):
                self.put(a, r, w // 2 - 1, WHITE); self.put(a, r, w // 2, WHITE)
        return self._tag() + "mq_head_" + fk, a

    def thorax_tex(self, fk, w, h):
        p = self._pal(); DARK, WHITE = p["base"], p["band"]
        a = self.noise(w, h, DARK, 0.07)
        if fk == "pz":
            for r in range(h):
                self.put(a, r, w // 2 - 1, WHITE); self.put(a, r, w // 2, WHITE)
            for r, c in ((3, 1), (8, 1), (3, w - 2), (8, w - 2)):
                self.put(a, r, c, WHITE)
        elif fk in ("py", "ny"):
            self.put(a, 7, 3, WHITE); self.put(a, 4, 8, WHITE); self.put(a, 6, 9, WHITE)
        return self._tag() + "mq_thorax_" + fk, a

    def abdomen_tex(self, fk, w, h):
        p = self._pal(); BLACK, WHITE = p["body"], p["band"]
        a = self.noise(w, h, BLACK, 0.08)
        L = 16
        band = lambda d: d % 4 == 3
        if fk == "ny":
            for c in range(w):
                if band(L - 1 - c): a[:, c, :3] = WHITE
        elif fk == "py":
            for c in range(w):
                if band(c): a[:, c, :3] = WHITE
        elif fk in ("pz", "nz"):
            for r in range(h):
                if band(L - 1 - r): a[r, :, :3] = WHITE
        return self._tag() + "mq_abdomen_" + fk, a

    def leg_tex(self, kind):
        p = self._pal(); BLACK, WHITE = p["body"], p["band"]; tag = self._tag()
        def f(fk, w, h):
            a = self.noise(w, h, BLACK, 0.06)
            if fk not in ("pz", "nz"):
                for r in range(h):
                    if (kind == "tibia" and (h - 1 - r) % 4 == 3) or (kind == "femur" and r == 0):
                        a[r, :, :3] = WHITE
            return f"{tag}mq_{kind}_{fk}_{h}", a
        return f

    def solid_tex(self, name, col):
        tag = self._tag()
        return lambda fk, w, h: (f"{tag}mq_{name}_{fk}_{w}x{h}", self.noise(w, h, col, 0.05))

    @staticmethod
    def wing_tex(fk, w, h):
        a = np.zeros((h, w, 4))
        for r in range(h):
            for c in range(w):
                if ((c - (w - 1) / 2) / (w / 2)) ** 2 + ((r - (h - 1) / 2) / (h / 2)) ** 2 <= 1.0:
                    vein = (c == w // 2) or (r % 4 == 1 and 1 <= c <= w - 2)
                    a[r, c, :3] = (0.35, 0.38, 0.42) if vein else (0.85, 0.92, 1.0)
                    a[r, c, 3] = 0.95 if vein else 0.55
        return f"mq_wing_{fk}_{w}x{h}", a

    def mosquito(self, name="HERO_mosquito", coll=None, flap_frames=(1, 600), pal=None, tag="",
                 male=False, resting=False):
        """원점 기준 모기 한 마리. (root, wings) 반환.
        flap_frames: 날개 퍼덕임 구간(None이면 정지). pal/tag: 색 변형(텍스처 캐시 구분용 tag 필수).
        male: 털 더듬이(수컷). resting: 날개를 배 위로 접고 퍼덕이지 않는다."""
        self.cur_pal = pal or self.PAL_AEDES
        self.cur_tag = tag
        p = self.cur_pal
        BLACK = p["body"]
        coll = coll or self.coll
        root = bpy.data.objects.new(name, None)
        coll.objects.link(root)
        b = lambda *a, **k: self.box(*a, parent=root, coll=coll, **k)
        b(f"{name}_thorax", (12*P, 10*P, 10*P), tex=self.thorax_tex)
        b(f"{name}_head", (10*P, 10*P, 10*P), tex=self.head_tex, loc=(11*P, 0, -1*P))
        b(f"{name}_proboscis", (14*P, 1*P, 1*P), offset=(7*P, 0, 0), tex=self.solid_tex("prob", BLACK),
          loc=(15*P, 0, -4.5*P), rot=(0, 0.6, 0))
        for s in (-1, 1):
            ant = b(f"{name}_antenna_{s:+d}", (1*P, 1*P, 7*P), offset=(0, 0, 3.5*P),
                    tex=self.solid_tex("ant", (0.30, 0.28, 0.27)), loc=(15*P, s*2.5*P, 3*P), rot=(-s*0.45, 0.65, 0))
            if male:   # 수컷: 깃털 같은 털 더듬이
                for k, z in enumerate((2.0, 3.5, 5.0, 6.3)):
                    wd = (4.0, 3.5, 2.8, 2.0)[k] * P
                    self.box(f"{name}_plume_{s:+d}_{k}", (wd, wd, 0.6*P), tex=self.solid_tex("plume", (0.55, 0.52, 0.48)),
                             loc=(0, 0, z*P), parent=ant, coll=coll)
        b(f"{name}_abdomen", (16*P, 8*P, 8*P), offset=(-8*P, 0, 0), tex=self.abdomen_tex,
          loc=(-6*P, 0, -1*P), rot=(0, -0.22, 0))
        wings = []
        for s in (-1, 1):
            rot = (s*0.08, 0, s*0.3) if resting else (s*0.5, 0, 0)
            w = b(f"{name}_wing_{s:+d}", (14*P, 7*P, 0.25*P), offset=(-7*P, s*3.5*P, 0), tex=self.wing_tex,
                  loc=(1*P, s*(2.5 if resting else 4)*P, 5.3*P), rot=rot, alpha=True)
            wings.append((w, s))
        L1, L2 = 12*P, 14*P
        for x, (fx, fy), (tx_, ty) in [(4*P, (0.75, -0.60), (0.30, 0.35)),
                                        (0, (0.95, 0.10), (0.20, 0.50)),
                                        (-4*P, (0.70, 0.75), (0.30, 1.10))]:
            for s in (-1, 1):
                attach = Vector((x, s*4*P, -5*P))
                r1 = Euler((s*fx, fy, 0))
                b(f"{name}_femur_{x:+.2f}_{s:+d}", (1*P, 1*P, L1), offset=(0, 0, -L1/2),
                  tex=self.leg_tex("femur"), loc=attach, rot=r1)
                knee = attach + r1.to_matrix() @ Vector((0, 0, -L1))
                b(f"{name}_tibia_{x:+.2f}_{s:+d}", (1*P, 1*P, L2), offset=(0, 0, -L2/2),
                  tex=self.leg_tex("tibia"), loc=knee, rot=(s*(fx + tx_), fy + ty, 0))
        self.cur_pal, self.cur_tag = self.PAL_AEDES, ""
        if resting or not flap_frames:
            return root, wings
        f0, f1 = flap_frames
        for w, s in wings:
            for f in range(f0, f1 + 1):
                w.rotation_euler = (s * (0.7 if f % 2 else 0.1), 0, 0)
                w.keyframe_insert("rotation_euler", frame=f)
            for fc in self.fcurves(w):
                for kp in fc.keyframe_points:
                    kp.interpolation = 'LINEAR'
        return root, wings

    # ---------------- 꽃 (원점 기준, 줄기 + 꽃머리 + 잎) ----------------
    FLOWER_KINDS = {
        "poppy": ((0.85, 0.12, 0.10), (0.15, 0.10, 0.08)),
        "dandelion": ((0.98, 0.82, 0.15), (0.85, 0.60, 0.10)),
        "cornflower": ((0.30, 0.45, 0.95), (0.95, 0.95, 0.95)),
        "daisy": ((0.97, 0.97, 0.95), (0.98, 0.80, 0.15)),
    }
    FLOWER_TOP = 17 * P  # 꽃머리 윗면 높이

    def flower(self, kind, name, coll=None):
        petal, center = self.FLOWER_KINDS[kind]
        def head(fk, w, h):
            a = self.noise(w, h, petal, 0.08)
            if fk == "pz":
                for r in range(1, h - 1):
                    for c in range(1, w - 1):
                        a[r, c, :3] = center
            return f"fl_{kind}_{fk}", a
        root = bpy.data.objects.new(name, None)
        (coll or self.coll).objects.link(root)
        stem = lambda fk, w, h: ("fl_stem", self.noise(w, h, (0.20, 0.50, 0.14), 0.10))
        self.box(f"{name}_stem", (1*P, 1*P, 12*P), offset=(0, 0, 6*P), tex=stem, parent=root, coll=coll)
        self.box(f"{name}_head", (5*P, 5*P, 5*P), offset=(0, 0, 14.5*P), tex=head, parent=root, coll=coll)
        self.box(f"{name}_leaf_a", (4*P, 1*P, 1*P), offset=(2*P, 0, 5*P), tex=stem, parent=root, coll=coll)
        self.box(f"{name}_leaf_b", (1*P, 3*P, 1*P), offset=(0, -1.5*P, 8*P), tex=stem, parent=root, coll=coll)
        return root

    # ---------------- 색 복셀 메쉬 (블록 수천 개를 한 메쉬로) ----------------
    VOX_DIRS = [((1,0,0), [(1,0,0),(1,1,0),(1,1,1),(1,0,1)]), ((-1,0,0), [(0,1,0),(0,0,0),(0,0,1),(0,1,1)]),
                ((0,1,0), [(1,1,0),(0,1,0),(0,1,1),(1,1,1)]), ((0,-1,0), [(0,0,0),(1,0,0),(1,0,1),(0,0,1)]),
                ((0,0,1), [(0,0,1),(1,0,1),(1,1,1),(0,1,1)]), ((0,0,-1), [(0,1,0),(1,1,0),(1,0,0),(0,0,0)])]

    def voxel_mesh(self, name, vox, size, center=(0, 0, 0), emit=0.0):
        """vox: {(i,j,k): (r,g,b)}. 보이는 면만, 블록마다 색 흔들기. center: 격자 원점 보정(블록 단위)."""
        verts, faces, cols = [], [], []
        for (i, j, k), col in vox.items():
            c = tuple(min(1, x * (1 + self.rng.uniform(-0.07, 0.07))) for x in col) + (1.0,)
            for d, quad in self.VOX_DIRS:
                if (i + d[0], j + d[1], k + d[2]) in vox:
                    continue
                base = len(verts)
                for (a, b, e) in quad:
                    verts.append(((i + a - center[0]) * size, (j + b - center[1]) * size, (k + e - center[2]) * size))
                faces.append((base, base + 1, base + 2, base + 3)); cols.append(c)
        me = bpy.data.meshes.new(self.prefix + name)
        me.from_pydata(verts, [], faces)
        attr = me.attributes.new("Col", 'FLOAT_COLOR', 'FACE')
        for idx, c in enumerate(cols):
            attr.data[idx].color = c
        m = bpy.data.materials.new(self.prefix + name + "_mat"); m.use_nodes = True
        nt = m.node_tree; bsdf = nt.nodes["Principled BSDF"]
        at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "Col"
        nt.links.new(at.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.8
        if emit:
            nt.links.new(at.outputs["Color"], bsdf.inputs["Emission Color"])
            bsdf.inputs["Emission Strength"].default_value = emit
        me.materials.append(m)
        ob = bpy.data.objects.new(name, me); self.coll.objects.link(ob)
        return ob

    # 대륙 근사(위도, 경도, 위도반경, 경도반경) — 블록 지구용 거친 육지 마스크
    LAND = [(5, 20, 35, 22), (25, 12, 12, 28), (10, 42, 8, 8), (-20, 47, 7, 4),
            (52, 15, 10, 25), (62, 25, 8, 15), (50, 90, 20, 50), (65, 100, 10, 50), (20, 78, 10, 8),
            (15, 103, 9, 8), (23, 47, 8, 10), (35, 110, 10, 15), (0, 113, 4, 10), (-5, 140, 4, 8),
            (50, -100, 20, 30), (65, -110, 10, 35), (20, -100, 8, 10), (72, -40, 8, 14),
            (-12, -58, 22, 15), (-38, -66, 14, 6), (-25, 134, 10, 16), (36, 138, 5, 4)]

    def is_land(self, lat, lon):
        if lat < -68:
            return True
        for la, lo, rla, rlo in self.LAND:
            dlo = (lon - lo + 180) % 360 - 180
            if ((lat - la) / rla) ** 2 + (dlo / rlo) ** 2 <= 1:
                return True
        return False

    def voxel_earth(self, name, R=20, size=0.5):
        """블록 지구(속 빈 껍질). 경도 0°가 +X, 북극 +Z. 오브젝트 원점 = 지구 중심."""
        vox = {}
        for i in range(-R, R + 1):
            for j in range(-R, R + 1):
                for k in range(-R, R + 1):
                    d = math.sqrt((i + .5) ** 2 + (j + .5) ** 2 + (k + .5) ** 2)
                    if not (R - 1.8 <= d <= R):
                        continue
                    lat = math.degrees(math.asin((k + .5) / d)); lon = math.degrees(math.atan2(j + .5, i + .5))
                    if abs(lat) > 72:
                        col = (0.93, 0.95, 0.97)
                    elif self.is_land(lat, lon):
                        dry = (abs(lat) < 32 and abs(lat) > 12) or (15 < lat < 32 and -20 < lon < 60)
                        col = (0.78, 0.66, 0.38) if dry else (0.30, 0.58, 0.20)
                    else:
                        col = (0.12, 0.34, 0.78) if d > R - 1 else (0.08, 0.25, 0.62)
                    vox[(i, j, k)] = col
        return self.voxel_mesh(name, vox, size, center=(0, 0, 0))

    # ---------------- 얼굴 없는 블록 인형 ----------------
    def person(self, name, shirt=(0.25, 0.45, 0.75), pants=(0.20, 0.20, 0.30), skin=(0.55, 0.38, 0.26), coll=None):
        """마인크래프트 비율, 얼굴 없음(머리는 머리카락+피부만). 원점 = 발바닥 중앙, 정면 -Y."""
        root = bpy.data.objects.new(name, None); (coll or self.coll).objects.link(root)
        tag = f"pp_{name}_"
        def sol(col, nm):
            return lambda fk, w, h: (f"{tag}{nm}_{fk}_{w}x{h}", self.noise(w, h, col, 0.06))
        def head(fk, w, h):
            a = self.noise(w, h, skin, 0.05)
            hair = (0.10, 0.07, 0.05)
            if fk == "pz":
                a[..., :3] = hair
            elif fk != "nz":
                a[h - 2:, :, :3] = hair
                if fk == "py":   # 뒤통수
                    a[2:, :, :3] = hair
            return f"{tag}head_{fk}", a
        b = lambda *a, **k: self.box(*a, parent=root, coll=coll, **k)
        b(f"{name}_legL", (4*P, 4*P, 12*P), offset=(-2*P, 0, 6*P), tex=sol(pants, "pants"))
        b(f"{name}_legR", (4*P, 4*P, 12*P), offset=(2*P, 0, 6*P), tex=sol(pants, "pants"))
        b(f"{name}_body", (8*P, 4*P, 12*P), offset=(0, 0, 18*P), tex=sol(shirt, "shirt"))
        b(f"{name}_armL", (4*P, 4*P, 12*P), offset=(-6*P, 0, 18*P), tex=sol(skin, "skin"))
        b(f"{name}_armR", (4*P, 4*P, 12*P), offset=(6*P, 0, 18*P), tex=sol(skin, "skin"))
        b(f"{name}_head", (8*P, 8*P, 8*P), offset=(0, 0, 28*P), tex=head)
        return root

    def instance(self, name, src_coll, loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0):
        e = bpy.data.objects.new(name, None)
        e.instance_type = 'COLLECTION'; e.instance_collection = src_coll
        self.coll.objects.link(e)
        e.location = loc; e.rotation_euler = rot; e.scale = (scale,) * 3
        return e

    def source_collection(self, name):
        """인스턴스 원본용 컬렉션: 씬에 연결하되 뷰 레이어에서 제외."""
        c = bpy.data.collections.new(name)
        self.SC.collection.children.link(c)
        self.SC.view_layers[0].layer_collection.children[c.name].exclude = True
        return c

    def day_sky(self, sun_energy=3.5):
        sun_d = bpy.data.lights.new(self.prefix + "sun", 'SUN'); sun_d.energy = sun_energy
        sun_d.angle = math.radians(2); sun_d.color = (1.0, 0.96, 0.9)
        sun = bpy.data.objects.new("LGT_sun", sun_d); self.SC.collection.objects.link(sun)
        sun.rotation_euler = (math.radians(50), 0, math.radians(-35))
        w = bpy.data.worlds.new(self.prefix + "world"); self.SC.world = w
        w.use_nodes = True
        w.node_tree.nodes["Background"].inputs[0].default_value = (0.22, 0.45, 1.0, 1)
        w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
        return sun

    def camera(self, name, lens, fstop, keys, tgt_keys, focus=None):
        """keys/tgt_keys: [(frame, (x,y,z)), ...]. 타깃을 바라보며 이동하는 카메라."""
        tgt = bpy.data.objects.new(f"{name}_target", None); self.coll.objects.link(tgt)
        cd = bpy.data.cameras.new(self.prefix + name); cd.lens = lens
        cd.clip_end = 6000.0   # 별(반지름 1800m)이 기본 1000m에서 잘려 우주가 단색으로 나왔음(04화 Gemini 1차, 2026-10-22)
        cd.dof.use_dof = fstop > 0; cd.dof.focus_object = focus or tgt; cd.dof.aperture_fstop = max(fstop, 0.5)
        cam = bpy.data.objects.new(name, cd); self.coll.objects.link(cam)
        tc = cam.constraints.new('TRACK_TO'); tc.target = tgt; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
        for f, loc in keys:
            cam.location = loc; cam.keyframe_insert("location", frame=f)
        for f, loc in tgt_keys:
            tgt.location = loc; tgt.keyframe_insert("location", frame=f)
        return cam

    def bind_cameras(self, pairs):
        for f, cam in pairs:
            m = self.SC.timeline_markers.new(cam.name, frame=f); m.camera = cam
        self.SC.camera = pairs[0][1]

    @staticmethod
    def fcurves(ob):
        """Blender 4.4+ 레이어드 액션과 이전 방식 둘 다에서 F-Curve 목록을 돌려준다."""
        ad = ob.animation_data
        if not ad or not ad.action:
            return []
        act = ad.action
        try:
            return list(act.fcurves)
        except AttributeError:
            pass
        out = []
        for layer in getattr(act, "layers", []):
            for strip in layer.strips:
                for cb in strip.channelbags:
                    out.extend(cb.fcurves)
        return out

    # ---------------- 거리 ----------------
    HOUSES = [(-30, 8, 8, "brick"), (-21, 7, 10, "plaster_yellow"), (-13, 9, 7, "plaster_gray"),
              (-3, 8, 9, "brick"), (6, 7, 8, "plaster_white"), (14, 9, 10, "brick"), (24, 7, 7, "plaster_yellow")]

    def street(self, night=False, trees=(-24.5, -12, 20)):
        """X축을 따라가는 도로, +Y 쪽에 집들. night=True면 창문 절반에 불이 켜진다."""
        B = self.box
        B("ENV_road", (90, 8, 0.2), offset=(0, 0, -0.1), tex="asphalt", tile=1)
        for x in range(-44, 44, 4):
            B(f"ENV_lane_{x}", (2, 0.2, 0.01), offset=(x + 1, 0, 0.005), tex="lane", tile=1)
        for y in (-3.6, 3.6):
            B(f"ENV_edge_{y}", (90, 0.15, 0.01), offset=(0, y, 0.005), tex="lane", tile=1)
        for s in (-1, 1):
            B(f"ENV_sidewalk_{s}", (90, 2.5, 0.15), offset=(0, s*5.25, 0.075), tex="stone", tile=1)
            B(f"ENV_grass_{s}", (90, 4, 1), offset=(0, s*8.5, -0.35),
              tex={"pz": "grass_top", "all": "grass_side"}, tile=1)
        B("ENV_far_ground", (400, 400, 1), offset=(0, 0, -0.65), tex="grass_top", tile=1)
        for x0, wd, ht, mt in self.HOUSES:
            cx = x0 + wd / 2
            B(f"ENV_house_{x0}", (wd, 6, ht), offset=(cx, 13.5, ht/2 + 0.15), tex=mt, tile=1)
            for z in np.arange(2.2, ht - 1.0, 2.8):
                for x in np.arange(x0 + 1.5, x0 + wd - 0.9, 2.2):
                    if z < 3 and abs(x - cx) < 1.2:
                        continue
                    if night:
                        lit = self.rng.random() < 0.5
                        B(f"ENV_win_{x0}_{x:.1f}_{z:.1f}", (1.2, 0.1, 1.6), offset=(x, 10.45, z),
                          tex="window_lit" if lit else "window_dark", emit=1.6 if lit else 0.0,
                          glow="window_lit_glow" if lit else None)
                    else:
                        B(f"ENV_win_{x0}_{x:.1f}_{z:.1f}", (1.2, 0.1, 1.6), offset=(x, 10.45, z), tex="window")
            B(f"ENV_door_{x0}", (1.2, 0.1, 2.2), offset=(cx, 10.45, 1.25), tex="door")
            for k in range(4):
                B(f"ENV_roof_{x0}_{k}", (wd + 0.4, 6.4 - 1.5*k, 1), offset=(cx, 13.5, ht + 0.65 + k),
                  tex="plaster_white", tile=1)
        for tx in trees:
            B(f"ENV_log_{tx}", (1, 1, 4), offset=(tx, 8.2, 2.15), tex="log", tile=1)
            B(f"ENV_leaves_a_{tx}", (5, 5, 3), offset=(tx, 8.2, 4.65), tex="leaves", tile=1)
            B(f"ENV_leaves_b_{tx}", (3, 3, 1.5), offset=(tx, 8.2, 6.9), tex="leaves", tile=1)

    def clouds(self, n=16):
        for i in range(n):
            self.box(f"ENV_cloud_{i}", (self.rng.uniform(6, 14), self.rng.uniform(3, 7), 1.2),
                     offset=(self.rng.uniform(-70, 70), self.rng.uniform(25, 100), self.rng.uniform(22, 32)),
                     tex="cloud", tile=1)

    # ---------------- 렌더 공통 ----------------
    def render_setup(self, samples=48, res=(1920, 1080), motion_blur=0.3, look="v3"):
        SC = self.SC
        SC.render.engine = "BLENDER_EEVEE"
        SC.eevee.taa_render_samples = samples
        SC.render.use_motion_blur = motion_blur > 0
        SC.render.motion_blur_shutter = motion_blur
        SC.view_settings.view_transform = 'Standard'
        SC.render.resolution_x, SC.render.resolution_y = res
        SC.render.fps = 24
        if look == "v3":
            self.look_v3()

    def look_v3(self, glare=0.55, vignette=0.22, saturation=1.08):
        """화질 v3(2026-10-20): 레이트레이싱 반사 + 빠른 GI(간접광·AO) + 부드러운 그림자 + 컴포지터(빛 번짐·비네트·채도).
        블록 스타일은 그대로 두고 빛과 깊이만 올린다."""
        SC = self.SC; e = SC.eevee
        try:
            e.use_raytracing = True
            e.ray_tracing_method = 'SCREEN'
            e.use_fast_gi = True
            e.fast_gi_method = 'GLOBAL_ILLUMINATION'
            e.fast_gi_distance = 12.0
            e.fast_gi_quality = 0.5
            e.use_shadows = True
            e.shadow_ray_count = 2
            e.shadow_step_count = 8
            e.clamp_surface_indirect = 10.0
            e.shadow_pool_size = '2048'   # 04화: 1024에서 "Shadow buffer full" 경고 → 그림자 일부 누락
        except Exception as ex:
            print("look_v3 eevee:", ex)
        # 바다·물이 "바바박" 깜빡임(사용자 지적 2026-10-20): 반투명 상자의 앞뒷면이 서로 그리는 순서를 다툼 → 뒷면 숨김·겹침 끔
        for m in bpy.data.materials:
            if getattr(m, "surface_render_method", "") == 'BLENDED':
                m.use_backface_culling = True
                for attr in ("use_transparency_overlap", "show_transparent_back"):
                    if hasattr(m, attr):
                        setattr(m, attr, False)
        for ob in SC.objects:          # 해 그림자 가장자리를 조금 부드럽게
            if ob.type == 'LIGHT' and ob.data.type == 'SUN' and ob.data.angle < math.radians(2.5):
                ob.data.angle = math.radians(2.5)
        try:
            self._compositor_v3(glare, vignette, saturation)
        except Exception as ex:
            print("look_v3 compositor:", ex)

    def _compositor_v3(self, glare, vignette, saturation):
        SC = self.SC
        ng = bpy.data.node_groups.new(self.prefix + "comp_v3", 'CompositorNodeTree')
        SC.compositing_node_group = ng
        ng.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
        N = ng.nodes; Lk = ng.links.new
        rl = N.new("CompositorNodeRLayers"); rl.scene = SC
        out = N.new("NodeGroupOutput")
        img = rl.outputs["Image"]
        haze = getattr(self, "haze_keys", None)
        if haze and any(v for _, v in haze):    # 낮 숏 공기 원근: 미스트 패스로 먼 곳을 하늘색 쪽으로
            SC.view_layers[0].use_pass_mist = True
            if SC.world:
                ms = SC.world.mist_settings; ms.start = 40.0; ms.depth = 700.0; ms.falloff = 'QUADRATIC'
            rl = rl   # 패스를 켠 뒤 소켓이 생김
            mm = N.new("ShaderNodeMath"); mm.operation = 'MULTIPLY'
            Lk(rl.outputs["Mist"], mm.inputs[0])
            for f, v in haze:
                mm.inputs[1].default_value = 0.15 * v; mm.inputs[1].keyframe_insert("default_value", frame=f)
            fcs = []
            ad = ng.animation_data
            if ad and ad.action:
                try: fcs = list(ad.action.fcurves)
                except AttributeError:
                    for ly in ad.action.layers:
                        for st in ly.strips:
                            for cb in st.channelbags: fcs.extend(cb.fcurves)
            for fc in fcs:
                for kp in fc.keyframe_points: kp.interpolation = 'CONSTANT'
            hm = N.new("ShaderNodeMix"); hm.data_type = 'RGBA'
            hm.inputs["B"].default_value = (0.72, 0.84, 1.0, 1)
            Lk(mm.outputs[0], hm.inputs["Factor"]); Lk(img, hm.inputs["A"])
            img = hm.outputs["Result"]
        if glare > 0:                   # 발광체(태양·오로라·창문)에 은은한 빛 번짐
            g = N.new("CompositorNodeGlare")
            for k, v in (("glare_type", 'FOG_GLOW'), ("quality", 'HIGH')):
                try: setattr(g, k, v)
                except Exception: pass
            def setin(name, val):
                if name in g.inputs:
                    g.inputs[name].default_value = val; return True
                return False
            setin("Threshold", 1.6) or setattr(g, "threshold", 1.6)
            setin("Strength", glare) or setin("Mix", glare - 1.0)
            setin("Size", 0.5)
            Lk(img, g.inputs["Image"]); img = g.outputs["Image"]
        cc = N.new("CompositorNodeColorCorrection")   # 채도·대비 살짝
        for nm in ("Master Saturation",):
            if nm in cc.inputs: cc.inputs[nm].default_value = saturation
        try: cc.master_saturation = saturation
        except Exception: pass
        # 대비는 올리지 않는다: 컴포지터 대비는 0.5 기준이라 어두운 색(우주 남색·그림자)을 0으로 눌러 순흑이 됨(2026-10-20 진단)
        Lk(img, cc.inputs["Image"]); img = cc.outputs["Image"]
        if vignette > 0:                # 가장자리를 살짝 어둡게 → 시선이 가운데로
            em = N.new("CompositorNodeEllipseMask")
            for k, v in (("Size", (0.95, 0.95)),):
                if k in em.inputs: em.inputs[k].default_value = v
            try: em.width, em.height = 0.95, 0.95
            except Exception: pass
            bl = N.new("CompositorNodeBlur")
            try: bl.size_x = bl.size_y = 260
            except Exception:
                if "Size" in bl.inputs: bl.inputs["Size"].default_value = (260, 260)
            Lk(em.outputs[0], bl.inputs["Image"])
            mx = N.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
            mx.inputs["Factor"].default_value = vignette
            mr = N.new("ShaderNodeMapRange")       # 마스크 0(가장자리)~1(가운데) → 0.0~1.0 곱
            Lk(bl.outputs["Image"] if "Image" in bl.outputs else bl.outputs[0], mr.inputs["Value"])
            Lk(img, mx.inputs["A"]); Lk(mr.outputs["Result"], mx.inputs["B"])
            img = mx.outputs["Result"]
        Lk(img, out.inputs[0])
