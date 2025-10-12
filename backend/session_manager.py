"""
SC AI Lead Generation System - Session Manager
Stores AI analysis results and passes them to the scraper
"""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


class SessionManager:
    """Manage AI analysis results and scraping session data"""
    
    def __init__(self, storage_path: str = None):
        """
        Initialize session manager
        
        Args:
            storage_path: Path to store session data (defaults to data/session.json)
        """
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            # Default to data directory
            base_dir = Path(__file__).parent.parent
            self.storage_path = base_dir / 'data' / 'session.json'
        
        # Ensure directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage if it doesn't exist
        if not self.storage_path.exists():
            self._initialize_storage()
    
    def _initialize_storage(self):
        """Create empty session storage"""
        initial_data = {
            'ai_analysis': None,
            'linkedin_query': '',
            'target_personas': [],
            'last_updated': None,
            'scraping_config': {
                'max_pages': 1,
                'max_leads': 100,
                'filters_active': False
            }
        }
        
        with open(self.storage_path, 'w') as f:
            json.dump(initial_data, f, indent=2)
        
        print(f"✅ Initialized session storage at: {self.storage_path}")
    
    def _load_session(self) -> Dict:
        """Load session data from storage"""
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading session: {e}")
            return {}
    
    def _save_session(self, session_data: Dict):
        """Save session data to storage"""
        try:
            session_data['last_updated'] = datetime.utcnow().isoformat()
            
            with open(self.storage_path, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            print(f"✅ Session saved: {self.storage_path}")
        except Exception as e:
            print(f"Error saving session: {e}")
    
    def save_ai_analysis(self, analysis: Dict) -> bool:
        """
        Save AI analysis results from document upload
        
        Args:
            analysis: Dict containing:
                - personas: List of persona dicts
                - linkedin_search_query: Generated LinkedIn query
                - primary_titles: List of job titles
                - primary_industries: List of industries
        
        Returns:
            bool: True if successful
        """
        try:
            session = self._load_session()
            
            # Store full AI analysis
            session['ai_analysis'] = analysis
            
            # Extract key fields for easy access
            session['linkedin_query'] = analysis.get('linkedin_search_query', '')
            session['target_personas'] = [p.get('name', 'Unknown') for p in analysis.get('personas', [])]
            session['scraping_config']['filters_active'] = True
            
            self._save_session(session)
            
            print(f"✅ Saved AI analysis for {len(session['target_personas'])} personas")
            print(f"   LinkedIn Query: {session['linkedin_query'][:100]}...")
            
            return True
        except Exception as e:
            print(f"Error saving AI analysis: {e}")
            return False
    
    def get_ai_analysis(self) -> Optional[Dict]:
        """
        Get stored AI analysis results
        
        Returns:
            Dict with AI analysis or None if not found
        """
        try:
            session = self._load_session()
            return session.get('ai_analysis')
        except Exception as e:
            print(f"Error getting AI analysis: {e}")
            return None
    
    def get_linkedin_query(self) -> str:
        """
        Get the AI-generated LinkedIn search query
        
        Returns:
            str: LinkedIn search query or empty string
        """
        try:
            session = self._load_session()
            query = session.get('linkedin_query', '')
            
            if not query:
                print("⚠️  No LinkedIn query found - using default")
                return 'plastic surgeon dermatologist med spa owner aesthetic nurse'
            
            return query
        except Exception as e:
            print(f"Error getting LinkedIn query: {e}")
            return 'plastic surgeon dermatologist med spa owner aesthetic nurse'
    
    def get_target_personas(self) -> list:
        """
        Get list of target persona names
        
        Returns:
            List of persona names
        """
        try:
            session = self._load_session()
            return session.get('target_personas', [])
        except Exception as e:
            print(f"Error getting personas: {e}")
            return []
    
    def get_scraping_config(self) -> Dict:
        """
        Get scraping configuration
        
        Returns:
            Dict with scraping config (max_pages, max_leads, etc.)
        """
        try:
            session = self._load_session()
            return session.get('scraping_config', {
                'max_pages': 1,
                'max_leads': 100,
                'filters_active': False
            })
        except Exception as e:
            print(f"Error getting scraping config: {e}")
            return {'max_pages': 1, 'max_leads': 100, 'filters_active': False}
    
    def update_scraping_config(self, max_pages: int = None, max_leads: int = None) -> bool:
        """
        Update scraping configuration
        
        Args:
            max_pages: Maximum pages to scrape
            max_leads: Maximum leads to collect
        
        Returns:
            bool: True if successful
        """
        try:
            session = self._load_session()
            
            if max_pages is not None:
                session['scraping_config']['max_pages'] = max_pages
            
            if max_leads is not None:
                session['scraping_config']['max_leads'] = max_leads
            
            self._save_session(session)
            return True
        except Exception as e:
            print(f"Error updating scraping config: {e}")
            return False
    
    def has_active_analysis(self) -> bool:
        """
        Check if there's an active AI analysis available
        
        Returns:
            bool: True if AI analysis is stored and active
        """
        try:
            session = self._load_session()
            return session.get('scraping_config', {}).get('filters_active', False)
        except Exception as e:
            print(f"Error checking active analysis: {e}")
            return False
    
    def get_session_summary(self) -> Dict:
        """
        Get a summary of the current session
        
        Returns:
            Dict with session summary
        """
        try:
            session = self._load_session()
            
            return {
                'has_analysis': session.get('ai_analysis') is not None,
                'personas_count': len(session.get('target_personas', [])),
                'personas': session.get('target_personas', []),
                'linkedin_query': session.get('linkedin_query', ''),
                'filters_active': session.get('scraping_config', {}).get('filters_active', False),
                'last_updated': session.get('last_updated'),
                'config': session.get('scraping_config', {})
            }
        except Exception as e:
            print(f"Error getting session summary: {e}")
            return {
                'has_analysis': False,
                'personas_count': 0,
                'personas': [],
                'linkedin_query': '',
                'filters_active': False,
                'last_updated': None,
                'config': {}
            }
    
    def clear_session(self) -> bool:
        """
        Clear all session data
        
        Returns:
            bool: True if successful
        """
        try:
            self._initialize_storage()
            print("✅ Session cleared")
            return True
        except Exception as e:
            print(f"Error clearing session: {e}")
            return False


# Singleton instance
session_manager = SessionManager()


# CLI for testing
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Session Manager')
    parser.add_argument('--show', action='store_true', help='Show session summary')
    parser.add_argument('--clear', action='store_true', help='Clear session')
    parser.add_argument('--query', action='store_true', help='Show LinkedIn query')
    
    args = parser.parse_args()
    
    if args.show:
        summary = session_manager.get_session_summary()
        print("\n📋 Session Summary:")
        print(json.dumps(summary, indent=2))
    
    if args.query:
        query = session_manager.get_linkedin_query()
        print(f"\n🔍 LinkedIn Query:")
        print(f"   {query}")
    
    if args.clear:
        if session_manager.clear_session():
            print("✅ Session cleared")