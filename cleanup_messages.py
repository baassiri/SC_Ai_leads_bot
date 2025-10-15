"""
Quick script to delete all messages from database
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from backend.database.db_manager import db_manager

def cleanup_messages():
    """Delete all messages"""
    
    print("\n" + "="*60)
    print("🗑️  CLEANING UP MESSAGES")
    print("="*60)
    
    # Get current count
    stats = db_manager.get_message_stats()
    print(f"\nCurrent messages:")
    print(f"  Draft: {stats.get('draft', 0)}")
    print(f"  Approved: {stats.get('approved', 0)}")
    print(f"  Sent: {stats.get('sent', 0)}")
    print(f"  Total: {stats.get('total', 0)}")
    
    # Confirm
    confirm = input("\n⚠️  Delete ALL messages? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("❌ Cancelled")
        return
    
    # Delete all messages
    conn = db_manager.engine.raw_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM messages")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='messages'")
    
    conn.commit()
    conn.close()
    
    # Verify
    stats = db_manager.get_message_stats()
    print(f"\n✅ Cleanup complete!")
    print(f"  Remaining: {stats.get('total', 0)} messages")

if __name__ == "__main__":
    cleanup_messages()
