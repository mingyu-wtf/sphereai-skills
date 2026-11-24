# 백그라운드 빌드: 컷 스크립트를 실행하고 그 씬만 남긴 .blend로 저장한다.
# blender -b --factory-startup -P bg_build.py -- <cut_script.py> <out.blend>
import bpy, sys

argv = sys.argv[sys.argv.index("--") + 1:]
script, out = argv[0], argv[1]
g = {"__file__": script, "__name__": "__main__"}
exec(compile(open(script, encoding="utf-8").read(), script, "exec"), g)
built = g["SC"]
for s in list(bpy.data.scenes):
    if s != built:
        bpy.data.scenes.remove(s)
bpy.context.preferences.filepaths.save_version = 0   # .blend1 자동 백업을 만들지 않음(스크립트로 언제든 재생성 가능)
bpy.ops.wm.save_as_mainfile(filepath=out)
print("SAVED", out, built.name, len(built.objects))
