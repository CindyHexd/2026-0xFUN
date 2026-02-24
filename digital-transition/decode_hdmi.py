import numpy as np
from PIL import Image

MASK10 = 0x3FF

# --- TMDS encode (reference) ---
def tmds_encode(byte, rd):
    # returns (symbol10, new_rd)
    d = [(byte >> i) & 1 for i in range(8)]
    n1 = sum(d)

    # step 1: build q_m[0..8]
    q = [0]*9
    q[0] = d[0]
    use_xnor = (n1 > 4) or (n1 == 4 and d[0] == 0)
    for i in range(1,8):
        if use_xnor:
            q[i] = 1 ^ (q[i-1] ^ d[i])  # XNOR
        else:
            q[i] = q[i-1] ^ d[i]        # XOR
    q[8] = 0 if use_xnor else 1

    # disparity of q[0..7]
    ones_q = sum(q[:8])
    bal = ones_q - (8 - ones_q)  # ones - zeros

    # step 2: form 10-bit output based on running disparity
    if rd == 0 or bal == 0:
        c9 = 1 - q[8]
        c8 = q[8]
        data = q[:8]
        if c9 == 0:
            data = [1-x for x in data]
            new_rd = rd - bal
        else:
            new_rd = rd + bal
    else:
        invert = (rd > 0 and bal > 0) or (rd < 0 and bal < 0)
        if invert:
            c9 = 0
            c8 = q[8]
            data = [1-x for x in q[:8]]
            new_rd = rd - bal
        else:
            c9 = 1
            c8 = q[8]
            data = q[:8]
            new_rd = rd + bal

    sym = 0
    # bits 0..7
    for i in range(8):
        sym |= (data[i] & 1) << i
    # bit8, bit9
    sym |= (c8 & 1) << 8
    sym |= (c9 & 1) << 9
    return sym & MASK10, new_rd


# Build decode table by enumerating all bytes for both rd signs
# (Decoding can ignore rd if we precompute all possible symbols.)
decode_tbl = {}
for start_rd in (-8, 8):
    rd = start_rd
    for b in range(256):
        sym, rd2 = tmds_encode(b, rd)
        decode_tbl[sym] = b
        rd = rd2

# TMDS control symbols (during blanking); map but we can ignore as pixels
CTRL = {
    0b1101010100,
    0b0010101011,
    0b0101010100,
    0b1010101011,
}

# --- Parameters (same 640x480 timing crop as VGA) ---
W_TOTAL, H_TOTAL = 800, 525
X0, Y0 = 144 - 140, 35 - 30
W_ACTIVE, H_ACTIVE = 640, 480

# --- Read packed stream ---
raw = np.fromfile("signal.bin", dtype="<u4")  # little-endian uint32
raw = raw[:W_TOTAL * H_TOTAL]                 # ignore trailing 216 bytes
pix = raw.reshape(H_TOTAL, W_TOTAL)

b_sym = (pix >> 0)  & MASK10
g_sym = (pix >> 10) & MASK10
r_sym = (pix >> 20) & MASK10

# Decode symbols to bytes (unknown/control -> 0)
def decode_chan(sym_arr):
    out = np.zeros(sym_arr.shape, dtype=np.uint8)
    flat = sym_arr.ravel()
    out_flat = out.ravel()
    for i, s in enumerate(flat):
        s = int(s)
        if s in decode_tbl:
            out_flat[i] = decode_tbl[s]
        else:
            # control/invalid symbol -> 0
            out_flat[i] = 0
    return out

R = decode_chan(r_sym)
G = decode_chan(g_sym)
B = decode_chan(b_sym)

rgb = np.stack([R, G, B], axis=2)

# Crop active video region
frame = rgb[Y0:Y0+H_ACTIVE, X0:X0+W_ACTIVE]
Image.fromarray(frame, "RGB").save("decoded.png")
print("Wrote decoded.png")
