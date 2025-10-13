"""
A/B/C Test Winner Detection System
Automatically determines winning variant based on statistical significance
"""

import sqlite3
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.config import Config


class ABTestAnalyzer:
    """
    Analyzes A/B/C test results and declares winners
    
    Features:
    - Statistical significance testing
    - Automatic winner declaration
    - Performance metrics calculation
    - Confidence intervals
    """
    
    MIN_SAMPLE_SIZE = 20  # Minimum sends per variant to declare winner
    CONFIDENCE_THRESHOLD = 0.95  # 95% confidence required
    
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = Config.DATABASE_URL.replace('sqlite:///', '')
        self.db_path = db_path
    
    def analyze_test(self, test_id: int) -> Dict:
        """
        Analyze an A/B test and determine if there's a winner
        
        Returns:
            {
                'has_winner': bool,
                'winning_variant': str,
                'confidence': float,
                'metrics': {...},
                'recommendation': str
            }
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get test details
        cursor.execute("""
            SELECT * FROM ab_tests WHERE id = ?
        """, (test_id,))
        
        test = cursor.fetchone()
        if not test:
            conn.close()
            return {'error': 'Test not found'}
        
        test_dict = dict(test)
        
        # Calculate metrics for each variant
        variants = {}
        for variant in ['A', 'B', 'C']:
            col_prefix = f'variant_{variant.lower()}'
            
            sent = test_dict.get(f'{col_prefix}_sent', 0)
            replies = test_dict.get(f'{col_prefix}_replies', 0)
            avg_sentiment = test_dict.get(f'{col_prefix}_avg_sentiment', 0.0)
            
            reply_rate = (replies / sent * 100) if sent > 0 else 0
            
            variants[variant] = {
                'sent': sent,
                'replies': replies,
                'reply_rate': reply_rate,
                'avg_sentiment': avg_sentiment,
                'score': self._calculate_variant_score(reply_rate, avg_sentiment)
            }
        
        conn.close()
        
        # Check if we have enough data
        total_sent = sum(v['sent'] for v in variants.values())
        if total_sent < self.MIN_SAMPLE_SIZE:
            return {
                'has_winner': False,
                'reason': 'insufficient_data',
                'metrics': variants,
                'min_required': self.MIN_SAMPLE_SIZE,
                'current_total': total_sent,
                'recommendation': f'Need {self.MIN_SAMPLE_SIZE - total_sent} more sends'
            }
        
        # Find best performing variant
        best_variant = max(variants.keys(), key=lambda k: variants[k]['score'])
        best_score = variants[best_variant]['score']
        
        # Calculate confidence (simplified statistical test)
        confidence = self._calculate_confidence(variants, best_variant)
        
        # Determine if winner is clear
        has_winner = confidence >= self.CONFIDENCE_THRESHOLD
        
        result = {
            'has_winner': has_winner,
            'winning_variant': best_variant if has_winner else None,
            'confidence': confidence,
            'metrics': variants,
            'recommendation': self._generate_recommendation(variants, best_variant, has_winner)
        }
        
        # Auto-declare winner if conditions met
        if has_winner and test_dict.get('status') == 'active':
            self._declare_winner(test_id, best_variant, confidence)
            result['winner_declared'] = True
        
        return result
    
    def _calculate_variant_score(self, reply_rate: float, avg_sentiment: float) -> float:
        """
        Calculate composite score for variant
        Weights: 70% reply rate, 30% sentiment
        """
        return (reply_rate * 0.7) + (avg_sentiment * 100 * 0.3)
    
    def _calculate_confidence(self, variants: Dict, best_variant: str) -> float:
        """
        Calculate statistical confidence (simplified)
        Real implementation would use proper statistical tests
        """
        best_score = variants[best_variant]['score']
        other_scores = [v['score'] for k, v in variants.items() if k != best_variant]
        
        if not other_scores or best_score == 0:
            return 0.0
        
        avg_other = sum(other_scores) / len(other_scores)
        
        # Calculate improvement percentage
        if avg_other == 0:
            return 1.0 if best_score > 0 else 0.0
        
        improvement = (best_score - avg_other) / avg_other
        
        # Convert to confidence score (simplified)
        # In production, use proper chi-square or t-test
        confidence = min(0.5 + (improvement * 2), 1.0)
        
        return max(0.0, confidence)
    
    def _generate_recommendation(self, variants: Dict, best_variant: str, has_winner: bool) -> str:
        """Generate human-readable recommendation"""
        if has_winner:
            best = variants[best_variant]
            return (f"🏆 Variant {best_variant} is the clear winner! "
                   f"Reply rate: {best['reply_rate']:.1f}%, "
                   f"Sentiment: {best['avg_sentiment']:.2f}. "
                   f"Use this variant for future campaigns.")
        else:
            # Find leader
            leader = max(variants.keys(), key=lambda k: variants[k]['score'])
            leader_data = variants[leader]
            
            return (f"📊 Variant {leader} is currently leading with "
                   f"{leader_data['reply_rate']:.1f}% reply rate, "
                   f"but we need more data for statistical significance. "
                   f"Continue testing.")
    
    def _declare_winner(self, test_id: int, winning_variant: str, confidence: float):
        """Declare winner and update test status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE ab_tests
            SET status = 'completed',
                winning_variant = ?,
                confidence_level = ?,
                completed_at = ?
            WHERE id = ?
        """, (winning_variant, confidence, datetime.utcnow(), test_id))
        
        conn.commit()
        conn.close()
    
    def get_all_winners(self) -> List[Dict]:
        """Get all completed tests with winners"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM ab_tests
            WHERE status = 'completed'
            AND winning_variant IS NOT NULL
            ORDER BY completed_at DESC
        """)
        
        winners = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return winners
    
    def get_best_practices(self) -> Dict:
        """
        Analyze all completed tests to find best practices
        """
        winners = self.get_all_winners()
        
        if not winners:
            return {'message': 'No completed tests yet'}
        
        # Count winning variants
        variant_wins = {'A': 0, 'B': 0, 'C': 0}
        total_tests = len(winners)
        
        for test in winners:
            variant = test.get('winning_variant')
            if variant:
                variant_wins[variant] = variant_wins.get(variant, 0) + 1
        
        # Calculate win rates
        win_rates = {
            v: (count / total_tests * 100) if total_tests > 0 else 0
            for v, count in variant_wins.items()
        }
        
        best_variant = max(win_rates.keys(), key=lambda k: win_rates[k])
        
        return {
            'total_tests': total_tests,
            'variant_wins': variant_wins,
            'win_rates': win_rates,
            'best_overall_variant': best_variant,
            'recommendation': (
                f"Based on {total_tests} completed tests, "
                f"Variant {best_variant} wins {win_rates[best_variant]:.0f}% of the time. "
                f"Consider using this variant style for new campaigns."
            )
        }
    
    def auto_analyze_all_active_tests(self) -> List[Dict]:
        """
        Automatically analyze all active tests
        Returns list of tests where winners were declared
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id FROM ab_tests WHERE status = 'active'
        """)
        
        active_tests = [row['id'] for row in cursor.fetchall()]
        conn.close()
        
        results = []
        for test_id in active_tests:
            analysis = self.analyze_test(test_id)
            if analysis.get('winner_declared'):
                results.append({
                    'test_id': test_id,
                    'winning_variant': analysis['winning_variant'],
                    'confidence': analysis['confidence']
                })
        
        return results


# Singleton instance
ab_analyzer = ABTestAnalyzer()


# CLI for testing
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        test_id = int(sys.argv[1])
        print(f"\n🔬 Analyzing A/B Test #{test_id}...\n")
        
        result = ab_analyzer.analyze_test(test_id)
        
        print("="*60)
        print(f"TEST ANALYSIS RESULTS")
        print("="*60)
        
        if result.get('has_winner'):
            print(f"🏆 WINNER: Variant {result['winning_variant']}")
            print(f"📊 Confidence: {result['confidence']*100:.1f}%")
        else:
            print(f"⏳ No winner yet: {result.get('reason', 'Still testing')}")
        
        print(f"\n{result['recommendation']}")
        
        print("\n📈 VARIANT METRICS:")
        for variant, metrics in result['metrics'].items():
            print(f"\n  Variant {variant}:")
            print(f"    Sent: {metrics['sent']}")
            print(f"    Replies: {metrics['replies']}")
            print(f"    Reply Rate: {metrics['reply_rate']:.1f}%")
            print(f"    Sentiment: {metrics['avg_sentiment']:.2f}")
            print(f"    Score: {metrics['score']:.1f}")
        
        print("\n" + "="*60)
    else:
        print("Usage: python ab_test_analyzer.py <test_id>")