"""
Scraping Cooldown Manager - SIMPLIFIED VERSION
Works directly with database without requiring SQLAlchemy models
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Tuple, Dict
from backend.config import Config
from backend.database.db_manager import db_manager

class ScrapingCooldownManager:
    """
    Manages scraping cooldowns to prevent LinkedIn account restrictions
    
    Default limits:
    - 1 scrape per week (configurable)
    - Cooldown resets every Monday at midnight
    """
    
    def __init__(self, weekly_limit: int = 1):
        self.weekly_limit = weekly_limit
        self.db_path = Config.DATABASE_URL.replace('sqlite:///', '')
    
    def _ensure_user_exists(self, user_id: int = 1) -> bool:
        """Ensure default user exists, create if missing"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                print(f"⚠️ User {user_id} not found. Creating default user...")
                cursor.execute("""
                    INSERT INTO users (id, email, is_active)
                    VALUES (?, ?, ?)
                """, (user_id, "default@scai.com", 1))
                conn.commit()
                print(f"✅ Default user created (ID: {user_id})")
            
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Error ensuring user exists: {str(e)}")
            return False
    
    def check_can_scrape(self, user_id: int = 1) -> Tuple[bool, str, Dict]:
        """
        Check if user can scrape based on cooldown rules
        
        Args:
            user_id: User ID to check (default: 1)
        
        Returns:
            Tuple of (can_scrape: bool, message: str, details: dict)
        """
        try:
            # Ensure user exists
            self._ensure_user_exists(user_id)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get start of current week (Monday 00:00)
            now = datetime.now()
            week_start = now - timedelta(days=now.weekday(), 
                                        hours=now.hour,
                                        minutes=now.minute,
                                        seconds=now.second,
                                        microseconds=now.microsecond)
            
            # Count scrapes this week
            cursor.execute("""
                SELECT COUNT(*) FROM scraping_cooldown
                WHERE user_id = ? AND scrape_timestamp >= ?
            """, (user_id, week_start.isoformat()))
            
            scrapes_this_week = cursor.fetchone()[0]
            conn.close()
            
            scrapes_remaining = max(0, self.weekly_limit - scrapes_this_week)
            
            if scrapes_remaining > 0:
                return (
                    True,
                    f"✅ Ready to scrape! {scrapes_remaining} of {self.weekly_limit} scrapes remaining this week.",
                    {
                        'scrapes_this_week': scrapes_this_week,
                        'scrapes_remaining': scrapes_remaining,
                        'weekly_limit': self.weekly_limit,
                        'week_start': week_start.isoformat(),
                        'next_reset': (week_start + timedelta(days=7)).isoformat()
                    }
                )
            else:
                next_reset = week_start + timedelta(days=7)
                hours_until_reset = (next_reset - now).total_seconds() / 3600
                
                return (
                    False,
                    f"⏸️ Weekly scrape limit reached ({self.weekly_limit} scrapes/week). Resets in {hours_until_reset:.1f} hours.",
                    {
                        'scrapes_this_week': scrapes_this_week,
                        'scrapes_remaining': 0,
                        'weekly_limit': self.weekly_limit,
                        'week_start': week_start.isoformat(),
                        'next_reset': next_reset.isoformat(),
                        'hours_until_reset': round(hours_until_reset, 1)
                    }
                )
        
        except Exception as e:
            print(f"❌ Error checking cooldown: {str(e)}")
            return (
                False,
                f"Error checking cooldown: {str(e)}",
                {}
            )
    
    def record_scrape(self, user_id: int = 1, leads_scraped: int = 0) -> bool:
        """
        Record a scraping session
        
        Args:
            user_id: User who performed the scrape
            leads_scraped: Number of leads collected
        
        Returns:
            bool: True if recorded successfully
        """
        try:
            # Ensure user exists
            self._ensure_user_exists(user_id)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO scraping_cooldown (user_id, scrape_timestamp, leads_scraped)
                VALUES (?, ?, ?)
            """, (user_id, datetime.now().isoformat(), leads_scraped))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Scrape recorded: {leads_scraped} leads collected")
            
            # Log activity
            db_manager.log_activity(
                activity_type='cooldown_recorded',
                description=f'Scraping session recorded: {leads_scraped} leads',
                status='success'
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Error recording scrape: {str(e)}")
            return False
    
    def get_scraping_stats(self, user_id: int = 1) -> Dict:
        """
        Get scraping statistics for a user
        
        Args:
            user_id: User ID
        
        Returns:
            Dict with scraping statistics
        """
        try:
            # Ensure user exists
            self._ensure_user_exists(user_id)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get current week start
            now = datetime.now()
            week_start = now - timedelta(days=now.weekday(), 
                                        hours=now.hour,
                                        minutes=now.minute,
                                        seconds=now.second,
                                        microseconds=now.microsecond)
            
            # This week's scrapes
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(leads_scraped), 0)
                FROM scraping_cooldown
                WHERE user_id = ? AND scrape_timestamp >= ?
            """, (user_id, week_start.isoformat()))
            
            this_week = cursor.fetchone()
            scrapes_this_week = this_week[0]
            leads_this_week = this_week[1]
            
            # All time stats
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(leads_scraped), 0), MAX(scrape_timestamp)
                FROM scraping_cooldown
                WHERE user_id = ?
            """, (user_id,))
            
            all_time = cursor.fetchone()
            scrapes_all_time = all_time[0]
            leads_all_time = all_time[1]
            last_scrape = all_time[2]
            
            conn.close()
            
            return {
                'scrapes_this_week': scrapes_this_week,
                'leads_this_week': leads_this_week,
                'scrapes_all_time': scrapes_all_time,
                'leads_all_time': leads_all_time,
                'weekly_limit': self.weekly_limit,
                'week_start': week_start.isoformat(),
                'last_scrape': last_scrape
            }
            
        except Exception as e:
            print(f"❌ Error getting stats: {str(e)}")
            return {}
    
    def update_weekly_limit(self, new_limit: int) -> bool:
        """
        Update the weekly scraping limit
        
        Args:
            new_limit: New weekly limit (0-7)
        
        Returns:
            bool: True if updated successfully
        """
        if 0 <= new_limit <= 7:
            self.weekly_limit = new_limit
            print(f"✅ Weekly limit updated to {new_limit} scrapes/week")
            return True
        else:
            print(f"❌ Invalid limit: {new_limit} (must be 0-7)")
            return False
    
    def reset_user_cooldown(self, user_id: int = 1) -> bool:
        """
        ADMIN: Reset cooldown for a user (delete all records)
        
        Args:
            user_id: User to reset
        
        Returns:
            bool: True if reset successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM scraping_cooldown WHERE user_id = ?", (user_id,))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Cooldown reset for user {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error resetting cooldown: {str(e)}")
            return False


# Singleton instance
_cooldown_manager = None

def get_cooldown_manager(weekly_limit: int = 1) -> ScrapingCooldownManager:
    """Get singleton instance of cooldown manager"""
    global _cooldown_manager
    if _cooldown_manager is None:
        _cooldown_manager = ScrapingCooldownManager(weekly_limit=weekly_limit)
    return _cooldown_manager


# Quick test
if __name__ == '__main__':
    print("=" * 60)
    print("🧪 Testing Scraping Cooldown Manager")
    print("=" * 60)
    
    manager = get_cooldown_manager(weekly_limit=1)
    
    print("\n1️⃣ Checking if scraping is allowed...")
    can_scrape, message, details = manager.check_can_scrape()
    print(f"   Result: {message}")
    print(f"   Details: {details}")
    
    if can_scrape:
        print("\n2️⃣ Recording a test scrape...")
        manager.record_scrape(user_id=1, leads_scraped=25)
        
        print("\n3️⃣ Checking again after scrape...")
        can_scrape, message, details = manager.check_can_scrape()
        print(f"   Result: {message}")
    
    print("\n4️⃣ Getting statistics...")
    stats = manager.get_scraping_stats()
    print(f"   Stats: {stats}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)