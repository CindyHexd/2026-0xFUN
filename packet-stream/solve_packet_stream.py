import numpy as np
from PIL import Image

# ----------------------------
# 8b/10b tables (IBM)
# Source: standard Widmer/Franaszek tables (same as Wikipedia / LibSV docs)
# ----------------------------

# 5b/6b: x -> (RD-, RD+) as 6-bit strings abcdei (MSB->LSB)
TAB_5B6B = {
  0: ("100111","011000"),  1: ("011101","100010"),  2: ("101101","010010"),  3: ("110001","110001"),
  4: ("110101","001010"),  5: ("101001","101001"),  6: ("011001","011001"),  7: ("111000","000111"),
  8: ("111001","000110"),  9: ("100101","100101"), 10: ("010101","010101"), 11: ("110100","001011"),
 12: ("001101","001101"), 13: ("101100","010011"), 14: ("011100","011100"), 15: ("010111","101000"),
 16: ("011011","100100"), 17: ("100011","100011"), 18: ("010011","010011"), 19: ("110010","001101"),
 20: ("001011","001011"), 21: ("101010","010101"), 22: ("011010","011010"),
 23: ("111010","000101"), 24: ("110011","001100"), 25: ("100110","100110"), 26: ("010110","010110"),
 27: ("110110","001001"), 28: ("001110","001110"), 29: ("101110","010001"), 30: ("011110","100001"),
 31: ("101011","010100"),
}

# Special 5b/6b for K.28.x (x=28): RD- = 001111, RD+ = 110000
K28_6B = ("001111","110000")

# 3b/4b for data: y -> (RD-, RD+) primary (fghj)
TAB_3B4B_P = {
 0: ("1011","0100"),
 1: ("1001","1001"),
 2: ("0101","0101"),
 3: ("1100","0011"),
 4: ("1101","0010"),
 5: ("1010","1010"),
 6: ("0110","0110"),
 # y=7 has primary + alternate; handled separately
}

# 3b/4b alternate for D.x.7 (only used for some x depending on RD, but we can accept both)
D7_ALT = ("0111","1000")  # (RD-, RD+)

# 3b/4b primary for D.x.7:
D7_PRI = ("1110","0001")  # (RD-, RD+)

# 3b/4b for K.x.y when y=7 uses 1000/0111 (same as D7_ALT for some x’s)
K7 = ("1000","0111")  # (RD-, RD+)

# K-symbol set allowed in 8b/10b (12 controls)
K_SET = {(28,0),(28,1),(28,2),(28,3),(28,4),(28,5),(28,6),(28,7),(23,7),(27,7),(29,7),(30,7)}

def bits_to_int(msb_first_bits: str) -> int:
    return int(msb_first_bits, 2)

def disparity(bits: str) -> int:
    ones = bits.count("1")
    zeros = len(bits) - ones
    return ones - zeros

def build_decode_maps():
    # Two maps: depending on current RD sign (- or +), map 10b -> (byte, is_control, next_rd_sign)
    # We’ll compute next RD by adding disparity of the 10-bit code.
    maps = { -1: {}, +1: {} }

    def add_symbol(rd_sign, tenbits, byte_val, is_k):
        sym = bits_to_int(tenbits)
        rd_next = rd_sign
        d = disparity(tenbits)
        # update running disparity (track as sign only)
        rd_next = +1 if ( (1 if rd_sign>0 else -1) + d ) > 0 else -1
        maps[rd_sign][sym] = (byte_val, is_k, rd_next)

    for rd_sign in (-1, +1):
        # DATA symbols D.x.y
        for x in range(32):
            six = TAB_5B6B[x][0] if rd_sign==-1 else TAB_5B6B[x][1]
            for y in range(8):
                if y != 7:
                    four = TAB_3B4B_P[y][0] if rd_sign==-1 else TAB_3B4B_P[y][1]
                    ten = six + four
                    byte = (y<<5) | x
                    add_symbol(rd_sign, ten, byte, False)
                else:
                    # accept both primary and alternate for D.x.7
                    four_p = D7_PRI[0] if rd_sign==-1 else D7_PRI[1]
                    four_a = D7_ALT[0] if rd_sign==-1 else D7_ALT[1]
                    byte = (7<<5) | x
                    add_symbol(rd_sign, six + four_p, byte, False)
                    add_symbol(rd_sign, six + four_a, byte, False)

        # CONTROL symbols K.x.y (12 allowed)
        for (x,y) in K_SET:
            # 6b part
            if x == 28:
                six = K28_6B[0] if rd_sign==-1 else K28_6B[1]
            else:
                six = TAB_5B6B[x][0] if rd_sign==-1 else TAB_5B6B[x][1]

            # 4b part
            if y != 7:
                four = TAB_3B4B_P[y][0] if rd_sign==-1 else TAB_3B4B_P[y][1]
            else:
                four = K7[0] if rd_sign==-1 else K7[1]

            ten = six + four
            byte = (y<<5) | x  # conventional packed form
            add_symbol(rd_sign, ten, byte, True)

    return maps[-1], maps[+1]

DEC_NEG, DEC_POS = build_decode_maps()

# ----------------------------
# Read + align bitstream
# ----------------------------

# Your proven best alignment:
PHASE = 5
REVBYTE = bytes(int(f"{i:08b}"[::-1], 2) for i in range(256))

data = open("signal.bin","rb").read().translate(REVBYTE)

# MSB-first bits
bitstr = ''.join(f"{b:08b}" for b in data)
bitstr = bitstr[PHASE:]
bitstr = bitstr[: (len(bitstr)//10)*10]

syms = [int(bitstr[i:i+10], 2) for i in range(0, len(bitstr), 10)]
print("10-bit symbols:", len(syms))

# ----------------------------
# 8b/10b decode
# ----------------------------
decoded = bytearray()
rd = -1  # start RD- (common); if wrong, we’ll still mostly decode
unknown = 0
kcount = 0

for s in syms:
    m = DEC_NEG if rd == -1 else DEC_POS
    tup = m.get(s)
    if tup is None:
        unknown += 1
        continue
    b, is_k, rd_next = tup
    if is_k:
        kcount += 1
    decoded.append(b)
    rd = rd_next

print("decoded bytes:", len(decoded), "unknown symbols:", unknown, "K symbols decoded:", kcount)

# We expect ~1,680,000 bytes for a 800x525x4 framebuffer
# Drop any trailing padding beyond that.
W_TOTAL, H_TOTAL = 800, 525
needed = W_TOTAL * H_TOTAL * 4
if len(decoded) < needed:
    print("WARNING: decoded too short for 800x525x4. Likely RD init or tables mismatch.")
decoded = decoded[:needed]

raw = np.frombuffer(decoded, dtype=np.uint8).reshape(H_TOTAL, W_TOTAL, 4)

# ----------------------------
# Try common 32bpp byte layouts + crop active 640x480
# ----------------------------
X0, Y0 = 144, 35
W_ACTIVE, H_ACTIVE = 640, 480

candidates = {
    "RGBX": raw[:, :, [0,1,2]],
    "BGRX": raw[:, :, [2,1,0]],
    "XRGB": raw[:, :, [1,2,3]],
    "XBGR": raw[:, :, [3,2,1]],
}

for name, rgb in candidates.items():
    frame = rgb[Y0:Y0+H_ACTIVE, X0:X0+W_ACTIVE]
    Image.fromarray(frame, "RGB").save(f"out_{name}.png")

print("Wrote:", ", ".join(f"out_{k}.png" for k in candidates))
