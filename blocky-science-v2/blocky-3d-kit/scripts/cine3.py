# 카메라 연출 v3 (2026-11-05, 사용자 "카메라 워킹을 추가해서 더 업그레이드")
#  L.camera(타깃을 바라보는 카메라) 위에 얹는 도우미. 전부 키프레임만 쓴다(F커브 모디파이어 없음 → 버전이 바뀌어도 안 깨짐).
#    orbit_keys  : 대상 둘레를 도는 위치 키 목록(반지름·높이를 같이 바꾸면 나선)
#    crane_keys  : 천천히 출발·천천히 도착하는 이동 키 목록(크레인·푸시인)
#    dolly_zoom  : 다가가면서 화각을 넓혀(또는 반대로) 대상 크기는 그대로, 배경만 밀려나는 효과
#    handheld    : 손으로 든 카메라(느린 표류 + 잔떨림 두 겹) + 충격 킥(폭발·충격파 순간 크게 흔들리고 잦아듦)
#    lens_keys   : 화각 키(순간 줌)
#    rack_focus  : 초점 거리 키(앞 인물 → 먼 하늘)
import bpy, math, random
from mathutils import Vector


def _fcurves(idb):
    ad = idb.animation_data
    if not ad or not ad.action:
        return []
    try:
        return list(ad.action.fcurves)
    except AttributeError:
        return [fc for ly in ad.action.layers for st in ly.strips for cb in st.channelbags for fc in cb.fcurves]


def set_interp(idb, kind='LINEAR', path=None):
    for fc in _fcurves(idb):
        if path and fc.data_path != path:
            continue
        for kp in fc.keyframe_points:
            kp.interpolation = kind


def orbit_keys(center, r0, a0, a1, z0, f0, f1, n=8, r1=None, z1=None):
    """center 둘레를 a0→a1(도, +X 기준 반시계)로 도는 [(frame,(x,y,z))]. r1·z1을 주면 나선(다가가며 오르기)."""
    c = Vector(center); r1 = r0 if r1 is None else r1; z1 = z0 if z1 is None else z1
    ks = []
    for i in range(n + 1):
        t = i / n
        a = math.radians(a0 + (a1 - a0) * t); r = r0 + (r1 - r0) * t
        ks.append((int(round(f0 + (f1 - f0) * t)), (c.x + math.cos(a) * r, c.y + math.sin(a) * r, c.z + z0 + (z1 - z0) * t)))
    return ks


def crane_keys(p0, p1, f0, f1, n=6, ease=2.0):
    """p0→p1을 천천히 출발·천천히 도착하는 [(frame, pos)] (ease 클수록 가운데가 빠름)."""
    p0, p1 = Vector(p0), Vector(p1)
    ks = []
    for i in range(n + 1):
        t = i / n
        s = t ** ease / (t ** ease + (1 - t) ** ease)
        ks.append((int(round(f0 + (f1 - f0) * t)), tuple(p0.lerp(p1, s))))
    return ks


def lens_keys(cam, keys, interp='BEZIER'):
    """keys=[(frame, mm)]. 순간 줌은 두 키를 2~4프레임 간격으로."""
    for f, mm in keys:
        cam.data.lens = mm; cam.data.keyframe_insert("lens", frame=f)
    set_interp(cam.data, interp, "lens")


def dolly_zoom(cam, subject, p0, p1, f0, f1, lens0, step=2):
    """p0→p1로 움직이는 동안 subject(월드 좌표)가 화면에서 같은 크기로 보이게 화각을 맞춘다(lens = lens0 × 거리 ÷ 처음 거리).
    위치 키는 여기서 직선으로 넣는다. 다가가면 배경이 멀어지고(넓은 화각), 물러나면 배경이 밀려온다."""
    s = Vector(subject); p0, p1 = Vector(p0), Vector(p1)
    d0 = (p0 - s).length
    for f in range(f0, f1 + 1, step):
        t = (f - f0) / max(1, f1 - f0)
        p = p0.lerp(p1, t)
        cam.location = p; cam.keyframe_insert("location", frame=f)
        cam.data.lens = lens0 * (p - s).length / d0; cam.data.keyframe_insert("lens", frame=f)
    set_interp(cam, 'LINEAR', "location"); set_interp(cam.data, 'LINEAR', "lens")


def handheld(cam, f0, f1, dist, drift=0.35, jitter=0.10, kicks=(), seed=1):
    """손으로 든 느낌. 카메라가 바라보는 타깃을 흔든다(타깃의 delta_location 키 → 원래 타깃 키와 더해짐).
    dist = 카메라~타깃 거리(m, 대략). drift = 느린 표류(도), jitter = 잔떨림(도). 한 겹만 쓰면 둥둥 떠다니는 느낌이 난다.
    kicks = [(frame, 세기°, 지속 프레임)] — 그 프레임에 크게 흔들리고 지수적으로 잦아듦(폭발 섬광·충격파 도착)."""
    rng = random.Random(seed)
    tgt = cam.constraints[0].target
    ph = [rng.uniform(0, 6.283) for _ in range(12)]
    k = dist * math.tan(math.radians(1.0))

    def slow(f, i):
        return math.sin(f / 47.0 * 6.283 + ph[i]) * 0.6 + math.sin(f / 29.0 * 6.283 + ph[i + 3]) * 0.4

    def fast(f, i):
        return math.sin(f / 7.3 * 6.283 + ph[i + 6]) * 0.6 + math.sin(f / 4.1 * 6.283 + ph[i + 9]) * 0.4

    for f in range(f0, f1 + 1):
        amp = [drift * slow(f, i) + jitter * fast(f, i) for i in range(3)]
        for (fk, deg, dur) in kicks:
            if f >= fk:
                e = deg * math.exp(-3.0 * (f - fk) / max(1, dur))
                if e > 0.01:
                    for i in range(3):
                        amp[i] += e * rng.uniform(-1, 1)
        tgt.delta_location = (amp[0] * k, amp[1] * k * 0.3, amp[2] * k)
        tgt.keyframe_insert("delta_location", frame=f)
    for fb in (f0 - 1, f1 + 1):
        tgt.delta_location = (0, 0, 0); tgt.keyframe_insert("delta_location", frame=fb)
    set_interp(tgt, 'LINEAR', "delta_location")


def rack_focus(cam, keys, fstop=2.0):
    """keys=[(frame, 초점 거리 m)]. 타깃 초점 대신 거리 키를 쓴다(앞 인물 또렷 → 먼 혜성 또렷)."""
    d = cam.data.dof
    d.use_dof = True; d.focus_object = None; d.aperture_fstop = fstop
    for f, dist in keys:
        d.focus_distance = dist; d.keyframe_insert("focus_distance", frame=f)
