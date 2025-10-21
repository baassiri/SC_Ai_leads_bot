"""
Improved LinkedIn Scraper with Enhanced Features
- Cookie persistence for faster logins
- CAPTCHA detection and handling
- Better error recovery
- Rate limiting
- Multiple selector fallbacks
"""

import os
import time
import pickle
import random
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class ImprovedLinkedInScraper:
    """
    Enhanced LinkedIn scraper with:
    - Cookie persistence
    - CAPTCHA detection
    - Better error handling
    - Rate limiting
    - Multiple selector strategies
    """
    
    def __init__(self, email: str, password: str, headless: bool = False, 
                 sales_nav: bool = False):
        """
        Initialize scraper
        
        Args:
            email: LinkedIn email
            password: LinkedIn password
            headless: Run browser in headless mode
            sales_nav: Use Sales Navigator if available
        """
        self.email = email
        self.password = password
        self.headless = headless
        self.sales_nav = sales_nav
        self.driver = None
        self.is_logged_in = False
        
        # Paths
        self.data_dir = Path('data')
        self.data_dir.mkdir(exist_ok=True)
        self.cookies_file = self.data_dir / 'linkedin_cookies.pkl'
        
        # Stats
        self.stats = {
            'leads_scraped': 0,
            'pages_scraped': 0,
            'errors': 0,
            'started_at': None
        }
    
    def start_session(self):
        """Start browser session"""
        print("🚀 Starting LinkedIn session...")
        
        # Setup Chrome options
        options = Options()
        if self.headless:
            options.add_argument('--headless=new')
        
        # Anti-detection
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User agent
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Start driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(10)
        
        # Set page load timeout
        self.driver.set_page_load_timeout(30)
        
        # Login
        self._login()
        
        self.stats['started_at'] = datetime.now()
    
    def _login(self):
        """Login to LinkedIn with cookie persistence"""
        print("🔐 Logging into LinkedIn...")
        
        # Try to load cookies first
        if self._load_cookies():
            print("   📦 Loaded saved cookies")
            self.driver.get('https://www.linkedin.com/feed/')
            time.sleep(3)
            
            # Check if still logged in
            if self._verify_login():
                self.is_logged_in = True
                print("   ✅ Logged in with cookies!")
                return
            else:
                print("   ⚠️ Cookies expired, logging in again...")
        
        # Login with credentials
        try:
            self.driver.get('https://www.linkedin.com/login')
            time.sleep(2)
            
            # Check for CAPTCHA
            if self._detect_captcha():
                print("   🤖 CAPTCHA detected!")
                print("   ⏸️  Please solve CAPTCHA in browser...")
                input("   Press ENTER when done...")
            
            # Enter credentials
            email_field = self._find_element_with_fallbacks([
                (By.ID, 'username'),
                (By.NAME, 'session_key'),
                (By.CSS_SELECTOR, 'input[type="text"]')
            ])
            
            password_field = self._find_element_with_fallbacks([
                (By.ID, 'password'),
                (By.NAME, 'session_password'),
                (By.CSS_SELECTOR, 'input[type="password"]')
            ])
            
            if not email_field or not password_field:
                raise Exception("Could not find login fields")
            
            # Type credentials (human-like)
            self._human_type(email_field, self.email)
            time.sleep(random.uniform(0.5, 1.5))
            self._human_type(password_field, self.password)
            time.sleep(random.uniform(0.5, 1.5))
            
            # Click login
            login_button = self._find_element_with_fallbacks([
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.XPATH, '//button[contains(text(), "Sign in")]')
            ])
            
            if login_button:
                login_button.click()
            else:
                # Fallback: press Enter
                password_field.send_keys('\n')
            
            # Wait for redirect
            time.sleep(5)
            
            # Check for 2FA
            if self._detect_2fa():
                print("   🔐 2FA detected!")
                print("   ⏸️  Please complete 2FA in browser...")
                input("   Press ENTER when done...")
            
            # Verify login
            if self._verify_login():
                self.is_logged_in = True
                print("   ✅ Logged in successfully!")
                
                # Save cookies
                self._save_cookies()
            else:
                print("   ❌ Login failed!")
                print("   Current URL:", self.driver.current_url)
                raise Exception("Login verification failed")
        
        except Exception as e:
            print(f"   ❌ Login error: {str(e)}")
            raise
    
    def _verify_login(self) -> bool:
        """Check if successfully logged in"""
        try:
            current_url = self.driver.current_url
            
            # Check URL
            if any(path in current_url for path in ['/feed', '/mynetwork', '/in/']):
                return True
            
            # Check for nav bar (logged in indicator)
            try:
                self.driver.find_element(By.CSS_SELECTOR, 'nav.global-nav')
                return True
            except:
                pass
            
            return False
        except:
            return False
    
    def _detect_captcha(self) -> bool:
        """Detect if CAPTCHA is present"""
        try:
            # Check for common CAPTCHA indicators
            captcha_indicators = [
                'captcha',
                'challenge',
                'robot',
                'verification'
            ]
            
            page_source = self.driver.page_source.lower()
            return any(indicator in page_source for indicator in captcha_indicators)
        except:
            return False
    
    def _detect_2fa(self) -> bool:
        """Detect if 2FA is required"""
        try:
            current_url = self.driver.current_url
            
            # Check URL
            if 'checkpoint' in current_url or 'challenge' in current_url:
                return True
            
            # Check page content
            page_source = self.driver.page_source.lower()
            if 'verification code' in page_source or 'two-step' in page_source:
                return True
            
            return False
        except:
            return False
    
    def _save_cookies(self):
        """Save cookies to file"""
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, 'wb') as f:
                pickle.dump(cookies, f)
            print("   💾 Cookies saved")
        except Exception as e:
            print(f"   ⚠️ Could not save cookies: {str(e)}")
    
    def _load_cookies(self) -> bool:
        """Load cookies from file"""
        try:
            if not self.cookies_file.exists():
                return False
            
            self.driver.get('https://www.linkedin.com')
            time.sleep(1)
            
            with open(self.cookies_file, 'rb') as f:
                cookies = pickle.load(f)
            
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            
            return True
        except Exception as e:
            print(f"   ⚠️ Could not load cookies: {str(e)}")
            return False
    
    def _human_type(self, element, text: str):
        """Type text with human-like delays"""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def _find_element_with_fallbacks(self, selectors: List[tuple]) -> Optional[object]:
        """Try multiple selectors to find element"""
        for by, selector in selectors:
            try:
                element = self.driver.find_element(by, selector)
                if element and element.is_displayed():
                    return element
            except:
                continue
        return None
    
    def scrape_leads(self, search_query: str, max_pages: int = 3, 
                    filters: Dict = None) -> List[Dict]:
        """
        Scrape leads from LinkedIn search
        
        Args:
            search_query: Search keywords
            max_pages: Maximum pages to scrape
            filters: Optional search filters
        
        Returns:
            List of lead dictionaries
        """
        if not self.is_logged_in:
            print("❌ Not logged in!")
            return []
        
        print(f"\n🔍 Searching LinkedIn for: {search_query}")
        print(f"📄 Max pages: {max_pages}")
        
        all_leads = []
        
        try:
            # Build search URL
            if self.sales_nav:
                search_url = self._build_sales_nav_url(search_query, filters)
            else:
                search_url = self._build_standard_search_url(search_query, filters)
            
            print(f"🌐 URL: {search_url}")
            
            # Scrape pages
            for page in range(1, max_pages + 1):
                print(f"\n📄 Page {page}/{max_pages}")
                
                # Navigate to page
                page_url = f"{search_url}&page={page}"
                self.driver.get(page_url)
                
                # Random delay (rate limiting)
                time.sleep(random.uniform(3, 6))
                
                # Scrape current page
                page_leads = self._scrape_current_page()
                all_leads.extend(page_leads)
                
                print(f"   Found {len(page_leads)} leads on this page")
                
                # Check if last page
                if not self._has_next_page():
                    print("   ℹ️ No more pages")
                    break
                
                # Rate limiting between pages
                time.sleep(random.uniform(5, 10))
            
            print(f"\n✅ Scraping complete! Total leads: {len(all_leads)}")
            
            return all_leads
        
        except Exception as e:
            print(f"❌ Scraping error: {str(e)}")
            import traceback
            traceback.print_exc()
            return all_leads
    
    def _build_standard_search_url(self, query: str, filters: Dict = None) -> str:
        """Build standard LinkedIn search URL"""
        base_url = "https://www.linkedin.com/search/results/people/"
        params = f"?keywords={query.replace(' ', '%20')}"
        
        # Add filters if provided
        if filters:
            if filters.get('location'):
                params += f"&geoUrn={filters['location']}"
            if filters.get('industry'):
                params += f"&industry={filters['industry']}"
        
        return base_url + params
    
    def _build_sales_nav_url(self, query: str, filters: Dict = None) -> str:
        """Build Sales Navigator search URL"""
        base_url = "https://www.linkedin.com/sales/search/people"
        params = f"?query={query.replace(' ', '%20')}"
        return base_url + params
    
    def _scrape_current_page(self) -> List[Dict]:
        """Scrape all leads on current page"""
        leads = []
        
        try:
            # Scroll to load all results
            self._scroll_page()
            
            # Find all result cards
            result_cards = self._find_result_cards()
            
            print(f"   🎯 Found {len(result_cards)} result cards")
            
            # Extract data from each card
            for i, card in enumerate(result_cards, 1):
                try:
                    lead_data = self._extract_lead_data(card)
                    
                    if lead_data and lead_data.get('name'):
                        leads.append(lead_data)
                        print(f"      [{i}] ✅ {lead_data['name']}")
                    else:
                        print(f"      [{i}] ⚠️ Skipped (incomplete data)")
                
                except Exception as e:
                    print(f"      [{i}] ❌ Error: {str(e)}")
                    self.stats['errors'] += 1
                    continue
            
            self.stats['pages_scraped'] += 1
            self.stats['leads_scraped'] += len(leads)
            
        except Exception as e:
            print(f"   ❌ Page scrape error: {str(e)}")
        
        return leads
    
    def _find_result_cards(self) -> List:
        """Find all result cards on page"""
        selectors = [
            (By.CSS_SELECTOR, 'li.reusable-search__result-container'),
            (By.CSS_SELECTOR, '.search-result'),
            (By.CSS_SELECTOR, '[data-chameleon-result-urn]'),
            (By.CSS_SELECTOR, '.entity-result')
        ]
        
        for by, selector in selectors:
            try:
                cards = self.driver.find_elements(by, selector)
                if cards and len(cards) > 0:
                    return cards
            except:
                continue
        
        return []
    
    def _extract_lead_data(self, card) -> Optional[Dict]:
        """Extract lead data from result card"""
        try:
            # Name
            name = self._extract_text_from_card(card, [
                '.entity-result__title-text a span[aria-hidden="true"]',
                '.app-aware-link span[aria-hidden="true"]',
                '.entity-result__title-text'
            ])
            
            # Profile URL
            profile_url = self._extract_url_from_card(card)
            
            # Title
            title = self._extract_text_from_card(card, [
                '.entity-result__primary-subtitle',
                '.entity-result__summary'
            ])
            
            # Company
            company = self._extract_text_from_card(card, [
                '.entity-result__secondary-subtitle',
                '.entity-result__meta'
            ])
            
            # Location
            location = self._extract_text_from_card(card, [
                '.entity-result__location',
                '.entity-result__divider'
            ])
            
            return {
                'name': name,
                'title': title,
                'company': company,
                'location': location,
                'profile_url': profile_url,
                'ai_score': 0,
                'status': 'new',
                'scraped_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            print(f"         ⚠️ Extract error: {str(e)}")
            return None
    
    def _extract_text_from_card(self, card, selectors: List[str]) -> Optional[str]:
        """Extract text using multiple selectors"""
        for selector in selectors:
            try:
                element = card.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip()
                if text:
                    return text
            except:
                continue
        return None
    
    def _extract_url_from_card(self, card) -> Optional[str]:
        """Extract profile URL from card"""
        try:
            link = card.find_element(By.CSS_SELECTOR, 'a[href*="/in/"]')
            href = link.get_attribute('href')
            # Clean URL
            return href.split('?')[0].rstrip('/')
        except:
            return None
    
    def _scroll_page(self):
        """Scroll page to load all content"""
        try:
            # Scroll down in chunks
            for _ in range(3):
                self.driver.execute_script("window.scrollBy(0, window.innerHeight);")
                time.sleep(random.uniform(0.5, 1.5))
            
            # Scroll back up
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
        except:
            pass
    
    def _has_next_page(self) -> bool:
        """Check if next page button exists"""
        try:
            next_button = self.driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Next"]')
            return next_button.is_enabled()
        except:
            return False
    
    def close_session(self):
        """Close browser session"""
        if self.driver:
            self.driver.quit()
            print("👋 Session closed")
    
    def get_stats(self) -> Dict:
        """Get scraping statistics"""
        stats = self.stats.copy()
        if stats['started_at']:
            elapsed = (datetime.now() - stats['started_at']).seconds
            stats['duration_seconds'] = elapsed
            stats['leads_per_minute'] = (stats['leads_scraped'] / elapsed * 60) if elapsed > 0 else 0
        return stats


if __name__ == '__main__':
    """Test scraper"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Scraper')
    parser.add_argument('--email', required=True, help='LinkedIn email')
    parser.add_argument('--password', required=True, help='LinkedIn password')
    parser.add_argument('--query', default='CEO founder startup', help='Search query')
    parser.add_argument('--pages', type=int, default=2, help='Max pages')
    parser.add_argument('--headless', action='store_true', help='Run headless')
    
    args = parser.parse_args()
    
    # Create scraper
    scraper = ImprovedLinkedInScraper(
        email=args.email,
        password=args.password,
        headless=args.headless
    )
    
    # Start session
    scraper.start_session()
    
    # Scrape leads
    leads = scraper.scrape_leads(args.query, max_pages=args.pages)
    
    # Print results
    print("\n" + "="*70)
    print("📊 RESULTS")
    print("="*70)
    print(f"Total leads scraped: {len(leads)}")
    
    for i, lead in enumerate(leads[:5], 1):
        print(f"\n{i}. {lead['name']}")
        print(f"   Title: {lead.get('title', 'N/A')}")
        print(f"   Company: {lead.get('company', 'N/A')}")
        print(f"   URL: {lead.get('profile_url', 'N/A')}")
    
    if len(leads) > 5:
        print(f"\n... and {len(leads) - 5} more")
    
    # Stats
    stats = scraper.get_stats()
    print(f"\n📈 Stats:")
    print(f"   Pages scraped: {stats['pages_scraped']}")
    print(f"   Duration: {stats.get('duration_seconds', 0)} seconds")
    print(f"   Rate: {stats.get('leads_per_minute', 0):.1f} leads/minute")
    
    # Close
    scraper.close_session()