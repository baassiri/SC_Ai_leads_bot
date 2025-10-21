import sqlite3
from datetime import datetime, timedelta
import random

class LeadSelector:
    def __init__(self, db_path='database.db'):
        self.db_path = db_path
        
    def get_priority_leads(self, limit=10):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT profile_url, name, title, company, priority, last_contacted
            FROM leads
            WHERE status = 'pending'
            ORDER BY priority DESC, added_date ASC
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        leads = []
        for row in results:
            leads.append({
                'profile_url': row[0],
                'name': row[1],
                'title': row[2],
                'company': row[3],
                'priority': row[4],
                'last_contacted': row[5]
            })
        
        return leads
        
    def get_follow_up_leads(self, days_since_contact=7):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days_since_contact)).isoformat()
        
        cursor.execute('''
            SELECT profile_url, name, title, company, last_contacted
            FROM leads
            WHERE status = 'contacted' 
            AND last_contacted < ?
            AND profile_url NOT IN (
                SELECT profile_url FROM messages 
                WHERE response_received = 1
            )
        ''', (cutoff_date,))
        
        results = cursor.fetchall()
        conn.close()
        
        leads = []
        for row in results:
            leads.append({
                'profile_url': row[0],
                'name': row[1],
                'title': row[2],
                'company': row[3],
                'last_contacted': row[4]
            })
        
        return leads
        
    def set_lead_priority(self, profile_url, priority):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE leads SET priority = ?
            WHERE profile_url = ?
        ''', (priority, profile_url))
        conn.commit()
        conn.close()
        return True
        
    def auto_prioritize_leads(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # High priority: C-level executives
        cursor.execute('''
            UPDATE leads SET priority = 10
            WHERE (title LIKE '%CEO%' OR title LIKE '%CTO%' OR title LIKE '%CFO%')
            AND status = 'pending'
        ''')
        
        # Medium-high priority: VPs and Directors
        cursor.execute('''
            UPDATE leads SET priority = 7
            WHERE (title LIKE '%VP%' OR title LIKE '%Vice President%' OR title LIKE '%Director%')
            AND status = 'pending' AND priority < 7
        ''')
        
        # Medium priority: Managers
        cursor.execute('''
            UPDATE leads SET priority = 5
            WHERE title LIKE '%Manager%'
            AND status = 'pending' AND priority < 5
        ''')
        
        conn.commit()
        affected_rows = conn.total_changes
        conn.close()
        
        return affected_rows
        
    def get_leads_by_company(self, company):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT profile_url, name, title, status, priority
            FROM leads
            WHERE company LIKE ?
        ''', (f'%{company}%',))
        
        results = cursor.fetchall()
        conn.close()
        
        leads = []
        for row in results:
            leads.append({
                'profile_url': row[0],
                'name': row[1],
                'title': row[2],
                'status': row[3],
                'priority': row[4]
            })
        
        return leads
        
    def get_leads_by_title(self, title):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT profile_url, name, company, status, priority
            FROM leads
            WHERE title LIKE ?
        ''', (f'%{title}%',))
        
        results = cursor.fetchall()
        conn.close()
        
        leads = []
        for row in results:
            leads.append({
                'profile_url': row[0],
                'name': row[1],
                'company': row[2],
                'status': row[3],
                'priority': row[4]
            })
        
        return leads
        
    def bulk_import_leads(self, leads_list):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        success_count = 0
        duplicate_count = 0
        
        for lead in leads_list:
            try:
                cursor.execute('''
                    INSERT INTO leads (profile_url, name, title, company, priority, added_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    lead.get('profile_url'),
                    lead.get('name', ''),
                    lead.get('title', ''),
                    lead.get('company', ''),
                    lead.get('priority', 0),
                    datetime.now().isoformat()
                ))
                success_count += 1
            except sqlite3.IntegrityError:
                duplicate_count += 1
        
        conn.commit()
        conn.close()
        
        return {
            'success': success_count,
            'duplicates': duplicate_count,
            'total': len(leads_list)
        }
        
    def get_lead_stats(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM leads WHERE status = "pending"')
        pending = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM leads WHERE status = "contacted"')
        contacted = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM leads WHERE status = "responded"')
        responded = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM leads WHERE status = "converted"')
        converted = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM leads')
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'pending': pending,
            'contacted': contacted,
            'responded': responded,
            'converted': converted,
            'total': total
        }
        
    def remove_lead(self, profile_url):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM leads WHERE profile_url = ?', (profile_url,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0