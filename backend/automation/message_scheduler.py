"""
SC AI Lead Generation System - Message Scheduler
Handles scheduled sending of approved messages with rate limiting
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
import time

sys.path.append(str(Path(__file__).parent.parent))

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from backend.database.db_manager import db_manager


class MessageScheduler:
    """Scheduler for sending LinkedIn messages with rate limiting"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        
        # Rate limiting settings
        self.max_messages_per_hour = 15
        self.max_messages_per_day = 50
        self.messages_sent_today = 0
        self.messages_sent_this_hour = 0
        self.last_reset_hour = datetime.now().hour
        self.last_reset_day = datetime.now().date()
        
        # Business hours (9 AM - 6 PM)
        self.business_hours_start = 9
        self.business_hours_end = 18
    
    def start(self):
        """Start the scheduler"""
        if not self.is_running:
            # Schedule the message processor to run every 5 minutes
            self.scheduler.add_job(
                self.process_message_queue,
                'interval',
                minutes=5,
                id='message_processor'
            )
            
            # Schedule hourly rate limit reset
            self.scheduler.add_job(
                self.reset_hourly_counter,
                'interval',
                hours=1,
                id='hourly_reset'
            )
            
            # Schedule daily rate limit reset at midnight
            self.scheduler.add_job(
                self.reset_daily_counter,
                CronTrigger(hour=0, minute=0),
                id='daily_reset'
            )
            
            self.scheduler.start()
            self.is_running = True
            
            print("✅ Message scheduler started")
            print(f"   - Max {self.max_messages_per_hour} messages/hour")
            print(f"   - Max {self.max_messages_per_day} messages/day")
            print(f"   - Business hours: {self.business_hours_start}:00 - {self.business_hours_end}:00")
    
    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            print("⏹️ Message scheduler stopped")
    
    def process_message_queue(self):
        """Process approved messages waiting to be sent"""
        
        # Check if we're in business hours
        current_hour = datetime.now().hour
        if not self.is_business_hours():
            print(f"⏰ Outside business hours ({current_hour}:00), skipping message processing")
            return
        
        # Check rate limits
        if self.messages_sent_this_hour >= self.max_messages_per_hour:
            print(f"⚠️ Hourly rate limit reached ({self.messages_sent_this_hour}/{self.max_messages_per_hour})")
            return
        
        if self.messages_sent_today >= self.max_messages_per_day:
            print(f"⚠️ Daily rate limit reached ({self.messages_sent_today}/{self.max_messages_per_day})")
            return
        
        # Get approved messages
        messages_to_send = self.get_messages_to_send()
        
        if not messages_to_send:
            print("📭 No messages in queue")
            return
        
        print(f"\n📬 Processing {len(messages_to_send)} messages...")
        
        for message in messages_to_send:
            # Check if we've hit limits
            if self.messages_sent_this_hour >= self.max_messages_per_hour:
                print(f"⚠️ Hourly limit reached, stopping for now")
                break
            
            if self.messages_sent_today >= self.max_messages_per_day:
                print(f"⚠️ Daily limit reached, stopping for now")
                break
            
            # Send the message
            success = self.send_message(message)
            
            if success:
                self.messages_sent_this_hour += 1
                self.messages_sent_today += 1
                
                print(f"✅ Sent: {message['lead_name']} (Variant {message['variant']})")
                print(f"   Rate: {self.messages_sent_this_hour}/{self.max_messages_per_hour} hour, " +
                      f"{self.messages_sent_today}/{self.max_messages_per_day} day")
                
                # Add delay between messages (3-8 seconds for human-like behavior)
                import random
                delay = random.uniform(3, 8)
                time.sleep(delay)
            else:
                print(f"❌ Failed to send: {message['lead_name']}")
    
    def get_messages_to_send(self) -> List[Dict]:
        """Get approved messages ready to send"""
        
        # Calculate how many we can send
        remaining_this_hour = self.max_messages_per_hour - self.messages_sent_this_hour
        remaining_today = self.max_messages_per_day - self.messages_sent_today
        limit = min(remaining_this_hour, remaining_today, 10)  # Max 10 at a time
        
        if limit <= 0:
            return []
        
        # Get approved messages from database
        messages = db_manager.get_pending_messages(limit=limit)
        
        return messages
    
    def send_message(self, message: Dict) -> bool:
        """
        Send a single message via LinkedIn
        
        For now, this is a MOCK implementation
        In production, this would use the LinkedIn automation
        """
        
        try:
            # TODO: Integrate with LinkedIn automation
            # For now, just mark as sent in database
            
            success = db_manager.update_message_status(
                message_id=message['id'],
                new_status='sent'
            )
            
            if success:
                # Log the activity
                db_manager.log_activity(
                    activity_type='message_sent',
                    description=f"📤 Sent message to {message['lead_name']} (Variant {message['variant']})",
                    lead_id=message['lead_id'],
                    status='success'
                )
            
            return success
            
        except Exception as e:
            print(f"Error sending message: {str(e)}")
            
            # Mark as failed
            db_manager.update_message_status(
                message_id=message['id'],
                new_status='failed'
            )
            
            # Log the error
            db_manager.log_activity(
                activity_type='message_send_failed',
                description=f"❌ Failed to send message to {message['lead_name']}",
                lead_id=message['lead_id'],
                status='error',
                error_message=str(e)
            )
            
            return False
    
    def is_business_hours(self) -> bool:
        """Check if current time is within business hours"""
        current_hour = datetime.now().hour
        return self.business_hours_start <= current_hour < self.business_hours_end
    
    def reset_hourly_counter(self):
        """Reset hourly message counter"""
        current_hour = datetime.now().hour
        
        if current_hour != self.last_reset_hour:
            print(f"🔄 Resetting hourly counter (was {self.messages_sent_this_hour})")
            self.messages_sent_this_hour = 0
            self.last_reset_hour = current_hour
    
    def reset_daily_counter(self):
        """Reset daily message counter"""
        current_date = datetime.now().date()
        
        if current_date != self.last_reset_day:
            print(f"🔄 Resetting daily counter (was {self.messages_sent_today})")
            self.messages_sent_today = 0
            self.last_reset_day = current_date
    
    def schedule_message(self, message_id: int, send_at: datetime):
        """
        Schedule a specific message to be sent at a specific time
        
        Args:
            message_id: ID of the message to send
            send_at: DateTime when to send the message
        """
        
        job_id = f"message_{message_id}"
        
        self.scheduler.add_job(
            self.send_specific_message,
            DateTrigger(run_date=send_at),
            args=[message_id],
            id=job_id
        )
        
        print(f"📅 Scheduled message {message_id} for {send_at.strftime('%Y-%m-%d %H:%M')}")
    
    def send_specific_message(self, message_id: int):
        """Send a specific message by ID"""
        
        # Get message from database
        message = db_manager.get_message_by_id(message_id)
        
        if not message:
            print(f"❌ Message {message_id} not found")
            return
        
        # Check rate limits
        if self.messages_sent_this_hour >= self.max_messages_per_hour:
            print(f"⚠️ Rate limit reached, rescheduling message {message_id}")
            # Reschedule for next hour
            next_send = datetime.now() + timedelta(hours=1)
            self.schedule_message(message_id, next_send)
            return
        
        # Send the message
        self.send_message(message)
    
    def get_status(self) -> Dict:
        """Get scheduler status"""
        return {
            'running': self.is_running,
            'messages_sent_hour': self.messages_sent_this_hour,
            'messages_sent_day': self.messages_sent_today,
            'max_per_hour': self.max_messages_per_hour,
            'max_per_day': self.max_messages_per_day,
            'in_business_hours': self.is_business_hours(),
            'pending_messages': len(self.get_messages_to_send())
        }


# Singleton instance
message_scheduler = MessageScheduler()


# Helper functions
def start_scheduler():
    """Start the message scheduler"""
    message_scheduler.start()


def stop_scheduler():
    """Stop the message scheduler"""
    message_scheduler.stop()


def get_scheduler_status():
    """Get scheduler status"""
    return message_scheduler.get_status()


if __name__ == "__main__":
    # Test the scheduler
    print("\n" + "="*60)
    print("🧪 MESSAGE SCHEDULER TEST")
    print("="*60)
    
    print("\nStarting scheduler...")
    message_scheduler.start()
    
    print("\nScheduler status:")
    status = message_scheduler.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print("\nScheduler will run in background. Press Ctrl+C to stop.")
    
    try:
        # Keep running
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n\nStopping scheduler...")
        message_scheduler.stop()
        print("✅ Scheduler stopped")