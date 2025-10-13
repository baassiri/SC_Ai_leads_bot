"""
SC AI Lead Generation System - Queue Processor
Automatically sends scheduled messages at the right time
"""

import time
import sqlite3
from datetime import datetime
from typing import Dict
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.automation.scheduler import scheduler
from backend.database.db_manager import db_manager
from backend.automation.linkedin_message_sender import LinkedInMessageSender


class QueueProcessor:
    """
    Process message queue and send scheduled messages
    
    Features:
    - Runs continuously in background
    - Checks for pending messages every minute
    - Sends messages at scheduled time
    - Handles errors and retries
    - Logs all activity
    """
    
    def __init__(self, check_interval: int = 60):
        """
        Initialize queue processor
        
        Args:
            check_interval: Seconds between queue checks (default: 60)
        """
        self.check_interval = check_interval
        self.running = False
        self.sender = None
        
        # Stats
        self.stats = {
            'messages_sent': 0,
            'messages_failed': 0,
            'started_at': None,
            'last_check': None
        }
    
    def start(self, headless: bool = True):
        """
        Start the queue processor
        
        Args:
            headless: Run browser in headless mode
        """
        print("\n" + "="*60)
        print("🚀 STARTING QUEUE PROCESSOR")
        print("="*60)
        print(f"Check interval: {self.check_interval} seconds")
        print(f"Headless mode: {headless}")
        print(f"Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        # Initialize LinkedIn sender
        try:
            self.sender = LinkedInMessageSender(headless=headless)
            print("✅ LinkedIn sender initialized")
        except Exception as e:
            print(f"❌ Failed to initialize sender: {str(e)}")
            return
        
        self.running = True
        self.stats['started_at'] = datetime.utcnow()
        
        try:
            while self.running:
                self._process_queue()
                
                # Wait before next check
                self.stats['last_check'] = datetime.utcnow()
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping queue processor...")
            self.stop()
        except Exception as e:
            print(f"\n❌ Error in queue processor: {str(e)}")
            self.stop()
    
    def stop(self):
        """Stop the queue processor"""
        self.running = False
        
        if self.sender:
            self.sender.close()
        
        self._print_summary()
    
    def _print_summary(self):
        """Print final statistics"""
        print("\n" + "="*60)
        print("📊 QUEUE PROCESSOR SUMMARY")
        print("="*60)
        print(f"✅ Messages sent: {self.stats['messages_sent']}")
        print(f"❌ Messages failed: {self.stats['messages_failed']}")
        
        if self.stats['started_at']:
            duration = datetime.utcnow() - self.stats['started_at']
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            print(f"⏱️  Running time: {hours}h {minutes}m")
        
        print("="*60)
    
    def _process_queue(self):
        """Process pending messages in the queue"""
        # Get pending messages
        pending = scheduler.get_pending_messages(limit=10)
        
        if not pending:
            # No messages to send
            print(f"⏰ [{datetime.utcnow().strftime('%H:%M:%S')}] No messages ready to send...")
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
                scheduler.mark_as_sent(schedule_id)
                
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
                error_msg = result.get('error', 'Unknown error')
                scheduler.mark_as_failed(schedule_id, error_msg)
                
                # Log failure
                db_manager.log_activity(
                    activity_type='message_failed',
                    description=f"Failed to send to {lead_name}: {error_msg}",
                    status='failed'
                )
                
                self.stats['messages_failed'] += 1
                print(f"   ❌ Failed: {error_msg}")
                return False
                
        except Exception as e:
            # Mark as failed
            error_msg = str(e)
            scheduler.mark_as_failed(schedule_id, error_msg)
            
            # Log error
            db_manager.log_activity(
                activity_type='message_error',
                description=f"Error sending to {lead_name}: {error_msg}",
                status='failed'
            )
            
            self.stats['messages_failed'] += 1
            print(f"   ❌ Error: {error_msg}")
            return False
    
    def process_once(self):
        """Process queue once (for testing)"""
        print("\n🧪 Processing queue once...")
        self._process_queue()
        self._print_summary()


# CLI for running queue processor
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Message Queue Processor')
    parser.add_argument('--interval', type=int, default=60, 
                       help='Check interval in seconds (default: 60)')
    parser.add_argument('--headless', action='store_true',
                       help='Run browser in headless mode')
    parser.add_argument('--test', action='store_true',
                       help='Process queue once and exit (testing mode)')
    
    args = parser.parse_args()
    
    processor = QueueProcessor(check_interval=args.interval)
    
    if args.test:
        # Test mode - process once
        processor.process_once()
    else:
        # Normal mode - run continuously
        processor.start(headless=args.headless)