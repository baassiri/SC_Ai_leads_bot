"""
SC AI Lead Generation System - LinkedIn Scraper
IMPROVED VERSION - Better Sales Nav integration + API compatibility
October 2025
"""

import time
import random
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import traceback

# Fix Python path
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

# Import backend modules
try:
    from backend.config import Config
    from backend.utils.csv_handler import csv_handler
    from backend.database.db_manager import db_manager
    USE_DATABASE = True
except ImportError:
    print("⚠️ Warning: Database modules not available. CSV-only mode.")
    USE_DATABASE = False
    
    class Config:
        SCRAPE_DELAY_MIN = 2
        SCRAPE_DELAY_MAX = 5
        MAX_LEADS_PER_SESSION = 100
        EXPORT_DIR = Path(__file__).parent / 'exports'
    
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
    """LinkedIn scraper with Sales Navigator support - IMPROVED"""
    
    # FIXED selectors for October 2025
    SELECTORS = {
        'login': {
            'email': '#username',
            'password': '#password',
            'submit': 'button[type="submit"]'
        },
        'regular_linkedin': {
            'search_result': 'div.b9fd59a4',
            'profile_link': 'a[href*="/in/"]',
            'next_button': 'button[aria-label="Next"]'
        },
        'sales_navigator': {
            'search_result': 'li.artdeco-list__item',
            'name': '.artdeco-entity-lockup__title',
            'title': '.artdeco-entity-lockup__subtitle',
            'company': '.artdeco-entity-lockup__caption',
            'profile_link': 'a.artdeco-entity-lockup__title-link',
            'next_button': 'button[aria-label="Next"]'
        }
    }
    
    def __init__(self, email: str, password: str, headless: bool = False, sales_nav_preference: bool = True):
        """
        Initialize scraper
        
        Args:
            email: LinkedIn login email
            password: LinkedIn password
            headless: Run browser invisibly
            sales_nav_preference: Prefer Sales Navigator if available
        """
        self.email = email
        self.password = password
        self.headless = headless
        self.sales_nav_preference = sales_nav_preference
        self.driver = None
        self.wait = None
        
        self.stats = {
            'leads_scraped': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None,
            'using_sales_nav': False,
            'pages_scraped': 0
        }
    
    def setup_driver(self):
        """Setup Chrome WebDriver with anti-detection measures"""
        print("\n🚗 Setting up Chrome driver...")
        
        options = Options()
        
        # Stealth mode enhancements
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Additional stealth
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-setuid-sandbox')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        
        # User agent
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        if self.headless:
            options.add_argument('--headless=new')
            options.add_argument('--window-size=1920,1080')
        
        # Install and setup driver
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Execute stealth scripts
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            # Hide webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.wait = WebDriverWait(self.driver, 20)
            self.driver.implicitly_wait(10)
            
            print("✅ Driver setup complete")
            return True
            
        except Exception as e:
            print(f"❌ Driver setup failed: {str(e)}")
            return False
    
    def human_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """Random delay to mimic human behavior"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def safe_find_element(self, by: By, selector: str, timeout: int = 10):
        """Safely find element with timeout"""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
        except TimeoutException:
            return None
    
    def login(self) -> bool:
        """Login to LinkedIn"""
        try:
            print("\n🔐 Logging into LinkedIn...")
            
            self.driver.get('https://www.linkedin.com/login')
            self.human_delay(2, 4)
            
            # Enter email
            email_field = self.safe_find_element(By.CSS_SELECTOR, self.SELECTORS['login']['email'])
            if not email_field:
                print("❌ Cannot find email field")
                return False
            
            email_field.clear()
            for char in self.email:
                email_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            self.human_delay(0.5, 1.0)
            
            # Enter password
            password_field = self.driver.find_element(By.CSS_SELECTOR, self.SELECTORS['login']['password'])
            password_field.clear()
            for char in self.password:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            self.human_delay(0.5, 1.0)
            
            # Submit
            login_btn = self.driver.find_element(By.CSS_SELECTOR, self.SELECTORS['login']['submit'])
            login_btn.click()
            
            print("  → Waiting for login...")
            self.human_delay(4, 6)
            
            # Check success
            current_url = self.driver.current_url
            
            if 'feed' in current_url or 'sales' in current_url:
                print("✅ Successfully logged in!")
                
                # Check for verification
                if 'checkpoint' in current_url or 'challenge' in current_url:
                    print("\n⚠️ LinkedIn requires verification!")
                    print("Please complete the verification in the browser window.")
                    print("Waiting 60 seconds...")
                    time.sleep(60)
                
                if USE_DATABASE:
                    db_manager.log_activity(
                        activity_type='login',
                        description='Successfully logged into LinkedIn',
                        status='success'
                    )
                return True
            else:
                print(f"❌ Login failed")
                print(f"   Current URL: {current_url}")
                return False
        
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            traceback.print_exc()
            return False
    
    def detect_sales_nav_access(self) -> bool:
        """Check if user has Sales Navigator access"""
        try:
            print("\n🔍 Checking Sales Navigator access...")
            
            self.driver.get('https://www.linkedin.com/sales/homepage')
            self.human_delay(3, 5)
            
            current_url = self.driver.current_url
            
            if 'sales' in current_url and 'homepage' in current_url:
                print("✅ Sales Navigator access confirmed!")
                return True
            else:
                print("⚠️ No Sales Navigator access - will use regular LinkedIn")
                return False
        
        except Exception as e:
            print(f"⚠️ Cannot detect Sales Nav: {str(e)}")
            return False
    
    def search_leads(self, keywords: str) -> bool:
        """
        Search for leads using keywords
        IMPROVED: Better Sales Nav URL formatting
        """
        try:
            # Clean and prepare keywords
            clean_keywords = keywords.strip()
            if not clean_keywords:
                clean_keywords = "CEO founder"  # Default fallback
            
            # Try Sales Navigator first if preferred
            if self.sales_nav_preference:
                has_sales_nav = self.detect_sales_nav_access()
                
                if has_sales_nav:
                    print(f"\n🔎 Searching Sales Navigator for: {clean_keywords}")
                    
                    # IMPROVED: Better Sales Nav URL formatting
                    # Sales Nav works better with title-based searches
                    url_keywords = clean_keywords.replace(' ', '%20')
                    search_url = f"https://www.linkedin.com/sales/search/people?keywords={url_keywords}"
                    
                    self.driver.get(search_url)
                    self.human_delay(4, 6)  # Longer wait for Sales Nav
                    
                    if 'sales/search/people' in self.driver.current_url:
                        print("✅ Sales Navigator search loaded!")
                        self.stats['using_sales_nav'] = True
                        
                        if USE_DATABASE:
                            db_manager.log_activity(
                                activity_type='search',
                                description=f'🎯 Sales Nav search: {clean_keywords}',
                                status='success'
                            )
                        return True
            
            # Fallback to regular LinkedIn
            print(f"\n🔎 Searching Regular LinkedIn for: {clean_keywords}")
            url_keywords = clean_keywords.replace(' ', '%20')
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={url_keywords}"
            self.driver.get(search_url)
            self.human_delay(3, 5)
            
            if 'search/results/people' in self.driver.current_url:
                print("✅ Regular LinkedIn search loaded!")
                self.stats['using_sales_nav'] = False
                
                if USE_DATABASE:
                    db_manager.log_activity(
                        activity_type='search',
                        description=f'🎯 LinkedIn search: {clean_keywords}',
                        status='success'
                    )
                return True
            else:
                print("❌ Search failed!")
                return False
        
        except Exception as e:
            print(f"❌ Search error: {str(e)}")
            return False
    
    def extract_lead_data(self, card_element) -> Optional[Dict]:
        """Extract lead data from search result card"""
        try:
            lead = {
                'name': None,
                'title': None,
                'company': None,
                'location': None,
                'profile_url': None,
                'headline': None,
                'industry': None,
                'company_size': None,
                'ai_score': 0,
                'status': 'new'
            }
            
            # Choose selectors based on mode
            if self.stats['using_sales_nav']:
                selectors = self.SELECTORS['sales_navigator']
                
                try:
                    name_elem = card_element.find_element(By.CSS_SELECTOR, selectors['name'])
                    lead['name'] = name_elem.text.strip()
                except:
                    return None
                
                try:
                    title_elem = card_element.find_element(By.CSS_SELECTOR, selectors['title'])
                    lead['title'] = title_elem.text.strip()
                except:
                    pass
                
                try:
                    company_elem = card_element.find_element(By.CSS_SELECTOR, selectors['company'])
                    lead['company'] = company_elem.text.strip()
                except:
                    pass
                
                try:
                    link_elem = card_element.find_element(By.CSS_SELECTOR, selectors['profile_link'])
                    profile_url = link_elem.get_attribute('href')
                    if '?' in profile_url:
                        profile_url = profile_url.split('?')[0]
                    lead['profile_url'] = profile_url
                except:
                    return None
            
            else:
                # Regular LinkedIn extraction
                selectors = self.SELECTORS['regular_linkedin']
                
                try:
                    link = card_element.find_element(By.CSS_SELECTOR, selectors['profile_link'])
                    profile_url = link.get_attribute('href')
                    
                    if '?' in profile_url:
                        profile_url = profile_url.split('?')[0]
                    
                    lead['profile_url'] = profile_url
                    
                    name_text = link.text.strip()
                    if name_text:
                        lead['name'] = name_text
                
                except Exception as e:
                    return None
                
                # Parse card text
                try:
                    full_text = card_element.text.strip()
                    if full_text:
                        lines = [l.strip() for l in full_text.split('\n') if l.strip()]
                        
                        if len(lines) >= 2:
                            title_line = lines[1]
                            
                            if ' at ' in title_line:
                                parts = title_line.split(' at ', 1)
                                lead['title'] = parts[0].strip()
                                lead['company'] = parts[1].strip()
                            elif ' · ' in title_line:
                                parts = title_line.split(' · ', 1)
                                lead['title'] = parts[0].strip()
                            else:
                                lead['title'] = title_line
                        
                        if len(lines) >= 3:
                            location_line = lines[2]
                            if not any(word in location_line.lower() for word in ['connect', 'message', 'follow']):
                                lead['location'] = location_line
                
                except Exception as e:
                    pass
            
            # Validate
            if not lead['name'] or not lead['profile_url']:
                return None
            
            if '/in/' not in lead['profile_url']:
                return None
            
            return lead
        
        except Exception as e:
            return None
    
    def scrape_current_page(self) -> List[Dict]:
        """Scrape all leads from current page"""
        leads = []
        
        try:
            print("\n📊 Scraping current page...")
            self.human_delay(2, 4)
            
            if self.stats['using_sales_nav']:
                result_selector = self.SELECTORS['sales_navigator']['search_result']
            else:
                result_selector = self.SELECTORS['regular_linkedin']['search_result']
            
            cards = self.driver.find_elements(By.CSS_SELECTOR, result_selector)
            
            if not cards:
                print("  ⚠️ No results found on page")
                return leads
            
            print(f"  → Found {len(cards)} potential cards")
            
            # Deduplicate
            seen_urls = set()
            valid_cards = []
            for card in cards:
                try:
                    link = card.find_element(By.CSS_SELECTOR, 'a[href*="/in/"]')
                    href = link.get_attribute('href')
                    
                    if href and '/in/' in href and 'linkedin.com/in/' in href:
                        clean_url = href.split('?')[0]
                        
                        if clean_url not in seen_urls:
                            seen_urls.add(clean_url)
                            valid_cards.append(card)
                except:
                    continue
            
            print(f"  → {len(valid_cards)} unique person cards")
            
            # Extract leads
            for i, card in enumerate(valid_cards, 1):
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", card)
                    self.human_delay(0.3, 0.6)
                    
                    lead_data = self.extract_lead_data(card)
                    
                    if lead_data:
                        leads.append(lead_data)
                        print(f"  ✅ [{i}/{len(valid_cards)}] {lead_data['name']}")
                        self.stats['leads_scraped'] += 1
                    else:
                        print(f"  ⚠️ [{i}/{len(valid_cards)}] Skipped")
                    
                    self.human_delay(0.2, 0.5)
                
                except Exception as e:
                    print(f"  ❌ [{i}/{len(valid_cards)}] Error: {str(e)}")
                    self.stats['errors'] += 1
                    continue
            
            print(f"\n✅ Scraped {len(leads)} leads from this page")
            self.stats['pages_scraped'] += 1
        
        except Exception as e:
            print(f"❌ Page scrape error: {str(e)}")
            traceback.print_exc()
        
        return leads
    
    def go_to_next_page(self) -> bool:
        """Navigate to next page"""
        try:
            print("\n➡️ Going to next page...")
            
            if self.stats['using_sales_nav']:
                next_selector = self.SELECTORS['sales_navigator']['next_button']
            else:
                next_selector = self.SELECTORS['regular_linkedin']['next_button']
            
            next_btn = self.safe_find_element(By.CSS_SELECTOR, next_selector, timeout=5)
            
            if not next_btn or not next_btn.is_enabled():
                print("  ⚠️ No next page available")
                return False
            
            self.driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
            self.human_delay(0.5, 1.0)
            next_btn.click()
            
            print("  ✅ Navigated to next page")
            self.human_delay(3, 5)
            return True
        
        except Exception as e:
            print(f"  ⚠️ Cannot go to next page: {str(e)}")
            return False
    
    def scrape_leads(self, filters: Dict, max_pages: int = 3) -> List[Dict]:
        """
        Main scraping function
        
        Args:
            filters: Dict with 'keywords' key
            max_pages: Number of pages to scrape
        
        Returns:
            List of lead dictionaries
        """
        all_leads = []
        self.stats['start_time'] = datetime.now()
        
        try:
            print("\n" + "="*70)
            print("🚀 LINKEDIN LEAD SCRAPER - STARTING (IMPROVED VERSION)")
            print("="*70)
            
            # Setup
            if not self.setup_driver():
                return all_leads
            
            # Login
            if not self.login():
                print("\n❌ Cannot proceed without login")
                return all_leads
            
            # Get keywords
            keywords = filters.get('keywords', 'CEO founder')
            print(f"\n🎯 Target Keywords: {keywords}")
            
            # Search
            if not self.search_leads(keywords):
                print("\n❌ Search failed")
                return all_leads
            
            # Scrape pages
            for page in range(1, max_pages + 1):
                print(f"\n{'='*70}")
                print(f"📄 PAGE {page} of {max_pages}")
                print(f"{'='*70}")
                
                page_leads = self.scrape_current_page()
                all_leads.extend(page_leads)
                
                print(f"\n📈 Progress: {len(all_leads)} total leads scraped")
                
                # Stop conditions
                if page >= max_pages:
                    print("\n✅ Reached max pages")
                    break
                
                if len(all_leads) >= Config.MAX_LEADS_PER_SESSION:
                    print(f"\n✅ Reached max leads ({Config.MAX_LEADS_PER_SESSION})")
                    break
                
                # Next page
                if not self.go_to_next_page():
                    print("\n✅ No more pages available")
                    break
            
            # Save results
            if all_leads:
                self.save_results(all_leads)
            
            self.stats['end_time'] = datetime.now()
            self.print_summary()
        
        except KeyboardInterrupt:
            print("\n\n⚠️ Scraping interrupted by user")
        
        except Exception as e:
            print(f"\n❌ Fatal error: {str(e)}")
            traceback.print_exc()
        
        finally:
            if self.driver:
                print("\n🔒 Closing browser...")
                self.driver.quit()
        
        return all_leads
    
    def save_results(self, leads: List[Dict]):
        """Save leads to CSV and database"""
        print(f"\n💾 Saving {len(leads)} leads...")
        
        # CSV
        try:
            csv_path = csv_handler.save_scrape_backup(leads, source='linkedin')
            print(f"  ✅ CSV: {csv_path}")
        except Exception as e:
            print(f"  ❌ CSV error: {str(e)}")
        
        # Database
        if USE_DATABASE:
            self.import_to_database(leads)
    
    def import_to_database(self, leads: List[Dict]):
        """Import leads to database"""
        print("\n📥 Importing to database...")
        imported = 0
        skipped = 0
        
        for lead in leads:
            try:
                lead_id = db_manager.create_lead(
                    name=lead['name'],
                    profile_url=lead['profile_url'],
                    title=lead.get('title'),
                    company=lead.get('company'),
                    industry=lead.get('industry'),
                    location=lead.get('location'),
                    headline=lead.get('headline'),
                    company_size=lead.get('company_size')
                )
                
                if lead_id:
                    imported += 1
                else:
                    skipped += 1
            
            except Exception as e:
                print(f"  ⚠️ Import error for {lead.get('name')}: {str(e)}")
                skipped += 1
        
        print(f"  ✅ Imported: {imported}")
        print(f"  ⚠️ Skipped: {skipped} (duplicates/errors)")
    
    def print_summary(self):
        """Print scraping summary"""
        print("\n" + "="*70)
        print("📊 SCRAPING SUMMARY")
        print("="*70)
        
        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            minutes = duration.seconds // 60
            seconds = duration.seconds % 60
            print(f"⏱️  Duration: {minutes}m {seconds}s")
        
        print(f"✅ Leads Scraped: {self.stats['leads_scraped']}")
        print(f"📄 Pages Scraped: {self.stats['pages_scraped']}")
        print(f"❌ Errors: {self.stats['errors']}")
        
        mode = "Sales Navigator" if self.stats['using_sales_nav'] else "Regular LinkedIn"
        print(f"🔍 Mode: {mode}")
        
        if self.stats['leads_scraped'] > 0:
            avg_per_page = self.stats['leads_scraped'] / max(self.stats['pages_scraped'], 1)
            print(f"📈 Avg per page: {avg_per_page:.1f}")
        
        print("="*70)
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()


# CLI Testing
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Lead Scraper - IMPROVED')
    parser.add_argument('--email', required=True, help='LinkedIn email')
    parser.add_argument('--password', required=True, help='LinkedIn password')
    parser.add_argument('--keywords', default='CEO founder', help='Search keywords')
    parser.add_argument('--pages', type=int, default=1, help='Pages to scrape')
    parser.add_argument('--headless', action='store_true', help='Run invisibly')
    parser.add_argument('--no-sales-nav', action='store_true', help='Skip Sales Navigator')
    
    args = parser.parse_args()
    
    scraper = LinkedInScraper(
        email=args.email,
        password=args.password,
        headless=args.headless,
        sales_nav_preference=not args.no_sales_nav
    )
    
    filters = {'keywords': args.keywords}
    leads = scraper.scrape_leads(filters, max_pages=args.pages)
    
    print(f"\n🎉 Complete! Total leads: {len(leads)}")