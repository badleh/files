"Created on 2026-03-01 by Only Badle. "
"""
Assignment 2: Garbled Circuits in Practice

Option A: Fully oblivious (no early exit)
Option B: Leaky but efficient (early exit)
"""
import time
import random
from garbled_nand import GarbledNAND


def build_nand_tree_equality(a_bits: list, b_bits: list):
    """
    Compute AND of (a_i XNOR b_i) for all i using NAND gates only.
    XNOR(a,b) = NOT(a XOR b) = (a NAND (a NAND b)) NAND (b NAND (a NAND b))
    Actually simpler: equal(a,b) = NOT(a XOR b) = NAND(NAND(a,b), NAND(NOT a, NOT b))
    
    Simpler approach using NAND:
    eq(a,b) = NAND(NAND(a,b), NAND(NAND(a,a), NAND(b,b)))
    Because: NAND(a,a) = NOT a, NAND(b,b) = NOT b
             NAND(NOT a, NOT b) = NOT(NOT a AND NOT b) = a OR b  (De Morgan)
             NAND(a,b) = NOT(a AND b)
             NAND(NOT(a AND b), a OR b) = NOT(NOT(a AND b) AND (a OR b))
                                        = (a AND b) OR NOT(a OR b)
                                        = (a AND b) OR (NOT a AND NOT b)
                                        = XNOR(a,b) ✓
    """
    pass  # We'll use a direct simulation approach


def simulate_garbled_equality_check(a_bits: list, b_bits: list) -> bool:
    """
    Simulate garbled circuit for equality check.
    Each bit comparison requires multiple NAND gates.
    Returns True if all bits match.
    
    We represent the full oblivious computation using garbled NAND gates.
    For simplicity in this educational implementation, we use the garbled circuit
    structure but simulate the NAND tree logic.
    
    eq(a_i, b_i) using only NAND:
      t1 = NAND(a_i, b_i)
      t2 = NAND(a_i, a_i)  = NOT a_i
      t3 = NAND(b_i, b_i)  = NOT b_i
      t4 = NAND(t2, t3)    = a_i OR b_i
      eq = NAND(t1, t4)    = XNOR(a_i, b_i)
    
    Then AND all eq_i using: AND(x,y) = NAND(NAND(x,y), NAND(x,y))
    """
    n = len(a_bits)
    assert len(b_bits) == n
    
    def garbled_nand_eval(a: int, b: int) -> int:
        """Single NAND gate evaluation via garbled circuit."""
        gate = GarbledNAND()
        gate.garble()
        lx, ly = gate.get_input_labels(a, b)
        return int(gate.evaluate(lx, ly))
    
    def garbled_eq(a: int, b: int) -> int:
        """Equality check for two bits using NAND gates."""
        t1 = garbled_nand_eval(a, b)          # NAND(a, b)
        t2 = garbled_nand_eval(a, a)          # NOT a
        t3 = garbled_nand_eval(b, b)          # NOT b
        t4 = garbled_nand_eval(t2, t3)        # a OR b
        eq = garbled_nand_eval(t1, t4)        # XNOR(a, b)
        return eq
    
    def garbled_and(x: int, y: int) -> int:
        """AND using NAND: AND(x,y) = NAND(NAND(x,y), NAND(x,y))"""
        t = garbled_nand_eval(x, y)
        return garbled_nand_eval(t, t)
    
    # Oblivious: evaluate ALL bits regardless of intermediate results
    eq_bits = [garbled_eq(a_bits[i], b_bits[i]) for i in range(n)]
    
    # Conjunct all eq bits
    result = eq_bits[0]
    for i in range(1, n):
        result = garbled_and(result, eq_bits[i])
    
    return bool(result)


# ============================================================
# Option A: Fully Oblivious
# ============================================================

def option_a_oblivious(a_bits: list, b_bits: list) -> bool:
    """
    Fully oblivious equality check.
    - No early termination
    - All indices always evaluated
    - Only final result revealed
    """
    return simulate_garbled_equality_check(a_bits, b_bits)


# ============================================================
# Option B: Leaky but Efficient
# ============================================================

def option_b_leaky(a_bits: list, b_bits: list) -> bool:
    """
    Leaky early-exit equality check.
    - Uses public control flow
    - Stops at first mismatch
    - Leaks position of first mismatch via timing
    """
    for i in range(len(a_bits)):
        # Still use garbled gate for each comparison (bit values stay hidden)
        # but we exit early on mismatch — leaking the position
        gate = GarbledNAND()
        gate.garble()
        # eq(a,b): evaluate using 5 NAND gates
        def nand_eval(a, b):
            g = GarbledNAND()
            g.garble()
            lx, ly = g.get_input_labels(a, b)
            return int(g.evaluate(lx, ly))
        
        t1 = nand_eval(a_bits[i], b_bits[i])
        t2 = nand_eval(a_bits[i], a_bits[i])
        t3 = nand_eval(b_bits[i], b_bits[i])
        t4 = nand_eval(t2, t3)
        eq_i = nand_eval(t1, t4)
        
        if not eq_i:
            return False  # Early exit — leaks that mismatch is at index i
    return True


# ============================================================
# Performance Evaluation
# ============================================================

def benchmark(n: int, mismatch_pos: int = None):
    """
    Benchmark both versions for array size n.
    mismatch_pos: index of mismatch (None = arrays are equal)
    """
    a = [random.randint(0, 1) for _ in range(n)]
    b = a.copy()
    if mismatch_pos is not None:
        b[mismatch_pos] = 1 - b[mismatch_pos]
    
    # Option A
    start = time.time()
    res_a = option_a_oblivious(a, b)
    time_a = time.time() - start
    
    # Option B
    start = time.time()
    res_b = option_b_leaky(a, b)
    time_b = time.time() - start
    
    assert res_a == res_b, f"Results differ! A={res_a}, B={res_b}"
    return time_a, time_b, res_a


def run_benchmarks():
    print("\n=== Assignment 2: Performance Evaluation ===\n")
    
    sizes = [4, 8, 16]
    
    print("--- Equal arrays (no mismatch) ---")
    print(f"{'n':>4} | {'Option A (s)':>14} | {'Option B (s)':>14} | {'Speedup':>8}")
    print("-" * 50)
    for n in sizes:
        ta, tb, result = benchmark(n, mismatch_pos=None)
        speedup = ta / tb if tb > 0 else float('inf')
        print(f"{n:>4} | {ta:>14.4f} | {tb:>14.4f} | {speedup:>7.2f}x  result={result}")
    
    print("\n--- Mismatch at first position (worst case for B = best case) ---")
    print(f"{'n':>4} | {'Option A (s)':>14} | {'Option B (s)':>14} | {'Speedup':>8}")
    print("-" * 50)
    for n in sizes:
        ta, tb, result = benchmark(n, mismatch_pos=0)
        speedup = ta / tb if tb > 0 else float('inf')
        print(f"{n:>4} | {ta:>14.4f} | {tb:>14.4f} | {speedup:>7.2f}x  result={result}")


if __name__ == "__main__":
    print("=== Correctness Check ===")
    tests = [
        ([0,1,0,1], [0,1,0,1], True),
        ([0,1,0,1], [0,1,1,1], False),
        ([1,1,1,1], [1,1,1,1], True),
        ([0,0,0,0], [0,0,0,1], False),
    ]
    for a, b, expected in tests:
        res_a = option_a_oblivious(a, b)
        res_b = option_b_leaky(a, b)
        ok_a = "✓" if res_a == expected else "✗"
        ok_b = "✓" if res_b == expected else "✗"
        print(f"A={a} B={b} → expected={expected} | oblivious={res_a}{ok_a} leaky={res_b}{ok_b}")
    
    run_benchmarks()
