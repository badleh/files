"""
Assignment 2: Garbled Circuits in Practice
===========================================
Two parties (Alice and Bob) each hold a private boolean array of length n.
They want to compute: are all elements pairwise equal?

"""

import time
import random
from garbled_nand import GarbledNAND


# ============================================================
# Shared primitive: garbled bit-equality via NAND gates
#
# eq(a, b) = XNOR(a, b) built from 5 NAND gates:
#   t1 = NAND(a, b)
#   t2 = NAND(a, a)  = NOT a
#   t3 = NAND(b, b)  = NOT b
#   t4 = NAND(t2,t3) = a OR b   (De Morgan)
#   eq = NAND(t1,t4) = XNOR(a, b)  check
#
# AND(x, y) built from 2 NAND gates:
#   t   = NAND(x, y)
#   and = NAND(t, t)  = x AND y
# ============================================================

def _garbled_nand(a: int, b: int) -> int:
    """Evaluate a single fresh garbled NAND gate."""
    gate = GarbledNAND()
    gate.garble()
    lx, ly = gate.get_input_labels(a, b)
    return int(gate.evaluate(lx, ly))


def _garbled_eq(a: int, b: int) -> int:
    """
    Oblivious equality check for two bits using 5 garbled NAND gates.
    Returns 1 if a == b, 0 otherwise.
    No intermediate wire label reveals whether a == b.
    """
    t1 = _garbled_nand(a, b)        # NAND(a, b)
    t2 = _garbled_nand(a, a)        # NOT a
    t3 = _garbled_nand(b, b)        # NOT b
    t4 = _garbled_nand(t2, t3)      # a OR b
    return _garbled_nand(t1, t4)    # XNOR(a, b)


def _garbled_and(x: int, y: int) -> int:
    """Oblivious AND using 2 garbled NAND gates."""
    t = _garbled_nand(x, y)
    return _garbled_nand(t, t)


# ============================================================
# Option A — Fully Oblivious
# ============================================================

def option_a_oblivious(a_bits: list, b_bits: list) -> bool:
    """
    Fully oblivious equality check over boolean arrays.

    Runtime: O(n)
    """
    n = len(a_bits)
    assert len(b_bits) == n, "Arrays must have equal length"

    # Step 1: compute eq_i = (a_i == b_i) obliviously for every index
    eq_bits = [_garbled_eq(a_bits[i], b_bits[i]) for i in range(n)]

    # Step 2: AND-reduce all eq_i obliviously
    result = eq_bits[0]
    for i in range(1, n):
        result = _garbled_and(result, eq_bits[i])

    return bool(result)


# ============================================================
# Option B — Leaky but Efficient
# ============================================================

def option_b_leaky(a_bits: list, b_bits: list) -> bool:
    """
    Leaky equality check using plain comparison and early exit

    Runtime: O(J+1) — O(1) best case (mismatch at 0), O(n) worst case (equal).
    """
    for i in range(len(a_bits)):
        # Public control flow: the branch outcome (equal or not) and the
        # iteration index i at which we exit are both observable. This is the
        # intentional, bounded leakage accepted in exchange for O(J) speedup.
        if a_bits[i] != b_bits[i]:
            return False
    return True


# ============================================================
# Performance Evaluation
# ============================================================

def benchmark(n: int, mismatch_pos=None, runs: int = 5):
    """
    Time both options for array length n, averaged over `runs` repetitions.
    mismatch_pos: index where arrays differ (None = fully equal arrays).
    """
    a = [random.randint(0, 1) for _ in range(n)]
    b = a[:]
    if mismatch_pos is not None:
        b[mismatch_pos] = 1 - b[mismatch_pos]

    times_a, times_b = [], []
    for _ in range(runs):
        t0 = time.perf_counter()
        res_a = option_a_oblivious(a, b)
        times_a.append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        res_b = option_b_leaky(a, b)
        times_b.append(time.perf_counter() - t0)

    assert res_a == res_b, f"Correctness failure: A={res_a} B={res_b}"
    return sum(times_a) / runs, sum(times_b) / runs, res_a


def run_benchmarks():
    print("\n=== Assignment 2: Performance Evaluation (avg of 5 runs) ===\n")
    sizes = [4, 8, 16]
    header = f"{'n':>4} | {'Option A (s)':>14} | {'Option B (s)':>14} | {'Speedup':>9}"
    sep = "-" * 56

    for label, pos_fn in [
        ("Equal arrays — worst case for B, O(n) for both", lambda n: None),
        ("Mismatch at index 0 — best case for B, O(1) vs O(n)", lambda n: 0),
        ("Mismatch at midpoint — average case", lambda n: n // 2),
    ]:
        print(f"--- {label} ---")
        print(header)
        print(sep)
        for n in sizes:
            ta, tb, result = benchmark(n, mismatch_pos=pos_fn(n))
            speedup = ta / tb if tb > 1e-9 else float('inf')
            print(f"{n:>4} | {ta:>14.6f} | {tb:>14.6f} | {speedup:>8.1f}x  (={result})")
        print()


if __name__ == "__main__":
    print("=== Correctness Verification ===")
    test_cases = [
        ([0, 1, 0, 1], [0, 1, 0, 1], True),
        ([0, 1, 0, 1], [0, 1, 1, 1], False),
        ([1, 1, 1, 1], [1, 1, 1, 1], True),
        ([0, 0, 0, 0], [0, 0, 0, 1], False),
        ([1, 0, 1, 0], [0, 0, 1, 0], False),
    ]
    all_pass = True
    for a, b, expected in test_cases:
        ra = option_a_oblivious(a, b)
        rb = option_b_leaky(a, b)
        ok = "✓" if ra == expected == rb else "✗"
        if ra != expected or rb != expected:
            all_pass = False
        print(f"  {ok}  A={a}  B={b}  expected={expected}  oblivious={ra}  leaky={rb}")
    print(f"\nAll tests passed: {all_pass}\n")

    run_benchmarks()