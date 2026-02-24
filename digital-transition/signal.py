import numpy as np
from PIL import Image

W_TOTAL = 800
H_TOTAL = 525
X0 = 144 - 140
Y0 = 35 - 30
W_ACTIVE = 640
H_ACTIVE = 480

raw = np.fromfile("signal.bin", dtype=np.uint8)

needed = W_TOTAL * H_TOTAL * 4  # 1,680,000
raw = raw[:needed]              # drop the extra 216 bytes

img4 = raw.reshape(H_TOTAL, W_TOTAL, 4)

# Try common 32-bit pixel layouts:
candidates = {
    "RGBX": img4[:, :, [0, 1, 2]],
    "BGRX": img4[:, :, [2, 1, 0]],
    "XRGB": img4[:, :, [1, 2, 3]],
    "XBGR": img4[:, :, [3, 2, 1]],
    "ARGB": img4[:, :, [1, 2, 3]],  # same bytes, different naming depending on meaning of byte0
    "ABGR": img4[:, :, [3, 2, 1]],
}

for name, rgb in candidates.items():
    frame = rgb[Y0:Y0+H_ACTIVE, X0:X0+W_ACTIVE]
    Image.fromarray(frame.astype(np.uint8), mode="RGB").save(f"out_{name}.png")

print("Wrote:", ", ".join([f"out_{k}.png" for k in candidates.keys()]))
