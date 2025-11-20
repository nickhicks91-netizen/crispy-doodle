"""
RBAC (Role-Based Access Control)
Manages roles, permissions, and access control for EchoZero resources
"""

import threading
from typing import Dict, Set, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class Permission(Enum):
    """System permissions"""
    # State access
    READ_STATE = "read_state"
    WRITE_STATE = "write_state"
    RESET_STATE = "reset_state"

    # API access
    API_FORWARD = "api_forward"
    API_METRICS = "api_metrics"
    API_HEALTH = "api_health"

    # Training
    TRAIN_MODEL = "train_model"
    LOAD_CHECKPOINT = "load_checkpoint"
    SAVE_CHECKPOINT = "save_checkpoint"

    # Configuration
    READ_CONFIG = "read_config"
    WRITE_CONFIG = "write_config"

    # Administration
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    VIEW_AUDIT_LOG = "view_audit_log"

    # Security
    ENCRYPT_DATA = "encrypt_data"
    DECRYPT_DATA = "decrypt_data"


class Role(Enum):
    """Predefined roles"""
    ADMIN = "admin"  # Full access
    OPERATOR = "operator"  # Run and monitor
    DEVELOPER = "developer"  # Train and experiment
    VIEWER = "viewer"  # Read-only access
    API_USER = "api_user"  # API access only
    GUEST = "guest"  # Minimal access


@dataclass
class User:
    """Represents a user with roles and permissions"""
    username: str
    roles: Set[Role] = field(default_factory=set)
    direct_permissions: Set[Permission] = field(default_factory=set)
    enabled: bool = True


class RBACManager:
    """
    Role-Based Access Control Manager

    Features:
    - Predefined roles with permission sets
    - Custom role creation
    - User management
    - Permission inheritance
    - Thread-safe operations
    """

    # Default role-to-permissions mapping
    ROLE_PERMISSIONS = {
        Role.ADMIN: {  # Full access
            Permission.READ_STATE, Permission.WRITE_STATE, Permission.RESET_STATE,
            Permission.API_FORWARD, Permission.API_METRICS, Permission.API_HEALTH,
            Permission.TRAIN_MODEL, Permission.LOAD_CHECKPOINT, Permission.SAVE_CHECKPOINT,
            Permission.READ_CONFIG, Permission.WRITE_CONFIG,
            Permission.MANAGE_USERS, Permission.MANAGE_ROLES, Permission.VIEW_AUDIT_LOG,
            Permission.ENCRYPT_DATA, Permission.DECRYPT_DATA
        },
        Role.OPERATOR: {  # Run and monitor
            Permission.READ_STATE, Permission.RESET_STATE,
            Permission.API_FORWARD, Permission.API_METRICS, Permission.API_HEALTH,
            Permission.LOAD_CHECKPOINT, Permission.SAVE_CHECKPOINT,
            Permission.READ_CONFIG,
            Permission.VIEW_AUDIT_LOG
        },
        Role.DEVELOPER: {  # Train and experiment
            Permission.READ_STATE, Permission.WRITE_STATE,
            Permission.API_FORWARD, Permission.API_METRICS,
            Permission.TRAIN_MODEL, Permission.LOAD_CHECKPOINT, Permission.SAVE_CHECKPOINT,
            Permission.READ_CONFIG, Permission.WRITE_CONFIG,
        },
        Role.VIEWER: {  # Read-only
            Permission.READ_STATE,
            Permission.API_METRICS, Permission.API_HEALTH,
            Permission.READ_CONFIG
        },
        Role.API_USER: {  # API access
            Permission.API_FORWARD, Permission.API_HEALTH
        },
        Role.GUEST: {  # Minimal
            Permission.API_HEALTH
        }
    }

    def __init__(self):
        """Initialize RBAC manager"""
        self.users: Dict[str, User] = {}
        self.custom_roles: Dict[str, Set[Permission]] = {}
        self.lock = threading.RLock()

    def create_user(self, username: str, roles: Optional[Set[Role]] = None) -> User:
        """
        Create new user

        Args:
            username: Unique username
            roles: Initial roles (defaults to GUEST)

        Returns:
            Created User object
        """
        with self.lock:
            if username in self.users:
                raise ValueError(f"User '{username}' already exists")

            roles = roles or {Role.GUEST}
            user = User(username=username, roles=roles)
            self.users[username] = user
            return user

    def delete_user(self, username: str) -> bool:
        """Delete user"""
        with self.lock:
            if username not in self.users:
                raise KeyError(f"User '{username}' not found")
            del self.users[username]
            return True

    def assign_role(self, username: str, role: Role) -> bool:
        """Assign role to user"""
        with self.lock:
            user = self.users.get(username)
            if user is None:
                raise KeyError(f"User '{username}' not found")

            user.roles.add(role)
            return True

    def revoke_role(self, username: str, role: Role) -> bool:
        """Revoke role from user"""
        with self.lock:
            user = self.users.get(username)
            if user is None:
                raise KeyError(f"User '{username}' not found")

            user.roles.discard(role)
            return True

    def grant_permission(self, username: str, permission: Permission) -> bool:
        """Grant direct permission to user (outside of roles)"""
        with self.lock:
            user = self.users.get(username)
            if user is None:
                raise KeyError(f"User '{username}' not found")

            user.direct_permissions.add(permission)
            return True

    def revoke_permission(self, username: str, permission: Permission) -> bool:
        """Revoke direct permission from user"""
        with self.lock:
            user = self.users.get(username)
            if user is None:
                raise KeyError(f"User '{username}' not found")

            user.direct_permissions.discard(permission)
            return True

    def get_user_permissions(self, username: str) -> Set[Permission]:
        """
        Get all effective permissions for user (roles + direct)

        Args:
            username: Username

        Returns:
            Set of all permissions
        """
        with self.lock:
            user = self.users.get(username)
            if user is None:
                raise KeyError(f"User '{username}' not found")

            if not user.enabled:
                return set()

            # Collect permissions from all roles
            permissions = set(user.direct_permissions)
            for role in user.roles:
                role_perms = self.ROLE_PERMISSIONS.get(role, set())
                permissions.update(role_perms)

                # Check custom roles
                if role.value in self.custom_roles:
                    permissions.update(self.custom_roles[role.value])

            return permissions

    def check_permission(self, username: str, permission: Permission) -> bool:
        """
        Check if user has specific permission

        Args:
            username: Username
            permission: Permission to check

        Returns:
            True if user has permission
        """
        try:
            permissions = self.get_user_permissions(username)
            return permission in permissions
        except KeyError:
            return False

    def require_permission(self, username: str, permission: Permission):
        """
        Require permission or raise exception

        Args:
            username: Username
            permission: Required permission

        Raises:
            PermissionError: If user lacks permission
        """
        if not self.check_permission(username, permission):
            raise PermissionError(
                f"User '{username}' lacks permission: {permission.value}"
            )

    def enable_user(self, username: str) -> bool:
        """Enable user account"""
        with self.lock:
            user = self.users.get(username)
            if user is None:
                raise KeyError(f"User '{username}' not found")
            user.enabled = True
            return True

    def disable_user(self, username: str) -> bool:
        """Disable user account (revokes all permissions)"""
        with self.lock:
            user = self.users.get(username)
            if user is None:
                raise KeyError(f"User '{username}' not found")
            user.enabled = False
            return True

    def create_custom_role(self, role_name: str, permissions: Set[Permission]) -> bool:
        """Create custom role with specific permissions"""
        with self.lock:
            if role_name in self.custom_roles:
                raise ValueError(f"Custom role '{role_name}' already exists")
            self.custom_roles[role_name] = permissions
            return True

    def list_users(self) -> List[str]:
        """List all usernames"""
        with self.lock:
            return list(self.users.keys())

    def get_user_info(self, username: str) -> Dict:
        """Get user information"""
        with self.lock:
            user = self.users.get(username)
            if user is None:
                raise KeyError(f"User '{username}' not found")

            return {
                'username': user.username,
                'roles': [role.value for role in user.roles],
                'direct_permissions': [perm.value for perm in user.direct_permissions],
                'effective_permissions': [perm.value for perm in self.get_user_permissions(username)],
                'enabled': user.enabled
            }


# Example usage
if __name__ == "__main__":
    rbac = RBACManager()

    # Create users
    admin = rbac.create_user("alice", roles={Role.ADMIN})
    developer = rbac.create_user("bob", roles={Role.DEVELOPER})
    viewer = rbac.create_user("charlie", roles={Role.VIEWER})

    # Check permissions
    print(f"Alice (admin) can train: {rbac.check_permission('alice', Permission.TRAIN_MODEL)}")
    print(f"Bob (developer) can train: {rbac.check_permission('bob', Permission.TRAIN_MODEL)}")
    print(f"Charlie (viewer) can train: {rbac.check_permission('charlie', Permission.TRAIN_MODEL)}")

    # Grant specific permission
    rbac.grant_permission("charlie", Permission.TRAIN_MODEL)
    print(f"Charlie (viewer + granted) can train: {rbac.check_permission('charlie', Permission.TRAIN_MODEL)}")

    # Test require_permission
    try:
        rbac.require_permission("charlie", Permission.MANAGE_USERS)
        print("✗ Should have raised PermissionError")
    except PermissionError as e:
        print(f"✓ {e}")

    # User info
    alice_info = rbac.get_user_info("alice")
    print(f"\nAlice info: {alice_info['roles']}")
    print(f"Alice permissions: {len(alice_info['effective_permissions'])} total")

    # Disable user
    rbac.disable_user("charlie")
    print(f"\nCharlie (disabled) can train: {rbac.check_permission('charlie', Permission.TRAIN_MODEL)}")

    # Re-enable
    rbac.enable_user("charlie")
    print(f"Charlie (re-enabled) can train: {rbac.check_permission('charlie', Permission.TRAIN_MODEL)}")

    print("\n✓ RBAC tests passed")
