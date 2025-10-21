import sqlite3
import time
from datetime import datetime, timedelta
from linkedin_messenger import LinkedInMessenger
from lead_selector import LeadSelector
from optimal_time_ai import OptimalTimeAI
from credentials_manager import CredentialsManager
import random
import schedule
import threading

class BotController:
    def __init__(self, db_path='database.db'):
        self.db_path = db_path
        self.messenger = LinkedInMessenger(db_path)
        self.lead_selector = LeadSelector(db_path)
        self.optimal_time = OptimalTimeAI(db_path)
        self.credentials = CredentialsManager()
        self.running = False
        self.daily_limit = 50
        self.messages_sent_today = 0
        self.last_reset = datetime.now().date()
        
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_url TEXT UNIQUE,
                name TEXT,
                title TEXT,
                company TEXT,
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 0,
                added_date TEXT,
                last_contacted TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_url TEXT,
                message TEXT,
                status TEXT,
                timestamp TEXT,
                response_received INTEGER DEFAULT 0,
                FOREIGN KEY (profile_url) REFERENCES leads(profile_url)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                message_template TEXT,
                ab_variant TEXT,
                created_date TEXT,
                active INTEGER DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                messages_sent INTEGER,
                responses_received INTEGER,
                conversion_rate REAL,
                best_time TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def start(self, email=None, password=None):
        if not email or not password:
            creds = self.credentials.get_credentials()
            email = creds.get('email')
            password = creds.get('password')
            
        if not email or not password:
            raise ValueError("No credentials provided")
            
        self.messenger.init_driver()
        if not self.messenger.login(email, password):
            raise Exception("Login failed")
            
        self.running = True
        print("Bot started successfully")
        
    def stop(self):
        self.running = False
        self.messenger.close()
        print("Bot stopped")
        
    def reset_daily_counter(self):
        today = datetime.now().date()
        if today > self.last_reset:
            self.messages_sent_today = 0
            self.last_reset = today
            
    def send_campaign_messages(self, campaign_id, max_messages=None):
        self.reset_daily_counter()
        
        if max_messages is None:
            max_messages = self.daily_limit - self.messages_sent_today
            
        leads = self.lead_selector.get_priority_leads(max_messages)
        
        for lead in leads:
            if not self.running or self.messages_sent_today >= self.daily_limit:
                break
                
            profile_url = lead['profile_url']
            message = self.get_personalized_message(campaign_id, lead)
            
            optimal_wait = self.optimal_time.calculate_wait_time()
            time.sleep(optimal_wait)
            
            success = self.messenger.send_message(profile_url, message)
            
            if success:
                self.messages_sent_today += 1
                self.update_lead_status(profile_url, 'contacted')
                print(f"Message sent to {lead['name']} ({self.messages_sent_today}/{self.daily_limit})")
            else:
                print(f"Failed to send message to {lead['name']}")
                
            time.sleep(random.uniform(30, 60))
            
    def get_personalized_message(self, campaign_id, lead):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT message_template FROM campaigns WHERE id = ?', (campaign_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            template = result[0]
            message = template.replace('{name}', lead.get('name', 'there'))
            message = message.replace('{company}', lead.get('company', 'your company'))
            message = message.replace('{title}', lead.get('title', 'your role'))
            return message
        return "Hi, I'd like to connect with you!"
        
    def update_lead_status(self, profile_url, status):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE leads SET status = ?, last_contacted = ?
            WHERE profile_url = ?
        ''', (status, datetime.now().isoformat(), profile_url))
        conn.commit()
        conn.close()
        
    def add_lead(self, profile_url, name='', title='', company='', priority=0):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO leads (profile_url, name, title, company, priority, added_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (profile_url, name, title, company, priority, datetime.now().isoformat()))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
            
    def get_statistics(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM leads WHERE status = "contacted"')
        total_contacted = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM messages WHERE response_received = 1')
        total_responses = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM leads WHERE status = "pending"')
        pending_leads = cursor.fetchone()[0]
        
        conn.close()
        
        response_rate = (total_responses / total_contacted * 100) if total_contacted > 0 else 0
        
        return {
            'total_contacted': total_contacted,
            'total_responses': total_responses,
            'response_rate': response_rate,
            'pending_leads': pending_leads,
            'messages_sent_today': self.messages_sent_today,
            'daily_limit': self.daily_limit
        }
        
    def schedule_campaign(self, campaign_id, time_str, days=None):
        schedule.every().day.at(time_str).do(
            self.send_campaign_messages, campaign_id=campaign_id
        )
        
    def run_scheduler(self):
        while self.running:
            schedule.run_pending()
            time.sleep(60)