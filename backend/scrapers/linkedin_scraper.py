"""
SC AI Lead Generation System - LinkedIn Sales Navigator Scraper
Selenium-based automation for scraping leads from LinkedIn
FIXED VERSION - Complete implementation
"""

import time
import random
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Fix Python path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Now import backend modules
try:
    from backend.config import Config
    from backend.utils.csv_handler import csv_handler
    from backend.database.db_manager import db_manager
    USE_DATABASE = True
except ImportError:
    print("⚠️ Warning: Database modules not available. Will save to CSV only.")
    USE_DATABASE = False
    
    # Create a minimal Config class for standalone operation
    class Config:
        SCRAPE_DELAY_MIN = 2
        SCRAPE_DELAY_MAX = 5
        MAX_LEADS_PER_SESSION = 100
        EXPORT_DIR = Path(__file__).parent / 'exports'
    
    # Create a minimal csv_handler
    class CSVHandler:
        def __init__(self):
            self.export_dir = Config.EXPORT_DIR
            self.export_dir.mkdir(parents=True, exist_ok=True)
        
        def save_scrape_backup(self, leads, source='linkedin'):
            import csv
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'scrape_backup_{source}_{timestamp}.csv'
            filepath = self.export_dir / filename
            
            headers = ['name', 'title', 'company', 'industry', 'location', 'profile_url', 
                      'headline', 'company_size', 'ai_score', 'status']
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(leads)
            
            print(f"✅ Saved to {filepath}")
            return str(filepath)
    
    csv_handler = CSVHandler()


class LinkedInScraper:
    """LinkedIn Sales Navigator scraper using Selenium"""
    
    def __init__(self, email: str, password: str, headless: bool = False, sales_nav_preference: bool = False):
        """
        Initialize LinkedIn scraper
        
        Args:
            email: LinkedIn email/username
            password: LinkedIn password
            headless: Run browser in headless mode (invisible)
            sales_nav_preference: User's preference for using Sales Navigator
        """
        self.email = email
        self.password = password
        self.headless = headless
        self.sales_nav_preference = sales_nav_preference
        self.driver = None
        self.wait = None
        
        # Stats tracking
        self.stats = {
            'leads_scraped': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None,
            'using_sales_nav': False
        }
        
    def setup_driver(self):
        """Set up Chrome WebDriver with options"""
        print("🔧 Setting up Chrome WebDriver...")
        
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
            print("  → Running in headless mode (invisible)")
        
        # Additional options for stability
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Set user agent to avoid detection
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Initialize driver
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            print(f"❌ Error setting up Chrome driver: {str(e)}")
            print("\n💡 Trying alternative setup...")
            self.driver = webdriver.Chrome(options=chrome_options)
        
        self.wait = WebDriverWait(self.driver, 20)
        
        # Maximize window
        if not self.headless:
            self.driver.maximize_window()
        
        print("✅ Chrome WebDriver ready!")
    
    def human_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def login(self) -> bool:
        """
        Log into LinkedIn
        
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            print("\n🔐 Logging into LinkedIn...")
            
            # Navigate to LinkedIn login page
            self.driver.get('https://www.linkedin.com/login')
            self.human_delay(2, 4)
            
            # Enter email
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, 'username'))
            )
            email_field.clear()
            email_field.send_keys(self.email)
            self.human_delay(0.5, 1.5)
            
            # Enter password
            password_field = self.driver.find_element(By.ID, 'password')
            password_field.clear()
            password_field.send_keys(self.password)
            self.human_delay(0.5, 1.5)
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            login_button.click()
            
            print("  → Credentials submitted, waiting for login...")
            self.human_delay(3, 5)
            
            # Check if login successful
            if 'feed' in self.driver.current_url or 'sales/homepage' in self.driver.current_url:
                print("✅ Successfully logged in!")
                if USE_DATABASE:
                    db_manager.log_activity(
                        activity_type='login',
                        description='Successfully logged into LinkedIn',
                        status='success'
                    )
                return True
            else:
                print("❌ Login failed - check credentials or captcha")
                print(f"   Current URL: {self.driver.current_url}")
                if USE_DATABASE:
                    db_manager.log_activity(
                        activity_type='login',
                        description='Failed to log into LinkedIn',
                        status='failed',
                        error_message='Login verification failed'
                    )
                return False
                
        except Exception as e:
            print(f"❌ Error during login: {str(e)}")
            if USE_DATABASE:
                db_manager.log_activity(
                    activity_type='login',
                    description='Error during LinkedIn login',
                    status='failed',
                    error_message=str(e)
                )
            return False
    
    def search_with_keywords(self, keywords: str, use_sales_nav: bool = True) -> bool:
        """
        Search LinkedIn for REAL people using keywords
        
        Args:
            keywords: Search terms (e.g., "plastic surgeon dermatologist")
            use_sales_nav: Try Sales Navigator first, fallback to regular LinkedIn
        
        Returns:
            bool: Success status
        """
        try:
            # Try Sales Navigator first if enabled
            if use_sales_nav and self.sales_nav_preference:
                print("\n🔍 Attempting Sales Navigator search...")
                
                # Build Sales Nav URL with keywords
                sales_nav_url = f"https://www.linkedin.com/sales/search/people?keywords={keywords}"
                self.driver.get(sales_nav_url)
                self.human_delay(3, 5)
                
                # Check if we're on Sales Navigator
                if 'sales' in self.driver.current_url:
                    print("✅ Using Sales Navigator!")
                    self.stats['using_sales_nav'] = True
                    return True
                else:
                    print("⚠️ Sales Navigator not available, falling back...")
            
            # Fallback to regular LinkedIn search
            print("\n🔍 Using regular LinkedIn People Search...")
            
            # Build regular LinkedIn people search URL
            regular_url = f"https://www.linkedin.com/search/results/people/?keywords={keywords}"
            self.driver.get(regular_url)
            self.human_delay(3, 5)
            
            # Verify we're on search results
            if 'search/results/people' in self.driver.current_url:
                print("✅ Regular LinkedIn search loaded!")
                self.stats['using_sales_nav'] = False
                return True
            else:
                print("❌ Search failed!")
                return False
                
        except Exception as e:
            print(f"❌ Error during search: {str(e)}")
            return False

    def scrape_lead_from_card(self, card_element) -> Optional[Dict]:
        """
        Extract lead data from LinkedIn search result card
        Works for both Sales Navigator and regular LinkedIn
        """
        try:
            lead_data = {}
            
            # METHOD 1: Try Sales Navigator selectors
            try:
                # Sales Nav has different HTML structure
                name_elem = card_element.find_element(By.CSS_SELECTOR, '.artdeco-entity-lockup__title')
                lead_data['name'] = name_elem.text.strip()
                
                subtitle_elem = card_element.find_element(By.CSS_SELECTOR, '.artdeco-entity-lockup__subtitle')
                lead_data['title'] = subtitle_elem.text.strip()
                
                caption_elem = card_element.find_element(By.CSS_SELECTOR, '.artdeco-entity-lockup__caption')
                lead_data['company'] = caption_elem.text.strip()
                
                link_elem = card_element.find_element(By.CSS_SELECTOR, 'a.artdeco-entity-lockup__title-link')
                profile_url = link_elem.get_attribute('href')
                lead_data['profile_url'] = profile_url.split('?')[0]  # Clean URL
                
                print(f"  → Extracted (Sales Nav): {lead_data['name']}")
                
            except:
                # METHOD 2: Try regular LinkedIn selectors
                try:
                    # Regular LinkedIn structure
                    name_elem = card_element.find_element(By.CSS_SELECTOR, 'span.entity-result__title-text span[aria-hidden="true"]')
                    lead_data['name'] = name_elem.text.strip()
                    
                    subtitle_elem = card_element.find_element(By.CSS_SELECTOR, '.entity-result__primary-subtitle')
                    subtitle_text = subtitle_elem.text.strip()
                    
                    # Parse "Title at Company"
                    if ' at ' in subtitle_text:
                        parts = subtitle_text.split(' at ', 1)
                        lead_data['title'] = parts[0].strip()
                        lead_data['company'] = parts[1].strip()
                    else:
                        lead_data['title'] = subtitle_text
                        lead_data['company'] = None
                    
                    link_elem = card_element.find_element(By.CSS_SELECTOR, 'a.app-aware-link')
                    profile_url = link_elem.get_attribute('href')
                    lead_data['profile_url'] = profile_url.split('?')[0]
                    
                    print(f"  → Extracted (Regular): {lead_data['name']}")
                    
                except Exception as inner_e:
                    print(f"  ⚠️ Could not extract lead data: {str(inner_e)}")
                    return None
            
            # Extract location (optional)
            try:
                location_elem = card_element.find_element(By.CSS_SELECTOR, '.entity-result__secondary-subtitle')
                lead_data['location'] = location_elem.text.strip()
            except:
                lead_data['location'] = None
            
            # Extract headline (optional)
            try:
                headline_elem = card_element.find_element(By.CSS_SELECTOR, '.entity-result__summary')
                lead_data['headline'] = headline_elem.text.strip()
            except:
                lead_data['headline'] = None
            
            # Set defaults
            lead_data['industry'] = None
            lead_data['company_size'] = None
            lead_data['summary'] = None
            lead_data['ai_score'] = 0
            lead_data['status'] = 'new'
            
            # Validate we have minimum required fields
            if not lead_data.get('name') or not lead_data.get('profile_url'):
                print("  ⚠️ Missing required fields (name or URL)")
                return None
            
            return lead_data
            
        except Exception as e:
            print(f"  ❌ Error extracting lead: {str(e)}")
            return None
    
    def scrape_current_page(self) -> List[Dict]:
        """Scrape all leads from the current search results page"""
        leads = []
        
        try:
            print("\n📊 Scraping leads from current page...")
            
            # Wait for results to load
            self.human_delay(2, 4)
            
            # Find all lead cards
            if self.stats['using_sales_nav']:
                # Sales Navigator uses different selectors
                lead_cards = self.driver.find_elements(By.CSS_SELECTOR, 'li.artdeco-list__item')
            else:
                # Regular LinkedIn
                lead_cards = self.driver.find_elements(By.CSS_SELECTOR, 'li.reusable-search__result-container')
            
            if not lead_cards:
                print("  ⚠️ No lead cards found on this page")
                return leads
            
            print(f"  → Found {len(lead_cards)} potential leads")
            
            # Extract data from each card
            for i, card in enumerate(lead_cards, 1):
                try:
                    lead_data = self.scrape_lead_from_card(card)
                    
                    if lead_data and lead_data.get('name'):
                        leads.append(lead_data)
                        print(f"  ✅ [{i}/{len(lead_cards)}] Scraped: {lead_data['name']}")
                        self.stats['leads_scraped'] += 1
                    else:
                        print(f"  ⚠️ [{i}/{len(lead_cards)}] Skipped: Incomplete data")
                    
                    # Small delay between extractions
                    self.human_delay(0.3, 0.8)
                    
                except Exception as e:
                    print(f"  ❌ [{i}/{len(lead_cards)}] Error: {str(e)}")
                    self.stats['errors'] += 1
                    continue
            
            print(f"\n✅ Successfully scraped {len(leads)} leads from this page")
            
        except Exception as e:
            print(f"❌ Error scraping page: {str(e)}")
        
        return leads
    
    def scrape_leads(self, filters: Dict[str, any], max_pages: int = 3) -> List[Dict]:
        """
        Main scraping function - scrapes REAL leads from LinkedIn
        
        Args:
            filters: Dictionary with 'keywords' key
            max_pages: Number of search result pages to scrape
        
        Returns:
            List of lead dictionaries
        """
        all_leads = []
        self.stats['start_time'] = datetime.now()
        
        try:
            print("\n" + "="*60)
            print("🚀 Starting LinkedIn Lead Scraping")
            print("="*60)
            
            # Setup browser
            self.setup_driver()
            
            # Login to LinkedIn
            if not self.login():
                print("❌ Cannot proceed without login")
                return all_leads
            
            # Get search keywords
            keywords = filters.get('keywords', 'business professional')
            print(f"\n🔍 Searching for: {keywords}")
            
            # Perform search (Sales Nav or regular LinkedIn)
            if not self.search_with_keywords(keywords, use_sales_nav=True):
                print("❌ Search failed!")
                return all_leads
            
            # Scrape multiple pages
            for page_num in range(1, max_pages + 1):
                print(f"\n📄 Scraping page {page_num}/{max_pages}...")
                
                # Scrape current page
                page_leads = self.scrape_current_page()
                all_leads.extend(page_leads)
                
                # Go to next page
                if page_num < max_pages:
                    try:
                        # Look for pagination button
                        next_button = self.driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Next"]')
                        
                        if next_button.is_enabled():
                            print(f"  → Moving to page {page_num + 1}...")
                            next_button.click()
                            self.human_delay(3, 5)
                        else:
                            print("  → No more pages")
                            break
                            
                    except:
                        print("  → Cannot find next page button")
                        break
            
            # Save results
            if all_leads:
                print(f"\n💾 Saving {len(all_leads)} leads...")
                
                # Save CSV backup
                csv_path = csv_handler.save_scrape_backup(all_leads, source='linkedin')
                print(f"  ✅ CSV saved: {csv_path}")
                
                # Import to database
                if USE_DATABASE:
                    self.import_to_database(all_leads)
            
            self.stats['end_time'] = datetime.now()
            self.print_stats()
            
        except Exception as e:
            print(f"\n❌ Fatal error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        finally:
            if self.driver:
                print("\n🔒 Closing browser...")
                self.driver.quit()
        
        return all_leads
    
    def import_to_database(self, leads: List[Dict]):
        """Import scraped leads to database"""
        if not USE_DATABASE:
            print("  ⚠️ Database not available, skipping import")
            return
        
        print("\n📥 Importing leads to database...")
        imported = 0
        skipped = 0
        
        for lead_data in leads:
            try:
                # Create lead in database
                lead_id = db_manager.create_lead(
                    name=lead_data['name'],
                    profile_url=lead_data.get('profile_url'),
                    title=lead_data.get('title'),
                    company=lead_data.get('company'),
                    industry=lead_data.get('industry'),
                    location=lead_data.get('location'),
                    headline=lead_data.get('headline'),
                    summary=lead_data.get('summary'),
                    company_size=lead_data.get('company_size')
                )
                
                if lead_id:
                    imported += 1
                else:
                    skipped += 1
                    
            except Exception as e:
                print(f"  ⚠️ Error importing {lead_data.get('name')}: {str(e)}")
                skipped += 1
                continue
        
        print(f"  ✅ Imported: {imported} leads")
        print(f"  ⚠️ Skipped: {skipped} duplicates or errors")
    
    def print_stats(self):
        """Print scraping statistics"""
        print("\n" + "="*60)
        print("📊 Scraping Statistics")
        print("="*60)
        
        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            print(f"⏱️  Duration: {duration.seconds} seconds")
        
        print(f"✅ Leads Scraped: {self.stats['leads_scraped']}")
        print(f"❌ Errors: {self.stats['errors']}")
        
        # Show which mode was used
        mode = "Sales Navigator" if self.stats['using_sales_nav'] else "Regular LinkedIn"
        print(f"🔍 Search Mode: {mode}")
        
        print("="*60)


# CLI for testing
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Sales Navigator Scraper')
    parser.add_argument('--email', type=str, help='LinkedIn email', required=True)
    parser.add_argument('--password', type=str, help='LinkedIn password', required=True)
    parser.add_argument('--keywords', type=str, help='Search keywords', default='plastic surgeon dermatologist')
    parser.add_argument('--pages', type=int, help='Number of pages to scrape', default=1)
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    args = parser.parse_args()
    
    # Create scraper instance
    scraper = LinkedInScraper(
        email=args.email,
        password=args.password,
        headless=args.headless,
        sales_nav_preference=True
    )
    
    # Define search filters
    filters = {
        'keywords': args.keywords
    }
    
    # Run scraper
    leads = scraper.scrape_leads(filters, max_pages=args.pages)
    
    print(f"\n🎉 Scraping complete! Total leads: {len(leads)}")