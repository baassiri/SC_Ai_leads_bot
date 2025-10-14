"""
SC AI Lead Generation System - Scraping Cooldown Manager
Enforces weekly/monthly scraping limits to avoid LinkedIn detection
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Tuple
from pathlib import Path


class ScrapingCooldownManager:
    """
    Manages scraping cooldowns to prevent LinkedIn bans
    
    Features:
    - Weekly scraping limits (default: 1 scrape per week)
    - Monthly tracking
    - Automatic reset logic
    - Time-until-next-scrape calculations
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            from backend.config import Config
            db_path = Config.get_database_path()
        
        self.db_path = db_path
    
    def check_can_scrape(self, user_id: int = 1) -> Tuple[bool, str, Dict]:
        """
        Check if scraping is allowed right now
        
        Args:
            user_id: User ID to check (default: 1)
            
        Returns:
            Tuple of (can_scrape: bool, message: str, details: dict)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get user scraping data
        cursor.execute('''
            SELECT 
                last_scrape_date,
                scrapes_this_week,
                weekly_scrape_limit,
                scrapes_this_month,
                last_week_reset,
                total_scrapes_alltime
            FROM users
            WHERE id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return False, "User not found", {}
        
        (last_scrape_date, scrapes_this_week, weekly_limit, 
         scrapes_this_month, last_week_reset, total_alltime) = row
        
        # Parse dates
        last_scrape = datetime.fromisoformat(last_scrape_date) if last_scrape_date else None
        last_reset = datetime.fromisoformat(last_week_reset) if last_week_reset else None
        
        now = datetime.utcnow()
        
        # Check if week has rolled over (reset counter)
        if last_reset:
            days_since_reset = (now - last_reset).days
            if days_since_reset >= 7:
                # Week has passed, reset counter
                self._reset_weekly_counter(user_id)
                scrapes_this_week = 0
        
        # Check weekly limit
        if scrapes_this_week >= weekly_limit:
            # Calculate time until next allowed scrape
            if last_scrape:
                next_allowed = last_scrape + timedelta(days=7)
                time_remaining = next_allowed - now
                
                hours_left = int(time_remaining.total_seconds() // 3600)
                days_left = hours_left // 24
                hours_left = hours_left % 24
                
                if days_left > 0:
                    time_str = f"{days_left} day(s) and {hours_left} hour(s)"
                else:
                    time_str = f"{hours_left} hour(s)"
                
                message = (
                    f"🚫 Weekly scraping limit reached ({scrapes_this_week}/{weekly_limit})\n\n"
                    f"Next scrape available in: {time_str}\n"
                    f"Next available: {next_allowed.strftime('%Y-%m-%d %H:%M UTC')}"
                )
            else:
                message = f"🚫 Weekly scraping limit reached ({scrapes_this_week}/{weekly_limit})"
            
            details = {
                'can_scrape': False,
                'scrapes_used': scrapes_this_week,
                'weekly_limit': weekly_limit,
                'last_scrape': last_scrape.isoformat() if last_scrape else None,
                'next_allowed': (last_scrape + timedelta(days=7)).isoformat() if last_scrape else None
            }
            
            return False, message, details
        
        # Scraping is allowed!
        remaining = weekly_limit - scrapes_this_week
        
        message = (
            f"✅ Scraping allowed!\n"
            f"Scrapes remaining this week: {remaining}/{weekly_limit}"
        )
        
        details = {
            'can_scrape': True,
            'scrapes_used': scrapes_this_week,
            'scrapes_remaining': remaining,
            'weekly_limit': weekly_limit,
            'last_scrape': last_scrape.isoformat() if last_scrape else None
        }
        
        return True, message, details
    
    def record_scrape(self, user_id: int = 1, leads_scraped: int = 0) -> bool:
        """
        Record that a scrape was performed
        
        Args:
            user_id: User ID
            leads_scraped: Number of leads scraped
            
        Returns:
            bool: Success
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.utcnow()
        
        try:
            # Increment counters
            cursor.execute('''
                UPDATE users
                SET 
                    last_scrape_date = ?,
                    scrapes_this_week = scrapes_this_week + 1,
                    scrapes_this_month = scrapes_this_month + 1,
                    total_scrapes_alltime = total_scrapes_alltime + 1,
                    last_week_reset = COALESCE(last_week_reset, ?),
                    last_month_reset = COALESCE(last_month_reset, ?)
                WHERE id = ?
            ''', (now.isoformat(), now.isoformat(), now.isoformat(), user_id))
            
            conn.commit()
            
            print(f"✅ Recorded scrape for user {user_id}")
            print(f"   Leads scraped: {leads_scraped}")
            print(f"   Timestamp: {now.isoformat()}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error recording scrape: {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def _reset_weekly_counter(self, user_id: int = 1):
        """Reset weekly scrape counter"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.utcnow()
        
        cursor.execute('''
            UPDATE users
            SET 
                scrapes_this_week = 0,
                last_week_reset = ?
            WHERE id = ?
        ''', (now.isoformat(), user_id))
        
        conn.commit()
        conn.close()
        
        print(f"🔄 Reset weekly counter for user {user_id}")
    
    def get_scraping_stats(self, user_id: int = 1) -> Dict:
        """Get comprehensive scraping statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                last_scrape_date,
                scrapes_this_week,
                scrapes_this_month,
                weekly_scrape_limit,
                total_scrapes_alltime,
                last_week_reset
            FROM users
            WHERE id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {}
        
        (last_scrape, week_count, month_count, 
         weekly_limit, total, last_reset) = row
        
        last_scrape_dt = datetime.fromisoformat(last_scrape) if last_scrape else None
        last_reset_dt = datetime.fromisoformat(last_reset) if last_reset else None
        
        now = datetime.utcnow()
        
        # Calculate next available scrape
        next_available = None
        time_until_next = None
        
        if last_scrape_dt and week_count >= weekly_limit:
            next_available = last_scrape_dt + timedelta(days=7)
            time_until_next = next_available - now
        
        return {
            'last_scrape': last_scrape,
            'scrapes_this_week': week_count or 0,
            'scrapes_this_month': month_count or 0,
            'weekly_limit': weekly_limit or 1,
            'total_alltime': total or 0,
            'remaining_this_week': max(0, (weekly_limit or 1) - (week_count or 0)),
            'next_available': next_available.isoformat() if next_available else None,
            'seconds_until_next': int(time_until_next.total_seconds()) if time_until_next and time_until_next.total_seconds() > 0 else 0,
            'can_scrape_now': (week_count or 0) < (weekly_limit or 1)
        }
    
    def update_weekly_limit(self, new_limit: int, user_id: int = 1) -> bool:
        """Update weekly scraping limit"""
        if new_limit < 0 or new_limit > 7:
            print("❌ Invalid limit (must be 0-7)")
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users
            SET weekly_scrape_limit = ?
            WHERE id = ?
        ''', (new_limit, user_id))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Updated weekly limit to {new_limit} scrapes/week")
        return True


# Singleton instance
_cooldown_manager = None

def get_cooldown_manager() -> ScrapingCooldownManager:
    """Get or create cooldown manager instance"""
    global _cooldown_manager
    if _cooldown_manager is None:
        _cooldown_manager = ScrapingCooldownManager()
    return _cooldown_manager


# CLI for testing
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🧪 SCRAPING COOLDOWN MANAGER TEST")
    print("="*60)
    
    manager = get_cooldown_manager()
    
    # Check if can scrape
    can_scrape, message, details = manager.check_can_scrape()
    
    print(f"\n{message}")
    print(f"\nDetails: {details}")
    
    # Get stats
    stats = manager.get_scraping_stats()
    
    print("\n📊 Scraping Statistics:")
    print(f"   Last scrape: {stats['last_scrape'] or 'Never'}")
    print(f"   This week: {stats['scrapes_this_week']}/{stats['weekly_limit']}")
    print(f"   This month: {stats['scrapes_this_month']}")
    print(f"   All time: {stats['total_alltime']}")
    print(f"   Remaining: {stats['remaining_this_week']}")
    
    if not stats['can_scrape_now'] and stats['next_available']:
        hours = stats['seconds_until_next'] // 3600
        print(f"   Next available in: {hours} hours")
    
    print("\n" + "="*60)
