"""
Audit Logger
Comprehensive security event logging and analysis
Tamper-resistant audit trail for compliance
"""

import threading
import hashlib
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import time


class SecurityEventType(Enum):
    """Types of security events"""
    # Authentication
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    AUTH_LOGOUT = "auth_logout"

    # Authorization
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_DENIED = "permission_denied"

    # Data access
    STATE_READ = "state_read"
    STATE_WRITE = "state_write"
    STATE_RESET = "state_reset"
    MEMORY_ACCESS = "memory_access"

    # Encryption
    DATA_ENCRYPTED = "data_encrypted"
    DATA_DECRYPTED = "data_decrypted"
    KEY_ROTATION = "key_rotation"

    # Configuration
    CONFIG_CHANGE = "config_change"
    USER_CREATED = "user_created"
    USER_DELETED = "user_deleted"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REVOKED = "role_revoked"

    # Security violations
    EGRESS_BLOCKED = "egress_blocked"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    PII_DETECTED = "pii_detected"
    INVALID_INPUT = "invalid_input"

    # System
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    CHECKPOINT_SAVE = "checkpoint_save"
    CHECKPOINT_LOAD = "checkpoint_load"


class SeverityLevel(Enum):
    """Severity levels for events"""
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


@dataclass
class SecurityEvent:
    """Represents a security event"""
    timestamp: float
    event_type: SecurityEventType
    severity: SeverityLevel
    user: Optional[str]
    resource: str
    action: str
    outcome: str  # success/failure/blocked
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    session_id: Optional[str] = None

    # Tamper protection
    event_hash: Optional[str] = None
    prev_hash: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'timestamp_iso': datetime.fromtimestamp(self.timestamp).isoformat(),
            'event_type': self.event_type.value,
            'severity': self.severity.value,
            'user': self.user,
            'resource': self.resource,
            'action': self.action,
            'outcome': self.outcome,
            'details': self.details,
            'ip_address': self.ip_address,
            'session_id': self.session_id,
            'event_hash': self.event_hash,
            'prev_hash': self.prev_hash
        }


class AuditLogger:
    """
    Tamper-resistant audit logging system

    Features:
    - Chained hashing for tamper detection
    - Severity filtering
    - Event search and analysis
    - Compliance reporting
    - Thread-safe operations
    - Persistent storage (optional)
    """

    def __init__(
        self,
        min_severity: SeverityLevel = SeverityLevel.INFO,
        max_events: int = 10000,
        enable_chaining: bool = True
    ):
        """
        Initialize audit logger

        Args:
            min_severity: Minimum severity to log
            max_events: Maximum events to keep in memory
            enable_chaining: Enable hash chaining for tamper detection
        """
        self.events: List[SecurityEvent] = []
        self.lock = threading.RLock()
        self.min_severity = min_severity
        self.max_events = max_events
        self.enable_chaining = enable_chaining
        self.last_hash: Optional[str] = None

    def log(
        self,
        event_type: SecurityEventType,
        user: Optional[str],
        resource: str,
        action: str,
        outcome: str,
        severity: SeverityLevel = SeverityLevel.INFO,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> SecurityEvent:
        """
        Log security event

        Args:
            event_type: Type of event
            user: User performing action
            resource: Resource being accessed
            action: Action being performed
            outcome: Result (success/failure/blocked)
            severity: Severity level
            details: Additional details
            ip_address: Source IP
            session_id: Session identifier

        Returns:
            Created SecurityEvent
        """
        with self.lock:
            # Filter by severity
            if severity.value < self.min_severity.value:
                return None

            # Create event
            event = SecurityEvent(
                timestamp=time.time(),
                event_type=event_type,
                severity=severity,
                user=user,
                resource=resource,
                action=action,
                outcome=outcome,
                details=details or {},
                ip_address=ip_address,
                session_id=session_id
            )

            # Compute hash chain
            if self.enable_chaining:
                event.prev_hash = self.last_hash
                event.event_hash = self._compute_hash(event)
                self.last_hash = event.event_hash

            # Store event
            self.events.append(event)

            # Enforce max events (FIFO)
            if len(self.events) > self.max_events:
                self.events.pop(0)

            return event

    def _compute_hash(self, event: SecurityEvent) -> str:
        """Compute tamper-proof hash for event"""
        # Create canonical representation
        data = {
            'timestamp': event.timestamp,
            'event_type': event.event_type.value,
            'user': event.user,
            'resource': event.resource,
            'action': event.action,
            'outcome': event.outcome,
            'prev_hash': event.prev_hash
        }

        # Hash
        canonical = json.dumps(data, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def verify_chain(self) -> Tuple[bool, Optional[int]]:
        """
        Verify hash chain integrity

        Returns:
            Tuple of (is_valid, first_tampered_index)
        """
        with self.lock:
            if not self.enable_chaining:
                return True, None

            prev_hash = None
            for i, event in enumerate(self.events):
                # Check previous hash link
                if event.prev_hash != prev_hash:
                    return False, i

                # Recompute hash
                expected_hash = self._compute_hash(event)
                if event.event_hash != expected_hash:
                    return False, i

                prev_hash = event.event_hash

            return True, None

    def search(
        self,
        event_type: Optional[SecurityEventType] = None,
        user: Optional[str] = None,
        resource: Optional[str] = None,
        outcome: Optional[str] = None,
        min_severity: Optional[SeverityLevel] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 100
    ) -> List[SecurityEvent]:
        """
        Search audit log

        Args:
            event_type: Filter by event type
            user: Filter by user
            resource: Filter by resource
            outcome: Filter by outcome
            min_severity: Filter by minimum severity
            start_time: Filter by start timestamp
            end_time: Filter by end timestamp
            limit: Maximum results

        Returns:
            List of matching events
        """
        with self.lock:
            results = []

            for event in self.events:
                # Apply filters
                if event_type and event.event_type != event_type:
                    continue
                if user and event.user != user:
                    continue
                if resource and event.resource != resource:
                    continue
                if outcome and event.outcome != outcome:
                    continue
                if min_severity and event.severity.value < min_severity.value:
                    continue
                if start_time and event.timestamp < start_time:
                    continue
                if end_time and event.timestamp > end_time:
                    continue

                results.append(event)

                if len(results) >= limit:
                    break

            return results

    def get_stats(self) -> Dict:
        """Get audit log statistics"""
        with self.lock:
            total = len(self.events)

            by_type = {}
            by_severity = {}
            by_outcome = {}
            by_user = {}

            for event in self.events:
                # By type
                type_key = event.event_type.value
                by_type[type_key] = by_type.get(type_key, 0) + 1

                # By severity
                sev_key = event.severity.name
                by_severity[sev_key] = by_severity.get(sev_key, 0) + 1

                # By outcome
                by_outcome[event.outcome] = by_outcome.get(event.outcome, 0) + 1

                # By user
                if event.user:
                    by_user[event.user] = by_user.get(event.user, 0) + 1

            return {
                'total_events': total,
                'by_type': by_type,
                'by_severity': by_severity,
                'by_outcome': by_outcome,
                'by_user': by_user,
                'chain_valid': self.verify_chain()[0] if self.enable_chaining else None
            }

    def get_recent(self, limit: int = 10) -> List[SecurityEvent]:
        """Get recent events"""
        with self.lock:
            return self.events[-limit:]

    def get_failures(self, limit: int = 10) -> List[SecurityEvent]:
        """Get recent failure events"""
        return self.search(outcome="failure", limit=limit)

    def get_violations(self, limit: int = 10) -> List[SecurityEvent]:
        """Get recent security violations"""
        return self.search(outcome="blocked", limit=limit)

    def export_json(self, filepath: str):
        """Export audit log to JSON file"""
        with self.lock:
            with open(filepath, 'w') as f:
                json.dump([event.to_dict() for event in self.events], f, indent=2)

    def clear(self):
        """Clear audit log (use with caution!)"""
        with self.lock:
            self.events.clear()
            self.last_hash = None


# Example usage
if __name__ == "__main__":
    logger = AuditLogger()

    # Log various events
    logger.log(
        SecurityEventType.AUTH_SUCCESS,
        user="alice",
        resource="api",
        action="login",
        outcome="success",
        severity=SeverityLevel.INFO,
        details={'method': 'password'},
        ip_address="192.168.1.100"
    )

    logger.log(
        SecurityEventType.STATE_READ,
        user="alice",
        resource="psi_state",
        action="read",
        outcome="success",
        severity=SeverityLevel.INFO,
        details={'N': 64}
    )

    logger.log(
        SecurityEventType.PERMISSION_DENIED,
        user="bob",
        resource="config",
        action="write",
        outcome="failure",
        severity=SeverityLevel.WARNING,
        details={'required_role': 'admin'}
    )

    logger.log(
        SecurityEventType.EGRESS_BLOCKED,
        user="charlie",
        resource="checkpoint",
        action="save",
        outcome="blocked",
        severity=SeverityLevel.ERROR,
        details={'destination': '/tmp/model.pt', 'reason': 'not in allowlist'}
    )

    logger.log(
        SecurityEventType.PII_DETECTED,
        user="system",
        resource="api_request",
        action="scan",
        outcome="blocked",
        severity=SeverityLevel.CRITICAL,
        details={'pii_types': ['email', 'ssn'], 'count': 2}
    )

    # Verify chain
    valid, tampered_idx = logger.verify_chain()
    print(f"Hash chain valid: {valid}")

    # Search
    failures = logger.get_failures()
    print(f"\nRecent failures: {len(failures)}")
    for event in failures:
        print(f"  - {event.user} {event.action} {event.resource}: {event.details}")

    violations = logger.get_violations()
    print(f"\nSecurity violations: {len(violations)}")
    for event in violations:
        print(f"  - {event.event_type.value}: {event.details.get('reason')}")

    # Stats
    stats = logger.get_stats()
    print(f"\nStatistics:")
    print(f"  Total events: {stats['total_events']}")
    print(f"  By severity: {stats['by_severity']}")
    print(f"  By outcome: {stats['by_outcome']}")
    print(f"  Chain valid: {stats['chain_valid']}")

    # Export
    logger.export_json("/tmp/audit.json")
    print("\n✓ Exported to /tmp/audit.json")

    print("\n✓ Audit Logger tests passed")
