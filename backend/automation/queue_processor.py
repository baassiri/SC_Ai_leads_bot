"""
Message Queue Processor
Processes scheduled messages and sends them at the right time
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from backend.automation.scheduler import MessageScheduler
from backend.automation.linkedin_message_sender import LinkedInMessageSender
from backend.database.db_manager import db_manager
from backend.credentials_manager import credentials_manager

class QueueProcessor:
    """
    Processes the message queue and sends scheduled messages
    
    Features:
    - Checks queue every 60 seconds
    - Sends messages that are due
    - Updates message status
    - Handles errors and retries
    - Respects rate limits
    """
    
    def __init__(self, check_interval: int = 60):
        """
        Initialize queue processor
        
        Args:
            check_interval: Seconds between queue checks (default: 60)
        """
        self.scheduler = MessageScheduler()
        self.sender = None
        self.check_interval = check_interval
        self.running = False
        
        self.stats = {
            'messages_sent': 0,
            'messages_failed': 0,
            'last_check': None,
            'started_at': None
        }
    
    def start(self, headless: bool = True):
        """Start processing the queue"""
        print("="*60)
        print("🚀 MESSAGE QUEUE PROCESSOR STARTING")
        print("="*60)
        
        # Get LinkedIn credentials
        creds = credentials_manager.get_linkedin_credentials()
        
        if not creds:
            print("❌ LinkedIn credentials not configured!")
            print("   Please configure in the dashboard")
            return False
        
        email = creds.get('email')
        password = creds.get('password')
        
        if not email or not password:
            print("❌ LinkedIn credentials not configured!")
            print("   Please configure in the dashboard")
            return False
        
        # Initialize sender
        self.sender = LinkedInMessageSender(
            email=email,
            password=password,
            headless=headless
        )
        
        # Setup browser and login
        self.sender.setup_driver()
        
        if not self.sender.login():
            print("❌ Failed to login to LinkedIn")
            return False
        
        print("✅ LinkedIn login successful")
        print(f"⏰ Checking queue every {self.check_interval} seconds")
        print(f"📋 Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        self.running = True
        self.stats['started_at'] = datetime.utcnow()
        
        try:
            while self.running:
                self._process_queue()
                
                # Wait before next check
                self.stats['last_check'] = datetime.utcnow()
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print("\n\n⚠️ Stopping queue processor...")
            self.stop()
        
        return True
    
    def stop(self):
        """Stop processing the queue"""
        self.running = False
        
        if self.sender:
            self.sender.close()
        
        print("\n" + "="*60)
        print("📊 QUEUE PROCESSOR SUMMARY")
        print("="*60)
        print(f"✅ Messages sent: {self.stats['messages_sent']}")
        print(f"❌ Messages failed: {self.stats['messages_failed']}")
        
        if self.stats['started_at']:
            duration = datetime.utcnow() - self.stats['started_at']
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            print(f"⏱️ Running time: {hours}h {minutes}m")
        
        print("="*60)
    
    def _process_queue(self):
        """Process pending messages in the queue"""
        # Get pending messages
        pending = self.scheduler.get_pending_messages(limit=10)
        
        if not pending:
            # No messages to send
            return
        
        print(f"\n📬 Found {len(pending)} message(s) ready to send")
        
        for message in pending:
            self._send_message(message)
            
            # Brief pause between messages
            time.sleep(5)
    
    def _send_message(self, message: Dict) -> bool:
        """
        Send a single scheduled message
        
        Args:
            message: Dict with message details
            
        Returns:
            True if sent successfully
        """
        schedule_id = message['schedule_id']
        message_id = message['message_id']
        lead_name = message['lead_name']
        profile_url = message['profile_url']
        content = message['content']
        variant = message['variant']
        
        print(f"\n📤 Sending message to {lead_name} (Variant {variant})...")
        print(f"   Schedule ID: {schedule_id}")
        print(f"   Message ID: {message_id}")
        
        try:
            # Send the connection request
            result = self.sender.send_connection_request(
                profile_url=profile_url,
                message=content,
                lead_name=lead_name
            )
            
            if result['success']:
                # Mark as sent in schedule
                self.scheduler.mark_as_sent(schedule_id)
                
                # Update message status in messages table
                db_manager.update_message_status(
                    message_id=message_id,
                    status='sent',
                    sent_at=datetime.utcnow()
                )
                
                # Log activity
                db_manager.log_activity(
                    activity_type='message_sent',
                    description=f"Sent {variant} variant to {lead_name}",
                    status='success'
                )
                
                self.stats['messages_sent'] += 1
                print(f"   ✅ Message sent successfully!")
                
                return True
            else:
                # Mark as failed
                error_msg = result.get('message', 'Unknown error')
                self.scheduler.mark_as_failed(schedule_id, error_msg)
                
                # Log failure
                db_manager.log_activity(
                    activity_type='message_sent',
                    description=f"Failed to send to {lead_name}",
                    status='failed',
                    error_message=error_msg
                )
                
                self.stats['messages_failed'] += 1
                print(f"   ❌ Failed: {error_msg}")
                
                return False
                
        except Exception as e:
            error_msg = str(e)
            print(f"   ❌ Exception: {error_msg}")
            
            # Mark as failed
            self.scheduler.mark_as_failed(schedule_id, error_msg)
            
            # Log failure
            db_manager.log_activity(
                activity_type='message_sent',
                description=f"Exception sending to {lead_name}",
                status='failed',
                error_message=error_msg
            )
            
            self.stats['messages_failed'] += 1
            
            return False
    
    def get_stats(self) -> Dict:
        """Get processor statistics"""
        queue_stats = self.scheduler.get_schedule_stats()
        
        return {
            'processor': self.stats,
            'queue': queue_stats
        }


# CLI for running the processor
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Message Queue Processor')
    parser.add_argument(
        '--interval', 
        type=int, 
        default=60,
        help='Check interval in seconds (default: 60)'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode'
    )
    
    args = parser.parse_args()
    
    # Create and start processor
    processor = QueueProcessor(check_interval=args.interval)
    processor.start(headless=args.headless)