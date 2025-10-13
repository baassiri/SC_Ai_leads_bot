import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import time
import sqlite3
from datetime import datetime
from typing import Dict, List

try:
    from backend.config import Config
    db_path = Config.DATABASE_URL.replace('sqlite:///', '')
except:
    db_path = 'data/database.db'


class QueueProcessor:
    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self.running = False
        self.sender = None
        self.db_path = db_path
        
        self.stats = {
            'messages_sent': 0,
            'messages_failed': 0,
            'started_at': None
        }
    
    def start(self, headless: bool = True):
        print('\n' + '='*60)
        print('🚀 QUEUE PROCESSOR STARTING')
        print('='*60)
        print(f'⏱️  Check interval: {self.check_interval} seconds')
        print(f'🎯 Database: {self.db_path}')
        
        if not self._init_sender(headless):
            return
        
        self.running = True
        self.stats['started_at'] = datetime.now()
        
        print('\n✅ Queue processor is running!')
        print('Press Ctrl+C to stop\n')
        
        try:
            while self.running:
                self._process_queue()
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            print('\n\n⏹️  Stopping queue processor...')
            self.stop()
    
    def _init_sender(self, headless: bool = True):
        return True
    
    def stop(self):
        self.running = False
        if self.sender:
            pass
        self._print_summary()
    
    def _print_summary(self):
        print('\n' + '='*60)
        print('📊 SUMMARY')
        print('='*60)
        print(f'✅ Sent: {self.stats['messages_sent']}')
        print(f'❌ Failed: {self.stats['messages_failed']}')
        
        if self.stats['started_at']:
            duration = datetime.now() - self.stats['started_at']
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            print(f'⏱️  Running time: {hours}h {minutes}m')
        
        print('='*60)
    
    def _process_queue(self):
        pending = self._get_pending_messages()
        
        if not pending:
            print(f'⏰ [{datetime.now().strftime('%H:%M:%S')}] No messages ready...')
            return
        
        print(f'\n📬 Found {len(pending)} message(s) ready to send')
        
        for message in pending:
            self._send_message(message)
            time.sleep(5)
    
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
            LEFT JOIN leads l ON m.lead_id = l.id
            WHERE ms.status = 'scheduled'
            AND ms.scheduled_time <= ?
            AND m.lead_id IS NOT NULL
            AND l.id IS NOT NULL
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
        content = message['content']
        variant = message['variant']
        
        print(f'\n📤 Sending to {lead_name} (Variant {variant})...')
        
        try:
            self._mark_as_sent(schedule_id, message_id)
            self.stats['messages_sent'] += 1
            print(f'   ✅ Would send (test mode)')
            return True
                
        except Exception as e:
            error = str(e)
            self._mark_as_failed(schedule_id, error)
            self.stats['messages_failed'] += 1
            print(f'   ❌ Error: {error}')
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
    
    def process_once(self):
        print('\n🧪 Processing queue once...')
        
        if not self.sender:
            print('Initializing LinkedIn sender...')
            if not self._init_sender(headless=False):
                return
        
        self.stats['started_at'] = datetime.now()
        self._process_queue()
        self._print_summary()


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
