from collections import Counter

MASK10 = 0x3FF

# bit-reverse table per byte
REV = bytes(int(f"{i:08b}"[::-1], 2) for i in range(256))

def bytes_to_bits(data: bytes):
    out = []
    for b in data:
        for i in range(8):
            out.append((b >> (7-i)) & 1)
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

def rev10(x):
    y = 0
    for i in range(10):
        y = (y << 1) | ((x >> i) & 1)
    return y

# DP-like descrambler (current guess)
def descramble(bits, seed):
    lfsr = seed & 0xFFFF
    out = []
    for bit in bits:
        outbit = bit ^ (lfsr & 1)
        out.append(outbit)
        newbit = ((lfsr >> 15) ^ (lfsr >> 4) ^ (lfsr >> 3) ^ (lfsr >> 2)) & 1
        lfsr = ((lfsr << 1) & 0xFFFF) | newbit
    return out

# --- Build VALID 8b/10b symbol sets by brute force using a known-good reference table ---
# Instead of implementing full K/D mapping ourselves, we’ll accept BOTH polarities
# by using published 8b/10b tables embedded as codewords is hard.
# Practical trick: treat "valid symbol" as those with 5/6-ones property? Not enough.
# Better trick here: you already have lots of repeats; we'll just score how many symbols
# become *not dominated by 0101...* after each transform and also count comma-like patterns.

def comma_like(sym):
    b = f"{sym:010b}"
    return ("0011111" in b) or ("1100000" in b)

PHASE = 5
data = open("signal.bin","rb").read().translate(REV)
bits = bytes_to_bits(data)
bits = bits[PHASE:]
bits = bits[: (len(bits)//10)*10]

seeds = [0xFFFF, 0x0001, 0xACE1, 0x1D0F, 0x0000]

for seed in seeds:
    db = descramble(bits, seed)
    syms = bits_to_syms(db)

    # score both symbol-bit orders
    for name, arr in [("normal10", syms), ("rev10", [rev10(s) for s in syms])]:
        c = Counter(arr)
        top = c.most_common(5)
        cl = sum(n for s,n in c.items() if comma_like(s))
        print(f"seed {seed:04x} {name}: comma_like={cl} top={[(hex(s),n) for s,n in top]}")
