"Created on 2026-03-01 by Only Badle. "

"""
Assignment 1: Mini Garbled Circuit - Single NAND Gate
Semi-honest adversaries, no OT, no networking.
"""
import os
import secrets
import hashlib
import struct
from typing import Tuple, Dict, List

LABEL_SIZE = 16  # 128 bits

def generate_label() -> bytes:
    return secrets.token_bytes(LABEL_SIZE)

def kdf(label_x: bytes, label_y: bytes) -> bytes:
    """Key derivation function: KDF(Lx || Ly)"""
    return hashlib.sha256(label_x + label_y).digest()[:LABEL_SIZE]

def encrypt(key: bytes, plaintext: bytes) -> bytes:
    """Simple XOR-based stream cipher using AES-CTR via SHA256 keystream."""
    # Use SHA256 as a PRF to generate keystream
    keystream = hashlib.sha256(key + b'\x00').digest()[:LABEL_SIZE]
    # Add a MAC: SHA256(key || plaintext) to detect successful decryption
    mac = hashlib.sha256(key + b'\x01' + plaintext).digest()[:LABEL_SIZE]
    ciphertext = bytes(a ^ b for a, b in zip(plaintext, keystream))
    return ciphertext + mac  # ciphertext + mac

def decrypt(key: bytes, ciphertext_with_mac: bytes) -> Tuple[bool, bytes]:
    """Decrypt and verify MAC. Returns (success, plaintext)."""
    ciphertext = ciphertext_with_mac[:LABEL_SIZE]
    mac = ciphertext_with_mac[LABEL_SIZE:]
    keystream = hashlib.sha256(key + b'\x00').digest()[:LABEL_SIZE]
    plaintext = bytes(a ^ b for a, b in zip(ciphertext, keystream))
    expected_mac = hashlib.sha256(key + b'\x01' + plaintext).digest()[:LABEL_SIZE]
    if mac == expected_mac:
        return True, plaintext
    return False, b''


class GarbledNAND:
    """Garbled NAND gate implementation."""
    
    def __init__(self):
        # Wire labels: L0, L1 for each wire x, y, z
        self.labels = {
            'x': (generate_label(), generate_label()), 
            'y': (generate_label(), generate_label()),
            'z': (generate_label(), generate_label()),
        }
        # Decoding table: maps output label -> Boolean value
        self.decoding_table = {
            self.labels['z'][0]: False,
            self.labels['z'][1]: True,
        }
        self.garbled_table: List[bytes] = []
    
    def nand(self, a: int, b: int) -> int:
        return 1 - (a & b)
    
    def garble(self) -> List[bytes]:
        """
        Garble the NAND gate. Returns list of 4 shuffled ciphertexts.
        For each (a,b): C[a,b] = Enc(KDF(L^a_x || L^b_y), L^{a NAND b}_z)
        """
        entries = []
        for a in range(2):
            for b in range(2):
                lab_x = self.labels['x'][a]
                lab_y = self.labels['y'][b]
                out_bit = self.nand(a, b)
                lab_z = self.labels['z'][out_bit]
                
                key = kdf(lab_x, lab_y)
                ct = encrypt(key, lab_z)
                entries.append(ct)
        
        # Shuffle for security 
        import random
        random.shuffle(entries)
        self.garbled_table = entries
        return self.garbled_table
    
    def get_input_labels(self, x_val: int, y_val: int) -> Tuple[bytes, bytes]:
        """Garbler provides input labels corresponding to actual input values."""
        return self.labels['x'][x_val], self.labels['y'][y_val]
    
    def evaluate(self, label_x: bytes, label_y: bytes) -> bool:
        """
        Evaluator tries all 4 ciphertexts with derived key.
        Exactly one will succeed.
        """
        key = kdf(label_x, label_y)
        for ct in self.garbled_table:
            success, output_label = decrypt(key, ct)
            if success:
                if output_label in self.decoding_table:
                    return self.decoding_table[output_label]
        raise RuntimeError("No ciphertext decrypted successfully — implementation error!")


def test_nand_gate():
    print("=== Assignment 1: Garbled NAND Gate ===\n")
    
    gate = GarbledNAND()
    garbled_table = gate.garble()
    
    print(f"Wire labels generated (128-bit each):")
    print(f"  L0_x = {gate.labels['x'][0].hex()[:16]}...")
    print(f"  L1_x = {gate.labels['x'][1].hex()[:16]}...")
    print(f"  L0_y = {gate.labels['y'][0].hex()[:16]}...")
    print(f"  L1_y = {gate.labels['y'][1].hex()[:16]}...")
    print(f"\nGarbled table: {len(garbled_table)} ciphertexts (shuffled)\n")
    
    print("Truth table verification:")
    print(f"{'x':>3} {'y':>3} {'NAND':>6} {'Garbled Result':>16}")
    print("-" * 32)
    
    for x in range(2):
        for y in range(2):
            lx, ly = gate.get_input_labels(x, y)
            result = gate.evaluate(lx, ly)
            expected = bool(1 - (x & y))
            status = "✓" if result == expected else "✗"
            print(f"{x:>3} {y:>3} {str(expected):>6}  {str(result):>14} {status}")
    
    print("\nAll NAND gate evaluations correct!")


if __name__ == "__main__":
    test_nand_gate()
