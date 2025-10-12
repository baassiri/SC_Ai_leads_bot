"""
A/B Test Tracking Table Migration
Creates table to track A/B/C message variant performance
"""

import sqlite3
from datetime import datetime

def upgrade(db_path='data/database.db'):
    """Create ab_tests table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ab_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_name VARCHAR(100) NOT NULL,
            campaign_id INTEGER,
            lead_persona VARCHAR(200),
            
            -- Variant A Metrics
            variant_a_sent INTEGER DEFAULT 0,
            variant_a_replies INTEGER DEFAULT 0,
            variant_a_positive_replies INTEGER DEFAULT 0,
            variant_a_avg_sentiment REAL DEFAULT 0.0,
            variant_a_reply_rate REAL DEFAULT 0.0,
            
            -- Variant B Metrics
            variant_b_sent INTEGER DEFAULT 0,
            variant_b_replies INTEGER DEFAULT 0,
            variant_b_positive_replies INTEGER DEFAULT 0,
            variant_b_avg_sentiment REAL DEFAULT 0.0,
            variant_b_reply_rate REAL DEFAULT 0.0,
            
            -- Variant C Metrics
            variant_c_sent INTEGER DEFAULT 0,
            variant_c_replies INTEGER DEFAULT 0,
            variant_c_positive_replies INTEGER DEFAULT 0,
            variant_c_avg_sentiment REAL DEFAULT 0.0,
            variant_c_reply_rate REAL DEFAULT 0.0,
            
            -- Test Status
            winning_variant VARCHAR(1),
            status VARCHAR(20) DEFAULT 'active',
            min_sends_required INTEGER DEFAULT 20,
            confidence_threshold REAL DEFAULT 0.15,
            
            -- Timestamps
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ A/B Tests table created successfully")

def downgrade(db_path='data/database.db'):
    """Drop ab_tests table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('DROP TABLE IF EXISTS ab_tests')
    
    conn.commit()
    conn.close()
    print("✅ A/B Tests table dropped")

if __name__ == '__main__':
    upgrade()