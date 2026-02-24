import numpy as np
from PIL import Image

W_TOTAL, H_TOTAL = 800, 525
X0, Y0 = 144, 35
W_ACTIVE, H_ACTIVE = 640, 480

raw = np.fromfile("signal.bin", dtype=np.uint8)
raw = raw[:W_TOTAL * H_TOTAL * 4]   # 1,680,000 bytes

pix = raw.view("<u4").byteswap().reshape(H_TOTAL, W_TOTAL)

def save_rgb(r, g, b, name):
    r8 = r.astype(np.uint8)
    g8 = g.astype(np.uint8)
    b8 = b.astype(np.uint8)
    rgb = np.stack([r8, g8, b8], axis=2)
    frame = rgb[Y0:Y0+H_ACTIVE, X0:X0+W_ACTIVE]
    Image.fromarray(frame, "RGB").save(name)

# Try 8-bit-per-channel packed formats:
# 0xAARRGGBB, 0xAABBGGRR, 0xRRGGBBAA, etc (endianness matters)
save_rgb((pix >> 16) & 0xFF, (pix >> 8) & 0xFF, pix & 0xFF, "try_AARRGGBB.png")
save_rgb(pix & 0xFF, (pix >> 8) & 0xFF, (pix >> 16) & 0xFF, "try_AABBGGRR.png")
save_rgb((pix >> 24) & 0xFF, (pix >> 16) & 0xFF, (pix >> 8) & 0xFF, "try_RRGGBBAA.png")
save_rgb((pix >> 8) & 0xFF, (pix >> 16) & 0xFF, (pix >> 24) & 0xFF, "try_BBGGRRAA.png")

# Try 10-bit-per-channel packed formats:
# bits [29:20]=R, [19:10]=G, [9:0]=B (and permutations)
def save_10bit(rshift, gshift, bshift, name):
    r = (pix >> rshift) & 0x3FF
    g = (pix >> gshift) & 0x3FF
    b = (pix >> bshift) & 0x3FF
    r8 = (r * 255 // 1023).astype(np.uint8)
    g8 = (g * 255 // 1023).astype(np.uint8)
    b8 = (b * 255 // 1023).astype(np.uint8)
    rgb = np.stack([r8, g8, b8], axis=2)
    frame = rgb[Y0:Y0+H_ACTIVE, X0:X0+W_ACTIVE]
    Image.fromarray(frame, "RGB").save(name)

save_10bit(20, 10, 0,  "try_10bit_R20G10B0.png")
save_10bit(0, 10, 20,  "try_10bit_R0G10B20.png")
save_10bit(10, 20, 0,  "try_10bit_R10G20B0.png")
save_10bit(0, 20, 10,  "try_10bit_R0G20B10.png")

print("Wrote candidate images.")
