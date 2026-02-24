def read_symbols(path):
    data = open(path, "rb").read()
    bits = ''.join(f'{b:08b}' for b in data)
    # group into 10-bit symbols
    syms = [int(bits[i:i+10], 2) for i in range(0, len(bits), 10)]
    return syms

syms = read_symbols("signal.bin")
print("num symbols:", len(syms))

# count most common symbols
from collections import Counter
c = Counter(syms)
print("top 20 symbols:")
for s, n in c.most_common(20):
    print(f"{s:04x} {s:010b}  count={n}")
