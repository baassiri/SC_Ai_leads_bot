"""
SC AI Lead Generation System - Smart Message Scheduler
Handles intelligent message scheduling with rate limiting and optimal time selection
"""

import sqlite3
from datetime import datetime, timedelta, time
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.config import Config


class MessageScheduler:
    """
    Smart scheduler for LinkedIn messages with:
    - Rate limiting (15 msgs/hour, 50/day)
    - Business hours enforcement
    - AI-optimized send times
    - Queue management
    """
    
    # Rate limits (to avoid LinkedIn bans)
    MAX_MESSAGES_PER_HOUR = 15
    MAX_MESSAGES_PER_DAY = 50
    MIN_DELAY_BETWEEN_MESSAGES = 180  # 3 minutes in seconds
    
    # Business hours (default)
    DEFAULT_START_HOUR = 9  # 9 AM
    DEFAULT_END_HOUR = 18   # 6 PM
    
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = Config.DATABASE_URL.replace('sqlite:///', '')
        self.db_path = db_path
        self._init_schedule_table()
    
    def _init_schedule_table(self):
        """Create message_schedule table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                lead_id INTEGER,
                scheduled_time TIMESTAMP NOT NULL,
                time_zone VARCHAR(50) DEFAULT 'UTC',
                send_window_start TIME,
                send_window_end TIME,
                ai_optimized BOOLEAN DEFAULT FALSE,
                status VARCHAR(20) DEFAULT 'scheduled',
                sent_at TIMESTAMP,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (message_id) REFERENCES messages(id),
                FOREIGN KEY (lead_id) REFERENCES leads(id)
            )
        ''')
        
        # Add indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_scheduled_time 
            ON message_schedule(scheduled_time, status)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_message_schedule_status 
            ON message_schedule(status)
        ''')
        
        conn.commit()
        conn.close()
    
    def schedule_message(self, 
                        message_id: int, 
                        scheduled_time: datetime = None,
                        time_zone: str = 'UTC',
                        send_window: Tuple[time, time] = None,
                        ai_optimize: bool = False,
                        lead_id: int = None) -> int:
        """
        Schedule a message for sending
        
        Args:
            message_id: Message to schedule
            scheduled_time: When to send (None = ASAP)
            time_zone: Timezone for scheduling
            send_window: (start_time, end_time) for sending
            ai_optimize: Let AI pick optimal time
            lead_id: Lead ID for tracking
            
        Returns:
            schedule_id: ID of created schedule entry
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # If no time specified, schedule ASAP within rate limits
        if scheduled_time is None:
            scheduled_time = self._get_next_available_slot()
        else:
            # Adjust to business hours
            scheduled_time = self._adjust_to_business_hours(scheduled_time)
            
            # Check rate limits
            if not self._check_rate_limit(scheduled_time):
                scheduled_time = self._get_next_available_slot(after=scheduled_time)
        
        # Insert schedule
        cursor.execute('''
            INSERT INTO message_schedule (
                message_id, lead_id, scheduled_time, time_zone,
                send_window_start, send_window_end, ai_optimized, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'scheduled')
        ''', (
            message_id,
            lead_id,
            scheduled_time.isoformat(),
            time_zone,
            send_window[0].isoformat() if send_window else None,
            send_window[1].isoformat() if send_window else None,
            ai_optimize
        ))
        
        schedule_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return schedule_id
    
    def schedule_batch(self,
                      message_ids: List[int],
                      start_time: datetime = None,
                      spread_hours: int = 4,
                      ai_optimize: bool = False) -> List[int]:
        """
        Schedule multiple messages spread over time
        
        Args:
            message_ids: List of message IDs to schedule
            start_time: When to start (None = ASAP)
            spread_hours: Hours to spread messages over
            ai_optimize: Use AI optimization
            
        Returns:
            List of schedule IDs
        """
        if not message_ids:
            return []
        
        schedule_ids = []
        
        # Start from specified time or next available slot
        if start_time is None:
            current_time = self._get_next_available_slot()
        else:
            current_time = start_time
        
        # Calculate spacing between messages
        total_minutes = spread_hours * 60
        spacing_minutes = total_minutes // len(message_ids)
        
        # Ensure minimum spacing of 3 minutes
        spacing_minutes = max(spacing_minutes, 3)
        
        for i, message_id in enumerate(message_ids):
            # Calculate send time
            send_time = current_time + timedelta(minutes=i * spacing_minutes)
            
            # Ensure within business hours
            send_time = self._adjust_to_business_hours(send_time)
            
            # Check rate limits
            if not self._check_rate_limit(send_time):
                # Push to next available slot
                send_time = self._get_next_available_slot(after=send_time)
            
            # Schedule the message
            schedule_id = self.schedule_message(
                message_id=message_id,
                scheduled_time=send_time,
                ai_optimize=ai_optimize
            )
            
            schedule_ids.append(schedule_id)
        
        return schedule_ids
    
    def _get_next_available_slot(self, after: datetime = None) -> datetime:
        """Get next available time slot respecting rate limits"""
        if after is None:
            after = datetime.utcnow()
        
        # Check messages scheduled in the next hour
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        one_hour_later = after + timedelta(hours=1)
        
        cursor.execute('''
            SELECT COUNT(*) FROM message_schedule
            WHERE scheduled_time BETWEEN ? AND ?
            AND status = 'scheduled'
        ''', (after.isoformat(), one_hour_later.isoformat()))
        
        count_in_hour = cursor.fetchone()[0]
        conn.close()
        
        # If we're at hourly limit, push to next hour
        if count_in_hour >= self.MAX_MESSAGES_PER_HOUR:
            after = one_hour_later
        
        # Adjust to business hours
        after = self._adjust_to_business_hours(after)
        
        return after
    
    def _adjust_to_business_hours(self, dt: datetime) -> datetime:
        """Adjust datetime to be within business hours (9 AM - 6 PM)"""
        # Convert to time object
        current_time = dt.time()
        
        start_time = time(self.DEFAULT_START_HOUR, 0)
        end_time = time(self.DEFAULT_END_HOUR, 0)
        
        # If before business hours, move to start of business day
        if current_time < start_time:
            dt = dt.replace(hour=self.DEFAULT_START_HOUR, minute=0, second=0)
        
        # If after business hours, move to next business day
        elif current_time >= end_time:
            dt = dt + timedelta(days=1)
            dt = dt.replace(hour=self.DEFAULT_START_HOUR, minute=0, second=0)
        
        # Skip weekends
        while dt.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            dt = dt + timedelta(days=1)
        
        return dt
    
    def _check_rate_limit(self, send_time: datetime) -> bool:
        """Check if we can send at this time without exceeding rate limits"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check hourly limit
        hour_start = send_time.replace(minute=0, second=0, microsecond=0)
        hour_end = hour_start + timedelta(hours=1)
        
        cursor.execute('''
            SELECT COUNT(*) FROM message_schedule
            WHERE scheduled_time BETWEEN ? AND ?
            AND status = 'scheduled'
        ''', (hour_start.isoformat(), hour_end.isoformat()))
        
        hourly_count = cursor.fetchone()[0]
        
        if hourly_count >= self.MAX_MESSAGES_PER_HOUR:
            conn.close()
            return False
        
        # Check daily limit
        day_start = send_time.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        cursor.execute('''
            SELECT COUNT(*) FROM message_schedule
            WHERE scheduled_time BETWEEN ? AND ?
            AND status = 'scheduled'
        ''', (day_start.isoformat(), day_end.isoformat()))
        
        daily_count = cursor.fetchone()[0]
        conn.close()
        
        return daily_count < self.MAX_MESSAGES_PER_DAY
    
    def get_pending_messages(self, limit: int = 100) -> List[Dict]:
        """Get messages scheduled for sending (scheduled_time <= now)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        now = datetime.utcnow()
        
        cursor.execute('''
            SELECT 
                ms.id as schedule_id,
                ms.message_id,
                ms.scheduled_time,
                ms.ai_optimized,
                m.content,
                m.variant,
                m.lead_id,
                l.name as lead_name,
                l.profile_url
            FROM message_schedule ms
            JOIN messages m ON ms.message_id = m.id
            JOIN leads l ON m.lead_id = l.id
            WHERE ms.status = 'scheduled'
            AND ms.scheduled_time <= ?
            ORDER BY ms.scheduled_time
            LIMIT ?
        ''', (now.isoformat(), limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def mark_as_sent(self, schedule_id: int):
        """Mark a scheduled message as sent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE message_schedule
            SET status = 'sent',
                sent_at = ?,
                updated_at = ?
            WHERE id = ?
        ''', (datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), schedule_id))
        
        conn.commit()
        conn.close()
    
    def mark_as_failed(self, schedule_id: int, error_message: str):
        """Mark a scheduled message as failed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE message_schedule
            SET status = 'failed',
                error_message = ?,
                retry_count = retry_count + 1,
                updated_at = ?
            WHERE id = ?
        ''', (error_message, datetime.utcnow().isoformat(), schedule_id))
        
        conn.commit()
        conn.close()
    
    def get_schedule_stats(self) -> Dict:
        """Get scheduling statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total scheduled
        cursor.execute("SELECT COUNT(*) FROM message_schedule WHERE status = 'scheduled'")
        stats['scheduled'] = cursor.fetchone()[0]
        
        # Total sent
        cursor.execute("SELECT COUNT(*) FROM message_schedule WHERE status = 'sent'")
        stats['sent'] = cursor.fetchone()[0]
        
        # Total failed
        cursor.execute("SELECT COUNT(*) FROM message_schedule WHERE status = 'failed'")
        stats['failed'] = cursor.fetchone()[0]
        
        # Next scheduled
        cursor.execute('''
            SELECT MIN(scheduled_time) FROM message_schedule 
            WHERE status = 'scheduled'
        ''')
        next_time = cursor.fetchone()[0]
        stats['next_scheduled'] = next_time if next_time else None
        
        # Today's sent count
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
        cursor.execute('''
            SELECT COUNT(*) FROM message_schedule
            WHERE status = 'sent'
            AND sent_at >= ?
        ''', (today_start.isoformat(),))
        stats['sent_today'] = cursor.fetchone()[0]
        
        conn.close()
        
        return stats
    
    def cancel_scheduled_message(self, schedule_id: int) -> bool:
        """Cancel a scheduled message"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE message_schedule
            SET status = 'cancelled',
                updated_at = ?
            WHERE id = ? AND status = 'scheduled'
        ''', (datetime.utcnow().isoformat(), schedule_id))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def reschedule_message(self, schedule_id: int, new_time: datetime) -> bool:
        """Reschedule a message to a new time"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Adjust to business hours
        new_time = self._adjust_to_business_hours(new_time)
        
        cursor.execute('''
            UPDATE message_schedule
            SET scheduled_time = ?,
                updated_at = ?
            WHERE id = ? AND status = 'scheduled'
        ''', (new_time.isoformat(), datetime.utcnow().isoformat(), schedule_id))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0


# Singleton instance
scheduler = MessageScheduler()