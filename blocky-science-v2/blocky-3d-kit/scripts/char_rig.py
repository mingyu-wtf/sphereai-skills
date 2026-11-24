# 표정 있는 블록 캐릭터 리그 v1 (2026-10-24, 캐릭터는 전부 오리지널) — v2(char_rig2.py)가 이 파일을 불러 쓴다
#   import char_rig as CR
#   ch = CR.build(L, "HERO", CR.HERO)          # dict: root, hips, torso, head, armL, armR, legL, legR, faces{표정: 판}
#   CR.pose(ch, 120, armL=(-60, 0, 10), torso=(10, 0, 0), head=(0, 0, 15))   # 관절 회전(도), 키프레임
#   CR.face(ch, 120, "wink")                   # 표정 바꾸기(그 프레임부터, CONSTANT)
# 관절 축: 각 관절 빈 오브젝트의 로컬 축. 팔·다리 X회전 = 앞뒤로 흔들기(+면 뒤로), Y회전 = 옆으로 벌리기(왼팔 +, 오른팔 −), Z = 비틀기.
# 얼굴은 머리 앞면 바로 앞(1.5mm)에 표정마다 판을 하나씩 두고 보이기 키로 바꾼다(16×16 픽셀, 머리 8칸보다 촘촘).
import bpy, math
import numpy as np
from mathutils import Vector

P = 1 / 16

# ---------------- 캐릭터 설계(오리지널) ----------------
# 색은 0~1 RGB. bangs = 앞머리(위에서부터 16칸 행 문자열, h=머리카락, s=피부), hair = 머리 위·옆·뒤 색
HERO = dict(      # 여주인공 "보라" — 보라 크롭 재킷 + 흰 티 + 남색 반바지, 검은 단발 + 노란 핀, 청록 눈
    skin=(0.96, 0.80, 0.68), hair=(0.10, 0.08, 0.12), eye=(0.15, 0.75, 0.72),
    jacket=(0.52, 0.28, 0.80), jacket2=(1.0, 1.0, 1.0), shirt=(0.97, 0.97, 0.97),
    pants=(0.12, 0.15, 0.32), shorts=True, socks=(1.0, 1.0, 1.0), shoes=(0.98, 0.85, 0.20),
    arm_w=3, girl=True, long_hair=True, clip=(1.0, 0.85, 0.15), blush=True, midriff=True,
    bangs=["hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhh.hhhhhhh.hhhh", "hhsssssssssssshh"],
)
BOY = dict(       # 남자애 "도윤" — 초록 야구점퍼(흰 소매) + 회색 티 + 청바지, 갈색 머리, 갈색 눈
    skin=(0.93, 0.76, 0.62), hair=(0.36, 0.22, 0.12), eye=(0.35, 0.22, 0.10),
    jacket=(0.15, 0.50, 0.30), jacket2=(0.95, 0.95, 0.92), shirt=(0.62, 0.64, 0.68),
    pants=(0.25, 0.38, 0.62), shorts=False, socks=None, shoes=(0.92, 0.92, 0.92),
    arm_w=4, girl=False, long_hair=False, clip=None, blush=False, midriff=False,
    bangs=["hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hshhhshhhhshhhsh"],
)
BUDDY = dict(     # 친구 "곰이" — 하늘색 곰 귀 후드(얼굴만 열림) + 하늘색 바지, 통통, 까만 점눈
    skin=(0.96, 0.82, 0.70), hair=(0.55, 0.78, 0.95), eye=(0.08, 0.08, 0.10),
    jacket=(0.55, 0.78, 0.95), jacket2=(0.95, 0.95, 1.0), shirt=(0.55, 0.78, 0.95),
    pants=(0.42, 0.62, 0.85), shorts=False, socks=None, shoes=(0.95, 0.45, 0.35),
    arm_w=4, girl=False, long_hair=False, clip=None, blush=True, midriff=False, hood_ears=True, dot_eyes=True,
    bangs=["hhhhhhhhhhhhhhhh", "hhhhhhhhhhhhhhhh", "hhssssssssssssh.", "hsssssssssssssh.", "hsssssssssssssh."],
)
THIEF = dict(     # 날치기 — 검은 풀페이스 헬멧(바이저) + 회색 점퍼 + 검은 바지 (마인크래프트 좀비 아님)
    skin=(0.90, 0.74, 0.60), hair=(0.12, 0.12, 0.14), eye=(0.10, 0.10, 0.10),
    jacket=(0.40, 0.42, 0.46), jacket2=(0.95, 0.55, 0.15), shirt=(0.30, 0.31, 0.34),
    pants=(0.12, 0.12, 0.14), shorts=False, socks=None, shoes=(0.20, 0.20, 0.22),
    arm_w=4, girl=False, long_hair=False, clip=None, blush=False, midriff=False, helmet=True,
    bangs=["hhhhhhhhhhhhhhhh"] * 5,
)

EXPRESSIONS = ("normal", "blink", "happy", "wink", "smile", "shocked", "scared", "angry", "excited")


# ---------------- 픽셀 그리기 ----------------
def _img(h, w, col):
    a = np.ones((h, w, 4)); a[..., :3] = col
    return a


def _put(a, r_top, c, col):
    """위에서부터 행 번호(r_top)로 찍기 — 블렌더 이미지는 아래가 0행."""
    h, w = a.shape[:2]
    r = h - 1 - r_top
    if 0 <= r < h and 0 <= c < w:
        a[r, c, :3] = col


def _shade(col, k):
    return tuple(min(1.0, max(0.0, x * k)) for x in col)


def face_pixels(spec, expr):
    """16×16 얼굴 앞면(앞머리 포함)."""
    S = 16
    sk = spec["skin"]
    a = _img(S, S, sk)
    if spec.get("helmet"):
        return _helmet_face(spec, expr)
    hair = spec["hair"]
    for r, row in enumerate(spec["bangs"]):
        for c, ch in enumerate(row):
            if ch == "h":
                _put(a, r, c, hair)
            elif ch == ".":
                _put(a, r, c, _shade(hair, 0.7))
    if expr == "scared":                       # 이마가 파랗게 질림
        for r in range(5, 9):
            for c in range(1, 15):
                k = (8 - r) / 4
                _put(a, r, c, tuple(sk[i] * (1 - 0.55 * k) + (0.35, 0.55, 1.0)[i] * 0.55 * k for i in range(3)))
    K = (0.08, 0.06, 0.08); W = (1, 1, 1); I = spec["eye"]; L = (0.85, 0.97, 1.0)
    M = (0.70, 0.20, 0.25); dark = _shade(sk, 0.72)
    eyes = ((3, False), (10, True))            # (왼쪽 열, 오른눈이면 좌우 뒤집기)

    ID = _shade(I, 0.55)                       # 홍채 위쪽 진한 색

    def eye(c0, right, rows):
        for r, s in rows:
            s = s[::-1] if right else s
            for i, ch in enumerate(s):
                col = {"k": K, "w": W, "i": I, "I": ID, "l": L, "d": dark}.get(ch)
                if col:
                    _put(a, r, c0 + i, col)

    dot = spec.get("dot_eyes")
    OPEN = [(7, "kkk"), (8, "wIl"), (9, "wii")] if not dot else [(8, ".kk"), (9, ".kk")]
    if spec.get("girl") and not dot:           # 큰 눈: 속눈썹 + 진한 위 홍채 + 반짝이 + 아래 흰자
        OPEN = [(6, "kkk"), (7, "IIl"), (8, "iii"), (9, "wii")]
    for c0, right in eyes:
        if expr in ("normal",) or (expr == "wink" and not right):
            eye(c0, right, OPEN)
        elif expr == "blink" or (expr == "wink" and right):
            eye(c0, right, [(9, "kkk")] if not right or expr == "blink" else [(8, ".k."), (9, "k.k")])
        elif expr == "happy":
            eye(c0, right, [(8, ".k."), (9, "k.k")])
        elif expr == "smile":                  # 반쯤 감은 눈(여유)
            eye(c0, right, [(8, "kkk"), (9, "wii")] if not dot else [(9, "kkk")])
        elif expr in ("shocked", "scared"):
            eye(c0, right, [(6, "www"), (7, "wkw"), (8, "www"), (9, "www")])
        elif expr == "angry":
            eye(c0, right, [(6, "k.."), (7, ".kk"), (8, "kkk"), (9, "wii")] if not dot else [(7, "k.."), (8, ".kk"), (9, ".kk")])
        elif expr == "excited":
            eye(c0, right, [(7, "k.."), (8, ".k."), (9, "k..")])
    # 입
    mouths = {
        "normal": [(12, 7, "dd")], "blink": [(12, 7, "dd")], "wink": [(12, 6, "k..k"), (13, 6, ".kk.")],
        "happy": [(12, 6, "kkkk"), (13, 6, ".mm.")], "smile": [(12, 6, "k..k"), (13, 6, ".kk.")],
        "shocked": [(11, 7, "kk"), (12, 7, "mm"), (13, 7, "kk")], "scared": [(12, 6, "kkkk"), (13, 6, "k..k")],
        "angry": [(12, 6, "kkkk")], "excited": [(11, 6, "kkkk"), (12, 6, "kmmk"), (13, 6, ".kk.")],
    }
    for r, c0, s in mouths[expr]:
        for i, ch in enumerate(s):
            col = {"k": K, "m": M, "d": dark}.get(ch)
            if col:
                _put(a, r, c0 + i, col)
    if spec.get("blush") and expr in ("happy", "wink", "smile", "excited", "normal"):
        for c in (1, 2, 13, 14):
            _put(a, 11, c, (1.0, 0.62, 0.65))
    if expr == "scared":
        _put(a, 5, 13, (0.6, 0.85, 1.0)); _put(a, 6, 13, (0.6, 0.85, 1.0)); _put(a, 6, 12, (0.6, 0.85, 1.0))
    return a


def _helmet_face(spec, expr):
    S = 16
    shell = (0.13, 0.13, 0.15)
    a = _img(S, S, shell)
    if expr in ("shocked", "scared"):          # 바이저가 올라가고 겁먹은 눈이 보임
        for r in range(6, 15):
            for c in range(2, 14):
                _put(a, r, c, spec["skin"])
        for r in range(2, 6):
            for c in range(2, 14):
                _put(a, r, c, (0.25, 0.35, 0.45))
        for c0 in (4, 9):
            for r, s in ((7, "www"), (8, "wkw"), (9, "www")):
                for i, ch in enumerate(s):
                    _put(a, r, c0 + i, (1, 1, 1) if ch == "w" else (0.05, 0.05, 0.05))
        for r, s in ((12, "kkkk"), (13, "k..k")):
            for i, ch in enumerate(s):
                if ch == "k":
                    _put(a, r, 6 + i, (0.05, 0.05, 0.05))
        return a
    for r in range(5, 11):                     # 검은 바이저 + 비친 하늘빛 줄
        for c in range(2, 14):
            _put(a, r, c, (0.04, 0.05, 0.08))
    for c in range(3, 8):
        _put(a, 6, c, (0.35, 0.55, 0.75))
    _put(a, 7, 3, (0.25, 0.40, 0.55))
    if expr == "angry":
        for c in range(4, 12):
            _put(a, 9, c, (0.85, 0.15, 0.10))
    return a


def _body_tex(spec, tag):
    """부위별 면 텍스처 함수(fk, w, h) -> (key, arr)."""
    J, J2, SH, PA, SK = spec["jacket"], spec["jacket2"], spec["shirt"], spec["pants"], spec["skin"]

    def torso(fk, w, h):
        a = _img(h, w, J)
        if h < 12:                             # 위·아래 면
            return f"{tag}_torso_{fk}_{w}x{h}", a
        if fk == "ny":                         # 앞: 열린 재킷 사이로 티
            for r in range(h):
                for c in range(2, w - 2):
                    a[r, c, :3] = SH
            if spec.get("midriff"):
                for r in range(0, 2):
                    for c in range(2, w - 2):
                        a[r, c, :3] = SK
            for r in range(h):                 # 재킷 테두리(지퍼선)
                a[r, 1, :3] = J2; a[r, w - 2, :3] = J2
        elif fk in ("px", "nx"):
            for r in range(h):
                a[r, w // 2, :3] = J2 if spec.get("girl") else _shade(J, 0.85)
        elif fk == "py" and spec.get("hood_ears"):
            for r in range(h - 4, h):
                for c in range(1, w - 1):
                    a[r, c, :3] = _shade(J, 0.9)
        if fk == "pz":
            a[..., :3] = J
        return f"{tag}_torso_{fk}_{w}x{h}", a

    def arm(fk, w, h):
        a = _img(h, w, J)
        if h < 12:                             # 어깨 위·손 아래 면
            a[..., :3] = SK if fk == "nz" else J
            return f"{tag}_arm_{fk}_{w}x{h}", a
        for r in range(0, 3):                  # 손
            a[r, :, :3] = SK
        a[3, :, :3] = J2                       # 소매 끝 줄
        if J2 != J and not spec.get("hood_ears"):
            for r in range(4, h):              # 야구점퍼·트레이닝 소매 줄
                if fk in ("px", "nx"):
                    a[r, w // 2, :3] = J2
        if fk == "nz":
            a[..., :3] = SK
        return f"{tag}_arm_{fk}_{w}x{h}", a

    def leg(fk, w, h):
        a = _img(h, w, PA)
        if h < 12:                             # 위·아래 면(4×4)
            a[..., :3] = spec["shoes"] if fk == "nz" else PA
            return f"{tag}_leg_{fk}_{w}x{h}", a
        for r in range(0, 2):
            a[r, :, :3] = spec["shoes"]
        a[2, :, :3] = _shade(spec["shoes"], 0.8) if fk != "nz" else spec["shoes"]
        if spec.get("shorts"):
            for r in range(3, 8):
                a[r, :, :3] = SK
            if spec.get("socks"):
                a[3, :, :3] = spec["socks"]; a[4, :, :3] = spec["socks"]
        if fk == "nz":
            a[..., :3] = spec["shoes"]
        return f"{tag}_leg_{fk}_{w}x{h}", a

    def head(fk, w, h):
        hair = spec["hair"]
        a = _img(h, w, SK)
        if spec.get("helmet"):
            a[..., :3] = (0.13, 0.13, 0.15)
            if fk in ("px", "nx"):
                for c in range(w):
                    a[h // 2, c, :3] = spec["jacket2"]
            return f"{tag}_head_{fk}_{w}x{h}", a
        if fk == "pz" or fk == "py":
            a[..., :3] = hair
        elif fk in ("px", "nx"):
            top = 4 if not spec.get("long_hair") else h
            for r in range(h - top, h):
                a[r, :, :3] = hair
            if spec.get("hood_ears"):
                a[..., :3] = hair
        elif fk == "nz":
            a[..., :3] = SK
        return f"{tag}_head_{fk}_{w}x{h}", a

    return torso, arm, leg, head


def _part(fn, part):
    """12칸 팔·다리 텍스처 함수를 위(6~11행)/아래(0~5행) 토막용으로 자른다. 위·아래 면(4칸)은 그대로."""
    def f(fk, w, h):
        if fk in ("pz", "nz"):
            if (part == "upper" and fk == "nz") or (part == "lower" and fk == "pz"):
                key, a = fn("py", 4, 12)          # 토막 사이 이음면 = 이음 높이의 옆면 색 한 가지
                col = a[6 if part == "upper" else 5, 0, :3]
                return f"{key}_{part}_join", _img(h, w, tuple(col))
            key, a = fn(fk, w, h)
            return f"{key}_{part}", a
        key, a = fn(fk, w, 12)
        a = a[6:12] if part == "upper" else a[0:6]
        return f"{key}_{part}", a
    return f


# ---------------- 조립 ----------------
def _empty(L, name, loc=(0, 0, 0), parent=None):
    e = bpy.data.objects.new(name, None); L.coll.objects.link(e)
    e.empty_display_size = 0.15
    if parent:
        e.parent = parent
    e.location = loc
    return e


def build(L, name, spec, loc=(0, 0, 0), rot_z=0.0):
    """원점 = 발바닥 가운데, 정면 −Y. 반환 dict."""
    tag = f"cr_{name}"
    torso_t, arm_t, leg_t, head_t = _body_tex(spec, tag)
    root = _empty(L, name, loc)
    root.rotation_euler = (0, 0, math.radians(rot_z))
    hips = _empty(L, f"{name}_hips", (0, 0, 12 * P), root)
    ch = dict(root=root, hips=hips, spec=spec, faces={})
    # 다리 = 허벅지(엉덩이 축) + 정강이(무릎 축). 텍스처는 12칸 무늬를 위 6칸/아래 6칸으로 나눠 이어 보이게.
    # 무릎 X회전 +면 정강이가 뒤로 접힘. 이음매가 벌어지지 않게 각 토막을 0.5칸씩 겹침.
    for side, sx in (("L", -1), ("R", 1)):
        lp = _empty(L, f"{name}_leg{side}", (sx * 2 * P, 0, 0), hips)
        L.box(f"{name}_thigh{side}", (4 * P, 4 * P, 6.5 * P), offset=(0, 0, -3.25 * P), tex=_part(leg_t, "upper"), parent=lp)
        kp = _empty(L, f"{name}_knee{side}", (0, 0, -6 * P), lp)
        L.box(f"{name}_shin{side}", (3.96 * P, 3.96 * P, 6.5 * P), offset=(0, 0, -2.75 * P), tex=_part(leg_t, "lower"), parent=kp)
        ch["leg" + side] = lp; ch["knee" + side] = kp
    torso = _empty(L, f"{name}_torso", (0, 0, 0), hips)
    L.box(f"{name}_body", (8 * P, 4 * P, 12 * P), offset=(0, 0, 6 * P), tex=torso_t, parent=torso)
    ch["torso"] = torso
    aw = spec.get("arm_w", 4)
    for side, sx in (("L", -1), ("R", 1)):
        # 팔 = 위팔(어깨 축) + 아래팔(팔꿈치 축). 팔꿈치 X회전 −면 앞으로 굽힘.
        ap = _empty(L, f"{name}_arm{side}", (sx * (4 + aw / 2) * P, 0, 10 * P), torso)
        L.box(f"{name}_uparm{side}", (aw * P, 4 * P, 6.5 * P), offset=(0, 0, -1.25 * P), tex=_part(arm_t, "upper"), parent=ap)
        ep = _empty(L, f"{name}_elbow{side}", (0, 0, -4 * P), ap)
        L.box(f"{name}_forearm{side}", ((aw - 0.04) * P, 3.96 * P, 6.5 * P), offset=(0, 0, -3.0 * P), tex=_part(arm_t, "lower"), parent=ep)
        ch["arm" + side] = ap; ch["elbow" + side] = ep
    head = _empty(L, f"{name}_head", (0, 0, 12 * P), torso)
    hs = 9 if spec.get("helmet") else 8
    L.box(f"{name}_headbox", (hs * P, hs * P, hs * P), offset=(0, 0, hs / 2 * P), tex=head_t, parent=head)
    ch["head"] = head
    # 표정 판(머리 앞면 1.5mm 앞)
    for ex in EXPRESSIONS:
        key = f"{tag}_face_{ex}"
        arr = face_pixels(spec, ex)
        L.make_img(key, arr)
        f = L.box(f"{name}_face_{ex}", (hs * P, 0.001, hs * P), offset=(0, -hs / 2 * P - 0.0015, hs / 2 * P),
                  tex={"ny": key, "all": key}, parent=head)
        f.visible_shadow = False
        ch["faces"][ex] = f
    hair = spec["hair"]
    hk = f"{tag}_hair"
    L.make_img(hk, _img(4, 4, hair))
    if spec.get("long_hair"):                  # 뒤로 내려오는 긴 머리 + 옆머리(머리 위 끝을 축으로 흔들리게 빈 오브젝트에 매담)
        hp = _empty(L, f"{name}_hairpiv", (0, 3.6 * P, 7.5 * P), head)
        L.box(f"{name}_hair_back", (8.6 * P, 1.6 * P, 11 * P), offset=(0, 0.8 * P, -5.5 * P), tex=hk, parent=hp)
        ch["hair"] = hp
        for sx in (-1, 1):
            L.box(f"{name}_hair_side{sx}", (1.2 * P, 3 * P, 7 * P), offset=(sx * 4.5 * P, -2.2 * P, 3 * P), tex=hk, parent=head)
    else:
        L.box(f"{name}_hair_top", (8.4 * P, 8.4 * P, 1.2 * P), offset=(0, 0.2 * P, 8.3 * P), tex=hk, parent=head)
    if spec.get("clip"):
        ck = f"{tag}_clip"; L.make_img(ck, _img(2, 2, spec["clip"]))
        L.box(f"{name}_clip", (2.2 * P, 1 * P, 1.2 * P), offset=(3 * P, -4.5 * P, 6.2 * P), tex=ck, parent=head)
    if spec.get("hood_ears"):
        ek = f"{tag}_ear"; L.make_img(ek, _img(2, 2, _shade(hair, 0.9)))
        for sx in (-1, 1):
            L.box(f"{name}_ear{sx}", (2.4 * P, 1.4 * P, 2.4 * P), offset=(sx * 3 * P, 0, 9 * P), tex=ek, parent=head)
    face(ch, 1, "normal")
    return ch


# ---------------- 애니메이션 ----------------
def face(ch, f, expr):
    """f 프레임부터 표정 expr(CONSTANT)."""
    for ex, ob in ch["faces"].items():
        ob.hide_render = ob.hide_viewport = ex != expr
        ob.keyframe_insert("hide_render", frame=f); ob.keyframe_insert("hide_viewport", frame=f)
        ad = ob.animation_data
        if ad and ad.action:
            for fc in _fcurves(ad.action):
                for kp in fc.keyframe_points:
                    kp.interpolation = 'CONSTANT'


def _fcurves(act):
    try:
        return list(act.fcurves)
    except AttributeError:
        out = []
        for ly in getattr(act, "layers", []):
            for st in ly.strips:
                for cb in st.channelbags:
                    out.extend(cb.fcurves)
        return out


JOINTS = ("hips", "torso", "head", "armL", "armR", "legL", "legR", "kneeL", "kneeR", "elbowL", "elbowR")


def set_ease(ob, f, interp="BACK", easing="EASE_OUT", back=1.6, path=None):
    """ob의 f 프레임 키에서 시작하는 구간의 보간을 바꾼다(블렌더: 키의 보간 = 그 키에서 다음 키까지).
    쫀득한 손맛: 'EXPO'+EASE_OUT(확 튀어나가 감속), 'BACK'+EASE_OUT(살짝 지나쳤다 돌아옴), 'CONSTANT'(딱 끊김)."""
    if not (ob.animation_data and ob.animation_data.action):
        return
    for fc in _fcurves(ob.animation_data.action):
        if path and path not in fc.data_path:
            continue
        for kp in fc.keyframe_points:
            if abs(kp.co.x - f) < 0.5:
                kp.interpolation = interp
                if interp not in ("CONSTANT", "LINEAR", "BEZIER"):
                    kp.easing = easing
                if interp == "BACK":
                    kp.back = back


def pose(ch, f, interp=None, easing="EASE_OUT", back=1.6, **rot):
    """관절 회전(도)을 f에 키프레임. hips_z=높이 오프셋(m)도 가능. 안 준 관절은 키 안 넣음.
    interp를 주면 f에서 다음 키까지의 구간에 그 보간(쫀득: 'BACK'/'EXPO')."""
    for j, v in rot.items():
        if j == "hips_z":
            ch["hips"].location.z = 12 * P + v; ch["hips"].keyframe_insert("location", index=2, frame=f)
            continue
        ob = ch[j]
        ob.rotation_euler = tuple(math.radians(x) for x in v)
        ob.keyframe_insert("rotation_euler", frame=f)
    if interp:
        for j in rot:
            set_ease(ch["hips"] if j == "hips_z" else ch[j], f, interp, easing, back)


def snap(ch, f_from, f_to, ease="BACK", lag=2, **rot):
    """쫀득한 포즈 전환: f_from(현재 포즈 유지 키) → f_to(새 포즈)로 ease 보간.
    lag: 머리·팔은 몸통보다 lag프레임 늦게 도착(뒤따름). rot는 새 포즈."""
    order = {"hips": 0, "hips_z": 0, "torso": 0, "legL": 0, "legR": 0, "armL": lag, "armR": lag, "head": lag + 1}
    for j, v in rot.items():
        ob = ch["hips"] if j == "hips_z" else ch[j]
        d = order.get(j, 0)
        # 시작 키(지금 값 그대로)
        if j == "hips_z":
            ob.keyframe_insert("location", index=2, frame=f_from + d)
        else:
            ob.keyframe_insert("rotation_euler", frame=f_from + d)
        set_ease(ob, f_from + d, ease, "EASE_OUT")
        pose(ch, f_to + d, **{j: v})


def squash(ch, f, sz=0.8, interp="BACK"):
    """f에서 몸 전체를 위아래로 눌림(sz<1)/늘어남(sz>1). 부피 유지: 옆은 1/sqrt(sz)."""
    r = ch["root"]
    sx = 1 / math.sqrt(sz)
    r.scale = (sx, sx, sz); r.keyframe_insert("scale", frame=f)
    set_ease(r, f, interp, "EASE_OUT", path="scale")


def unsquash(ch, f, interp="BACK"):
    r = ch["root"]; r.scale = (1, 1, 1); r.keyframe_insert("scale", frame=f)
    set_ease(r, f, interp, "EASE_OUT", path="scale")


REST = dict(hips=(0, 0, 0), torso=(0, 0, 0), head=(0, 0, 0), armL=(0, 0, 0), armR=(0, 0, 0), legL=(0, 0, 0), legR=(0, 0, 0),
            kneeL=(0, 0, 0), kneeR=(0, 0, 0), elbowL=(0, 0, 0), elbowR=(0, 0, 0), hips_z=0.0)
# ⚠️ 키는 앞뒤로 보간된다 — 나중 컷에서 웅크린(hips_z) 키만 넣으면 그 전 컷들도 서서히 가라앉음.
#    포즈를 바꾸기 직전엔 REST/현재 포즈로 '버티는 키'를 꼭 넣을 것(REST에 hips_z 포함).


def planted_hips(legL, kneeL, legR, kneeR):
    """두 발이 땅에 닿게 하는 hips_z(사용자 지적: 공중에 떠 있음). 허벅지·정강이 6칸씩, 각도는 X회전(도).
    발이 엉덩이 아래로 내려가는 거리 = 0.375·cos(허벅지) + 0.375·cos(허벅지+무릎). 더 짧은 쪽(덜 내려간 발)에 맞춤."""
    seg = 6 * P
    def drop(a, k):
        return seg * math.cos(math.radians(a)) + seg * math.cos(math.radians(a + k))
    return min(drop(legL, kneeL), drop(legR, kneeR)) - 12 * P


def rest(ch, f):
    pose(ch, f, **REST)


def walk(ch, f0, f1, stride=0.5, period=16, arm=35, leg=35, bob=0.02):
    """제자리 걷기 사이클(이동은 root 키로 따로)."""
    for f in range(f0, f1 + 1, max(1, period // 8)):
        t = 2 * math.pi * (f - f0) / period
        s = math.sin(t)
        # 뒤로 간 다리가 앞으로 넘어올 때 무릎이 접힘, 팔꿈치는 살짝 굽힌 채 흔들림
        kL = 8 + 32 * max(0.0, math.sin(t + 1.2)); kR = 8 + 32 * max(0.0, math.sin(t + 1.2 + math.pi))
        pose(ch, f, armL=(arm * s, 0, 0), armR=(-arm * s, 0, 0), legL=(-leg * s, 0, 0), legR=(leg * s, 0, 0),
             kneeL=(kL, 0, 0), kneeR=(kR, 0, 0), elbowL=(-12 - 8 * max(0, -s), 0, 0), elbowR=(-12 - 8 * max(0, s), 0, 0),
             hips_z=bob * abs(math.cos(t)) - 0.01)


def run(ch, f0, f1, period=10, arm=70, leg=60, lean=18):
    for f in range(f0, f1 + 1, max(1, period // 8)):
        t = 2 * math.pi * (f - f0) / period
        s = math.sin(t)
        kL = 20 + 85 * max(0.0, math.sin(t + 1.0)); kR = 20 + 85 * max(0.0, math.sin(t + 1.0 + math.pi))
        pose(ch, f, torso=(lean, 0, 0), armL=(arm * s, 0, 10), armR=(-arm * s, 0, -10),
             legL=(-leg * s, 0, 0), legR=(leg * s, 0, 0), kneeL=(kL, 0, 0), kneeR=(kR, 0, 0),
             elbowL=(-80, 0, 0), elbowR=(-80, 0, 0), hips_z=0.06 * abs(math.cos(t)) - 0.04)


def move(ob, keys):
    """keys: [(frame, (x,y,z))] — root 위치."""
    for f, p in keys:
        ob.location = p; ob.keyframe_insert("location", frame=f)


def turn(ob, keys):
    for f, z in keys:
        ob.rotation_euler = (0, 0, math.radians(z)); ob.keyframe_insert("rotation_euler", index=2, frame=f)
