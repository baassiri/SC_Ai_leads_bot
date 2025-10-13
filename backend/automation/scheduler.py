"""
Smart Message Scheduler
Handles intelligent message scheduling with rate limiting and optimal time selection
"""

import sqlite3
from datetime import datetime, timedelta, time
from typing import List, Dict, Optional, Tuple
import pytz
from collections import defaultdict
import random

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
    
    def __init__(self, db_path='data/database.db'):
        self.db_path = db_path
    
    def schedule_message(self, message_id: int, 
                        scheduled_time: datetime = None,
                        time_zone: str = 'UTC',
                        send_window: Tuple[time, time] = None,
                        ai_optimize: bool = False) -> int:
        """
        Schedule a message for sending
        
        Args:
            message_id: Message to schedule
            scheduled_time: When to send (None = ASAP)
            time_zone: Timezone for scheduling
            send_window: (start_time, end_time) for sending
            ai_optimize: Let AI pick optimal time
            
        Returns:
            schedule_id: ID of created schedule entry
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # If no time specified, schedule ASAP within rate limits
        if scheduled_time is None:
            scheduled_time = self._get_next_available_slot()
        
        # If AI optimize, adjust time based on lead activity
        if ai_optimize:
            scheduled_time = self._optimize_send_time(message_id, scheduled_time)
        
        # Extract window times
        window_start = send_window[0] if send_window else None
        window_end = send_window[1] if send_window else None
        
        cursor.execute('''
            INSERT INTO message_schedule 
            (message_id, scheduled_time, time_zone, send_window_start, 
             send_window_end, ai_optimized, status)
            VALUES (?, ?, ?, ?, ?, ?, 'scheduled')
        ''', (
            message_id, 
            scheduled_time,
            time_zone,
            window_start.strftime('%H:%M:%S') if window_start else None,
            window_end.strftime('%H:%M:%S') if window_end else None,
            ai_optimize
        ))
        
        schedule_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"📅 Scheduled message {message_id} for {scheduled_time}")
        
        return schedule_id
    
    def schedule_batch(self, message_ids: List[int],
                      start_time: datetime = None,
                      spread_hours: int = 8,
                      ai_optimize: bool = True) -> List[int]:
        """
        Schedule multiple messages intelligently across time
        
        Args:
            message_ids: List of message IDs to schedule
            start_time: When to start sending (None = now)
            spread_hours: Hours to spread messages across
            ai_optimize: Use AI to pick optimal times
            
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
        
        print(f"\n📅 Scheduling {len(message_ids)} messages...")
        print(f"   Start: {current_time}")
        print(f"   Spread: {spread_hours} hours")
        print(f"   AI Optimize: {ai_optimize}")
        
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
            
            if (i + 1) % 10 == 0:
                print(f"   ✅ Scheduled {i + 1}/{len(message_ids)} messages")
        
        print(f"✅ All {len(message_ids)} messages scheduled!")
        
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
        ''', (after, one_hour_later))
        
        count_in_hour = cursor.fetchone()[0]
        
        # If we're at hourly limit, push to next hour
        if count_in_hour >= self.MAX_MESSAGES_PER_HOUR:
            after = one_hour_later
        
        # Adjust to business hours
        after = self._adjust_to_business_hours(after)
        
        conn.close()
        
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
        ''', (hour_start, hour_end))
        
        hourly_count = cursor.fetchone()[0]
        
        # Check daily limit
        day_start = send_time.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        cursor.execute('''
            SELECT COUNT(*) FROM message_schedule
            WHERE scheduled_time BETWEEN ? AND ?
            AND status = 'scheduled'
        ''', (day_start, day_end))
        
        daily_count = cursor.fetchone()[0]
        
        conn.close()
        
        # Check both limits
        within_hourly = hourly_count < self.MAX_MESSAGES_PER_HOUR
        within_daily = daily_count < self.MAX_MESSAGES_PER_DAY
        
        return within_hourly and within_daily
    
    def _optimize_send_time(self, message_id: int, base_time: datetime) -> datetime:
        """
        Use AI to pick optimal send time based on lead activity
        
        For now, uses simple heuristics:
        - Mid-morning (10-11 AM) - people check LinkedIn after settling in
        - Mid-afternoon (2-3 PM) - post-lunch LinkedIn check
        - Avoid early morning, lunch, late afternoon
        """
        hour = base_time.hour
        
        # Optimal sending windows (in order of preference)
        optimal_hours = [10, 11, 14, 15, 9, 16]
        
        # If already in optimal window, keep it
        if hour in optimal_hours:
            return base_time
        
        # Otherwise, adjust to nearest optimal hour
        # Pick randomly from top 2 optimal hours to spread load
        best_hour = random.choice(optimal_hours[:2])
        
        optimized_time = base_time.replace(
            hour=best_hour,
            minute=random.randint(0, 59)  # Random minute for variation
        )
        
        return self._adjust_to_business_hours(optimized_time)
    
    def get_pending_messages(self, limit: int = 50) -> List[Dict]:
        """Get messages ready to be sent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.utcnow()
        
        cursor.execute('''
            SELECT 
                ms.id as schedule_id,
                ms.message_id,
                ms.scheduled_time,
                ms.status,
                m.content,
                m.lead_id,
                m.variant,
                l.name as lead_name,
                l.profile_url
            FROM message_schedule ms
            JOIN messages m ON ms.message_id = m.id
            JOIN leads l ON m.lead_id = l.id
            WHERE ms.status = 'scheduled'
            AND ms.scheduled_time <= ?
            ORDER BY ms.scheduled_time ASC
            LIMIT ?
        ''', (now, limit))
        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        messages = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        
        return messages
    
    def mark_as_sent(self, schedule_id: int, sent_at: datetime = None):
        """Mark a scheduled message as sent"""
        if sent_at is None:
            sent_at = datetime.utcnow()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE message_schedule
            SET status = 'sent', sent_at = ?, updated_at = ?
            WHERE id = ?
        ''', (sent_at, datetime.utcnow(), schedule_id))
        
        conn.commit()
        conn.close()
    
    def mark_as_failed(self, schedule_id: int, error_message: str):
        """Mark a scheduled message as failed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current retry count
        cursor.execute('''
            SELECT retry_count, max_retries FROM message_schedule
            WHERE id = ?
        ''', (schedule_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return
        
        retry_count, max_retries = result
        retry_count += 1
        
        # If under max retries, reschedule
        if retry_count < max_retries:
            new_time = datetime.utcnow() + timedelta(minutes=30)
            
            cursor.execute('''
                UPDATE message_schedule
                SET retry_count = ?,
                    error_message = ?,
                    last_error_at = ?,
                    scheduled_time = ?,
                    updated_at = ?
                WHERE id = ?
            ''', (retry_count, error_message, datetime.utcnow(), 
                  new_time, datetime.utcnow(), schedule_id))
            
            print(f"⚠️ Message {schedule_id} will retry at {new_time}")
        else:
            # Max retries exceeded, mark as permanently failed
            cursor.execute('''
                UPDATE message_schedule
                SET status = 'failed',
                    retry_count = ?,
                    failed_at = ?,
                    error_message = ?,
                    updated_at = ?
                WHERE id = ?
            ''', (retry_count, datetime.utcnow(), error_message, 
                  datetime.utcnow(), schedule_id))
            
            print(f"❌ Message {schedule_id} failed permanently after {max_retries} retries")
        
        conn.commit()
        conn.close()
    
    def get_schedule_stats(self) -> Dict:
        """Get scheduling statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count by status
        cursor.execute('''
            SELECT status, COUNT(*) as count
            FROM message_schedule
            GROUP BY status
        ''')
        
        stats = {
            'scheduled': 0,
            'sent': 0,
            'failed': 0,
            'total': 0
        }
        
        for status, count in cursor.fetchall():
            stats[status] = count
            stats['total'] += count
        
        # Get next scheduled message
        cursor.execute('''
            SELECT scheduled_time FROM message_schedule
            WHERE status = 'scheduled'
            ORDER BY scheduled_time ASC
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        stats['next_send'] = result[0] if result else None
        
        # Messages in next hour
        now = datetime.utcnow()
        one_hour = now + timedelta(hours=1)
        
        cursor.execute('''
            SELECT COUNT(*) FROM message_schedule
            WHERE status = 'scheduled'
            AND scheduled_time BETWEEN ? AND ?
        ''', (now, one_hour))
        
        stats['next_hour'] = cursor.fetchone()[0]
        
        # Messages today
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        cursor.execute('''
            SELECT COUNT(*) FROM message_schedule
            WHERE status = 'scheduled'
            AND scheduled_time BETWEEN ? AND ?
        ''', (today_start, today_end))
        
        stats['today'] = cursor.fetchone()[0]
        
        conn.close()
        
        return stats


# CLI for testing
if __name__ == '__main__':
    print("🧪 Testing Message Scheduler\n")
    
    scheduler = MessageScheduler()
    
    # Test: Get stats
    print("📊 Current Schedule Stats:")
    stats = scheduler.get_schedule_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ Scheduler initialized successfully!")