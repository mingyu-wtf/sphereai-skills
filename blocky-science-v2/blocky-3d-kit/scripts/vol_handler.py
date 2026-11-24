# 렌더 때 -P로 같이 넘긴다: blender -b x.blend -P scripts/vol_handler.py -o ... -a
# 장면에 vol_shots(sci_fx3.vol_shots)가 없으면 아무것도 안 한다 → 옛 컷에 넘겨도 안전
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sci_fx3
sci_fx3.install_vol_handler()
print("VOL_HANDLER ok")
