"""
Group database model.
"""

from dataclasses import dataclass


@dataclass
class Group:
    """Group model."""
    group_id: int
    config: str = "{}"
