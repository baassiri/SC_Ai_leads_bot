"""
SC AI Lead Generation System - LinkedIn Sales Navigator Scraper
Selenium-based automation for scraping leads from LinkedIn
"""

import time
import random
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.config import Config
from backend.scrapers.csv_handler import csv_handler
from backend.database.db_manager import db_manager


class LinkedInScraper:
    """LinkedIn Sales Navigator scraper using Selenium"""
    
    def __init__(self, email: str, password: str, headless: bool = False):
        """
        Initialize LinkedIn scraper
        
        Args:
            email: LinkedIn email/username
            password: LinkedIn password
            headless: Run browser in headless mode (invisible)
        """
        self.email = email
        self.password = password
        self.headless = headless
        self.driver = None
        self.wait = None
        
        # Stats tracking
        self.stats = {
            'leads_scraped': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
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
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        
        # Maximize window
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
                db_manager.log_activity(
                    activity_type='login',
                    description='Successfully logged into LinkedIn',
                    status='success'
                )
                return True
            else:
                print("❌ Login failed - check credentials or captcha")
                db_manager.log_activity(
                    activity_type='login',
                    description='Failed to log into LinkedIn',
                    status='failed',
                    error_message='Login verification failed'
                )
                return False
                
        except Exception as e:
            print(f"❌ Error during login: {str(e)}")
            db_manager.log_activity(
                activity_type='login',
                description='Error during LinkedIn login',
                status='failed',
                error_message=str(e)
            )
            return False
    
    def navigate_to_sales_navigator(self) -> bool:
        """
        Navigate to LinkedIn Sales Navigator
        
        Returns:
            bool: True if navigation successful
        """
        try:
            print("\n🧭 Navigating to Sales Navigator...")
            
            # Go to Sales Navigator
            self.driver.get('https://www.linkedin.com/sales/home')
            self.human_delay(3, 5)
            
            if 'sales' in self.driver.current_url:
                print("✅ Successfully navigated to Sales Navigator!")
                return True
            else:
                print("⚠️ Sales Navigator access may not be available")
                print("  → Trying regular LinkedIn search instead...")
                return False
                
        except Exception as e:
            print(f"⚠️ Error navigating to Sales Navigator: {str(e)}")
            print("  → Will try regular LinkedIn search...")
            return False
    
    def apply_search_filters(self, filters: Dict[str, any]):
        """
        Apply search filters in Sales Navigator or LinkedIn
        
        Args:
            filters: Dictionary of search filters
                - job_titles: List of job titles
                - locations: List of locations
                - industries: List of industries
                - keywords: Search keywords
        """
        print("\n🔍 Applying search filters...")
        
        try:
            # Navigate to search
            if 'sales' in self.driver.current_url:
                # Sales Navigator search
                search_url = 'https://www.linkedin.com/sales/search/people'
            else:
                # Regular LinkedIn search
                search_url = 'https://www.linkedin.com/search/results/people/'
            
            self.driver.get(search_url)
            self.human_delay(2, 4)
            
            # Build search query from filters
            keywords = filters.get('keywords', '')
            job_titles = filters.get('job_titles', [])
            
            if job_titles:
                keywords = ' OR '.join(job_titles)
            
            # Find search box and enter keywords
            search_box = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder*="Search"]'))
            )
            search_box.clear()
            search_box.send_keys(keywords)
            search_box.send_keys(Keys.RETURN)
            
            print(f"  ✅ Applied search: {keywords}")
            self.human_delay(3, 5)
            
            # Log activity
            db_manager.log_activity(
                activity_type='search',
                description=f'Applied search filters: {keywords}',
                status='success'
            )
            
        except Exception as e:
            print(f"⚠️ Error applying filters: {str(e)}")
            db_manager.log_activity(
                activity_type='search',
                description='Error applying search filters',
                status='failed',
                error_message=str(e)
            )
    
    def scrape_lead_from_card(self, card_element) -> Optional[Dict]:
        """
        Extract lead data from a LinkedIn search result card
        
        Args:
            card_element: Selenium WebElement for the lead card
            
        Returns:
            Dict: Lead data or None if extraction fails
        """
        try:
            lead_data = {}
            
            # Extract name
            try:
                name_element = card_element.find_element(By.CSS_SELECTOR, 'span[aria-hidden="true"]')
                lead_data['name'] = name_element.text.strip()
            except:
                return None  # Skip if no name found
            
            # Extract profile URL
            try:
                link_element = card_element.find_element(By.CSS_SELECTOR, 'a.app-aware-link')
                profile_url = link_element.get_attribute('href')
                # Clean URL (remove query parameters)
                if '?' in profile_url:
                    profile_url = profile_url.split('?')[0]
                lead_data['profile_url'] = profile_url
            except:
                lead_data['profile_url'] = None
            
            # Extract title and company
            try:
                subtitle_element = card_element.find_element(By.CSS_SELECTOR, '.entity-result__primary-subtitle')
                subtitle_text = subtitle_element.text.strip()
                
                # Parse "Title at Company" format
                if ' at ' in subtitle_text:
                    parts = subtitle_text.split(' at ', 1)
                    lead_data['title'] = parts[0].strip()
                    lead_data['company'] = parts[1].strip()
                else:
                    lead_data['title'] = subtitle_text
                    lead_data['company'] = None
            except:
                lead_data['title'] = None
                lead_data['company'] = None
            
            # Extract location
            try:
                location_element = card_element.find_element(By.CSS_SELECTOR, '.entity-result__secondary-subtitle')
                lead_data['location'] = location_element.text.strip()
            except:
                lead_data['location'] = None
            
            # Extract headline (summary)
            try:
                headline_element = card_element.find_element(By.CSS_SELECTOR, '.entity-result__summary')
                lead_data['headline'] = headline_element.text.strip()
            except:
                lead_data['headline'] = None
            
            # Set default values
            lead_data['industry'] = 'Medical Practice'  # Default for aesthetics
            lead_data['company_size'] = None
            lead_data['summary'] = None
            
            return lead_data
            
        except Exception as e:
            print(f"  ⚠️ Error extracting lead data: {str(e)}")
            return None
    
    def scrape_current_page(self) -> List[Dict]:
        """
        Scrape all leads from the current search results page
        
        Returns:
            List[Dict]: List of lead data dictionaries
        """
        leads = []
        
        try:
            print("\n📊 Scraping leads from current page...")
            
            # Wait for results to load
            self.human_delay(2, 4)
            
            # Find all lead cards
            lead_cards = self.driver.find_elements(By.CSS_SELECTOR, '.entity-result')
            
            if not lead_cards:
                print("  ⚠️ No lead cards found on this page")
                return leads
            
            print(f"  → Found {len(lead_cards)} potential leads")
            
            # Extract data from each card
            for i, card in enumerate(lead_cards, 1):
                try:
                    lead_data = self.scrape_lead_from_card(card)
                    
                    if lead_data and lead_data.get('name') and lead_data.get('profile_url'):
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
        Main scraping function - scrapes leads based on filters
        
        Args:
            filters: Search filters dictionary
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List[Dict]: All scraped leads
        """
        all_leads = []
        self.stats['start_time'] = datetime.now()
        
        try:
            print("\n" + "="*60)
            print("🚀 Starting LinkedIn Lead Scraping")
            print("="*60)
            
            # Setup driver
            self.setup_driver()
            
            # Login
            if not self.login():
                print("❌ Cannot proceed without login")
                return all_leads
            
            # Navigate to Sales Navigator (or fall back to regular search)
            self.navigate_to_sales_navigator()
            
            # Apply search filters
            self.apply_search_filters(filters)
            
            # Scrape multiple pages
            for page_num in range(1, max_pages + 1):
                print(f"\n📄 Scraping page {page_num}/{max_pages}...")
                
                # Scrape current page
                page_leads = self.scrape_current_page()
                all_leads.extend(page_leads)
                
                # Try to go to next page
                if page_num < max_pages:
                    try:
                        # Look for "Next" button
                        next_button = self.driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Next"]')
                        
                        if next_button.is_enabled():
                            print(f"  → Moving to page {page_num + 1}...")
                            next_button.click()
                            self.human_delay(3, 5)
                        else:
                            print("  → No more pages available")
                            break
                            
                    except NoSuchElementException:
                        print("  → No next page button found")
                        break
            
            # Save results
            if all_leads:
                print(f"\n💾 Saving {len(all_leads)} leads...")
                
                # Save to CSV backup
                csv_path = csv_handler.save_scrape_backup(all_leads, source='linkedin')
                print(f"  ✅ CSV backup saved: {csv_path}")
                
                # Import to database
                self.import_to_database(all_leads)
                
                # Log success
                db_manager.log_activity(
                    activity_type='scrape',
                    description=f'Successfully scraped {len(all_leads)} leads from LinkedIn',
                    status='success'
                )
            
        except Exception as e:
            print(f"\n❌ Scraping error: {str(e)}")
            db_manager.log_activity(
                activity_type='scrape',
                description='Error during LinkedIn scraping',
                status='failed',
                error_message=str(e)
            )
        
        finally:
            # Cleanup
            self.stats['end_time'] = datetime.now()
            self.close()
            self.print_stats()
        
        return all_leads
    
    def import_to_database(self, leads: List[Dict]):
        """
        Import scraped leads to database
        
        Args:
            leads: List of lead dictionaries
        """
        print("\n📥 Importing leads to database...")
        imported = 0
        skipped = 0
        
        for lead_data in leads:
            try:
                # Check if lead already exists (by profile URL)
                existing = db_manager.get_all_leads()
                profile_urls = [lead.profile_url for lead in existing if lead.profile_url]
                
                if lead_data.get('profile_url') in profile_urls:
                    skipped += 1
                    continue
                
                # Create lead in database
                lead_id = db_manager.create_lead(
                    name=lead_data['name'],
                    profile_url=lead_data['profile_url'],
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
                    
            except Exception as e:
                print(f"  ⚠️ Error importing {lead_data.get('name')}: {str(e)}")
                continue
        
        print(f"  ✅ Imported: {imported} leads")
        print(f"  ⚠️ Skipped: {skipped} duplicates")
    
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
        print("="*60)
    
    def close(self):
        """Close the browser"""
        if self.driver:
            print("\n🔒 Closing browser...")
            self.driver.quit()
            print("✅ Browser closed")


# CLI for testing
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Sales Navigator Scraper')
    parser.add_argument('--email', type=str, help='LinkedIn email', required=True)
    parser.add_argument('--password', type=str, help='LinkedIn password', required=True)
    parser.add_argument('--keywords', type=str, help='Search keywords', default='plastic surgeon dermatologist')
    parser.add_argument('--pages', type=int, help='Number of pages to scrape', default=3)
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    args = parser.parse_args()
    
    # Create scraper instance
    scraper = LinkedInScraper(
        email=args.email,
        password=args.password,
        headless=args.headless
    )
    
    # Define search filters
    filters = {
        'keywords': args.keywords,
        'job_titles': ['Plastic Surgeon', 'Dermatologist', 'Med Spa Owner', 'Aesthetic Nurse'],
        'locations': ['United States'],
        'industries': ['Medical Practice', 'Health, Wellness and Fitness']
    }
    
    # Run scraper
    leads = scraper.scrape_leads(filters, max_pages=args.pages)
    
    print(f"\n🎉 Scraping complete! Total leads: {len(leads)}")