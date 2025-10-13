"""
Lead Activity Timeline
Visual timeline of all interactions with a lead
"""

import sqlite3
from datetime import datetime
from typing import List, Dict
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.config import Config


class LeadTimeline:
    """
    Generate comprehensive timeline of lead activities
    """
    
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = Config.DATABASE_URL.replace('sqlite:///', '')
        self.db_path = db_path
    
    def get_timeline(self, lead_id: int) -> List[Dict]:
        """
        Get complete timeline for a lead
        
        Returns list of timeline events sorted chronologically
        """
        events = []
        
        # Add lead creation
        events.extend(self._get_lead_creation(lead_id))
        
        # Add scoring events
        events.extend(self._get_scoring_events(lead_id))
        
        # Add message events
        events.extend(self._get_message_events(lead_id))
        
        # Add schedule events
        events.extend(self._get_schedule_events(lead_id))
        
        # Add status changes
        events.extend(self._get_status_changes(lead_id))
        
        # Sort by timestamp
        events.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return events
    
    def _get_lead_creation(self, lead_id: int) -> List[Dict]:
        """Get lead creation event"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT created_at, name, title, company
            FROM leads WHERE id = ?
        """, (lead_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return []
        
        return [{
            'type': 'lead_created',
            'timestamp': row['created_at'],
            'icon': 'user-plus',
            'color': 'blue',
            'title': 'Lead Added',
            'description': f"{row['name']} ({row['title']} at {row['company']}) added to system"
        }]
    
    def _get_scoring_events(self, lead_id: int) -> List[Dict]:
        """Get AI scoring events"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT created_at, description
            FROM activity_logs
            WHERE activity_type = 'score'
            AND lead_id = ?
            ORDER BY created_at DESC
        """, (lead_id,))
        
        events = []
        for row in cursor.fetchall():
            events.append({
                'type': 'scored',
                'timestamp': row['created_at'],
                'icon': 'star',
                'color': 'purple',
                'title': 'AI Scored Lead',
                'description': row['description']
            })
        
        conn.close()
        return events
    
    def _get_message_events(self, lead_id: int) -> List[Dict]:
        """Get message generation and sending events"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                id,
                variant,
                status,
                created_at,
                sent_at
            FROM messages
            WHERE lead_id = ?
            ORDER BY created_at DESC
        """, (lead_id,))
        
        events = []
        for row in cursor.fetchall():
            # Message generated
            events.append({
                'type': 'message_generated',
                'timestamp': row['created_at'],
                'icon': 'edit',
                'color': 'gray',
                'title': f'Variant {row["variant"]} Generated',
                'description': f'AI created message variant {row["variant"]}'
            })
            
            # Message sent
            if row['sent_at']:
                events.append({
                    'type': 'message_sent',
                    'timestamp': row['sent_at'],
                    'icon': 'send',
                    'color': 'green',
                    'title': f'Variant {row["variant"]} Sent',
                    'description': f'Message sent via LinkedIn'
                })
        
        conn.close()
        return events
    
    def _get_schedule_events(self, lead_id: int) -> List[Dict]:
        """Get message scheduling events"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                scheduled_time,
                status,
                created_at
            FROM message_schedule
            WHERE lead_id = ?
            ORDER BY created_at DESC
        """, (lead_id,))
        
        events = []
        for row in cursor.fetchall():
            events.append({
                'type': 'scheduled',
                'timestamp': row['created_at'],
                'icon': 'calendar',
                'color': 'yellow',
                'title': 'Message Scheduled',
                'description': f'Scheduled for {row["scheduled_time"]}'
            })
        
        conn.close()
        return events
    
    def _get_status_changes(self, lead_id: int) -> List[Dict]:
        """Get lead status change events"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT created_at, description, activity_type
            FROM activity_logs
            WHERE lead_id = ?
            AND activity_type IN ('lead_status_changed', 'lead_replied', 'meeting_booked')
            ORDER BY created_at DESC
        """, (lead_id,))
        
        events = []
        for row in cursor.fetchall():
            icon = 'check-circle'
            color = 'green'
            title = 'Status Changed'
            
            if row['activity_type'] == 'lead_replied':
                icon = 'message-circle'
                color = 'blue'
                title = 'Lead Replied!'
            elif row['activity_type'] == 'meeting_booked':
                icon = 'calendar-check'
                color = 'green'
                title = 'Meeting Booked!'
            
            events.append({
                'type': row['activity_type'],
                'timestamp': row['created_at'],
                'icon': icon,
                'color': color,
                'title': title,
                'description': row['description']
            })
        
        conn.close()
        return events
    
    def get_summary(self, lead_id: int) -> Dict:
        """Get timeline summary stats"""
        timeline = self.get_timeline(lead_id)
        
        return {
            'total_events': len(timeline),
            'messages_generated': len([e for e in timeline if e['type'] == 'message_generated']),
            'messages_sent': len([e for e in timeline if e['type'] == 'message_sent']),
            'replies_received': len([e for e in timeline if e['type'] == 'lead_replied']),
            'last_activity': timeline[0]['timestamp'] if timeline else None
        }


# Singleton
timeline_manager = LeadTimeline()