"""
PII Boundary Agent
Detects and redacts Personally Identifiable Information in data streams
Prevents PII leakage in logs, checkpoints, and API responses
"""

import re
import hashlib
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum


class PIIType(Enum):
    """Types of detectable PII"""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    NAME = "name"  # Simple heuristic
    ADDRESS = "address"  # Street addresses
    CUSTOM = "custom"


@dataclass
class PIIMatch:
    """Represents a detected PII instance"""
    pii_type: PIIType
    start: int
    end: int
    matched_text: str
    redacted_text: str
    confidence: float = 1.0


class PIIBoundaryAgent:
    """
    Detects and redacts PII in text and structured data

    Features:
    - Regex-based detection for common PII types
    - Configurable redaction strategies (mask, hash, remove)
    - Allowlist for approved entities
    - Detection statistics
    """

    # Regex patterns for PII detection
    PATTERNS = {
        PIIType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        PIIType.PHONE: r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
        PIIType.SSN: r'\b\d{3}-\d{2}-\d{4}\b',
        PIIType.CREDIT_CARD: r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        PIIType.IP_ADDRESS: r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
    }

    def __init__(self, redaction_mode: str = "mask", allowlist: Optional[Set[str]] = None):
        """
        Initialize PII boundary agent

        Args:
            redaction_mode: "mask", "hash", or "remove"
            allowlist: Set of allowed values that shouldn't be redacted
        """
        self.redaction_mode = redaction_mode
        self.allowlist = allowlist or set()
        self.detection_count: Dict[PIIType, int] = {pii_type: 0 for pii_type in PIIType}

        # Compile regex patterns
        self.compiled_patterns = {
            pii_type: re.compile(pattern)
            for pii_type, pattern in self.PATTERNS.items()
        }

    def detect(self, text: str) -> List[PIIMatch]:
        """
        Detect all PII in text

        Args:
            text: Input text to scan

        Returns:
            List of PIIMatch objects
        """
        matches = []

        for pii_type, pattern in self.compiled_patterns.items():
            for match in pattern.finditer(text):
                matched_text = match.group()

                # Skip if in allowlist
                if matched_text in self.allowlist:
                    continue

                # Create redacted version
                redacted = self._redact_value(matched_text, pii_type)

                matches.append(PIIMatch(
                    pii_type=pii_type,
                    start=match.start(),
                    end=match.end(),
                    matched_text=matched_text,
                    redacted_text=redacted,
                    confidence=1.0
                ))

                self.detection_count[pii_type] += 1

        # Sort by start position
        matches.sort(key=lambda m: m.start)
        return matches

    def redact(self, text: str) -> Tuple[str, List[PIIMatch]]:
        """
        Redact all PII in text

        Args:
            text: Input text

        Returns:
            Tuple of (redacted_text, detected_matches)
        """
        matches = self.detect(text)

        # Replace in reverse order to maintain indices
        redacted_text = text
        for match in reversed(matches):
            redacted_text = (
                redacted_text[:match.start] +
                match.redacted_text +
                redacted_text[match.end:]
            )

        return redacted_text, matches

    def redact_dict(self, data: Dict) -> Tuple[Dict, List[PIIMatch]]:
        """
        Redact PII in dictionary values (recursive)

        Args:
            data: Dictionary with potential PII

        Returns:
            Tuple of (redacted_dict, all_matches)
        """
        redacted = {}
        all_matches = []

        for key, value in data.items():
            if isinstance(value, str):
                redacted_value, matches = self.redact(value)
                redacted[key] = redacted_value
                all_matches.extend(matches)
            elif isinstance(value, dict):
                redacted_value, matches = self.redact_dict(value)
                redacted[key] = redacted_value
                all_matches.extend(matches)
            elif isinstance(value, list):
                redacted_list = []
                for item in value:
                    if isinstance(item, str):
                        redacted_item, matches = self.redact(item)
                        redacted_list.append(redacted_item)
                        all_matches.extend(matches)
                    else:
                        redacted_list.append(item)
                redacted[key] = redacted_list
            else:
                redacted[key] = value

        return redacted, all_matches

    def _redact_value(self, value: str, pii_type: PIIType) -> str:
        """Apply redaction strategy to PII value"""
        if self.redaction_mode == "mask":
            # Mask with asterisks, keeping structure
            if pii_type == PIIType.EMAIL:
                parts = value.split('@')
                if len(parts) == 2:
                    username = parts[0]
                    domain = parts[1]
                    masked_user = username[0] + '*' * (len(username) - 1)
                    return f"{masked_user}@{domain}"
            elif pii_type == PIIType.PHONE:
                # XXX-XXX-1234
                return re.sub(r'\d(?=\d{4})', 'X', value)
            elif pii_type == PIIType.CREDIT_CARD:
                # Keep last 4 digits
                return re.sub(r'\d(?=\d{4})', '*', value)
            else:
                return '*' * len(value)

        elif self.redaction_mode == "hash":
            # Hash the value (one-way, but consistent)
            hash_obj = hashlib.sha256(value.encode())
            return f"[HASH:{hash_obj.hexdigest()[:16]}]"

        elif self.redaction_mode == "remove":
            # Complete removal
            return f"[{pii_type.value.upper()}_REDACTED]"

        else:
            raise ValueError(f"Invalid redaction mode: {self.redaction_mode}")

    def add_to_allowlist(self, value: str):
        """Add value to allowlist (won't be redacted)"""
        self.allowlist.add(value)

    def remove_from_allowlist(self, value: str):
        """Remove value from allowlist"""
        self.allowlist.discard(value)

    def get_stats(self) -> Dict:
        """Get detection statistics"""
        return {
            'total_detections': sum(self.detection_count.values()),
            'by_type': {pii_type.value: count for pii_type, count in self.detection_count.items()},
            'allowlist_size': len(self.allowlist),
            'redaction_mode': self.redaction_mode
        }

    def reset_stats(self):
        """Reset detection counters"""
        self.detection_count = {pii_type: 0 for pii_type in PIIType}


# Example usage
if __name__ == "__main__":
    agent = PIIBoundaryAgent(redaction_mode="mask")

    # Test text with various PII
    test_text = """
    Contact us at support@echozero.ai or call 555-123-4567.
    My SSN is 123-45-6789 and credit card is 4532-1234-5678-9010.
    Server IP: 192.168.1.100
    """

    print("Original text:")
    print(test_text)

    # Redact
    redacted, matches = agent.redact(test_text)

    print("\nRedacted text:")
    print(redacted)

    print("\nDetected PII:")
    for match in matches:
        print(f"  - {match.pii_type.value}: {match.matched_text} -> {match.redacted_text}")

    # Test dictionary redaction
    test_dict = {
        'user': 'john.doe@example.com',
        'phone': '555-987-6543',
        'metadata': {
            'ip': '10.0.0.1',
            'notes': 'Call me at 555-111-2222'
        }
    }

    redacted_dict, dict_matches = agent.redact_dict(test_dict)
    print("\nRedacted dictionary:")
    print(redacted_dict)

    # Stats
    stats = agent.get_stats()
    print(f"\nDetection stats: {stats}")

    # Test allowlist
    agent.add_to_allowlist("support@echozero.ai")
    redacted2, matches2 = agent.redact(test_text)
    print("\nWith allowlist:")
    print(redacted2)
