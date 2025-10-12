"""
A/B/C Test Manager
Handles variant assignment, performance tracking, and winner selection
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict, List
import statistics

class ABTestManager:
    def __init__(self, db_path='data/database.db'):
        self.db_path = db_path
    
    def create_test(self, test_name: str, campaign_id: Optional[int] = None, 
                   lead_persona: Optional[str] = None, min_sends: int = 20) -> int:
        """Create a new A/B/C test"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ab_tests (test_name, campaign_id, lead_persona, min_sends_required)
            VALUES (?, ?, ?, ?)
        ''', (test_name, campaign_id, lead_persona, min_sends))
        
        test_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Created A/B/C test: {test_name} (ID: {test_id})")
        return test_id
    
    def get_next_variant(self, test_id: int) -> str:
        """Get next variant to assign using round-robin rotation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT variant_a_sent, variant_b_sent, variant_c_sent
            FROM ab_tests WHERE id = ?
        ''', (test_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return 'A'
        
        a_sent, b_sent, c_sent = result
        
        if a_sent <= b_sent and a_sent <= c_sent:
            return 'A'
        elif b_sent <= c_sent:
            return 'B'
        else:
            return 'C'
    
    def record_message_sent(self, test_id: int, variant: str):
        """Record that a message was sent for a variant"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        variant_field = f'variant_{variant.lower()}_sent'
        
        cursor.execute(f'''
            UPDATE ab_tests 
            SET {variant_field} = {variant_field} + 1
            WHERE id = ?
        ''', (test_id,))
        
        conn.commit()
        conn.close()
    
    def record_reply(self, test_id: int, variant: str, sentiment_score: float = 0.5):
        """Record a reply for a variant"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        variant_lower = variant.lower()
        
        cursor.execute(f'''
            SELECT variant_{variant_lower}_replies, 
                   variant_{variant_lower}_positive_replies,
                   variant_{variant_lower}_avg_sentiment,
                   variant_{variant_lower}_sent
            FROM ab_tests WHERE id = ?
        ''', (test_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return
        
        replies, positive_replies, avg_sentiment, sent = result
        
        new_replies = replies + 1
        new_positive = positive_replies + (1 if sentiment_score > 0.6 else 0)
        new_avg_sentiment = ((avg_sentiment * replies) + sentiment_score) / new_replies
        reply_rate = (new_replies / sent * 100) if sent > 0 else 0
        
        cursor.execute(f'''
            UPDATE ab_tests 
            SET variant_{variant_lower}_replies = ?,
                variant_{variant_lower}_positive_replies = ?,
                variant_{variant_lower}_avg_sentiment = ?,
                variant_{variant_lower}_reply_rate = ?
            WHERE id = ?
        ''', (new_replies, new_positive, new_avg_sentiment, reply_rate, test_id))
        
        conn.commit()
        conn.close()
        
        self.check_and_declare_winner(test_id)
    
    def check_and_declare_winner(self, test_id: int) -> Optional[str]:
        """Check if enough data collected to declare winner"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT variant_a_sent, variant_a_reply_rate,
                   variant_b_sent, variant_b_reply_rate,
                   variant_c_sent, variant_c_reply_rate,
                   min_sends_required, status, confidence_threshold
            FROM ab_tests WHERE id = ?
        ''', (test_id,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return None
        
        (a_sent, a_rate, b_sent, b_rate, c_sent, c_rate, 
         min_sends, status, confidence_threshold) = result
        
        if status == 'completed':
            conn.close()
            return None
        
        if a_sent < min_sends or b_sent < min_sends or c_sent < min_sends:
            conn.close()
            return None
        
        rates = {'A': a_rate, 'B': b_rate, 'C': c_rate}
        winner = max(rates, key=rates.get)
        winner_rate = rates[winner]
        
        other_rates = [r for v, r in rates.items() if v != winner]
        avg_other_rate = statistics.mean(other_rates) if other_rates else 0
        
        if winner_rate >= avg_other_rate + (confidence_threshold * 100):
            cursor.execute('''
                UPDATE ab_tests 
                SET winning_variant = ?,
                    status = 'completed',
                    completed_at = ?
                WHERE id = ?
            ''', (winner, datetime.utcnow().isoformat(), test_id))
            
            conn.commit()
            conn.close()
            
            print(f"🏆 WINNER DECLARED: Variant {winner} ({winner_rate:.1f}% reply rate)")
            return winner
        
        conn.close()
        return None
    
    def get_test_results(self, test_id: int) -> Optional[Dict]:
        """Get current test results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT test_name, status, winning_variant,
                   variant_a_sent, variant_a_replies, variant_a_reply_rate,
                   variant_b_sent, variant_b_replies, variant_b_reply_rate,
                   variant_c_sent, variant_c_replies, variant_c_reply_rate,
                   created_at, completed_at
            FROM ab_tests WHERE id = ?
        ''', (test_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        return {
            'test_name': result[0],
            'status': result[1],
            'winning_variant': result[2],
            'variant_a': {
                'sent': result[3],
                'replies': result[4],
                'reply_rate': result[5]
            },
            'variant_b': {
                'sent': result[6],
                'replies': result[7],
                'reply_rate': result[8]
            },
            'variant_c': {
                'sent': result[9],
                'replies': result[10],
                'reply_rate': result[11]
            },
            'created_at': result[12],
            'completed_at': result[13]
        }
    
    def get_all_active_tests(self) -> List[Dict]:
        """Get all active tests"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, test_name, status, 
                   variant_a_sent + variant_b_sent + variant_c_sent as total_sent,
                   winning_variant
            FROM ab_tests 
            WHERE status = 'active'
            ORDER BY created_at DESC
        ''')
        
        tests = []
        for row in cursor.fetchall():
            tests.append({
                'id': row[0],
                'test_name': row[1],
                'status': row[2],
                'total_sent': row[3],
                'winning_variant': row[4]
            })
        
        conn.close()
        return tests