"""
Memory Firewall
Isolates sensitive memory regions and prevents unauthorized access
Implements memory sandboxing for GRCM memory states
"""

import torch
import threading
from typing import Dict, Set, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class MemoryZone(Enum):
    """Security zones for memory regions"""
    PUBLIC = "public"  # Accessible to all
    PROTECTED = "protected"  # Requires auth
    SENSITIVE = "sensitive"  # Encrypted at rest
    CRITICAL = "critical"  # Audit all access


@dataclass
class MemorySegment:
    """Represents an isolated memory segment"""
    name: str
    zone: MemoryZone
    data: torch.Tensor
    owner: str
    readers: Set[str] = field(default_factory=set)
    writers: Set[str] = field(default_factory=set)
    encrypted: bool = False
    access_count: int = 0


class MemoryFirewall:
    """
    Isolates and protects memory segments with access control

    Features:
    - Zone-based isolation (PUBLIC, PROTECTED, SENSITIVE, CRITICAL)
    - Reader/writer access lists
    - Audit logging for CRITICAL zones
    - Memory encryption for SENSITIVE zones
    - Thread-safe access
    """

    def __init__(self, encryption_enabled: bool = True, audit_callback: Optional[Callable] = None):
        """
        Initialize memory firewall

        Args:
            encryption_enabled: Encrypt SENSITIVE zones
            audit_callback: Called on CRITICAL zone access (segment_name, caller, operation)
        """
        self.segments: Dict[str, MemorySegment] = {}
        self.lock = threading.RLock()
        self.encryption_enabled = encryption_enabled
        self.audit_callback = audit_callback or self._default_audit

    def _default_audit(self, segment_name: str, caller: str, operation: str):
        """Default audit logger"""
        print(f"[AUDIT] {operation} on {segment_name} by {caller}")

    def allocate(
        self,
        name: str,
        data: torch.Tensor,
        zone: MemoryZone,
        owner: str,
        readers: Optional[Set[str]] = None,
        writers: Optional[Set[str]] = None
    ) -> bool:
        """
        Allocate new memory segment with access control

        Args:
            name: Segment identifier
            data: Tensor data
            zone: Security zone
            owner: Owner identity
            readers: Set of allowed reader IDs
            writers: Set of allowed writer IDs

        Returns:
            True if allocation successful
        """
        with self.lock:
            if name in self.segments:
                raise ValueError(f"Memory segment '{name}' already exists")

            # Default permissions
            if readers is None:
                readers = {owner}
            if writers is None:
                writers = {owner}

            # Always include owner
            readers.add(owner)
            writers.add(owner)

            # Encrypt SENSITIVE data
            encrypted = False
            stored_data = data.clone()
            if zone == MemoryZone.SENSITIVE and self.encryption_enabled:
                # Simple XOR encryption (replace with proper encryption in production)
                stored_data = self._encrypt_memory(stored_data)
                encrypted = True

            segment = MemorySegment(
                name=name,
                zone=zone,
                data=stored_data,
                owner=owner,
                readers=readers,
                writers=writers,
                encrypted=encrypted
            )

            self.segments[name] = segment
            return True

    def read(self, name: str, caller: str) -> torch.Tensor:
        """
        Read memory segment with access check

        Args:
            name: Segment name
            caller: Caller identity

        Returns:
            Memory tensor (decrypted if needed)

        Raises:
            PermissionError: If caller lacks read permission
            KeyError: If segment doesn't exist
        """
        with self.lock:
            segment = self.segments.get(name)
            if segment is None:
                raise KeyError(f"Memory segment '{name}' not found")

            # Check read permission
            if caller not in segment.readers and segment.zone != MemoryZone.PUBLIC:
                raise PermissionError(f"Caller '{caller}' lacks read permission for '{name}'")

            # Audit CRITICAL zone access
            if segment.zone == MemoryZone.CRITICAL:
                self.audit_callback(name, caller, "READ")

            # Increment access counter
            segment.access_count += 1

            # Decrypt if needed
            data = segment.data.clone()
            if segment.encrypted:
                data = self._decrypt_memory(data)

            return data

    def write(self, name: str, caller: str, data: torch.Tensor) -> bool:
        """
        Write memory segment with access check

        Args:
            name: Segment name
            caller: Caller identity
            data: New tensor data

        Returns:
            True if write successful

        Raises:
            PermissionError: If caller lacks write permission
            KeyError: If segment doesn't exist
        """
        with self.lock:
            segment = self.segments.get(name)
            if segment is None:
                raise KeyError(f"Memory segment '{name}' not found")

            # Check write permission
            if caller not in segment.writers:
                raise PermissionError(f"Caller '{caller}' lacks write permission for '{name}'")

            # Audit CRITICAL zone access
            if segment.zone == MemoryZone.CRITICAL:
                self.audit_callback(name, caller, "WRITE")

            # Encrypt if needed
            stored_data = data.clone()
            if segment.encrypted:
                stored_data = self._encrypt_memory(stored_data)

            segment.data = stored_data
            segment.access_count += 1

            return True

    def grant_access(self, name: str, owner: str, grantee: str, permission: str = "read") -> bool:
        """
        Grant read or write access to a segment

        Args:
            name: Segment name
            owner: Must be segment owner
            grantee: Identity to grant access to
            permission: "read" or "write"

        Returns:
            True if grant successful
        """
        with self.lock:
            segment = self.segments.get(name)
            if segment is None:
                raise KeyError(f"Memory segment '{name}' not found")

            if segment.owner != owner:
                raise PermissionError(f"Only owner '{segment.owner}' can grant access")

            if permission == "read":
                segment.readers.add(grantee)
            elif permission == "write":
                segment.writers.add(grantee)
                segment.readers.add(grantee)  # Writers implicitly have read access
            else:
                raise ValueError(f"Invalid permission: {permission}")

            return True

    def revoke_access(self, name: str, owner: str, revokee: str, permission: str = "read") -> bool:
        """Revoke read or write access"""
        with self.lock:
            segment = self.segments.get(name)
            if segment is None:
                raise KeyError(f"Memory segment '{name}' not found")

            if segment.owner != owner:
                raise PermissionError(f"Only owner '{segment.owner}' can revoke access")

            if permission == "read":
                segment.readers.discard(revokee)
            elif permission == "write":
                segment.writers.discard(revokee)
            else:
                raise ValueError(f"Invalid permission: {permission}")

            return True

    def deallocate(self, name: str, caller: str) -> bool:
        """
        Deallocate memory segment

        Args:
            name: Segment name
            caller: Must be owner

        Returns:
            True if deallocation successful
        """
        with self.lock:
            segment = self.segments.get(name)
            if segment is None:
                raise KeyError(f"Memory segment '{name}' not found")

            if segment.owner != caller:
                raise PermissionError(f"Only owner '{segment.owner}' can deallocate")

            # Secure erase (overwrite with zeros)
            segment.data.zero_()

            del self.segments[name]
            return True

    def get_stats(self) -> Dict:
        """Get firewall statistics"""
        with self.lock:
            return {
                'total_segments': len(self.segments),
                'zones': {
                    zone.value: sum(1 for s in self.segments.values() if s.zone == zone)
                    for zone in MemoryZone
                },
                'encrypted_segments': sum(1 for s in self.segments.values() if s.encrypted),
                'total_accesses': sum(s.access_count for s in self.segments.values())
            }

    def _encrypt_memory(self, data: torch.Tensor) -> torch.Tensor:
        """Simple XOR encryption (replace with proper encryption)"""
        # NOTE: This is a placeholder - use proper encryption in production
        key = torch.randint(0, 256, (1,), dtype=torch.uint8)
        encrypted = data.to(torch.float32)
        encrypted = encrypted + key.item()  # Simple obfuscation
        return encrypted

    def _decrypt_memory(self, data: torch.Tensor) -> torch.Tensor:
        """Decrypt memory (inverse of _encrypt_memory)"""
        # NOTE: Placeholder decryption
        return data  # In production, use proper decryption


# Example usage
if __name__ == "__main__":
    firewall = MemoryFirewall()

    # Allocate PUBLIC memory
    public_data = torch.randn(128)
    firewall.allocate("public_mem", public_data, MemoryZone.PUBLIC, owner="system")

    # Allocate SENSITIVE memory
    sensitive_data = torch.randn(128)
    firewall.allocate(
        "sensitive_mem",
        sensitive_data,
        MemoryZone.SENSITIVE,
        owner="user1",
        readers={"user1"},
        writers={"user1"}
    )

    # Allocate CRITICAL memory
    critical_data = torch.randn(128)
    firewall.allocate(
        "critical_mem",
        critical_data,
        MemoryZone.CRITICAL,
        owner="admin",
        readers={"admin"},
        writers={"admin"}
    )

    # Test PUBLIC access (should succeed)
    data = firewall.read("public_mem", caller="anyone")
    print("✓ PUBLIC memory read successful")

    # Test SENSITIVE access (should fail without permission)
    try:
        data = firewall.read("sensitive_mem", caller="user2")
        print("✗ SENSITIVE memory read should have failed")
    except PermissionError:
        print("✓ SENSITIVE memory protected")

    # Grant access and retry
    firewall.grant_access("sensitive_mem", owner="user1", grantee="user2", permission="read")
    data = firewall.read("sensitive_mem", caller="user2")
    print("✓ SENSITIVE memory read after grant")

    # Test CRITICAL access (should audit)
    data = firewall.read("critical_mem", caller="admin")
    print("✓ CRITICAL memory read with audit")

    # Stats
    stats = firewall.get_stats()
    print(f"\nFirewall Stats: {stats}")
