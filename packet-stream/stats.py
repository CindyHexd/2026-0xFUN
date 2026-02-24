import numpy as np

data = np.fromfile("signal.bin", dtype=np.uint8)

print("unique bytes:", len(set(data.tolist())))
print("mean:", data.mean())
print("std:", data.std())
