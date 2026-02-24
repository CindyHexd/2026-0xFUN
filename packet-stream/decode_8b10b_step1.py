from collections import defaultdict

K28_5 = {0b0011111010, 0b1100000101}  # comma

# bit-reverse table per byte
REV = bytes(int(f"{i:08b}"[::-1], 2) for i in range(256))

def bits_from_bytes(data: bytes) -> str:
    return ''.join(f'{b:08b}' for b in data)

def rev10(x):
    y = 0
    for i in range(10):
        y = (y << 1) | ((x >> i) & 1)
    return y

# Build 8b/10b encode table (data bytes only) for both RD polarities
def enc_8b10b(byte, rd):
    d = [(byte >> i) & 1 for i in range(8)]
    n1 = sum(d)

    q = [0]*9
    q[0] = d[0]
    use_xnor = (n1 > 4) or (n1 == 4 and d[0] == 0)
    for i in range(1,8):
        q[i] = (1 ^ (q[i-1] ^ d[i])) if use_xnor else (q[i-1] ^ d[i])
    q[8] = 0 if use_xnor else 1

    ones_q = sum(q[:8])
    bal = ones_q - (8 - ones_q)

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
    for i in range(8):
        sym |= (data[i] & 1) << i
    sym |= (c8 & 1) << 8
    sym |= (c9 & 1) << 9
    return sym & 0x3FF, new_rd

# decode table for data symbols
DEC = {}
for rd0 in (-8, 8):
    rd = rd0
    for b in range(256):
        sym, rd = enc_8b10b(b, rd)
        DEC[sym] = b

data = open("signal.bin","rb").read().translate(REV)
bits = bits_from_bytes(data)

PHASE = 5
bits = bits[PHASE:]
bits = bits[: (len(bits)//10)*10]

syms = [int(bits[i:i+10], 2) for i in range(0, len(bits), 10)]

# Count decodeability and comma positions
decoded = []
comma_pos = []
unknown = 0
for i, s in enumerate(syms):
    if s in K28_5:
        comma_pos.append(i)
        decoded.append(None)  # control
    elif s in DEC:
        decoded.append(DEC[s])
    else:
        decoded.append(None)
        unknown += 1

print("symbols:", len(syms))
print("unknown symbols:", unknown)
print("comma hits:", len(comma_pos))
print("first 20 comma positions:", comma_pos[:20])

# Write decoded bytes (skip None)
out = bytes([b for b in decoded if b is not None])
open("decoded_bytes.bin","wb").write(out)
print("wrote decoded_bytes.bin (data bytes only)")
