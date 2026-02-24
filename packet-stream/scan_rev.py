from collections import Counter

def rev10(x):
    y = 0
    for i in range(10):
        y = (y << 1) | ((x >> i) & 1)
    return y

def read_symbols(path):
    data = open(path, "rb").read()
    bits = ''.join(f'{b:08b}' for b in data)
    return [int(bits[i:i+10], 2) for i in range(0, len(bits), 10)]

syms = read_symbols("signal.bin")
syms_r = [rev10(s) for s in syms]

c = Counter(syms_r)
print("top 20 reversed-bit symbols:")
for s, n in c.most_common(20):
    print(f"{s:04x} {s:010b} count={n}")
