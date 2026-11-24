# 블록 캐릭터 리그 v2 (2026-11-05) — char_rig v1과 같은 함수 이름, import 한 줄만 바꾸면 된다:
#   import char_rig2 as CR
# v1에서 달라진 점
#   모양: 모서리 베벨(살짝 깎음), 재킷 겉층(깃 두께), 입체 앞머리·머리 껍데기, 소매 끝단, 앞코 나온 신발 + 발목 관절
#   리그: torso 아래 breath(숨 쉬기 전용) 관절, 발목(ankleL/R, 신발 바닥을 땅과 평행하게)
#   동작: walk_to/run_to = 발이 땅에 붙는 걷기·뛰기(다리 각도를 발 위치에서 역계산), 골반 좌우 이동·비틀림,
#         상체 반대 비틀림, 팔이 2프레임 늦게 따라옴, 머리카락 뒤로 날림
#         idle = 숨 쉬기, auto_blink = 자동 눈 깜빡임(표정이 normal일 때만)
# v1 함수(pose·snap·squash·face·move·turn·walk·run·rest·planted_hips)는 그대로 쓸 수 있다.
import bpy, math, random
import bmesh
from mathutils import Vector, Matrix, Euler
import char_rig as V1
from char_rig import (HERO, BOY, BUDDY, THIEF, EXPRESSIONS, face_pixels, _img, _shade, _fcurves, _part, _body_tex,
                      set_ease, pose, snap, squash, unsquash, move, turn, planted_hips, run, walk)

P = 1 / 16
THIGH, SHIN, ANKLE_H = 6 * P, 4 * P, 2 * P      # 엉덩이→무릎, 무릎→발목, 발목→발바닥

JOINTS = V1.JOINTS + ("ankleL", "ankleR")
REST = dict(V1.REST, ankleL=(0, 0, 0), ankleR=(0, 0, 0))


# ---------------- 모양 다듬기 ----------------
def _soft(ob, w=0.18 * P, seg=2):
    """L.box가 만든 상자(면마다 따로 떨어진 점)를 하나로 붙이고 베벨 — 모서리에 빛이 맺혀 덩어리감이 산다."""
    me = ob.data
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    m = ob.modifiers.new("soft", 'BEVEL')
    m.width = w; m.segments = seg; m.limit_method = 'ANGLE'; m.harden_normals = True
    return ob


def _solid(L, key, col):
    L.make_img(key, _img(2, 2, col))
    return key


def _shell_torso(spec, tag):
    """재킷 겉층: 앞면은 깃 두 줄만 남기고 투명(안쪽 티가 보임), 아랫면 투명."""
    J, J2 = spec["jacket"], spec["jacket2"]

    def f(fk, w, h):
        key = f"{tag}_shell_{fk}"
        if fk == "ny":
            a = _img(h, 8, J); a[..., 3] = 0
            for r in range(h):
                for c in (0, 1, 6, 7):
                    a[r, c, 3] = 1
                a[r, 1, :3] = J2; a[r, 6, :3] = J2
            return key, a
        a = _img(h, w, J)
        if fk == "nz":
            a[..., 3] = 0
        elif fk in ("px", "nx") and h >= 8:
            for r in range(h):
                a[r, w // 2, :3] = J2 if spec.get("girl") else _shade(J, 0.85)
        return key, a
    return f


def _seg(fn, lo, hi, tagp):
    """12칸 다리 무늬에서 lo~hi행(아래가 0)만 잘라 쓰는 토막 텍스처. 위·아래 면은 이음 높이 색 한 가지."""
    def f(fk, w, h):
        if fk in ("pz", "nz"):
            key, a = fn("py", 4, 12)
            row = hi - 1 if fk == "pz" else lo
            return f"{key}_{tagp}_{fk}", _img(h, w, tuple(a[row, 0, :3]))
        key, a = fn(fk, w, 12)
        return f"{key}_{tagp}", a[lo:hi].copy()
    return f


def _shoe_tex(spec, tag):
    S = spec["shoes"]
    sole = (0.96, 0.96, 0.94) if sum(S) < 1.6 else _shade(S, 0.62)

    def f(fk, w, h):
        a = _img(max(h, 2), w, S)
        if fk == "nz":
            a[..., :3] = _shade(sole, 0.7)
        elif fk != "pz":
            a[0, :, :3] = sole
            if fk == "ny":                     # 앞코 줄
                a[1, :, :3] = _shade(S, 0.88)
        return f"{tag}_shoe_{fk}_{w}x{h}", a
    return f


def _empty(L, name, loc=(0, 0, 0), parent=None):
    return V1._empty(L, name, loc, parent)


# ---------------- 조립 ----------------
def build(L, name, spec, loc=(0, 0, 0), rot_z=0.0, bevel=True):
    """원점 = 발바닥 가운데, 정면 −Y. 반환 dict(v1 키 + breath, ankleL/R)."""
    tag = f"cr2_{name}"
    torso_t, arm_t, leg_t, head_t = _body_tex(spec, tag)
    soft = _soft if bevel else (lambda ob, *a, **k: ob)
    root = _empty(L, name, loc)
    root.rotation_euler = (0, 0, math.radians(rot_z))
    hips = _empty(L, f"{name}_hips", (0, 0, 12 * P), root)
    ch = dict(root=root, hips=hips, spec=spec, faces={}, name=name, _facelog=[], v=2)

    # 다리: 허벅지(엉덩이 축) → 정강이(무릎 축) → 신발(발목 축)
    shoe_t = _shoe_tex(spec, tag)
    for side, sx in (("L", -1), ("R", 1)):
        lp = _empty(L, f"{name}_leg{side}", (sx * 2 * P, 0, 0), hips)
        soft(L.box(f"{name}_thigh{side}", (4 * P, 4 * P, 6.5 * P), offset=(0, 0, -3.25 * P),
                   tex=_seg(leg_t, 7, 12, "thigh"), parent=lp), 0.14 * P)
        kp = _empty(L, f"{name}_knee{side}", (0, 0, -THIGH), lp)
        soft(L.box(f"{name}_shin{side}", (3.92 * P, 3.92 * P, 4.5 * P), offset=(0, 0, -2.0 * P),
                   tex=_seg(leg_t, 3, 7, "shin"), parent=kp), 0.12 * P)
        ap = _empty(L, f"{name}_ankle{side}", (0, 0, -SHIN), kp)
        ap.rotation_mode = 'YXZ'               # 발목 보정 각을 정확히 되돌리기 위한 순서(walk_to 참고)
        soft(L.box(f"{name}_shoe{side}", (4.3 * P, 5.3 * P, 2.2 * P), offset=(0, -0.65 * P, -0.9 * P),
                   tex=shoe_t, parent=ap), 0.3 * P, 2)
        ch["leg" + side] = lp; ch["knee" + side] = kp; ch["ankle" + side] = ap

    torso = _empty(L, f"{name}_torso", (0, 0, 0), hips)
    breath = _empty(L, f"{name}_breath", (0, 0, 0), torso)
    soft(L.box(f"{name}_body", (8 * P, 4 * P, 12 * P), offset=(0, 0, 6 * P), tex=torso_t, parent=breath), 0.16 * P)
    if not spec.get("no_shell"):
        L.box(f"{name}_jacket", (8.6 * P, 4.6 * P, 12.25 * P), offset=(0, 0, 6.05 * P), tex=_shell_torso(spec, tag),
              parent=breath, alpha=True)
    ch["torso"] = torso; ch["breath"] = breath

    aw = spec.get("arm_w", 4)
    J, J2 = spec["jacket"], spec["jacket2"]
    cuff = _solid(L, f"{tag}_cuff", J2 if J2 != J else _shade(J, 0.85))
    for side, sx in (("L", -1), ("R", 1)):
        ap = _empty(L, f"{name}_arm{side}", (sx * (4 + aw / 2 + 0.05) * P, 0, 10 * P), breath)
        soft(L.box(f"{name}_uparm{side}", (aw * P, 4 * P, 6.5 * P), offset=(0, 0, -1.25 * P),
                   tex=_part(arm_t, "upper"), parent=ap), 0.14 * P)
        ep = _empty(L, f"{name}_elbow{side}", (0, 0, -4 * P), ap)
        soft(L.box(f"{name}_forearm{side}", ((aw - 0.04) * P, 3.96 * P, 6.5 * P), offset=(0, 0, -3.0 * P),
                   tex=_part(arm_t, "lower"), parent=ep), 0.14 * P)
        soft(L.box(f"{name}_cuff{side}", ((aw + 0.5) * P, 4.5 * P, 1.2 * P), offset=(0, 0, -2.45 * P),
                   tex=cuff, parent=ep), 0.15 * P)
        ch["arm" + side] = ap; ch["elbow" + side] = ep

    head = _empty(L, f"{name}_head", (0, 0, 12 * P), breath)
    hs = 9 if spec.get("helmet") else 8
    soft(L.box(f"{name}_headbox", (hs * P, hs * P, hs * P), offset=(0, 0, hs / 2 * P), tex=head_t, parent=head), 0.1 * P)
    ch["head"] = head
    for ex in EXPRESSIONS:
        key = f"{tag}_face_{ex}"
        L.make_img(key, face_pixels(spec, ex))
        f = L.box(f"{name}_face_{ex}", (hs * P, 0.001, hs * P), offset=(0, -hs / 2 * P - 0.0015, hs / 2 * P),
                  tex={"ny": key, "all": key}, parent=head)
        f.visible_shadow = False
        ch["faces"][ex] = f

    hair = spec["hair"]
    hk = _solid(L, f"{tag}_hair", hair)
    hd = _solid(L, f"{tag}_hairD", _shade(hair, 0.72))
    if not spec.get("helmet"):
        # 머리 껍데기: 윗판 + (짧은 머리) 뒤판·옆판 — 머리카락이 머리 위에 얹힌 두께
        soft(L.box(f"{name}_hair_top", (8.7 * P, 8.7 * P, 1.0 * P), offset=(0, 0.1 * P, 8.2 * P), tex=hk, parent=head), 0.2 * P)
        if spec.get("long_hair"):
            hp = _empty(L, f"{name}_hairpiv", (0, 3.6 * P, 7.5 * P), head)
            soft(L.box(f"{name}_hair_back", (8.7 * P, 1.6 * P, 11 * P), offset=(0, 0.8 * P, -5.5 * P), tex=hk, parent=hp), 0.2 * P)
            ch["hair"] = hp
            for sx in (-1, 1):
                soft(L.box(f"{name}_hair_side{sx}", (1.2 * P, 3 * P, 7 * P), offset=(sx * 4.5 * P, -2.2 * P, 3 * P),
                           tex=hk, parent=head), 0.15 * P)
        elif not spec.get("hood_ears"):
            soft(L.box(f"{name}_hair_back", (8.7 * P, 0.6 * P, 5.6 * P), offset=(0, 4.3 * P, 5.3 * P), tex=hk, parent=head), 0.15 * P)
            for sx in (-1, 1):
                soft(L.box(f"{name}_hair_side{sx}", (0.5 * P, 8.0 * P, 3.0 * P), offset=(sx * 4.25 * P, 0.6 * P, 6.6 * P),
                           tex=hk, parent=head), 0.12 * P)
        _bangs3d(L, ch, spec, head, hk, hd, soft)
    else:
        vk = _solid(L, f"{tag}_visor", (0.04, 0.05, 0.08))
        soft(L.box(f"{name}_visor", (7.4 * P, 0.6 * P, 3.4 * P), offset=(0, -4.5 * P - 0.3 * P, 5.0 * P), tex=vk, parent=head), 0.2 * P)
    if spec.get("clip"):
        ck = _solid(L, f"{tag}_clip", spec["clip"])
        soft(L.box(f"{name}_clip", (2.2 * P, 1.2 * P, 1.2 * P), offset=(3 * P, -4.9 * P, 6.2 * P), tex=ck, parent=head), 0.2 * P)
    if spec.get("hood_ears"):
        ek = _solid(L, f"{tag}_ear", _shade(hair, 0.9))
        for sx in (-1, 1):
            soft(L.box(f"{name}_ear{sx}", (2.4 * P, 1.4 * P, 2.4 * P), offset=(sx * 3 * P, 0, 9 * P), tex=ek, parent=head), 0.25 * P)
    face(ch, 1, "normal")
    return ch


def _bangs3d(L, ch, spec, head, hk, hd, soft):
    """앞머리 문자열(16칸)을 입체 블록으로: 같은 모양 행끼리 한 덩어리, 앞으로 0.45칸 돌출."""
    rows = spec["bangs"]
    D = 0.45 * P
    y = -4 * P - 0.0025 - D / 2

    def runs(row):
        out, c = [], 0
        while c < len(row):
            ch_ = row[c]
            if ch_ in "h.":
                c0 = c
                while c < len(row) and row[c] == ch_:
                    c += 1
                out.append((c0, c, ch_))
            else:
                c += 1
        return tuple(out)

    r = 0
    k = 0
    while r < len(rows):
        rs = runs(rows[r]); r1 = r
        while r1 + 1 < len(rows) and runs(rows[r1 + 1]) == rs:
            r1 += 1
        for c0, c1, kind in rs:
            w = (c1 - c0) * 0.5 * P
            hgt = (r1 - r + 1) * 0.5 * P
            x = -4 * P + (c0 + c1) / 2 * 0.5 * P
            z = 8 * P - (r + r1 + 1) / 2 * 0.5 * P
            depth = D * (1.0 if r == 0 else 0.8)
            soft(L.box(f"{ch['name']}_bang{k}", (w, depth, hgt), offset=(x, -4 * P - 0.0025 - depth / 2, z),
                       tex=hk if kind == "h" else hd, parent=head), min(0.08 * P, w / 4))
            k += 1
        r = r1 + 1


# ---------------- 표정 ----------------
def face(ch, f, expr):
    V1.face(ch, f, expr)
    log = ch.setdefault("_facelog", [])
    log.append((f, expr)); log.sort()


def _expr_at(ch, f):
    cur = "normal"
    for fr, ex in ch.get("_facelog", []):
        if fr <= f:
            cur = ex
    return cur


def auto_blink(ch, f0, f1, seed=0, gap=(55, 120), dur=3):
    """표정이 normal인 구간에만 자연스러운 눈 깜빡임(가끔 두 번 연속)."""
    rng = random.Random(seed + hash(ch["name"]) % 997)
    t = f0 + rng.randint(10, gap[0])
    while t < f1 - dur:
        busy = any(abs(fr - t) < 6 or t < fr < t + dur + 2 for fr, _ in ch.get("_facelog", []))
        if not busy and _expr_at(ch, t) == "normal":
            V1.face(ch, t, "blink"); V1.face(ch, t + dur, "normal")
            ch["_facelog"].extend([(t, "blink"), (t + dur, "normal")]); ch["_facelog"].sort()
            if rng.random() < 0.18 and t + dur + 5 < f1:
                t2 = t + dur + 3
                V1.face(ch, t2, "blink"); V1.face(ch, t2 + dur, "normal")
                ch["_facelog"].extend([(t2, "blink"), (t2 + dur, "normal")]); ch["_facelog"].sort()
        t += rng.randint(*gap)


def idle(ch, f0, f1, amp=1.0, period=84):
    """숨 쉬기(breath 관절만 씀 — pose 키와 안 겹침): 가슴이 살짝 올라가며 뒤로."""
    b = ch["breath"]
    f = f0
    k = 0
    while f <= f1:
        up = k % 2 == 1
        b.location = (0, 0, 0.0045 * amp if up else 0.0)
        b.rotation_euler = (math.radians(-1.1 * amp) if up else 0.0, 0, 0)
        b.keyframe_insert("location", frame=f); b.keyframe_insert("rotation_euler", frame=f)
        f += period // 2; k += 1


def rest(ch, f):
    pose(ch, f, **REST)


# ---------------- 발이 땅에 붙는 걷기·뛰기 ----------------
def _chaikin(pts, it=2):
    for _ in range(it):
        if len(pts) < 3:
            break
        out = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            out += [a.lerp(b, 0.25), a.lerp(b, 0.75)]
        out.append(pts[-1]); pts = out
    return pts


class _Path:
    def __init__(self, pts, smooth=True):
        P3 = [Vector(p) if len(p) == 3 else Vector((p[0], p[1], 0.0)) for p in pts]
        self.p = _chaikin(P3) if smooth else P3
        self.acc = [0.0]
        for a, b in zip(self.p[:-1], self.p[1:]):
            self.acc.append(self.acc[-1] + (b - a).length)
        self.L = self.acc[-1]

    def at(self, d):
        d = max(0.0, min(self.L, d))
        for i in range(len(self.p) - 1):
            if d <= self.acc[i + 1] or i == len(self.p) - 2:
                s = self.acc[i + 1] - self.acc[i]
                return self.p[i].lerp(self.p[i + 1], 0 if s <= 0 else (d - self.acc[i]) / s)

    def tan(self, d, w=0.22):
        v = self.at(d + w) - self.at(d - w); v.z = 0
        if v.length < 1e-6:
            v = self.p[-1] - self.p[0]; v.z = 0
        return v.normalized() if v.length > 1e-6 else Vector((0, -1, 0))


def _yaw_of(t):
    return math.atan2(t.x, -t.y)             # 정면(−Y)을 t로 돌리는 Z 회전


def _smooth(a, n=2):
    out = list(a)
    for i in range(len(a)):
        lo, hi = max(0, i - n), min(len(a), i + n + 1)
        out[i] = sum(a[lo:hi]) / (hi - lo)
    return out


def _leg_ik(d):
    """다리 축 기준 발목 목표 d → (허벅지 X, 허벅지 Y, 무릎 X) 라디안. 무릎은 앞으로 굽는다."""
    zp = -math.sqrt(d.x * d.x + d.z * d.z)
    phi = math.atan2(d.x / zp, d.z / zp) if abs(zp) > 1e-9 else 0.0
    a, b = THIGH, SHIN
    D = math.hypot(d.y, zp)
    D = max(abs(a - b) + 1e-4, min(D, (a + b) * 0.9995))
    th = math.atan2(d.y, -zp)
    beta = math.acos(max(-1, min(1, (a * a + D * D - b * b) / (2 * a * D))))
    gam = math.acos(max(-1, min(1, (a * a + b * b - D * D) / (2 * a * b))))
    return th - beta, phi, math.pi - gam


def walk_to(ch, pts, f0, f1, step=0.40, run=False, lift=None, ramp=None, ahead=None, behind=None,
            arm=None, lean=None, bob=None, face_path=True, hold=True):
    """pts(바닥 위 점들, (x,y) 또는 (x,y,z))를 따라 f0→f1 동안 걷기(run=True면 뛰기). 발은 찍힌 자리에 붙어 있다.
    step = 한 걸음(발 하나) 거리 m. root 위치·방향, 골반, 상체, 팔, 다리, 발목, 머리카락을 매 프레임 키."""
    path = _Path(pts)
    Lt = path.L
    T = f1 - f0
    if run:
        lift = 0.17 if lift is None else lift; ahead = 0.32 if ahead is None else ahead
        behind = 0.32 if behind is None else behind; arm = 78 if arm is None else arm
        lean = 19 if lean is None else lean; bob = 0.9 * P if bob is None else bob
        ramp = min(8, T / 4) if ramp is None else ramp
    else:
        lift = 0.075 if lift is None else lift; ahead = 0.5 if ahead is None else ahead
        behind = 0.5 if behind is None else behind; arm = 26 if arm is None else arm
        lean = 3 if lean is None else lean; bob = 0.35 * P if bob is None else bob
        ramp = min(12, T / 4) if ramp is None else ramp
    n = max(1, round(Lt / step)); st = Lt / n
    vmax = Lt / max(1e-6, (T - ramp))

    def s_at(t):
        if t <= 0:
            return 0.0
        if t >= T:
            return Lt
        if t < ramp:
            return 0.5 * vmax * t * t / ramp
        if t < T - ramp:
            return 0.5 * vmax * ramp + vmax * (t - ramp)
        return Lt - 0.5 * vmax * (T - t) ** 2 / ramp

    def side(d):
        th = _yaw_of(path.tan(d))
        return Vector((math.cos(th), math.sin(th), 0))

    W = 2.0 * P

    def print_at(d, sx):
        return path.at(d) + side(d) * (sx * W)

    # 발자국: (거리, 들기 시작 s, 닿는 s)
    feet = {"L": [(0.0, None, None)], "R": [(0.0, None, None)]}
    for k in range(1, n + 1):
        ft = "R" if k % 2 == 1 else "L"
        D = k * st
        prev = feet[ft][-1][0]
        land = D - ahead * st
        lift_s = prev + behind * st
        if lift_s > land - 0.25 * st:
            lift_s = max(0.0, land - 0.42 * st)
        feet[ft].append((D, lift_s, land))
    last = "L" if n % 2 == 1 else "R"             # 마지막에 따라붙는 발
    prev = feet[last][-1][0]
    feet[last].append((Lt, max(prev + behind * st * 0.6, Lt - 0.5 * st), Lt - 0.02 * st))

    def foot_state(ft, s):
        """→ (바닥 위 위치, 들림 높이, 스윙 u 또는 None, 앞쪽 진행량)"""
        sx = -1 if ft == "L" else 1
        pr = feet[ft]
        cur = pr[0]
        for j in range(1, len(pr)):
            D, a, b = pr[j]
            if s < a:
                break
            if s <= b:
                u = (s - a) / max(1e-6, b - a)
                e = u * u * (3 - 2 * u)
                p0 = print_at(pr[j - 1][0], sx); p1 = print_at(D, sx)
                return p0.lerp(p1, e), lift * math.sin(math.pi * u) ** 0.9, u
            cur = pr[j]
        return print_at(cur[0], sx), 0.0, None

    frames = list(range(f0, f1 + 1))
    S = [s_at(f - f0) for f in frames]
    V = [(S[min(i + 1, len(S) - 1)] - S[max(i - 1, 0)]) / (2 if 0 < i < len(S) - 1 else 1) for i in range(len(S))]
    vnorm = [min(1.0, v / max(1e-6, vmax)) for v in V]
    yaw = []
    for i, s in enumerate(S):
        y = _yaw_of(path.tan(s)) if face_path else ch["root"].rotation_euler.z
        if yaw:                                   # 360도 넘어감 방지
            while y - yaw[-1] > math.pi: y -= 2 * math.pi
            while y - yaw[-1] < -math.pi: y += 2 * math.pi
        yaw.append(y)
    yaw = _smooth(yaw, 3)

    # 1차: 발 위치, 앞뒤 차이(팔·골반용)
    FS = {ft: [foot_state(ft, s) for s in S] for ft in ("L", "R")}
    fwd = []
    for i, s in enumerate(S):
        c = path.at(s); t = path.tan(s)
        fL = (FS["L"][i][0] - c).dot(t); fR = (FS["R"][i][0] - c).dot(t)
        fwd.append((fR - fL) / (1.2 * st))           # 오른발이 앞이면 +
    # 골반 높이: 두 다리가 닿는 높이와 기본 높이 중 낮은 쪽
    base_drop = (0.9 if run else 0.12) * P
    HZ = []
    for i, s in enumerate(S):
        c = path.at(s)
        hz = 12 * P - base_drop * vnorm[i]
        for ft in ("L", "R"):
            p, h, u = FS[ft][i]
            if u is not None and 0.12 < u < 0.88:   # 공중에 든 발은 무릎을 굽히면 되니 골반 높이를 끌어내리지 않음
                continue
            ank = p + Vector((0, 0, ANKLE_H + h))
            hd = (ank.xy - c.xy).length
            reach = (THIGH + SHIN) * 0.985
            need = ank.z - c.z + math.sqrt(max(0.0, reach * reach - hd * hd))
            hz = min(hz, need)
        if run:                                   # 뛰기: 공중에 뜬 순간 살짝 위로
            air = all(FS[ft][i][2] is not None for ft in ("L", "R"))
            hz += bob * (1.0 if air else 0.0)
        HZ.append(hz)
    HZ = _smooth(HZ, 1)

    lag = 2
    for i, f in enumerate(frames):
        s = S[i]; c = path.at(s); vn = vnorm[i]
        # root
        ch["root"].location = c; ch["root"].keyframe_insert("location", frame=f)
        ch["root"].rotation_euler = (0, 0, yaw[i]); ch["root"].keyframe_insert("rotation_euler", frame=f)
        # 골반: 디딘 발 쪽으로 이동, 앞으로 나간 다리 쪽 엉덩이가 앞으로(비틀림)
        ph = math.pi * s / st
        sway = -0.45 * P * math.cos(ph) * vn * (0.5 if run else 1.0)
        hyaw = math.radians(-(7 if run else 6)) * fwd[i] * vn
        hroll = math.radians(2.0) * math.cos(ph) * vn
        # 방향을 틀면 몸을 안쪽으로 기울임(왼쪽으로 돌면 왼쪽으로) — 다리는 IK가 알아서 맞춤
        dy_ = (yaw[min(i + 1, len(yaw) - 1)] - yaw[max(i - 1, 0)]) / 2
        hroll += max(-0.3, min(0.3, -(2.6 if run else 1.2) * dy_ * vn))
        hz_local = HZ[i] - c.z
        ch["hips"].location = (sway, 0, hz_local); ch["hips"].keyframe_insert("location", frame=f)
        ch["hips"].rotation_euler = (0, hroll, hyaw); ch["hips"].keyframe_insert("rotation_euler", frame=f)
        # 상체: 반대로 비틀고 진행 속도만큼 앞으로 숙임
        ch["torso"].rotation_euler = (math.radians(lean) * vn, -hroll * 0.6, -1.7 * hyaw)
        ch["torso"].keyframe_insert("rotation_euler", frame=f)
        ch["head"].rotation_euler = (-math.radians(lean) * 0.5 * vn + math.radians(1.5) * math.sin(2 * ph) * vn, 0, 0.7 * hyaw)
        ch["head"].keyframe_insert("rotation_euler", frame=f)
        # 다리 IK
        Mroot = Matrix.Translation(c) @ Euler((0, 0, yaw[i])).to_matrix().to_4x4()
        Mh = Matrix.Translation((sway, 0, hz_local)) @ Euler((0, hroll, hyaw)).to_matrix().to_4x4()
        for ft, sx in (("L", -1), ("R", 1)):
            p, h, u = FS[ft][i]
            tgt = p + Vector((0, 0, ANKLE_H + h))
            Ml = Mroot @ Mh @ Matrix.Translation((sx * 2 * P, 0, 0))
            d = Ml.inverted() @ tgt
            a, phi, kn = _leg_ik(d)
            ch["leg" + ft].rotation_euler = (a, phi, 0); ch["leg" + ft].keyframe_insert("rotation_euler", frame=f)
            ch["knee" + ft].rotation_euler = (kn, 0, 0); ch["knee" + ft].keyframe_insert("rotation_euler", frame=f)
            toe = math.radians(22 if run else 14) * math.sin(math.pi * u) if u is not None else 0.0
            ch["ankle" + ft].rotation_euler = (-(a + kn) + toe, -phi - hroll, -hyaw * 0.5)
            ch["ankle" + ft].keyframe_insert("rotation_euler", frame=f)
        # 팔: 반대쪽 다리와 함께, 2프레임 늦게
        j = max(0, i - lag)
        sw = fwd[j] * vnorm[j]
        aL = -arm * sw; aR = arm * sw                 # 오른발이 앞(+) → 왼팔이 앞(음수)
        out = 4 if not run else 10
        elb = (-75 if run else -10)
        ch["armL"].rotation_euler = (math.radians(aL), math.radians(out), 0); ch["armL"].keyframe_insert("rotation_euler", frame=f)
        ch["armR"].rotation_euler = (math.radians(aR), math.radians(-out), 0); ch["armR"].keyframe_insert("rotation_euler", frame=f)
        ch["elbowL"].rotation_euler = (math.radians(elb - 18 * max(0, -sw)), 0, 0); ch["elbowL"].keyframe_insert("rotation_euler", frame=f)
        ch["elbowR"].rotation_euler = (math.radians(elb - 18 * max(0, sw)), 0, 0); ch["elbowR"].keyframe_insert("rotation_euler", frame=f)
        if "hair" in ch:
            j2 = max(0, i - 3)
            ch["hair"].rotation_euler = (math.radians(vnorm[j2] * (4 + (22 if run else 9) + 3 * math.sin(2 * math.pi * S[j2] / st))), 0, 0)
            ch["hair"].keyframe_insert("rotation_euler", frame=f)
    if hold:                                          # 끝난 뒤 자세가 다음 키 쪽으로 흘러가지 않게
        for k in ("hips", "torso", "head", "armL", "armR", "elbowL", "elbowR", "legL", "legR", "kneeL", "kneeR", "ankleL", "ankleR"):
            ch[k].keyframe_insert("rotation_euler", frame=f1 + 1)
    return path


def run_to(ch, pts, f0, f1, step=0.62, **kw):
    return walk_to(ch, pts, f0, f1, step=step, run=True, **kw)
