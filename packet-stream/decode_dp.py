from collections import Counter

# byte bit-reversal
REVBYTE = bytes(int(f"{i:08b}"[::-1], 2) for i in range(256))

PHASE = 5

def read_syms():
    data = open("signal.bin", "rb").read().translate(REVBYTE)
    bits = ''.join(f"{b:08b}" for b in data)
    bits = bits[PHASE:]
    bits = bits[: (len(bits)//10)*10]
    return [int(bits[i:i+10], 2) for i in range(0, len(bits), 10)]

syms = read_syms()
print("10b symbols:", len(syms))

# --- library decode ---
# Option A: package named 8b10b
try:
    from eightbtenb import decode_10b  # common API
    def dec(sym):
        # expected: returns (is_control, byte) or similar
        return decode_10b(sym)
except Exception:
    # Option B: package named py8b10b (API varies)
    from py8b10b import decode10b
    def dec(sym):
        return decode10b(sym)

decoded = bytearray()
kcount = 0
bad = 0

for s in syms:
    try:
        r = dec(s)
    except Exception:
        bad += 1
        continue

    # Normalize likely return forms:
    # - (byte, is_k)
    # - (is_k, byte)
    # - dict with fields
    if isinstance(r, dict):
        byte = r.get("data") if "data" in r else r.get("byte")
        is_k = r.get("is_k") or r.get("control") or False
    elif isinstance(r, tuple) and len(r) >= 2:
        a, b = r[0], r[1]
        # heuristics
        if isinstance(a, bool):
            is_k, byte = a, b
        elif isinstance(b, bool):
            byte, is_k = a, b
        else:
            # some libs return (byte, rd) etc.
            byte, is_k = a, False
    else:
        byte, is_k = int(r), False

    if byte is None:
        bad += 1
        continue

    decoded.append(byte & 0xFF)
    if is_k:
        kcount += 1

print("decoded bytes:", len(decoded), "bad:", bad, "K:", kcount)

open("decoded.bin", "wb").write(decoded)
print("wrote decoded.bin")
