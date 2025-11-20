"""
ψ-Envelope Encryption
Encrypts ψ state tensors for secure storage and transmission
Uses AES-256-GCM with state-derived nonces
"""

import torch
import hashlib
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Tuple, Optional
import base64


class PsiEnvelopeEncryption:
    """
    Encrypts and decrypts ψ-state tensors using AES-256-GCM

    Features:
    - State-derived nonces (deterministic but secure)
    - Key derivation from master secret
    - Authenticated encryption (prevents tampering)
    - Complex tensor support
    """

    def __init__(self, master_key: Optional[bytes] = None):
        """
        Initialize encryption with master key

        Args:
            master_key: 32-byte master key (generated if None)
        """
        if master_key is None:
            master_key = AESGCM.generate_key(bit_length=256)
        elif len(master_key) != 32:
            # Derive 32-byte key from arbitrary input
            master_key = self._derive_key(master_key, salt=b'echozero-psi-v4.2.1')

        self.master_key = master_key
        self.aesgcm = AESGCM(master_key)

    def _derive_key(self, password: bytes, salt: bytes, iterations: int = 100000) -> bytes:
        """Derive encryption key from password using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
        )
        return kdf.derive(password)

    def _generate_nonce(self, psi: torch.Tensor) -> bytes:
        """
        Generate deterministic nonce from ψ state

        Uses hash of tensor data to ensure uniqueness while being reproducible
        for the same state (useful for deduplication)
        """
        # Hash tensor bytes
        psi_real = psi.real.cpu().numpy().tobytes()
        psi_imag = psi.imag.cpu().numpy().tobytes() if torch.is_complex(psi) else b''

        hasher = hashlib.sha256()
        hasher.update(psi_real)
        hasher.update(psi_imag)
        hash_digest = hasher.digest()

        # Use first 12 bytes as nonce (GCM standard)
        return hash_digest[:12]

    def encrypt(self, psi: torch.Tensor, associated_data: Optional[bytes] = None) -> bytes:
        """
        Encrypt ψ state tensor

        Args:
            psi: Complex tensor [batch, N] or [N]
            associated_data: Optional authenticated but unencrypted data

        Returns:
            Encrypted envelope (nonce + ciphertext + tag)
        """
        # Convert tensor to bytes
        psi_cpu = psi.cpu()

        # Separate real and imaginary parts
        if torch.is_complex(psi):
            real_bytes = psi_cpu.real.numpy().tobytes()
            imag_bytes = psi_cpu.imag.numpy().tobytes()
            plaintext = real_bytes + b'|SPLIT|' + imag_bytes
        else:
            plaintext = psi_cpu.numpy().tobytes()

        # Store tensor metadata
        metadata = f"{psi.shape}|{psi.dtype}|{'complex' if torch.is_complex(psi) else 'real'}".encode()
        full_plaintext = metadata + b'|META|' + plaintext

        # Generate nonce
        nonce = self._generate_nonce(psi)

        # Encrypt
        ciphertext = self.aesgcm.encrypt(nonce, full_plaintext, associated_data)

        # Return nonce + ciphertext
        return nonce + ciphertext

    def decrypt(
        self,
        envelope: bytes,
        associated_data: Optional[bytes] = None,
        device: torch.device = torch.device('cpu')
    ) -> torch.Tensor:
        """
        Decrypt ψ state tensor

        Args:
            envelope: Encrypted envelope from encrypt()
            associated_data: Must match data used in encrypt()
            device: Target device for tensor

        Returns:
            Decrypted ψ tensor
        """
        # Extract nonce and ciphertext
        nonce = envelope[:12]
        ciphertext = envelope[12:]

        # Decrypt
        plaintext = self.aesgcm.decrypt(nonce, ciphertext, associated_data)

        # Parse metadata
        meta_split = plaintext.split(b'|META|', 1)
        if len(meta_split) != 2:
            raise ValueError("Invalid encrypted envelope format")

        metadata_str, tensor_data = meta_split
        metadata = metadata_str.decode().split('|')
        shape_str, dtype_str, complexity = metadata[0], metadata[1], metadata[2]

        # Parse shape
        shape = eval(shape_str)  # e.g., "torch.Size([64])" -> tuple

        # Reconstruct tensor
        if complexity == 'complex':
            parts = tensor_data.split(b'|SPLIT|')
            if len(parts) != 2:
                raise ValueError("Invalid complex tensor format")

            real_bytes, imag_bytes = parts
            real_array = torch.frombuffer(real_bytes, dtype=torch.float32).reshape(shape)
            imag_array = torch.frombuffer(imag_bytes, dtype=torch.float32).reshape(shape)

            psi = torch.complex(real_array, imag_array)
        else:
            psi = torch.frombuffer(tensor_data, dtype=torch.float32).reshape(shape)

        return psi.to(device)

    def export_key(self) -> str:
        """Export master key as base64 string"""
        return base64.b64encode(self.master_key).decode('utf-8')

    @classmethod
    def from_key(cls, key_b64: str) -> 'PsiEnvelopeEncryption':
        """Load encryption from exported key"""
        master_key = base64.b64decode(key_b64.encode('utf-8'))
        return cls(master_key=master_key)

    def rotate_key(self, new_master_key: Optional[bytes] = None) -> 'PsiEnvelopeEncryption':
        """
        Generate new encryptor with rotated key

        Args:
            new_master_key: New master key (generated if None)

        Returns:
            New PsiEnvelopeEncryption instance
        """
        return PsiEnvelopeEncryption(master_key=new_master_key)


# Example usage
if __name__ == "__main__":
    # Create encryptor
    encryptor = PsiEnvelopeEncryption()

    # Example ψ state
    psi = torch.randn(64, dtype=torch.complex64)

    # Encrypt
    envelope = encryptor.encrypt(psi, associated_data=b'echozero-checkpoint-001')
    print(f"Encrypted envelope size: {len(envelope)} bytes")

    # Decrypt
    psi_decrypted = encryptor.decrypt(envelope, associated_data=b'echozero-checkpoint-001')

    # Verify
    assert torch.allclose(psi, psi_decrypted, atol=1e-6)
    print("✓ Encryption/decryption successful")

    # Export key
    key_export = encryptor.export_key()
    print(f"Exported key: {key_export[:32]}...")

    # Load from key
    encryptor2 = PsiEnvelopeEncryption.from_key(key_export)
    psi_decrypted2 = encryptor2.decrypt(envelope, associated_data=b'echozero-checkpoint-001')
    assert torch.allclose(psi, psi_decrypted2, atol=1e-6)
    print("✓ Key export/import successful")
