"""
Warning database model.
"""

from dataclasses import dataclass


@dataclass
class Warning:
    """Warning model."""
    user_id: int
    group_id: int
    moderator_id: int
    reason: str
    timestamp: str
