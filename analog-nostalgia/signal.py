# debug: arm64 vs x86_64
# import sys, platform
# print(sys.executable)
# print(platform.machine())


import numpy as np
from PIL import Image

W_TOTAL = 800
H_TOTAL = 525
SAMPLES_PER_PIXEL = 5

# VGA 640x480@60 timing
HSYNC = 96
HBACK = 48
VSYNC = 2
VBACK = 33

# adjust cropping here
X0 = HSYNC + HBACK - 130
Y0 = VSYNC + VBACK - 30
W_ACTIVE = 640
H_ACTIVE = 480

raw = np.fromfile("signal.bin", dtype=np.uint8)

# drop possible trailing padding
needed = H_TOTAL * W_TOTAL * SAMPLES_PER_PIXEL  # 2,100,000
raw = raw[:needed]

# reshape into lines
lines = raw.reshape(H_TOTAL, W_TOTAL * SAMPLES_PER_PIXEL)

# downsample 5 samples -> 1 pixel-clock (average)
pix = lines.reshape(H_TOTAL, W_TOTAL, SAMPLES_PER_PIXEL).mean(axis=2)

# crop active region
frame = pix[Y0:Y0+H_ACTIVE, X0:X0+W_ACTIVE]

# normalize to 0..255
frame = frame - frame.min()
frame = (255 * frame / (frame.max() if frame.max() else 1)).astype(np.uint8)

Image.fromarray(frame, mode="L").save("out7.png")
# print("Wrote out.png")
