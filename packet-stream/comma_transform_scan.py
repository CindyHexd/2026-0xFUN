from collections import Counter

# K28.5 comma in 10-bit (MSB-first integer)
COMMAS = {0x0FA, 0x305}

def rev10(x):
    y = 0
    for i in range(10):
        y = (y << 1) | ((x >> i) & 1)
    return y

def inv10(x):
    return x ^ 0x3FF

def bits_from_bytes_msb(data: bytes) -> str:
    return ''.join(f"{b:08b}" for b in data)

REVBYTE = bytes(int(f"{i:08b}"[::-1], 2) for i in range(256))

def read_syms(filename, byte_bitrev: bool, phase: int):
    data = open(filename, "rb").read()
    if byte_bitrev:
        data = data.translate(REVBYTE)
    bits = bits_from_bytes_msb(data)
    bits = bits[phase:]
    bits = bits[: (len(bits)//10)*10]
    syms = [int(bits[i:i+10], 2) for i in range(0, len(bits), 10)]
    return syms

def count_commas(syms):
    f_id  = lambda x: x
    f_rev = rev10
    f_inv = inv10
    f_riv = lambda x: inv10(rev10(x))

    transforms = {
        "id":  f_id,
        "rev10": f_rev,
        "inv10": f_inv,
        "rev10+inv10": f_riv,
    }

    for name, f in transforms.items():
        hits = 0
        for s in syms:
            if f(s) in COMMAS:
                hits += 1
        top = Counter(f(s) for s in syms).most_common(5)
        print(f"{name:10s} comma_hits={hits:6d} top={[(hex(a),n) for a,n in top]}")

# Use your known best alignment settings first
PHASE = 5

for byte_rev in (False, True):
    print("\n== byte_bit_reversed =", byte_rev, "==")
    syms = read_syms("signal.bin", byte_rev, PHASE)
    print("num syms:", len(syms))
    count_commas(syms)
