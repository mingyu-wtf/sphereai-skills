---
name: impact-fx-recipes
description: Five basic blocky impact effects in Blender Python: shockwave, flash, dust burst, speed lines and camera shake, built from simple boxes, and when to use each. 기본 임팩트 이펙트 5종.
---

# Impact FX Recipes

All effects are made from simple boxes with emission, keyed in Blender. No particle simulation and no plugins, so every frame is predictable and renders the same every time. Claude writes one function per effect and reuses them.

## Recipes
| Effect | Built from | Animation | Use it when |
|---|---|---|---|
| **Shockwave** | a flat ring of small emissive boxes on the ground | grows outward and fades | landing, punch contact |
| **Flash** | a white emissive card in front of the camera | on for a moment, then gone | the contact frame of a hit |
| **Dust burst** | small grey-brown cubes | fly out and up, shrink to 0 | landing, skid, fall |
| **Speed lines** | thin long boxes around the camera axis | slide past the camera | dash, flying |
| **Camera shake** | noise on camera location | short and strong for hits | every impact |

## Basic rules
1. Start the flash, shockwave and shake on the same frame as the contact.
2. Effects appear fast and fade slowly.
3. Keep dust away from the hero's face.
4. Key an effect's scale to 0 on the frame before it starts, so it does not show early.

## Output
A small effects module with one function per recipe (position, start frame, size, colour) and a note of which effect is used on which shot.

---
만든이: sphereai.work (https://sphereai.work)
