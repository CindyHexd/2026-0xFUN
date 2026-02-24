def bit_reverse_byte(b):
    return int(f"{b:08b}"[::-1], 2)

REV = bytes(bit_reverse_byte(i) for i in range(256))

data = open("signal.bin","rb").read().translate(REV)

# Convert to bit list
bits = []
for b in data:
    for i in range(8):
        bits.append((b >> (7-i)) & 1)

# Apply phase shift (5)
bits = bits[5:]

# Truncate to multiple of 10
bits = bits[: (len(bits)//10)*10]

# --- DP descrambler ---
# 16-bit LFSR, seed = all ones (typical DP start)
lfsr = 0xFFFF

descrambled = []
for bit in bits:
    # output bit is XOR of input and LFSR[0]
    out = bit ^ (lfsr & 1)
    descrambled.append(out)

    # update LFSR
    newbit = ((lfsr >> 15) ^ (lfsr >> 4) ^ (lfsr >> 3) ^ (lfsr >> 2)) & 1
    lfsr = ((lfsr << 1) & 0xFFFF) | newbit

# Now group into 10-bit symbols
syms = []
for i in range(0, len(descrambled), 10):
    val = 0
    for j in range(10):
        val = (val << 1) | descrambled[i+j]
    syms.append(val)

print("symbols after descramble:", len(syms))
