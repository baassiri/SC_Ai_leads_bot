"""
SC AI Lead Generation System - Database Package
This file makes the database folder a Python package
"""

# Import commonly used database components for easier access
from backend.database.models import (
    Base,
    User,
    Persona,
    Lead,
    Message,
    Campaign,
    Response,
    ActivityLog
)

from backend.database.db_manager import DatabaseManager

__all__ = [
    'Base',
    'User',
    'Persona',
    'Lead',
    'Message',
    'Campaign',
    'Response',
    'ActivityLog',
    'DatabaseManager'
]