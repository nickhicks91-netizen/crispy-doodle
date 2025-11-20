"""
Egress Guard
Controls outbound data flow to prevent data exfiltration
Monitors and filters all external communication
"""

import torch
import threading
from typing import Dict, List, Optional, Callable, Set
from dataclasses import dataclass
from enum import Enum
import time


class EgressChannel(Enum):
    """Types of egress channels"""
    API_RESPONSE = "api_response"
    CHECKPOINT_SAVE = "checkpoint_save"
    LOG_OUTPUT = "log_output"
    METRIC_EXPORT = "metric_export"
    WEBSOCKET = "websocket"
    FILE_WRITE = "file_write"


@dataclass
class EgressEvent:
    """Represents an egress attempt"""
    timestamp: float
    channel: EgressChannel
    destination: str
    data_size: int
    user: Optional[str]
    allowed: bool
    reason: str = ""


class EgressGuard:
    """
    Controls and monitors outbound data flow

    Features:
    - Channel-specific policies
    - Size limits per channel
    - Rate limiting
    - Destination allowlists/blocklists
    - Event logging
    - Alert callbacks for violations
    """

    def __init__(
        self,
        size_limits: Optional[Dict[EgressChannel, int]] = None,
        rate_limits: Optional[Dict[EgressChannel, Tuple[int, int]]] = None,
        alert_callback: Optional[Callable[[EgressEvent], None]] = None
    ):
        """
        Initialize egress guard

        Args:
            size_limits: Max bytes per channel (channel -> bytes)
            rate_limits: Rate limits per channel (channel -> (max_count, window_seconds))
            alert_callback: Called on policy violations
        """
        self.lock = threading.RLock()

        # Default size limits (in bytes)
        self.size_limits = size_limits or {
            EgressChannel.API_RESPONSE: 10 * 1024 * 1024,  # 10MB
            EgressChannel.CHECKPOINT_SAVE: 1024 * 1024 * 1024,  # 1GB
            EgressChannel.LOG_OUTPUT: 100 * 1024,  # 100KB
            EgressChannel.METRIC_EXPORT: 1 * 1024 * 1024,  # 1MB
            EgressChannel.WEBSOCKET: 1 * 1024 * 1024,  # 1MB
            EgressChannel.FILE_WRITE: 100 * 1024 * 1024,  # 100MB
        }

        # Default rate limits (count, window_seconds)
        self.rate_limits = rate_limits or {
            EgressChannel.API_RESPONSE: (1000, 60),  # 1000 per minute
            EgressChannel.CHECKPOINT_SAVE: (10, 3600),  # 10 per hour
            EgressChannel.LOG_OUTPUT: (10000, 60),  # 10k per minute
            EgressChannel.METRIC_EXPORT: (1000, 60),  # 1k per minute
            EgressChannel.WEBSOCKET: (10000, 60),  # 10k per minute
            EgressChannel.FILE_WRITE: (100, 60),  # 100 per minute
        }

        self.alert_callback = alert_callback or self._default_alert

        # Tracking
        self.event_history: List[EgressEvent] = []
        self.rate_tracking: Dict[EgressChannel, List[float]] = {
            channel: [] for channel in EgressChannel
        }
        self.allowlists: Dict[EgressChannel, Set[str]] = {}
        self.blocklists: Dict[EgressChannel, Set[str]] = {}

    def _default_alert(self, event: EgressEvent):
        """Default alert handler"""
        print(f"[EGRESS ALERT] {event.channel.value} to {event.destination}: {event.reason}")

    def check_egress(
        self,
        channel: EgressChannel,
        destination: str,
        data_size: int,
        user: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Check if egress is allowed

        Args:
            channel: Egress channel type
            destination: Destination identifier (URL, path, etc.)
            data_size: Size of data in bytes
            user: User initiating egress

        Returns:
            Tuple of (allowed, reason)
        """
        with self.lock:
            # Check blocklist
            if channel in self.blocklists and destination in self.blocklists[channel]:
                reason = f"Destination '{destination}' is blocklisted"
                self._log_event(channel, destination, data_size, user, False, reason)
                return False, reason

            # Check allowlist (if set, only allowed destinations permitted)
            if channel in self.allowlists and self.allowlists[channel]:
                if destination not in self.allowlists[channel]:
                    reason = f"Destination '{destination}' not in allowlist"
                    self._log_event(channel, destination, data_size, user, False, reason)
                    return False, reason

            # Check size limit
            size_limit = self.size_limits.get(channel)
            if size_limit and data_size > size_limit:
                reason = f"Data size {data_size} exceeds limit {size_limit}"
                self._log_event(channel, destination, data_size, user, False, reason)
                return False, reason

            # Check rate limit
            if not self._check_rate_limit(channel):
                reason = f"Rate limit exceeded for {channel.value}"
                self._log_event(channel, destination, data_size, user, False, reason)
                return False, reason

            # All checks passed
            self._log_event(channel, destination, data_size, user, True, "Allowed")
            return True, "Allowed"

    def _check_rate_limit(self, channel: EgressChannel) -> bool:
        """Check if rate limit allows this egress"""
        rate_limit = self.rate_limits.get(channel)
        if not rate_limit:
            return True

        max_count, window = rate_limit
        now = time.time()

        # Get recent events for this channel
        recent_events = self.rate_tracking.get(channel, [])

        # Remove events outside the window
        recent_events = [t for t in recent_events if now - t < window]

        # Check if under limit
        if len(recent_events) >= max_count:
            return False

        # Record this event
        recent_events.append(now)
        self.rate_tracking[channel] = recent_events

        return True

    def _log_event(
        self,
        channel: EgressChannel,
        destination: str,
        data_size: int,
        user: Optional[str],
        allowed: bool,
        reason: str
    ):
        """Log egress event"""
        event = EgressEvent(
            timestamp=time.time(),
            channel=channel,
            destination=destination,
            data_size=data_size,
            user=user,
            allowed=allowed,
            reason=reason
        )

        self.event_history.append(event)

        # Alert on violations
        if not allowed and self.alert_callback:
            self.alert_callback(event)

    def allow_destination(self, channel: EgressChannel, destination: str):
        """Add destination to channel allowlist"""
        with self.lock:
            if channel not in self.allowlists:
                self.allowlists[channel] = set()
            self.allowlists[channel].add(destination)

    def block_destination(self, channel: EgressChannel, destination: str):
        """Add destination to channel blocklist"""
        with self.lock:
            if channel not in self.blocklists:
                self.blocklists[channel] = set()
            self.blocklists[channel].add(destination)

    def remove_from_allowlist(self, channel: EgressChannel, destination: str):
        """Remove destination from allowlist"""
        with self.lock:
            if channel in self.allowlists:
                self.allowlists[channel].discard(destination)

    def remove_from_blocklist(self, channel: EgressChannel, destination: str):
        """Remove destination from blocklist"""
        with self.lock:
            if channel in self.blocklists:
                self.blocklists[channel].discard(destination)

    def get_stats(self) -> Dict:
        """Get egress statistics"""
        with self.lock:
            total_events = len(self.event_history)
            allowed_events = sum(1 for e in self.event_history if e.allowed)
            blocked_events = total_events - allowed_events

            by_channel = {}
            for channel in EgressChannel:
                channel_events = [e for e in self.event_history if e.channel == channel]
                by_channel[channel.value] = {
                    'total': len(channel_events),
                    'allowed': sum(1 for e in channel_events if e.allowed),
                    'blocked': sum(1 for e in channel_events if not e.allowed),
                    'total_bytes': sum(e.data_size for e in channel_events if e.allowed)
                }

            return {
                'total_events': total_events,
                'allowed': allowed_events,
                'blocked': blocked_events,
                'by_channel': by_channel,
                'allowlists': {ch.value: len(dests) for ch, dests in self.allowlists.items()},
                'blocklists': {ch.value: len(dests) for ch, dests in self.blocklists.items()},
            }

    def get_recent_violations(self, limit: int = 10) -> List[EgressEvent]:
        """Get recent policy violations"""
        with self.lock:
            violations = [e for e in self.event_history if not e.allowed]
            return violations[-limit:]

    def clear_history(self):
        """Clear event history"""
        with self.lock:
            self.event_history.clear()
            self.rate_tracking = {channel: [] for channel in EgressChannel}


# Example usage
if __name__ == "__main__":
    guard = EgressGuard()

    # Test size limit
    print("Test 1: Size limit")
    allowed, reason = guard.check_egress(
        EgressChannel.API_RESPONSE,
        destination="client-123",
        data_size=5 * 1024 * 1024,  # 5MB (within 10MB limit)
        user="alice"
    )
    print(f"  5MB API response: {allowed} - {reason}")

    allowed, reason = guard.check_egress(
        EgressChannel.API_RESPONSE,
        destination="client-123",
        data_size=15 * 1024 * 1024,  # 15MB (exceeds 10MB limit)
        user="alice"
    )
    print(f"  15MB API response: {allowed} - {reason}")

    # Test blocklist
    print("\nTest 2: Blocklist")
    guard.block_destination(EgressChannel.FILE_WRITE, "/etc/passwd")
    allowed, reason = guard.check_egress(
        EgressChannel.FILE_WRITE,
        destination="/etc/passwd",
        data_size=1024,
        user="bob"
    )
    print(f"  Write to /etc/passwd: {allowed} - {reason}")

    # Test allowlist
    print("\nTest 3: Allowlist")
    guard.allow_destination(EgressChannel.CHECKPOINT_SAVE, "/app/checkpoints/model.pt")
    allowed, reason = guard.check_egress(
        EgressChannel.CHECKPOINT_SAVE,
        destination="/app/checkpoints/model.pt",
        data_size=500 * 1024 * 1024,
        user="alice"
    )
    print(f"  Save to allowed path: {allowed} - {reason}")

    allowed, reason = guard.check_egress(
        EgressChannel.CHECKPOINT_SAVE,
        destination="/tmp/model.pt",
        data_size=500 * 1024 * 1024,
        user="alice"
    )
    print(f"  Save to non-allowed path: {allowed} - {reason}")

    # Test rate limit
    print("\nTest 4: Rate limit")
    count_limit, window = guard.rate_limits[EgressChannel.LOG_OUTPUT]
    print(f"  Log output limit: {count_limit} per {window}s")

    # Simulate many log outputs
    for i in range(count_limit + 5):
        allowed, reason = guard.check_egress(
            EgressChannel.LOG_OUTPUT,
            destination="stdout",
            data_size=100,
            user="system"
        )
        if not allowed:
            print(f"  Rate limited at {i+1} events")
            break

    # Stats
    print("\nStatistics:")
    stats = guard.get_stats()
    print(f"  Total events: {stats['total_events']}")
    print(f"  Allowed: {stats['allowed']}")
    print(f"  Blocked: {stats['blocked']}")

    # Recent violations
    violations = guard.get_recent_violations(limit=5)
    print(f"\nRecent violations: {len(violations)}")
    for v in violations:
        print(f"  - {v.channel.value} to {v.destination}: {v.reason}")

    print("\n✓ Egress Guard tests passed")
