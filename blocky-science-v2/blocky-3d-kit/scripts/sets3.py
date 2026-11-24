# 블록 3D 키트 세트 빌더 — 설명 컷 무대(하늘에 뜬 잔디 섬)와 빈 평지 둘레 채우기
#   import sets3 as ST
#   ST.stage3(L, "STG", (0, 0, 0), size=(90, 90))      # 윗면 z=0, 10m 눈금 잔디 + 흙·돌 4단 + 매달린 흙 블록 + 귀퉁이 나무
#   ST.dress_plain(L, "DP", (0, 0, 0), r_in=40, r_out=260, kind="grass"|"desert")   # r_in 밖에 나무·덤불·바위·먼 숲 띠·블록 구름
import bpy, math, random
import numpy as np
from mathutils import Vector
import mc_world3 as W

PXB = 8


def _tex(L, key, fn):
    L.ENV_TEX.setdefault(key, fn)
    return L.mat_for(key)


def _solid(L, key, col, var=0.05, emit=0.0):
    L.ENV_TEX.setdefault(key, lambda: L.noise(8, 8, col, var))
    return L.mat_for(key, emit=emit) if emit else L.mat_for(key)


def dress_plain(L, name, center, r_in=40.0, r_out=260.0, kind="grass", seed=5, clouds_z=150.0, frange=(1, 250), ridge=True, n=90):
    """세트 둘레(반지름 r_in 밖 ~ r_out)를 나무·바위·덤불·먼 숲 띠·낮은 언덕·블록 구름으로 채운다.
    kind = 'grass'(초록 들) / 'night'(같은 것, 밤) / 'sand'(사막: 바위·마른 덤불·모래 언덕). 세트 안쪽(r_in)은 건드리지 않는다."""
    rng = random.Random(seed)
    cx, cy, cz = center
    wood = _solid(L, "dp_wood", (0.32, 0.23, 0.14), 0.10)
    leaf = [_solid(L, "dp_leaf%d" % i, c, 0.12) for i, c in enumerate(((0.16, 0.42, 0.14), (0.22, 0.50, 0.18), (0.13, 0.34, 0.16)))]
    rock = _solid(L, "dp_rock", (0.46, 0.45, 0.44), 0.10)
    sandm = _solid(L, "dp_sand", (0.80, 0.70, 0.48), 0.06)
    dry = _solid(L, "dp_dry", (0.55, 0.50, 0.28), 0.10)
    b = W.MB()

    def tr(x, y, z):
        return (cx + x, cy + y, cz + z)

    for _ in range(n):
        a = rng.uniform(0, 6.283); r = rng.uniform(r_in, r_out)
        x, y = math.cos(a) * r, math.sin(a) * r
        t = rng.random()
        if kind == "sand":
            if t < 0.5:        # 바위
                s = rng.uniform(0.6, 2.6)
                b.box(tr(x, y, 0), tr(x + s, y + s * rng.uniform(0.6, 1.3), s * rng.uniform(0.4, 0.9)), rock, uvs=2)
            elif t < 0.8:      # 마른 덤불
                s = rng.uniform(0.5, 1.1)
                b.box(tr(x, y, 0), tr(x + s, y + s, s * 0.7), dry, uvs=2)
            else:              # 모래 언덕(계단)
                s = rng.uniform(8, 22)
                for k in range(3):
                    b.box(tr(x + k * s * 0.12, y + k * s * 0.1, 0), tr(x + s - k * s * 0.12, y + s * 0.7 - k * s * 0.1, 0.5 + k * 0.5), sandm, uvs=2)
        else:
            if t < 0.6:        # 나무(통나무 + 잎 블록)
                s = rng.uniform(0.8, 1.5); h = rng.uniform(3.0, 5.0) * s
                b.box(tr(x - 0.3 * s, y - 0.3 * s, 0), tr(x + 0.3 * s, y + 0.3 * s, h), wood, uvs=2)
                lm = rng.choice(leaf)
                for k, rr in enumerate((1.9, 1.9, 1.2)):
                    b.box(tr(x - rr * s, y - rr * s, h - 1.0 * s + k * 1.1 * s), tr(x + rr * s, y + rr * s, h + 0.1 * s + k * 1.1 * s), lm, uvs=2)
            elif t < 0.8:      # 덤불
                s = rng.uniform(0.7, 1.4)
                b.box(tr(x, y, 0), tr(x + s * 1.4, y + s, s * 0.8), rng.choice(leaf), uvs=2)
            else:              # 바위
                s = rng.uniform(0.6, 2.0)
                b.box(tr(x, y, 0), tr(x + s, y + s * 0.8, s * 0.6), rock, uvs=2)
    if ridge:                  # 먼 숲 띠(지평선) 또는 모래 언덕 띠
        m_far = sandm if kind == "sand" else leaf[2]
        for k in range(64):
            a = k / 64 * 6.283
            r = r_out * rng.uniform(1.15, 1.5)
            x, y = math.cos(a) * r, math.sin(a) * r
            w = r_out * 0.16; h = rng.uniform(5, 13) if kind != "sand" else rng.uniform(3, 9)
            b.box(tr(x - w / 2, y - w / 2, 0), tr(x + w / 2, y + w / 2, h), m_far, uvs=4)
            if rng.random() < 0.5:
                b.box(tr(x - w / 4, y - w / 4, h), tr(x + w / 4, y + w / 4, h + rng.uniform(2, 6)), m_far, uvs=4)
    ob = b.finish(L, f"{name}_dress")
    if clouds_z:
        W.clouds3(L, f"{name}_dcld", center=(cx, cy), z=cz + clouds_z, cell=16.0, thick=6.0, extent=(1000, 1000), cover=0.25, seed=seed,
                  drift=(1.5, 0.0), f0=frange[0], f1=frange[1])
    return ob


def _key(L, key, fn):
    L.ENV_TEX.setdefault(key, fn)
    return key


def _grid_grass(L, key="st3_grass", blocks=5, px=8):
    """잔디 윗면(한 장 = 10m): 2m 블록 이음줄(옅게) + 10m 굵은 눈금(진하게). 크기 비교 컷의 '자' 역할."""
    def fn():
        n = blocks * px
        rng = np.random.default_rng(3)
        base = np.array((0.40, 0.55, 0.30))      # 색 보정(채도 1.45) 뒤에 쨍하지 않게
        a = np.ones((n, n, 4))
        a[..., :3] = base * (1 + rng.uniform(-0.08, 0.08, (n, n)))[..., None]
        for b in range(blocks):
            a[b * px, :, :3] *= 0.90
            a[:, b * px, :3] *= 0.90
        a[0, :, :3] = base * 0.64
        a[:, 0, :3] = base * 0.64
        return a
    return _key(L, key, fn)


def _grass_side(L, key="st3_side"):
    """잔디 블록 옆면(한 장 = 2m): 위 3~5줄 초록(칸마다 길이가 다름) + 흙."""
    def fn():
        rng = np.random.default_rng(5)
        a = np.ones((16, 16, 4))
        dirt = np.array((0.47, 0.33, 0.21)); gr = np.array((0.40, 0.55, 0.30))
        a[..., :3] = dirt * (1 + rng.uniform(-0.12, 0.12, (16, 16)))[..., None]
        for c in range(16):
            d = 3 + int(rng.integers(0, 3))
            a[16 - d:, c, :3] = gr * (1 + rng.uniform(-0.08, 0.08))
        return a
    return _key(L, key, fn)


def stage3(L, name, center, size=(90.0, 90.0), seed=1, trees=True):
    """설명 컷 무대: 하늘에 뜬 마인크래프트 잔디 섬. 윗면 = 10m 눈금 잔디(바닥 높이 = center z), 옆 = 잔디 블록, 밑 = 흙·돌 계단식."""
    rng = random.Random(seed)
    cx, cy, cz = center; sx, sy = size
    g = _grid_grass(L); side = _grass_side(L)
    dirt = _key(L, "st3_dirt", lambda: L.noise(16, 16, (0.47, 0.33, 0.21), 0.12))
    stone = _key(L, "st3_stone", lambda: L.noise(16, 16, (0.48, 0.48, 0.50), 0.12))
    L.box(f"{name}_top", (sx, sy, 0.04), offset=(cx, cy, cz - 0.02), tex=g, tile=10.0)
    L.box(f"{name}_slab", (sx, sy, 2.0), offset=(cx, cy, cz - 1.06), tex=side, tile=2.0)
    z = cz - 2.06
    for k, (f, h, t) in enumerate(((0.92, 4.0, dirt), (0.74, 4.0, dirt), (0.52, 6.0, stone), (0.28, 6.0, stone))):
        ox, oy = rng.uniform(-2, 2) * 2, rng.uniform(-2, 2) * 2
        L.box(f"{name}_under{k}", (sx * f, sy * f, h), offset=(cx + ox, cy + oy, z - h / 2), tex=t, tile=2.0)
        z -= h
    for k in range(int((sx + sy) / 6)):     # 가장자리에 매달린 흙 블록
        e = rng.random()
        x = cx + (rng.uniform(-sx / 2, sx / 2) if e < 0.5 else rng.choice((-1, 1)) * (sx / 2 - 2))
        y = cy + (rng.choice((-1, 1)) * (sy / 2 - 2) if e < 0.5 else rng.uniform(-sy / 2, sy / 2))
        L.box(f"{name}_hang{k}", (4, 4, 2 * rng.randint(1, 3)), offset=(x, y, cz - 2.06 - rng.uniform(1, 4)), tex=dirt, tile=2.0)
    if trees:                                # 네 귀퉁이 블록 나무 + 가장자리 꽃(비교 물체와 겹치지 않게 가장자리 4m 안)
        wood = _key(L, "st3_wood", lambda: L.noise(8, 8, (0.36, 0.26, 0.15), 0.10))
        leaf = _key(L, "st3_leaf", lambda: L.noise(8, 8, (0.20, 0.46, 0.17), 0.14))
        for k, (qx, qy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
            for j in range(2):
                x = cx + qx * (sx / 2 - 3 - j * rng.uniform(4, 7)); y = cy + qy * (sy / 2 - 3 - (1 - j) * rng.uniform(3, 6))
                h = rng.uniform(4.0, 6.0)
                L.box(f"{name}_tw{k}{j}", (0.9, 0.9, h), offset=(x, y, cz + h / 2), tex=wood, tile=1.0)
                L.box(f"{name}_tl{k}{j}", (4.4, 4.4, 2.2), offset=(x, y, cz + h), tex=leaf, tile=1.0)
                L.box(f"{name}_tt{k}{j}", (2.4, 2.4, 1.4), offset=(x, y, cz + h + 1.7), tex=leaf, tile=1.0)
        fl = [_key(L, f"st3_fl{i}", (lambda c: (lambda: L.noise(2, 2, c, 0.05)))(c)) for i, c in
              enumerate(((0.95, 0.85, 0.20), (0.90, 0.30, 0.30), (0.95, 0.95, 0.95)))]
        for k in range(int((sx + sy) / 3)):
            e = rng.random()
            x = cx + (rng.uniform(-sx / 2 + 1, sx / 2 - 1) if e < 0.5 else rng.choice((-1, 1)) * rng.uniform(sx / 2 - 4, sx / 2 - 1))
            y = cy + (rng.choice((-1, 1)) * rng.uniform(sy / 2 - 4, sy / 2 - 1) if e < 0.5 else rng.uniform(-sy / 2 + 1, sy / 2 - 1))
            if abs(x - cx) < sx * 0.3 and abs(y - cy) < sy * 0.5 - 0.5 and y < cy:     # 카메라 쪽 가장자리 한가운데는 비움(점처럼 보임)
                continue
            L.box(f"{name}_fl{k}", (0.35, 0.35, 0.5), offset=(x, y, cz + 0.25), tex=rng.choice(fl), tile=1.0)
    return {"top_z": cz}

