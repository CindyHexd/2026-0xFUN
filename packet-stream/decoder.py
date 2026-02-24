import numpy as np
from PIL import Image

W_TOTAL, H_TOTAL = 800, 525
SAMPLES_PER_PIXEL = 5

# standard 640x480@60 active offsets
X0, Y0 = 144, 35
W_ACTIVE, H_ACTIVE = 640, 480

raw = np.fromfile("signal.bin", dtype=np.uint8)

needed = W_TOTAL * H_TOTAL * SAMPLES_PER_PIXEL  # 2,100,000
raw = raw[:needed]  # drop trailing 220 bytes

# (525, 4000)
lines = raw.reshape(H_TOTAL, W_TOTAL * SAMPLES_PER_PIXEL)

# -> (525, 800) by averaging 5 samples per pixel-clock
pix = lines.reshape(H_TOTAL, W_TOTAL, SAMPLES_PER_PIXEL).mean(axis=2)

# crop active video
frame = pix[Y0:Y0+H_ACTIVE, X0:X0+W_ACTIVE]

# normalize to 0..255
# frame = frame - frame.min()
frame = 255 - frame
frame = (255 * frame / (frame.max() if frame.max() else 1)).astype(np.uint8)

Image.fromarray(frame, "L").save("out.png")
print("Wrote out.png")
