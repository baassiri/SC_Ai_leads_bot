"""
Bot Controller - Manages LinkedIn automation bot operations
Coordinates between scraping, scoring, and message generation
"""

import threading
import time
from datetime import datetime
from typing import Dict, Optional, Callable

class BotController:
    """Controls the LinkedIn automation bot lifecycle"""
    
    def __init__(self, db_manager, scraper, lead_scorer, credentials_manager):
        """
        Initialize bot controller
        
        Args:
            db_manager: Database manager instance
            scraper: LinkedIn scraper instance
            lead_scorer: Lead scoring AI instance
            credentials_manager: Credentials manager instance
        """
        self.db_manager = db_manager
        self.scraper = scraper
        self.lead_scorer = lead_scorer
        self.credentials_manager = credentials_manager
        
        self.is_running = False
        self.current_activity = "Stopped"
        self.leads_scraped = 0
        self.progress = 0
        self.bot_thread = None
        self.stop_flag = threading.Event()
        
        # Callbacks
        self.on_status_change: Optional[Callable] = None
        self.on_lead_scraped: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
    
    def start(self, target_profiles: list = None, max_leads: int = 100) -> Dict:
        """
        Start the bot
        
        Args:
            target_profiles: List of target persona profiles to scrape
            max_leads: Maximum number of leads to scrape
        
        Returns:
            Dict with success status and message
        """
        if self.is_running:
            return {
                'success': False,
                'message': 'Bot is already running'
            }
        
        # Reset state
        self.stop_flag.clear()
        self.leads_scraped = 0
        self.progress = 0
        
        # Start bot thread
        self.bot_thread = threading.Thread(
            target=self._run_bot,
            args=(target_profiles, max_leads),
            daemon=True
        )
        self.bot_thread.start()
        
        self.is_running = True
        self._update_status("Starting bot...")
        
        self.db_manager.log_activity(
            activity_type='bot_started',
            description=f'Bot started (target: {max_leads} leads)',
            status='success'
        )
        
        return {
            'success': True,
            'message': 'Bot started successfully'
        }
    
    def stop(self) -> Dict:
        """
        Stop the bot
        
        Returns:
            Dict with success status and message
        """
        if not self.is_running:
            return {
                'success': False,
                'message': 'Bot is not running'
            }
        
        self._update_status("Stopping bot...")
        self.stop_flag.set()
        
        # Wait for thread to finish (with timeout)
        if self.bot_thread:
            self.bot_thread.join(timeout=10)
        
        self.is_running = False
        self._update_status("Stopped")
        
        self.db_manager.log_activity(
            activity_type='bot_stopped',
            description=f'Bot stopped (scraped {self.leads_scraped} leads)',
            status='success'
        )
        
        return {
            'success': True,
            'message': f'Bot stopped successfully (scraped {self.leads_scraped} leads)'
        }
    
    def get_status(self) -> Dict:
        """
        Get current bot status
        
        Returns:
            Dict with bot status information
        """
        return {
            'running': self.is_running,
            'current_activity': self.current_activity,
            'leads_scraped': self.leads_scraped,
            'progress': self.progress
        }
    
    def _run_bot(self, target_profiles: list, max_leads: int):
        """
        Main bot execution loop (runs in separate thread)
        
        Args:
            target_profiles: List of target personas
            max_leads: Maximum leads to scrape
        """
        try:
            # Get personas from database if none provided
            if not target_profiles or len(target_profiles) == 0:
                self._update_status("Loading personas...")
                personas = self.db_manager.get_all_personas()
                if not personas or len(personas) == 0:
                    self._on_error_internal("No personas found. Please upload a target document first.")
                    self.is_running = False
                    return
                target_profiles = personas
            
            total_personas = len(target_profiles)
            
            # Process each persona
            for idx, persona in enumerate(target_profiles):
                if self.stop_flag.is_set():
                    break
                
                self._update_status(f"Scraping persona {idx+1}/{total_personas}: {persona.get('job_title', 'Unknown')}")
                self.progress = int((idx / total_personas) * 100)
                
                try:
                    # Scrape leads for this persona
                    leads_per_persona = max_leads // total_personas
                    scraped_leads = self._scrape_for_persona(persona, leads_per_persona)
                    
                    # Score and save leads
                    for lead in scraped_leads:
                        if self.stop_flag.is_set():
                            break
                        
                        self._process_lead(lead, persona)
                        self.leads_scraped += 1
                        
                        if self.on_lead_scraped:
                            self.on_lead_scraped(lead)
                        
                        # Small delay to avoid rate limiting
                        time.sleep(2)
                
                except Exception as e:
                    print(f"Error processing persona {persona.get('job_title')}: {e}")
                    self._on_error_internal(f"Error scraping persona: {str(e)}")
            
            # Done
            self.is_running = False
            self.progress = 100
            self._update_status(f"Completed - Scraped {self.leads_scraped} leads")
            
        except Exception as e:
            print(f"Fatal error in bot: {e}")
            self._on_error_internal(f"Bot error: {str(e)}")
            self.is_running = False
            self._update_status("Error - Stopped")
    
    def _scrape_for_persona(self, persona: Dict, max_leads: int) -> list:
        """
        Scrape leads for a specific persona
        
        Args:
            persona: Persona dictionary
            max_leads: Maximum leads to scrape
        
        Returns:
            List of scraped leads
        """
        # Build search query from persona
        search_query = self._build_search_query(persona)
        
        # Scrape LinkedIn
        leads = self.scraper.search_leads(
            query=search_query,
            max_results=max_leads
        )
        
        return leads
    
    def _build_search_query(self, persona: Dict) -> str:
        """
        Build LinkedIn search query from persona
        
        Args:
            persona: Persona dictionary
        
        Returns:
            Search query string
        """
        query_parts = []
        
        # Add job title
        if persona.get('job_title'):
            query_parts.append(persona['job_title'])
        
        # Add company type
        if persona.get('company_type'):
            query_parts.append(persona['company_type'])
        
        # Add keywords
        if persona.get('linkedin_keywords'):
            keywords = persona['linkedin_keywords']
            if isinstance(keywords, str):
                query_parts.append(keywords)
        
        # Use smart search query if available
        if persona.get('smart_search_query'):
            return persona['smart_search_query']
        
        return ' '.join(query_parts)
    
    def _process_lead(self, lead: Dict, persona: Dict):
        """
        Score and save a lead
        
        Args:
            lead: Lead data dictionary
            persona: Persona the lead was scraped for
        """
        # Score the lead
        score = self.lead_scorer.score_lead(lead, persona)
        lead['ai_score'] = score
        lead['persona_id'] = persona.get('id')
        lead['status'] = 'new'
        lead['scraped_at'] = datetime.now().isoformat()
        
        # Save to database
        lead_id = self.db_manager.save_lead(lead)
        
        # Log activity
        self.db_manager.log_activity(
            activity_type='lead_scraped',
            description=f"Scraped lead: {lead.get('name', 'Unknown')} (Score: {score})",
            status='success'
        )
        
        return lead_id
    
    def _update_status(self, activity: str):
        """Update bot status and notify listeners"""
        self.current_activity = activity
        
        if self.on_status_change:
            self.on_status_change(self.get_status())
    
    def _on_error_internal(self, error_message: str):
        """Handle internal errors"""
        print(f"Bot error: {error_message}")
        
        self.db_manager.log_activity(
            activity_type='bot_error',
            description=error_message,
            status='error'
        )
        
        if self.on_error:
            self.on_error(error_message)


# Singleton instance
_bot_controller_instance = None

def get_bot_controller(db_manager=None, scraper=None, lead_scorer=None, credentials_manager=None):
    """
    Get or create bot controller singleton
    
    Args:
        db_manager: Database manager (required on first call)
        scraper: Scraper instance (required on first call)
        lead_scorer: Lead scorer instance (required on first call)
        credentials_manager: Credentials manager (required on first call)
    
    Returns:
        BotController instance
    """
    global _bot_controller_instance
    
    if _bot_controller_instance is None:
        if not all([db_manager, scraper, lead_scorer, credentials_manager]):
            raise ValueError("All parameters required for first initialization")
        
        _bot_controller_instance = BotController(
            db_manager,
            scraper,
            lead_scorer,
            credentials_manager
        )
    
    return _bot_controller_instance