"""
SC AI Lead Generation System - AB Test Analyzer
Automatically detect winning variants using statistical analysis
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import statistics

sys.path.append(str(Path(__file__).parent.parent))

from backend.database.db_manager import db_manager


class ABTestAnalyzer:
    """Analyze AB tests and detect winning variants"""
    
    def __init__(self):
        self.min_sample_size = 20  # Minimum sends per variant
        self.confidence_threshold = 0.10  # 10% improvement needed
    
    def analyze_test(self, test_id: int) -> Dict:
        """
        Analyze a specific AB test
        
        Returns:
            Dict with analysis results including winner if detected
        """
        test = db_manager.get_ab_test_by_id(test_id)
        
        if not test:
            return {'error': 'Test not found'}
        
        # Get variant stats
        variant_a = test['variant_a']
        variant_b = test['variant_b']
        variant_c = test['variant_c']
        
        # Check if we have enough data
        if (variant_a['sent'] < self.min_sample_size or
            variant_b['sent'] < self.min_sample_size or
            variant_c['sent'] < self.min_sample_size):
            return {
                'test_id': test_id,
                'test_name': test['test_name'],
                'status': 'insufficient_data',
                'message': f'Need at least {self.min_sample_size} sends per variant',
                'variants': {
                    'A': variant_a,
                    'B': variant_b,
                    'C': variant_c
                }
            }
        
        # Calculate which variant is performing best
        variants = {
            'A': variant_a,
            'B': variant_b,
            'C': variant_c
        }
        
        # Find best performer
        best_variant = max(variants.keys(), key=lambda v: variants[v]['reply_rate'])
        best_rate = variants[best_variant]['reply_rate']
        
        # Check if winner is statistically significant
        other_rates = [variants[v]['reply_rate'] for v in variants if v != best_variant]
        avg_other_rate = statistics.mean(other_rates)
        
        improvement = best_rate - avg_other_rate
        is_significant = improvement >= (self.confidence_threshold * 100)
        
        analysis = {
            'test_id': test_id,
            'test_name': test['test_name'],
            'status': test['status'],
            'variants': variants,
            'best_variant': best_variant,
            'best_reply_rate': best_rate,
            'improvement': round(improvement, 2),
            'is_significant': is_significant,
            'confidence': round((improvement / avg_other_rate * 100) if avg_other_rate > 0 else 0, 1)
        }
        
        # Auto-declare winner if significant and test is active
        if is_significant and test['status'] == 'active':
            db_manager.update_ab_test_status(test_id, 'completed')
            
            # Update winning variant
            with db_manager.session_scope() as session:
                from backend.database.models import ABTest
                ab_test = session.query(ABTest).filter(ABTest.id == test_id).first()
                if ab_test:
                    ab_test.winning_variant = best_variant
                    ab_test.completed_at = datetime.utcnow()
            
            analysis['auto_winner_declared'] = True
            
            print(f"🏆 WINNER DECLARED: Variant {best_variant} for test '{test['test_name']}'")
            print(f"   Reply Rate: {best_rate:.1f}% (Improvement: +{improvement:.1f}%)")
        
        return analysis
    
    def auto_analyze_all_active_tests(self) -> List[Dict]:
        """
        Analyze all active AB tests and declare winners where appropriate
        
        Returns:
            List of tests where winners were declared
        """
        active_tests = db_manager.get_active_ab_tests()
        
        winners = []
        
        for test in active_tests:
            analysis = self.analyze_test(test['id'])
            
            if analysis.get('auto_winner_declared'):
                winners.append({
                    'test_id': test['id'],
                    'test_name': test['test_name'],
                    'winning_variant': analysis['best_variant'],
                    'reply_rate': analysis['best_reply_rate'],
                    'improvement': analysis['improvement'],
                    'confidence': analysis['confidence']
                })
        
        return winners
    
    def get_best_practices(self) -> Dict:
        """
        Analyze all completed tests to extract best practices
        
        Returns:
            Dict with insights and patterns
        """
        all_tests = db_manager.get_all_ab_tests(status='completed')
        
        if not all_tests:
            return {
                'message': 'No completed tests yet',
                'insights': []
            }
        
        insights = {
            'total_completed_tests': len(all_tests),
            'variant_performance': {
                'A': {'wins': 0, 'avg_reply_rate': 0, 'total_tests': 0},
                'B': {'wins': 0, 'avg_reply_rate': 0, 'total_tests': 0},
                'C': {'wins': 0, 'avg_reply_rate': 0, 'total_tests': 0}
            },
            'top_performers': [],
            'patterns': []
        }
        
        # Analyze each completed test
        for test in all_tests:
            winner = test.get('winning_variant')
            
            if winner:
                insights['variant_performance'][winner]['wins'] += 1
            
            # Get full test data
            full_test = db_manager.get_ab_test_by_id(test['id'])
            
            if full_test:
                for variant_letter in ['A', 'B', 'C']:
                    variant_key = f'variant_{variant_letter.lower()}'
                    variant_data = full_test.get(variant_key, {})
                    
                    reply_rate = variant_data.get('reply_rate', 0)
                    insights['variant_performance'][variant_letter]['total_tests'] += 1
                    
                    # Calculate running average
                    current_avg = insights['variant_performance'][variant_letter]['avg_reply_rate']
                    total = insights['variant_performance'][variant_letter]['total_tests']
                    
                    new_avg = ((current_avg * (total - 1)) + reply_rate) / total
                    insights['variant_performance'][variant_letter]['avg_reply_rate'] = round(new_avg, 2)
        
        # Find top performing tests
        for test in all_tests:
            full_test = db_manager.get_ab_test_by_id(test['id'])
            if full_test and full_test.get('winning_variant'):
                winner = full_test['winning_variant']
                winner_data = full_test.get(f'variant_{winner.lower()}', {})
                
                insights['top_performers'].append({
                    'test_name': test['test_name'],
                    'winning_variant': winner,
                    'reply_rate': winner_data.get('reply_rate', 0),
                    'completed_at': test.get('completed_at')
                })
        
        # Sort top performers by reply rate
        insights['top_performers'] = sorted(
            insights['top_performers'],
            key=lambda x: x['reply_rate'],
            reverse=True
        )[:5]  # Top 5
        
        # Generate insights
        patterns = []
        
        # Which variant wins most often?
        best_variant = max(
            insights['variant_performance'].keys(),
            key=lambda v: insights['variant_performance'][v]['wins']
        )
        
        patterns.append(
            f"Variant {best_variant} wins most often ({insights['variant_performance'][best_variant]['wins']} times)"
        )
        
        # Which has highest average reply rate?
        highest_avg = max(
            insights['variant_performance'].keys(),
            key=lambda v: insights['variant_performance'][v]['avg_reply_rate']
        )
        
        patterns.append(
            f"Variant {highest_avg} has highest avg reply rate ({insights['variant_performance'][highest_avg]['avg_reply_rate']:.1f}%)"
        )
        
        insights['patterns'] = patterns
        
        return insights
    
    def get_all_winners(self) -> List[Dict]:
        """Get all tests with declared winners"""
        completed = db_manager.get_all_ab_tests(status='completed')
        
        winners = []
        for test in completed:
            if test.get('winning_variant'):
                full_test = db_manager.get_ab_test_by_id(test['id'])
                if full_test:
                    winner = test['winning_variant']
                    winner_data = full_test.get(f'variant_{winner.lower()}', {})
                    
                    winners.append({
                        'test_id': test['id'],
                        'test_name': test['test_name'],
                        'winning_variant': winner,
                        'reply_rate': winner_data.get('reply_rate', 0),
                        'total_sent': winner_data.get('sent', 0),
                        'total_replies': winner_data.get('replies', 0),
                        'completed_at': test.get('completed_at')
                    })
        
        return winners
    
    def compare_variants(self, test_id: int) -> Dict:
        """
        Get detailed comparison of variants
        
        Returns:
            Detailed comparison data for visualization
        """
        test = db_manager.get_ab_test_by_id(test_id)
        
        if not test:
            return {'error': 'Test not found'}
        
        comparison = {
            'test_name': test['test_name'],
            'status': test['status'],
            'winning_variant': test.get('winning_variant'),
            'variants': []
        }
        
        for variant_letter in ['A', 'B', 'C']:
            variant_data = test[f'variant_{variant_letter.lower()}']
            
            comparison['variants'].append({
                'variant': variant_letter,
                'sent': variant_data['sent'],
                'replies': variant_data['replies'],
                'reply_rate': variant_data['reply_rate'],
                'avg_sentiment': variant_data['avg_sentiment'],
                'positive_replies': variant_data['positive_replies'],
                'is_winner': variant_letter == test.get('winning_variant')
            })
        
        return comparison


# Singleton instance
ab_analyzer = ABTestAnalyzer()


if __name__ == '__main__':
    # Test the analyzer
    print("\n" + "="*60)
    print("🧪 AB TEST ANALYZER TEST")
    print("="*60)
    
    # Get active tests
    active = db_manager.get_active_ab_tests()
    print(f"\n📊 Found {len(active)} active tests")
    
    if active:
        test_id = active[0]['id']
        print(f"\n🔍 Analyzing test: {active[0]['test_name']}")
        
        analysis = ab_analyzer.analyze_test(test_id)
        
        print(f"\n📈 Results:")
        print(f"   Status: {analysis['status']}")
        print(f"   Best Variant: {analysis.get('best_variant', 'N/A')}")
        print(f"   Reply Rate: {analysis.get('best_reply_rate', 0):.1f}%")
        
        if analysis.get('is_significant'):
            print(f"   ✅ Statistically significant!")
    else:
        print("\n⚠️ No active tests to analyze")