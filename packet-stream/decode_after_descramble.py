from collections import Counter

MASK10 = 0x3FF

def bit_reverse_byte(b):
    return int(f"{b:08b}"[::-1], 2)

REV = bytes(bit_reverse_byte(i) for i in range(256))

def bytes_to_bits(data: bytes):
    # MSB-first
    out = []
    for b in data:
        for i in range(8):
            out.append((b >> (7 - i)) & 1)
    return out

def bits_to_syms(bits):
    bits = bits[: (len(bits)//10)*10]
    syms = []
    for i in range(0, len(bits), 10):
        v = 0
        for j in range(10):
            v = (v << 1) | bits[i+j]
        syms.append(v)
    return syms

# 8b/10b encode (data bytes only) to build a decode table
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
    return sym & MASK10, new_rd

# Build decode table: symbol -> byte (data symbols)
DEC = {}
for rd0 in (-8, 8):
    rd = rd0
    for b in range(256):
        sym, rd = enc_8b10b(b, rd)
        DEC[sym] = b

def descramble(bits, seed):
    # DP-like 16-bit LFSR; you may need to try a few seeds.
    lfsr = seed & 0xFFFF
    out = []
    for bit in bits:
        outbit = bit ^ (lfsr & 1)
        out.append(outbit)
        newbit = ((lfsr >> 15) ^ (lfsr >> 4) ^ (lfsr >> 3) ^ (lfsr >> 2)) & 1
        lfsr = ((lfsr << 1) & 0xFFFF) | newbit
    return out

PHASE = 5

data = open("signal.bin","rb").read().translate(REV)
bits = bytes_to_bits(data)
bits = bits[PHASE:]
bits = bits[: (len(bits)//10)*10]

# Try a few common seeds; pick the one with the most decodable symbols.
seeds = [0xFFFF, 0x0001, 0xACE1, 0x1D0F, 0x0000]
best = None

for seed in seeds:
    dbits = descramble(bits, seed)
    syms = bits_to_syms(dbits)
    dec_ok = sum(1 for s in syms if s in DEC)
    top = Counter(syms).most_common(3)
    key = (dec_ok, seed)
    if best is None or dec_ok > best[0]:
        best = (dec_ok, seed, top)
    print(f"seed {seed:04x}: decodable={dec_ok}/{len(syms)}  top={[(hex(s),n) for s,n in top]}")

dec_ok, seed, _ = best
print("BEST seed:", f"{seed:04x}", "decodable:", dec_ok)

# Decode with best seed
dbits = descramble(bits, seed)
syms = bits_to_syms(dbits)

out_bytes = bytearray()
unknown = 0
for s in syms:
    b = DEC.get(s)
    if b is None:
        unknown += 1
    else:
        out_bytes.append(b)

open("decoded_bytes.bin","wb").write(out_bytes)
print("wrote decoded_bytes.bin, bytes:", len(out_bytes), "unknown symbols:", unknown)
