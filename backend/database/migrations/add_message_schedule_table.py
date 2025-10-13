"""
Message Scheduling Table Migration
Creates table to manage scheduled message sending with rate limiting
"""

import sqlite3
from datetime import datetime

def upgrade(db_path='data/database.db'):
    """Create message_schedule table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS message_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            
            -- Schedule Configuration
            scheduled_time TIMESTAMP NOT NULL,
            time_zone VARCHAR(50) DEFAULT 'UTC',
            send_window_start TIME,
            send_window_end TIME,
            
            -- Optimization
            ai_optimized BOOLEAN DEFAULT FALSE,
            optimal_time_reason TEXT,
            priority INTEGER DEFAULT 1,
            
            -- Status Tracking
            status VARCHAR(20) DEFAULT 'scheduled',
            sent_at TIMESTAMP,
            failed_at TIMESTAMP,
            retry_count INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 3,
            
            -- Error Handling
            error_message TEXT,
            last_error_at TIMESTAMP,
            
            -- Rate Limiting
            rate_limit_bucket VARCHAR(50),
            
            -- Timestamps
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
        )
    ''')
    
    # Create indexes for performance
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_schedule_status 
        ON message_schedule(status)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_schedule_time 
        ON message_schedule(scheduled_time)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_schedule_message 
        ON message_schedule(message_id)
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Message Schedule table created successfully")

def downgrade(db_path='data/database.db'):
    """Drop message_schedule table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('DROP TABLE IF EXISTS message_schedule')
    
    conn.commit()
    conn.close()
    print("✅ Message Schedule table dropped")

if __name__ == '__main__':
    upgrade()
    print("\n📋 Testing table creation...")
    
    # Verify table exists
    conn = sqlite3.connect('data/database.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='message_schedule'
    """)
    
    result = cursor.fetchone()
    if result:
        print("✅ Table 'message_schedule' exists")
        
        # Show schema
        cursor.execute("PRAGMA table_info(message_schedule)")
        columns = cursor.fetchall()
        print(f"\n📊 Table has {len(columns)} columns:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
    else:
        print("❌ Table not found!")
    
    conn.close()