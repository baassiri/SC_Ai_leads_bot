"""
Optimal Time AI - Determines best times to send messages
Uses simple heuristics and can be enhanced with ML in future
"""

from datetime import datetime, timedelta
from typing import List, Dict
import random


class OptimalTimeAI:
    """AI-powered optimal time calculator for message sending"""
    
    def __init__(self):
        # Best times based on LinkedIn engagement data
        self.peak_hours = [
            (10, 11),  # 10-11 AM - Morning coffee time
            (14, 15),  # 2-3 PM - Post-lunch check
            (16, 17),  # 4-5 PM - End of day wrap-up
        ]
        
        # Good hours (still business hours but lower engagement)
        self.good_hours = [9, 11, 12, 13, 15, 16, 17]
        
        # Avoid these hours
        self.avoid_hours = list(range(0, 9)) + list(range(18, 24))
    
    def get_optimal_time(self, preferred_time: datetime = None) -> datetime:
        """
        Get the optimal time to send a message
        
        Args:
            preferred_time: User's preferred time (optional)
        
        Returns:
            Optimized datetime for sending
        """
        if preferred_time is None:
            preferred_time = datetime.now()
        
        # Start from preferred time
        optimal_time = preferred_time
        
        # If it's outside business hours, move to next business day 9 AM
        if optimal_time.hour < 9 or optimal_time.hour >= 18:
            optimal_time = self._next_business_day(optimal_time, hour=9)
        
        # If it's weekend, move to Monday
        if optimal_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
            optimal_time = self._next_business_day(optimal_time, hour=9)
        
        # Try to align with peak hours if close
        optimal_time = self._align_to_peak_hour(optimal_time)
        
        return optimal_time
    
    def distribute_times(self, 
                        count: int, 
                        start_time: datetime = None,
                        spread_hours: int = 8,
                        ai_optimize: bool = True) -> List[datetime]:
        """
        Distribute multiple message send times intelligently
        
        Args:
            count: Number of messages to distribute
            start_time: When to start sending (default: now)
            spread_hours: Hours to spread messages over
            ai_optimize: Use AI optimization for timing
        
        Returns:
            List of optimal send times
        """
        if start_time is None:
            start_time = datetime.now()
        
        send_times = []
        
        if count == 0:
            return send_times
        
        # Calculate interval between messages
        interval_minutes = (spread_hours * 60) / count if count > 0 else 60
        
        current_time = start_time
        
        for i in range(count):
            if ai_optimize:
                # Use AI to optimize this time
                optimal_time = self.get_optimal_time(current_time)
            else:
                # Just use the scheduled time
                optimal_time = current_time
            
            # Ensure it's during business hours
            optimal_time = self._ensure_business_hours(optimal_time)
            
            send_times.append(optimal_time)
            
            # Move to next time slot
            current_time = current_time + timedelta(minutes=interval_minutes)
        
        return send_times
    
    def _align_to_peak_hour(self, time: datetime) -> datetime:
        """Adjust time to align with peak engagement hours"""
        current_hour = time.hour
        
        # Check if we're close to a peak hour
        for start_hour, end_hour in self.peak_hours:
            # If within 30 minutes of a peak hour, align to it
            if start_hour - 1 <= current_hour <= start_hour:
                return time.replace(hour=start_hour, minute=random.randint(0, 30))
            elif end_hour - 1 <= current_hour <= end_hour:
                return time.replace(hour=end_hour - 1, minute=random.randint(30, 59))
        
        # If not near peak, keep original time but add some randomness
        return time + timedelta(minutes=random.randint(-10, 10))
    
    def _ensure_business_hours(self, time: datetime) -> datetime:
        """Ensure time is during business hours (9 AM - 6 PM, Mon-Fri)"""
        # Check if weekend
        if time.weekday() >= 5:
            time = self._next_business_day(time, hour=9)
        
        # Check if outside business hours
        if time.hour < 9:
            time = time.replace(hour=9, minute=0)
        elif time.hour >= 18:
            time = self._next_business_day(time, hour=9)
        
        return time
    
    def _next_business_day(self, time: datetime, hour: int = 9) -> datetime:
        """Get next business day (Mon-Fri) at specified hour"""
        next_day = time + timedelta(days=1)
        next_day = next_day.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        # Skip weekend
        while next_day.weekday() >= 5:
            next_day = next_day + timedelta(days=1)
        
        return next_day
    
    def get_next_available_slot(self, after: datetime = None) -> datetime:
        """Get the next available time slot for sending a message"""
        if after is None:
            after = datetime.now()
        
        return self.get_optimal_time(after + timedelta(minutes=15))
    
    def analyze_send_time(self, time: datetime) -> Dict:
        """
        Analyze a proposed send time and provide quality score
        
        Returns:
            Dict with score (0-100) and reasoning
        """
        score = 50  # Base score
        reasons = []
        
        # Check day of week
        if time.weekday() < 5:  # Monday-Friday
            score += 20
            reasons.append("Weekday (+20)")
        else:
            score -= 30
            reasons.append("Weekend (-30)")
        
        # Check hour
        hour = time.hour
        if any(start <= hour < end for start, end in self.peak_hours):
            score += 30
            reasons.append("Peak hour (+30)")
        elif hour in self.good_hours:
            score += 15
            reasons.append("Good hour (+15)")
        elif hour in self.avoid_hours:
            score -= 40
            reasons.append("Off-hours (-40)")
        
        # Check if it's too close to now (< 5 minutes)
        if (time - datetime.now()).total_seconds() < 300:
            score -= 10
            reasons.append("Very soon (-10)")
        
        # Clamp score between 0-100
        score = max(0, min(100, score))
        
        return {
            'score': score,
            'quality': self._score_to_quality(score),
            'reasons': reasons,
            'recommended_time': self.get_optimal_time(time) if score < 70 else time
        }
    
    def _score_to_quality(self, score: int) -> str:
        """Convert numerical score to quality label"""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        else:
            return "Poor"


# Singleton instance
optimal_time_ai = OptimalTimeAI()


# Helper functions
def get_optimal_send_time(preferred_time: datetime = None) -> datetime:
    """Get optimal time to send a message"""
    return optimal_time_ai.get_optimal_time(preferred_time)


def distribute_send_times(count: int, start_time: datetime = None, 
                         spread_hours: int = 8, ai_optimize: bool = True) -> List[datetime]:
    """Distribute multiple send times intelligently"""
    return optimal_time_ai.distribute_times(count, start_time, spread_hours, ai_optimize)


def analyze_send_time(time: datetime) -> Dict:
    """Analyze a proposed send time"""
    return optimal_time_ai.analyze_send_time(time)


if __name__ == "__main__":
    # Test the AI
    print("\n" + "="*60)
    print("🧪 OPTIMAL TIME AI TEST")
    print("="*60)
    
    # Test 1: Get optimal time for now
    now = datetime.now()
    optimal = get_optimal_send_time(now)
    print(f"\nCurrent time: {now.strftime('%Y-%m-%d %H:%M')}")
    print(f"Optimal time: {optimal.strftime('%Y-%m-%d %H:%M')}")
    
    # Test 2: Analyze the optimal time
    analysis = analyze_send_time(optimal)
    print(f"\nTime Quality: {analysis['quality']} (Score: {analysis['score']})")
    print("Reasons:")
    for reason in analysis['reasons']:
        print(f"  • {reason}")
    
    # Test 3: Distribute 10 messages over 8 hours
    print(f"\n📅 Distributing 10 messages over 8 hours:")
    send_times = distribute_send_times(10, now, spread_hours=8, ai_optimize=True)
    for i, time in enumerate(send_times, 1):
        print(f"  {i:2}. {time.strftime('%Y-%m-%d %H:%M')} ({time.strftime('%A')})")
    
    print("\n" + "="*60)