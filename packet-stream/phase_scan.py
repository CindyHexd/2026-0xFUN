from collections import Counter

K28_5 = {0b0011111010, 0b1100000101}  # 0x0FA, 0x305

def bit_reverse_byte(b: int) -> int:
    return int(f"{b:08b}"[::-1], 2)

REV = bytes(bit_reverse_byte(i) for i in range(256))

def bits_from_bytes(data: bytes) -> str:
    return ''.join(f'{b:08b}' for b in data)

def score(ph_bits: str):
    # chunk into 10-bit symbols
    syms = [int(ph_bits[i:i+10], 2) for i in range(0, len(ph_bits), 10)]
    c = Counter(syms)

    # score 1: exact K28.5 hits
    k_hits = sum(c[s] for s in K28_5 if s in c)

    # score 2: comma-like 7-bit substring hits (weaker but useful)
    def comma_like(sym):
        b = f"{sym:010b}"
        return ("0011111" in b) or ("1100000" in b)

    cl_hits = sum(n for s, n in c.items() if comma_like(s))

    top = c.most_common(5)
    return k_hits, cl_hits, top

data = open("signal.bin", "rb").read()

for mode_name, d in [("as-is", data), ("byte-bit-reversed", data.translate(REV))]:
    bits = bits_from_bytes(d)
    print("\n==", mode_name, "==")
    best = None
    for phase in range(10):
        ph = bits[phase:]
        ph = ph[: (len(ph)//10)*10]  # truncate to multiple of 10
        k_hits, cl_hits, top = score(ph)
        # choose best by (k_hits, cl_hits)
        key = (k_hits, cl_hits)
        if best is None or key > best[0]:
            best = (key, phase, top)
        print(f"phase {phase}: K28.5={k_hits:6d} comma_like={cl_hits:7d} top={[(hex(s),n) for s,n in top]}")
    print("BEST:", best)
