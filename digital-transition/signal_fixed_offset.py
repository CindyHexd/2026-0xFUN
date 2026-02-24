import numpy as np
from PIL import Image

W_TOTAL, H_TOTAL = 800, 525
W_ACTIVE, H_ACTIVE = 640, 480

raw = np.fromfile("signal.bin", dtype=np.uint8)[:W_TOTAL*H_TOTAL*4]
img4 = raw.reshape(H_TOTAL, W_TOTAL, 4)

# Use luma guess: try byte 0 first; change to 1/2/3 if needed
Y = img4[:,:,0].astype(np.int16)

def sharpness(patch):
    # simple edge energy
    return (np.abs(patch[:,1:]-patch[:,:-1]).sum() +
            np.abs(patch[1:,:]-patch[:-1,:]).sum())

best = None
best_xy = None

# search around the standard (144,35)
for dy in range(-40, 41, 2):
    for dx in range(-80, 81, 2):
        x0 = 144 + dx
        y0 = 35 + dy
        if x0 < 0 or y0 < 0 or x0+W_ACTIVE > W_TOTAL or y0+H_ACTIVE > H_TOTAL:
            continue
        patch = Y[y0:y0+H_ACTIVE, x0:x0+W_ACTIVE]
        sc = sharpness(patch)
        if best is None or sc > best:
            best = sc
            best_xy = (x0, y0)

print("Best crop:", best_xy, "score:", best)

x0, y0 = best_xy
frame = Y[y0:y0+H_ACTIVE, x0:x0+W_ACTIVE].astype(np.uint8)
Image.fromarray(frame, "L").save("best_crop_gray.png")
print("Wrote best_crop_gray.png")
