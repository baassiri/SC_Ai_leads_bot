"""
SC AI Lead Generation System - Complete Database Manager
All CRUD operations with proper session management and error handling
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any
from contextlib import contextmanager
from pathlib import Path
import json


class DatabaseManager:
    """Complete database manager with all required methods"""
    
    def __init__(self, db_path: str = None):
        """Initialize database manager"""
        if db_path:
            self.db_path = db_path
        else:
            # Default path
            self.db_path = Path(__file__).parent.parent.parent / 'data' / 'database.db'
        
        # Ensure database exists
        self._ensure_database_exists()
        print(f"✅ Database Manager initialized: {self.db_path}")
    
    def _ensure_database_exists(self):
        """Ensure database file and directory exist"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Create database if it doesn't exist
        if not Path(self.db_path).exists():
            print(f"Creating database at {self.db_path}...")
            # Touch the file
            Path(self.db_path).touch()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            return False
    
    # ========================================================================
    # PERSONA METHODS
    # ========================================================================
    
    def create_persona(self, name: str, description: str = None, **kwargs) -> Optional[int]:
        """Create a new persona"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build INSERT statement dynamically
                fields = ['name', 'description', 'created_at', 'updated_at']
                values = [name, description, datetime.now().isoformat(), datetime.now().isoformat()]
                
                # Add optional fields
                optional_fields = [
                    'age_range', 'gender_distribution', 'job_titles', 'decision_maker_roles',
                    'company_types', 'company_size', 'seniority_level', 'industry_focus',
                    'pain_points', 'goals', 'linkedin_keywords', 'smart_search_query',
                    'message_hooks', 'solutions', 'document_source', 'location_data'
                ]
                
                for field in optional_fields:
                    if field in kwargs and kwargs[field] is not None:
                        fields.append(field)
                        values.append(kwargs[field])
                
                placeholders = ', '.join(['?' for _ in fields])
                sql = f"INSERT INTO personas ({', '.join(fields)}) VALUES ({placeholders})"
                
                cursor.execute(sql, values)
                return cursor.lastrowid
        
        except Exception as e:
            print(f"❌ Error creating persona: {str(e)}")
            return None
    
    def get_all_personas(self) -> List[Dict]:
        """Get all personas"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM personas ORDER BY created_at DESC")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ Error getting personas: {str(e)}")
            return []
    
    def get_persona_by_id(self, persona_id: int) -> Optional[Dict]:
        """Get persona by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM personas WHERE id = ?", (persona_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"❌ Error getting persona: {str(e)}")
            return None
    
    def get_persona_by_name(self, name: str) -> Optional[Dict]:
        """Get persona by name"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM personas WHERE name = ?", (name,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"❌ Error getting persona by name: {str(e)}")
            return None
    
    def update_persona(self, persona_id: int, updates: Dict) -> bool:
        """Update persona"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build UPDATE statement
                updates['updated_at'] = datetime.now().isoformat()
                fields = ', '.join([f"{key} = ?" for key in updates.keys()])
                values = list(updates.values()) + [persona_id]
                
                sql = f"UPDATE personas SET {fields} WHERE id = ?"
                cursor.execute(sql, values)
                
                return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Error updating persona: {str(e)}")
            return False
    
    def delete_persona(self, persona_id: int) -> bool:
        """Delete persona"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM personas WHERE id = ?", (persona_id,))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Error deleting persona: {str(e)}")
            return False
    
    # ========================================================================
    # LEAD METHODS
    # ========================================================================
    
    def save_lead(self, lead_data: Dict) -> Optional[int]:
        """Save a new lead"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO leads (
                        name, title, company, industry, location, profile_url,
                        headline, summary, company_size, ai_score, persona_id,
                        status, connection_status, scraped_at, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    lead_data.get('name'),
                    lead_data.get('title'),
                    lead_data.get('company'),
                    lead_data.get('industry'),
                    lead_data.get('location'),
                    lead_data.get('profile_url'),
                    lead_data.get('headline'),
                    lead_data.get('summary'),
                    lead_data.get('company_size'),
                    lead_data.get('ai_score', 0),
                    lead_data.get('persona_id'),
                    lead_data.get('status', 'new'),
                    lead_data.get('connection_status', 'not_sent'),
                    lead_data.get('scraped_at', datetime.now().isoformat()),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                return cursor.lastrowid
        
        except Exception as e:
            print(f"❌ Error saving lead: {str(e)}")
            return None
    
    def get_all_leads(self, limit: int = 1000) -> List[Dict]:
        """Get all leads"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT l.*, p.name as persona_name
                    FROM leads l
                    LEFT JOIN personas p ON l.persona_id = p.id
                    ORDER BY l.created_at DESC
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ Error getting leads: {str(e)}")
            return []
    
    def get_lead_by_id(self, lead_id: int) -> Optional[Dict]:
        """Get lead by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT l.*, p.name as persona_name
                    FROM leads l
                    LEFT JOIN personas p ON l.persona_id = p.id
                    WHERE l.id = ?
                """, (lead_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"❌ Error getting lead: {str(e)}")
            return None
    
    def update_lead(self, lead_id: int, updates: Dict) -> bool:
        """Update lead"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                updates['updated_at'] = datetime.now().isoformat()
                fields = ', '.join([f"{key} = ?" for key in updates.keys()])
                values = list(updates.values()) + [lead_id]
                
                sql = f"UPDATE leads SET {fields} WHERE id = ?"
                cursor.execute(sql, values)
                
                return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Error updating lead: {str(e)}")
            return False
    
    def update_lead_status(self, lead_id: int, new_status: str) -> bool:
        """Update lead status"""
        return self.update_lead(lead_id, {'status': new_status})
    
    def delete_lead(self, lead_id: int) -> bool:
        """Delete lead"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Error deleting lead: {str(e)}")
            return False
    
    def get_top_leads(self, limit: int = 20, min_score: int = 70) -> List[Dict]:
        """Get top scoring leads"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT l.*, p.name as persona_name
                    FROM leads l
                    LEFT JOIN personas p ON l.persona_id = p.id
                    WHERE l.ai_score >= ?
                    ORDER BY l.ai_score DESC
                    LIMIT ?
                """, (min_score, limit))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ Error getting top leads: {str(e)}")
            return []
    
    # ========================================================================
    # MESSAGE METHODS
    # ========================================================================
    
    def save_message(self, message_data: Dict) -> Optional[int]:
        """Save a generated message"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO messages (
                        lead_id, message_type, content, variant, prompt_used,
                        generated_by, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    message_data.get('lead_id'),
                    message_data.get('message_type', 'connection_request'),
                    message_data.get('content'),
                    message_data.get('variant', 'A'),
                    message_data.get('prompt_used'),
                    message_data.get('generated_by', 'gpt-4'),
                    message_data.get('status', 'draft'),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                return cursor.lastrowid
        
        except Exception as e:
            print(f"❌ Error saving message: {str(e)}")
            return None
    
    def get_all_messages(self, status: str = None) -> List[Dict]:
        """Get all messages, optionally filtered by status"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if status:
                    cursor.execute("""
                        SELECT m.*, l.name as lead_name, l.title, l.company
                        FROM messages m
                        LEFT JOIN leads l ON m.lead_id = l.id
                        WHERE m.status = ?
                        ORDER BY m.created_at DESC
                    """, (status,))
                else:
                    cursor.execute("""
                        SELECT m.*, l.name as lead_name, l.title, l.company
                        FROM messages m
                        LEFT JOIN leads l ON m.lead_id = l.id
                        ORDER BY m.created_at DESC
                    """)
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ Error getting messages: {str(e)}")
            return []
    
    def get_message_by_id(self, message_id: int) -> Optional[Dict]:
        """Get message by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT m.*, l.name as lead_name, l.title, l.company, l.profile_url
                    FROM messages m
                    LEFT JOIN leads l ON m.lead_id = l.id
                    WHERE m.id = ?
                """, (message_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"❌ Error getting message: {str(e)}")
            return None
    
    def get_messages_by_lead(self, lead_id: int) -> List[Dict]:
        """Get all messages for a lead"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM messages
                    WHERE lead_id = ?
                    ORDER BY created_at DESC
                """, (lead_id,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ Error getting messages for lead: {str(e)}")
            return []
    
    def update_message_status(self, message_id: int, new_status: str) -> bool:
        """Update message status"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                update_data = {
                    'status': new_status,
                    'updated_at': datetime.now().isoformat()
                }
                
                if new_status == 'sent':
                    update_data['sent_at'] = datetime.now().isoformat()
                
                fields = ', '.join([f"{key} = ?" for key in update_data.keys()])
                values = list(update_data.values()) + [message_id]
                
                cursor.execute(f"UPDATE messages SET {fields} WHERE id = ?", values)
                
                return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Error updating message status: {str(e)}")
            return False
    
    def get_pending_messages(self, limit: int = 10) -> List[Dict]:
        """Get approved messages ready to send"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT m.*, l.name as lead_name, l.profile_url
                    FROM messages m
                    LEFT JOIN leads l ON m.lead_id = l.id
                    WHERE m.status = 'approved'
                    ORDER BY m.created_at
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ Error getting pending messages: {str(e)}")
            return []
    
    def delete_message(self, message_id: int) -> bool:
        """Delete message"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))
                return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Error deleting message: {str(e)}")
            return False
    
    # ========================================================================
    # ACTIVITY LOG METHODS
    # ========================================================================
    
    def log_activity(self, activity_type: str, description: str, status: str = 'success',
                    lead_id: int = None, campaign_id: int = None, error_message: str = None):
        """Log an activity"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO activity_logs (
                        activity_type, description, status, lead_id,
                        campaign_id, error_message, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    activity_type,
                    description,
                    status,
                    lead_id,
                    campaign_id,
                    error_message,
                    datetime.now().isoformat()
                ))
        except Exception as e:
            print(f"❌ Error logging activity: {str(e)}")
    
    def get_recent_activities(self, limit: int = 50) -> List[Dict]:
        """Get recent activities"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM activity_logs
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ Error getting activities: {str(e)}")
            return []
    
    # ========================================================================
    # STATISTICS METHODS
    # ========================================================================
    
    def get_dashboard_stats(self) -> Dict:
        """Get statistics for dashboard"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Total leads
                cursor.execute("SELECT COUNT(*) FROM leads")
                total_leads = cursor.fetchone()[0]
                
                # Qualified leads (score >= 70)
                cursor.execute("SELECT COUNT(*) FROM leads WHERE ai_score >= 70")
                qualified_leads = cursor.fetchone()[0]
                
                # Contacted leads
                cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'contacted'")
                contacted_leads = cursor.fetchone()[0]
                
                # Messages stats
                cursor.execute("SELECT COUNT(*), status FROM messages GROUP BY status")
                message_stats = {row[1]: row[0] for row in cursor.fetchall()}
                
                # Personas count
                cursor.execute("SELECT COUNT(*) FROM personas")
                personas_count = cursor.fetchone()[0]
                
                return {
                    'total_leads': total_leads,
                    'qualified_leads': qualified_leads,
                    'contacted_leads': contacted_leads,
                    'personas_count': personas_count,
                    'messages_draft': message_stats.get('draft', 0),
                    'messages_approved': message_stats.get('approved', 0),
                    'messages_sent': message_stats.get('sent', 0),
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"❌ Error getting dashboard stats: {str(e)}")
            return {}


# Singleton instance
_db_manager_instance = None

def get_db_manager(db_path: str = None) -> DatabaseManager:
    """Get singleton database manager instance"""
    global _db_manager_instance
    if _db_manager_instance is None:
        _db_manager_instance = DatabaseManager(db_path)
    return _db_manager_instance


# For backward compatibility
db_manager = get_db_manager()


if __name__ == '__main__':
    """Test database manager"""
    print("\n" + "="*70)
    print("🧪 TESTING DATABASE MANAGER")
    print("="*70)
    
    # Test connection
    print("\n1️⃣ Testing connection...")
    manager = DatabaseManager()
    if manager.test_connection():
        print("   ✅ Connection successful")
    else:
        print("   ❌ Connection failed")
    
    # Test stats
    print("\n2️⃣ Getting dashboard stats...")
    stats = manager.get_dashboard_stats()
    print(f"   Total leads: {stats.get('total_leads', 0)}")
    print(f"   Qualified leads: {stats.get('qualified_leads', 0)}")
    print(f"   Personas: {stats.get('personas_count', 0)}")
    
    print("\n" + "="*70)
    print("✅ Database manager test complete!")
    print("="*70)