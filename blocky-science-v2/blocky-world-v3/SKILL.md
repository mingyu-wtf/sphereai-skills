---
name: blocky-world-v3
description: Build the blocky world for science videos with the V2 kit - block city with lit windows, pixel river, bridge, cars, block clouds, square sun, a floating-island stage for explainer shots, and colour that does not burn white. 블록 세계 v3.
---

# Blocky World v3

Uses `blocky-3d-kit`. The target look is **"a block game with a shader pack on"**: every shape and pattern is blocks and pixels; only light, reflection and air are realistic.

## 1. Outdoor world (copy `examples/walk_basic.py`)
```python
W.city_lights(L, [(1, 3.0)])                        # windows, lamps, car lights: day 0, dusk 2-3, night 4
W.city3(L, "CITY", seed=21)                         # grid city
W.land3(L, "LAND"); W.land3(L, "LAND2", y_min=399, z=0.12)   # wide land, no world edge
W.river3(L, "RIVER", (0, 210), (4000, 380))         # pixel water with reflections
W.bridge3(L, "BR", x, y0, y1)
W.traffic3(L, "TR", p0, p1, n=16, f0=F0, f1=F1)     # block cars with lights
W.riverside3(L, "BANK", (0, 396), width=600)        # where people stand
W.hills3(L, "HILL", (0, -520, 0), low_x=(-950, -450))
W.clouds3(L, "CLD", z=360, cover=0.26)              # flat block clouds, last
W.block_sun3(L, "BSUN", sun_dir, keys=[(1, True)])  # square sun
```
Put the square sun, the sun lamp and the sky on the same direction.

## 2. Sky and time of day
| Time | Sky | Sun lamp | City lights |
|---|---|---|---|
| Day | `X.sky3(L, [(f, 40, az, 0.22)])` | 3.2 | 0 |
| Dusk | `X.sky3(L, [(f, 2.5, 220, 0.27)])` + square sun | 1.2, warm orange | 2-3 |
| Night | flat deep navy `A.world_keys(L, [(f, (0.03, 0.045, 0.11), 1.0)])` | moon 0.8, pale blue | 4 |
| Explainer | flat sky blue (0.34, 0.50, 0.80) + island stage | 3.2 | - |

Never pure black for night or space.

## 3. Explainer stage: floating grass island (copy `examples/stage_compare.py`)
```python
ST.stage3(L, "STG", (0, 0, 0), size=(90, 90))      # grass with a 10 m grid, dirt and stone below, corner trees
W.clouds3(L, "CLD", center=(0, 0), z=-38, cover=0.42, cell=16, thick=6, extent=(900, 900))   # clouds below the island
```
- Use it instead of a grey floor in empty space: the grid gives a sense of size.
- Size comparison: things in a row, popping in one by one, origin at the bottom so they grow out of the ground.
- Show the island edge in the first shot (camera 20-30 m up), then move closer.

## 4. Colour
- Always `BF.look3(L)` right after `render_setup` (round glare, not streaks) and `BF.grade3(L)` (AgX colour, bright areas keep their colour). For flat sky + sun lamp scenes use `BF.grade3(L, exposure=0.5, saturation=1.45)`.
- If something glowing looks like a white blob, lower its emission.

## Output
Set code for each block of the script and stills for every shot.

---
만든이: sphereai.work (https://sphereai.work)
