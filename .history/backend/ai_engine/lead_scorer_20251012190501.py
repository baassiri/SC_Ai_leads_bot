"""
SC AI Lead Generation System - AI Lead Scorer
Score leads based on persona match, profile quality, and business fit
"""

import sys
from pathlib import Path
from typing import Dict, Optional

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from backend.config import Config


class LeadScorer:
    """Score leads using rule-based + AI scoring"""
    
    def __init__(self, openai_api_key: str = None):
        """Initialize lead scorer"""
        self.api_key = openai_api_key or Config.OPENAI_API_KEY
        self.client = None
        
        # Scoring weights from config
        self.weights = Config.SCORING_WEIGHTS
        
        # Initialize OpenAI if available
        if OPENAI_AVAILABLE and self.api_key and not self.api_key.startswith('sk-your-'):
            try:
                self.client = OpenAI(api_key=self.api_key)
                print("✅ OpenAI client initialized for lead scoring")
            except Exception as e:
                print(f"⚠️  OpenAI initialization failed: {str(e)}")
    
    def score_lead(self, lead_data: Dict, persona_data: Dict = None) -> Dict:
        """
        Score a lead on 0-100 scale
        
        Args:
            lead_data: Dict with name, title, company, location, etc.
            persona_data: Target persona information
            
        Returns:
            Dict with 'score', 'reasoning', and 'breakdown'
        """
        # Calculate individual component scores
        title_score = self._score_title_match(lead_data, persona_data)
        company_score = self._score_company_size(lead_data)
        geo_score = self._score_geography(lead_data, persona_data)
        profile_score = self._score_profile_quality(lead_data)
        
        # Calculate weighted total
        final_score = (
            title_score * self.weights['title_match'] +
            company_score * self.weights['company_size'] +
            geo_score * self.weights['geography'] +
            profile_score * self.weights['profile_quality']
        )
        
        # Round to integer
        final_score = round(final_score)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            final_score, title_score, company_score, 
            geo_score, profile_score, lead_data, persona_data
        )
        
        return {
            'score': final_score,
            'reasoning': reasoning,
            'breakdown': {
                'title_match': round(title_score),
                'company_size': round(company_score),
                'geography': round(geo_score),
                'profile_quality': round(profile_score)
            }
        }
    
    def _score_title_match(self, lead_data: Dict, persona_data: Dict = None) -> float:
        """Score job title relevance (0-100)"""
        title = (lead_data.get('title') or '').lower()
        
        if not title:
            return 30  # Low score for missing title
        
        # Get target titles from persona
        if persona_data:
            persona_name = persona_data.get('name', '').lower()
            
            # High-value title keywords by persona
            if persona_name in title:
                return 95
        
        # Generic high-value keywords
        high_value_keywords = [
            'owner', 'founder', 'ceo', 'director', 'president', 
            'vp', 'chief', 'head', 'partner', 'managing'
        ]
        
        medium_value_keywords = [
            'manager', 'lead', 'senior', 'principal', 'consultant'
        ]
        
        # Check for high-value keywords
        for keyword in high_value_keywords:
            if keyword in title:
                return 85
        
        # Check for medium-value keywords
        for keyword in medium_value_keywords:
            if keyword in title:
                return 65
        
        # Has a title but not a high-value one
        return 45
    
    def _score_company_size(self, lead_data: Dict) -> float:
        """Score based on company size (0-100)"""
        company_size = lead_data.get('company_size', '')
        
        if not company_size:
            return 50  # Neutral score if unknown
        
        # Extract number from strings like "11-50 employees"
        if '1-10' in company_size:
            return 60  # Small but can still afford services
        elif '11-50' in company_size:
            return 80  # Sweet spot
        elif '51-200' in company_size:
            return 90  # Great size
        elif '201-500' in company_size:
            return 85  # Good but may have existing vendors
        elif '500+' in company_size or '1000+' in company_size:
            return 70  # Harder to reach decision maker
        
        return 50
    
    def _score_geography(self, lead_data: Dict, persona_data: Dict = None) -> float:
        """Score based on location (0-100)"""
        location = (lead_data.get('location') or '').lower()
        
        if not location:
            return 50  # Neutral if unknown
        
        # Priority locations (major US metros with high purchasing power)
        tier_1_cities = [
            'new york', 'los angeles', 'san francisco', 'chicago', 
            'boston', 'miami', 'seattle', 'atlanta', 'dallas'
        ]
        
        tier_2_cities = [
            'houston', 'philadelphia', 'phoenix', 'san diego',
            'denver', 'portland', 'austin', 'nashville'
        ]
        
        # Check tier 1
        for city in tier_1_cities:
            if city in location:
                return 95
        
        # Check tier 2
        for city in tier_2_cities:
            if city in location:
                return 80
        
        # US location (but not major metro)
        if 'united states' in location or any(state in location for state in ['ca', 'ny', 'tx', 'fl']):
            return 65
        
        # International
        return 40
    
    def _score_profile_quality(self, lead_data: Dict) -> float:
        """Score profile completeness (0-100)"""
        score = 0
        
        # Check for presence of key fields
        if lead_data.get('name'):
            score += 20
        
        if lead_data.get('title'):
            score += 20
        
        if lead_data.get('company'):
            score += 20
        
        if lead_data.get('headline'):
            score += 15
        
        if lead_data.get('location'):
            score += 10
        
        if lead_data.get('summary'):
            score += 15
        
        return min(score, 100)
    
    def _generate_reasoning(self, final_score: float, title_score: float, 
                          company_score: float, geo_score: float, 
                          profile_score: float, lead_data: Dict, 
                          persona_data: Dict = None) -> str:
        """Generate human-readable scoring reasoning"""
        
        reasons = []
        
        # Title reasoning
        if title_score >= 85:
            reasons.append("✅ Excellent title match")
        elif title_score >= 65:
            reasons.append("👍 Good title relevance")
        else:
            reasons.append("⚠️  Title may not be decision-maker")
        
        # Company size reasoning
        if company_score >= 80:
            reasons.append("✅ Ideal company size")
        elif company_score >= 60:
            reasons.append("👍 Acceptable company size")
        
        # Geography reasoning
        if geo_score >= 90:
            reasons.append("✅ Premium location")
        elif geo_score >= 70:
            reasons.append("👍 Good geographic market")
        
        # Profile quality reasoning
        if profile_score >= 80:
            reasons.append("✅ Complete profile")
        elif profile_score < 60:
            reasons.append("⚠️  Limited profile information")
        
        return " | ".join(reasons)


# Singleton instance
_lead_scorer = None

def get_lead_scorer(api_key: str = None) -> LeadScorer:
    """Get or create lead scorer instance"""
    global _lead_scorer
    if _lead_scorer is None:
        _lead_scorer = LeadScorer(openai_api_key=api_key)
    return _lead_scorer


# Convenience function
def score_lead(lead_data: Dict, persona_data: Dict = None, api_key: str = None) -> Dict:
    """Score a lead - convenience wrapper"""
    scorer = get_lead_scorer(api_key=api_key)
    return scorer.score_lead(lead_data, persona_data)


# CLI for testing
if __name__ == '__main__':
    # Test with sample lead
    test_lead = {
        'name': 'Dr. Sarah Johnson',
        'title': 'Owner & Medical Director',
        'company': 'Beverly Hills Aesthetics',
        'location': 'Los Angeles, CA',
        'company_size': '11-50 employees',
        'headline': 'Board-Certified Plastic Surgeon | Specializing in Facial Aesthetics',
        'summary': 'Over 15 years of experience in cosmetic surgery...'
    }
    
    test_persona = {
        'name': 'Plastic Surgeon',
        'description': 'The Prestige Provider'
    }
    
    print("\n" + "="*60)
    print("🧪 Testing Lead Scorer")
    print("="*60)
    
    result = score_lead(test_lead, test_persona)
    
    print(f"\n👤 Lead: {test_lead['name']}")
    print(f"💼 Title: {test_lead['title']}")
    print(f"🏢 Company: {test_lead['company']}")
    print(f"\n📊 SCORE: {result['score']}/100")
    print(f"\n💡 Reasoning: {result['reasoning']}")
    print(f"\n📈 Breakdown:")
    for component, score in result['breakdown'].items():
        print(f"   • {component}: {score}/100")
    
    print("\n" + "="*60)