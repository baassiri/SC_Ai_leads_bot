"""
Add Sales Navigator support tables
"""
import sqlite3
from datetime import datetime, timedelta

def upgrade():
    conn = sqlite3.connect('data/database.db')
    cursor = conn.cursor()
    
    # Sales Nav configuration
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_nav_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enabled BOOLEAN DEFAULT FALSE,
            plan_type VARCHAR(20) DEFAULT 'core',
            inmail_credits_remaining INTEGER DEFAULT 50,
            inmail_credits_total INTEGER DEFAULT 50,
            credits_reset_date DATE,
            crm_connected BOOLEAN DEFAULT FALSE,
            crm_type VARCHAR(50),
            last_sync_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Buyer intent signals
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS buyer_intent_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER,
            signal_type VARCHAR(50),
            signal_strength VARCHAR(20),
            signal_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            details TEXT,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_intent_lead 
        ON buyer_intent_signals(lead_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_intent_date 
        ON buyer_intent_signals(signal_date)
    """)
    
    # Saved searches
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saved_searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(200),
            filters TEXT,
            alert_enabled BOOLEAN DEFAULT TRUE,
            alert_frequency VARCHAR(20) DEFAULT 'daily',
            new_results_count INTEGER DEFAULT 0,
            last_run_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Lead lists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lead_lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(200),
            description TEXT,
            lead_count INTEGER DEFAULT 0,
            shared_with_team BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lead_list_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_id INTEGER,
            lead_id INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (list_id) REFERENCES lead_lists(id),
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """)
    
    # InMail tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inmail_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER,
            subject VARCHAR(500),
            content TEXT,
            sent_at TIMESTAMP,
            opened_at TIMESTAMP,
            replied_at TIMESTAMP,
            credits_used INTEGER DEFAULT 1,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    """)
    
    # Add new columns to leads table
    try:
        cursor.execute("""
            ALTER TABLE leads 
            ADD COLUMN intent_score INTEGER DEFAULT 0
        """)
    except:
        pass
    
    try:
        cursor.execute("""
            ALTER TABLE leads 
            ADD COLUMN profile_views INTEGER DEFAULT 0
        """)
    except:
        pass
    
    try:
        cursor.execute("""
            ALTER TABLE leads 
            ADD COLUMN last_activity_date TIMESTAMP
        """)
    except:
        pass
    
    # Insert default config
    cursor.execute("""
        INSERT OR IGNORE INTO sales_nav_config (id, enabled, plan_type)
        VALUES (1, FALSE, 'core')
    """)
    
    conn.commit()
    conn.close()
    
    print("✅ Sales Navigator tables created successfully")

if __name__ == '__main__':
    upgrade()