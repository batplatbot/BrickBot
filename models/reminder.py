"""
Reminder database model.
"""

from dataclasses import dataclass


@dataclass
class Reminder:
    """Reminder model."""
    id: int
    user_id: int
    chat_id: int
    message: str
    remind_at: str
    executed: bool = False
