import numpy as np
from PIL import Image

W, H = 640, 480
N = W*H*3

data = open("decoded_bytes.bin","rb").read()
print("decoded bytes:", len(data))

arr = np.frombuffer(data, dtype=np.uint8)

def score_window(x):
    # lower is “more image-like”: fewer big jumps between adjacent bytes
    d = np.abs(x[1:].astype(np.int16) - x[:-1].astype(np.int16))
    return d.mean()

best = None
best_i = None

# scan with step to be fast; refine later if needed
step = 5000
for i in range(0, len(arr) - N, step):
    s = score_window(arr[i:i+20000])  # sample first 20k bytes
    if best is None or s < best:
        best = s
        best_i = i

print("best coarse offset:", best_i, "score:", best)

# extract at best_i
frame = arr[best_i:best_i+N]
rgb = frame.reshape(H, W, 3)
Image.fromarray(rgb, "RGB").save("frame.png")
print("wrote frame.png")
