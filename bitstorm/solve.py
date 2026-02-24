# solve.py
from typing import List, Tuple

MASK64 = 0xFFFFFFFFFFFFFFFF

# --- PRNG copied from challenge, but parameterized by initial state ---
def rng_next(state: List[int]) -> Tuple[int, List[int]]:
    s = state
    taps = [0, 1, 3, 7, 13, 22, 28, 31]

    new_val = 0
    for i in taps:
        val = s[i]
        mixed = val ^ ((val << 11) & MASK64) ^ (val >> 7)
        rot = (i * 3) % 64
        mixed = ((mixed << rot) | (mixed >> (64 - rot))) & MASK64
        new_val ^= mixed

    new_val ^= (s[-1] >> 13) ^ ((s[-1] << 5) & MASK64)
    new_val &= MASK64

    new_state = s[1:] + [new_val]

    out = 0
    for i in range(len(new_state)):
        if i % 2 == 0:
            out ^= new_state[i]
        else:
            v = new_state[i]
            out ^= ((v >> 2) | (v << 62)) & MASK64

    return out, new_state


def seedint_to_state(seed_int: int, state_size: int = 32) -> List[int]:
    # same as chal: big-endian chunks of 64
    st = []
    for i in range(state_size):
        shift = 64 * (state_size - 1 - i)
        st.append((seed_int >> shift) & MASK64)
    return st


def run_outputs_from_seed(seed_int: int, n_out: int = 60) -> List[int]:
    st = seedint_to_state(seed_int, 32)
    outs = []
    for _ in range(n_out):
        y, st = rng_next(st)
        outs.append(y)
    return outs


# --- GF(2) linear algebra using Python ints as bitsets ---

def build_matrix(nbits: int, outputs_count: int) -> List[int]:
    """
    Returns rows as Python ints (bitset of length nbits).
    Row r corresponds to one output bit.
    """
    rows = outputs_count * 64
    M = [0] * rows

    for bit in range(nbits):
        # basis seed: only this bit set (LSB-indexed)
        seed = 1 << bit
        outs = run_outputs_from_seed(seed, outputs_count)

        for t, y in enumerate(outs):
            base = t * 64
            # for each output bit set, flip corresponding equation coefficient
            # (since output = XOR of contributing basis bits)
            v = y
            b = 0
            while v:
                lsb = v & -v
                idx = (lsb.bit_length() - 1)
                M[base + idx] ^= (1 << bit)
                v ^= lsb
            # bits not set contribute nothing (leave 0)
    return M


def outputs_to_rhs_bits(outputs: List[int]) -> List[int]:
    b = []
    for y in outputs:
        for i in range(64):
            b.append((y >> i) & 1)
    return b


def gauss_elim_gf2(M: List[int], b: List[int], nbits: int) -> int:
    """
    Solves M x = b over GF(2) with row-reduction.
    Returns one solution x as int (LSB-indexed variable vector).
    """
    rows = len(M)
    where = [-1] * nbits
    r = 0

    for c in range(nbits):
        # find pivot row with bit c set
        pivot = None
        for rr in range(r, rows):
            if (M[rr] >> c) & 1:
                pivot = rr
                break
        if pivot is None:
            continue

        # swap into row r
        M[r], M[pivot] = M[pivot], M[r]
        b[r], b[pivot] = b[pivot], b[r]
        where[c] = r

        # eliminate column c from all other rows
        for rr in range(rows):
            if rr != r and ((M[rr] >> c) & 1):
                M[rr] ^= M[r]
                b[rr] ^= b[r]

        r += 1
        if r == rows:
            break

    # consistency check (optional): rows with 0 LHS but b=1 => no solution
    for rr in range(rows):
        if M[rr] == 0 and b[rr] == 1:
            raise ValueError("No solution (inconsistent equations)")

    # back-substitute (because matrix is reduced, this is straightforward)
    x = 0
    for c in range(nbits):
        rr = where[c]
        if rr != -1 and b[rr] == 1:
            x |= (1 << c)
    return x


def int_to_flag(seed_int: int) -> str:
    data = seed_int.to_bytes(256, "big")
    # challenge uses content = flag[6:-1], then .ljust(256, b'\0')
    # so strip trailing nulls:
    content = data.rstrip(b"\0").decode(errors="replace")
    return f"0xfun{{{content}}}"


def main():
    outputs = [
        11329270341625800450, 14683377949987450496, 11656037499566818711,
        14613944493490807838, 370532313626579329, 5006729399082841610,
        8072429272270319226, 3035866339305997883, 8753420467487863273,
        15606411394407853524, 5092825474622599933, 6483262783952989294,
        15380511644426948242, 13769333495965053018, 5620127072433438895,
        6809804883045878003, 1965081297255415258, 2519823891124920624,
        8990634037671460127, 3616252826436676639, 1455424466699459058,
        2836976688807481485, 11291016575083277338, 1603466311071935653,
        14629944881049387748, 3844587940332157570, 584252637567556589,
        10739738025866331065, 11650614949586184265, 1828791347803497022,
        9101164617572571488, 16034652114565169975, 13629596693592688618,
        17837636002790364294, 10619900844581377650, 15079130325914713229,
        5515526762186744782, 1211604266555550739, 11543408140362566331,
        18425294270126030355, 2629175584127737886, 6074824578506719227,
        6900475985494339491, 3263181255912585281, 12421969688110544830,
        10785482337735433711, 10286647144557317983, 15284226677373655118,
        9365502412429803694, 4248763523766770934, 13642948918986007294,
        3512868807899248227, 14810275182048896102, 1674341743043240380,
        28462467602860499, 1060872896572731679, 13208674648176077254,
        14702937631401007104, 5386638277617718038, 8935128661284199759
    ]

    nbits = 32 * 64
    k = len(outputs)

    print("[*] Building matrix (this can take a while)...")
    M = build_matrix(nbits, k)

    print("[*] Building RHS...")
    b = outputs_to_rhs_bits(outputs)

    print("[*] Solving GF(2) system...")
    seed_bits_int = gauss_elim_gf2(M, b, nbits)

    # seed_bits_int is LSB-indexed. But seed_int in the challenge is a 2048-bit integer
    # where bit positions are the same; we can use it directly.
    seed_int = seed_bits_int

    flag = int_to_flag(seed_int)
    print("[+] Recovered flag:")
    print(flag)


if __name__ == "__main__":
    main()
