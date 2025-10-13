"""
Queue Processor - Sends scheduled messages automatically
"""

import time
import sqlite3
from datetime import datetime
from typing import Dict
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.config import Config
from backend.credentials_manager import credentials_manager


class QueueProcessor:
    
    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self.running = False
        self.sender = None
        self.db_path = Config.DATABASE_URL.replace('sqlite:///', '')
        
        self.stats = {
            'messages_sent': 0,
            'messages_failed': 0,
            'started_at': None,
            'last_check': None
        }
    
    def start(self, headless: bool = True):
        print("\n" + "="*60)
        print("🚀 STARTING QUEUE PROCESSOR")
        print("="*60)
        print(f"Check interval: {self.check_interval} seconds")
        print(f"Headless mode: {headless}")
        print(f"Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        # Initialize LinkedIn sender
        if not self._init_sender(headless):
            return
        
        self.running = True
        self.stats['started_at'] = datetime.now()
        
        try:
            while self.running:
                self._process_queue()
                self.stats['last_check'] = datetime.now()
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping queue processor...")
            self.stop()
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            self.stop()
    
    def _init_sender(self, headless: bool = True):
        """Initialize LinkedIn sender"""
        try:
            from backend.automation.linkedin_message_sender import LinkedInMessageSender
            
            creds = credentials_manager.get_linkedin_credentials()
            if not creds:
                print("❌ No LinkedIn credentials found!")
                return False
            
            self.sender = LinkedInMessageSender(
                email=creds['email'],
                password=creds['password'],
                headless=headless
            )
            self.sender.start_session()
            print("✅ LinkedIn sender initialized\n")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize sender: {str(e)}")
            return False
    
    def stop(self):
        self.running = False
        
        if self.sender:
            self.sender.close_session()
        
        self._print_summary()
    
    def _print_summary(self):
        print("\n" + "="*60)
        print("📊 SUMMARY")
        print("="*60)
        print(f"✅ Sent: {self.stats['messages_sent']}")
        print(f"❌ Failed: {self.stats['messages_failed']}")
        
        if self.stats['started_at']:
            duration = datetime.now() - self.stats['started_at']
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            print(f"⏱️  Running time: {hours}h {minutes}m")
        
        print("="*60)
    
    def _process_queue(self):
        # Get pending messages
        pending = self._get_pending_messages()
        
        if not pending:
            print(f"⏰ [{datetime.now().strftime('%H:%M:%S')}] No messages ready...")
            return
        
        print(f"\n📬 Found {len(pending)} message(s) ready to send")
        
        for message in pending:
            self._send_message(message)
            time.sleep(5)  # Pause between messages
    
    def _get_pending_messages(self, limit: int = 10):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        now = datetime.now()
        
        cursor.execute('''
            SELECT 
                ms.id as schedule_id,
                ms.message_id,
                ms.scheduled_time,
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
    
    def _send_message(self, message: Dict) -> bool:
        schedule_id = message['schedule_id']
        message_id = message['message_id']
        lead_name = message['lead_name']
        profile_url = message['profile_url']
        content = message['content']
        variant = message['variant']
        
        print(f"\n📤 Sending to {lead_name} (Variant {variant})...")
        
        try:
            result = self.sender.send_connection_request(
                profile_url=profile_url,
                message=content,
                lead_name=lead_name
            )
            
            if result['success']:
                self._mark_as_sent(schedule_id, message_id)
                self._log_activity('message_sent', f"Sent {variant} to {lead_name}", 'success')
                self.stats['messages_sent'] += 1
                print(f"   ✅ Sent!")
                return True
            else:
                error = result.get('error', 'Unknown')
                self._mark_as_failed(schedule_id, error)
                self._log_activity('message_failed', f"Failed to {lead_name}: {error}", 'failed')
                self.stats['messages_failed'] += 1
                print(f"   ❌ Failed: {error}")
                return False
                
        except Exception as e:
            error = str(e)
            self._mark_as_failed(schedule_id, error)
            self._log_activity('message_error', f"Error {lead_name}: {error}", 'failed')
            self.stats['messages_failed'] += 1
            print(f"   ❌ Error: {error}")
            return False
    
    def _mark_as_sent(self, schedule_id: int, message_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        cursor.execute('''
            UPDATE message_schedule
            SET status = 'sent', sent_at = ?, updated_at = ?
            WHERE id = ?
        ''', (now.isoformat(), now.isoformat(), schedule_id))
        
        cursor.execute('''
            UPDATE messages
            SET status = 'sent', sent_at = ?, updated_at = ?
            WHERE id = ?
        ''', (now.isoformat(), now.isoformat(), message_id))
        
        conn.commit()
        conn.close()
    
    def _mark_as_failed(self, schedule_id: int, error: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        cursor.execute('''
            UPDATE message_schedule
            SET status = 'failed', error_message = ?, 
                retry_count = retry_count + 1, updated_at = ?
            WHERE id = ?
        ''', (error, now.isoformat(), schedule_id))
        
        conn.commit()
        conn.close()
    
    def _log_activity(self, activity_type: str, description: str, status: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO activity_logs (activity_type, description, status, created_at)
            VALUES (?, ?, ?, ?)
        ''', (activity_type, description, status, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def process_once(self):
        """Process queue once (for testing)"""
        print("\n🧪 Processing queue once...")
        
        # Initialize sender for test mode
        if not self.sender:
            print("Initializing LinkedIn sender...")
            if not self._init_sender(headless=False):
                return
        
        self.stats['started_at'] = datetime.now()
        self._process_queue()
        self._print_summary()
        
        # Cleanup
        if self.sender:
            self.sender.close_session()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Message Queue Processor')
    parser.add_argument('--interval', type=int, default=60)
    parser.add_argument('--headless', action='store_true')
    parser.add_argument('--test', action='store_true')
    
    args = parser.parse_args()
    
    processor = QueueProcessor(check_interval=args.interval)
    
    if args.test:
        processor.process_once()
    else:
        processor.start(headless=args.headless)