"""
SC AI Lead Generation System - AI Engine Package
AI-powered lead scoring and message generation
"""

from .message_generator import MessageGenerator, generate_connection_message, generate_followup_message

__all__ = [
    'MessageGenerator',
    'generate_connection_message', 
    'generate_followup_message'
]