import numpy as np
from PIL import Image

W_TOTAL, H_TOTAL = 800, 525
X0, Y0 = 144, 35
W_ACTIVE, H_ACTIVE = 640, 480

raw = np.fromfile("signal.bin", dtype=np.uint8)
raw = raw[:W_TOTAL*H_TOTAL*4]
img4 = raw.reshape(H_TOTAL, W_TOTAL, 4)

for c in range(4):
    gray = img4[:,:,c]
    frame = gray[Y0:Y0+H_ACTIVE, X0:X0+W_ACTIVE]
    Image.fromarray(frame, "L").save(f"gray_byte.png")

print("Wrote gray_byte.png")
