"""
User database model.
"""

from dataclasses import dataclass


@dataclass
class User:
    """User model."""
    user_id: int
    group_id: int
    warnings: str = "[]"
    xp: int = 0
    level: int = 0
