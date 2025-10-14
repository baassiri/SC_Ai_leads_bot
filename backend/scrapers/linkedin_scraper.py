"""
SC AI Lead Generation System - LinkedIn Scraper
FIXED VERSION - Login flow corrected
October 2025
"""

import time
import random
import sys
import os
import pickle
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
        DATA_DIR = Path(__file__).parent / 'data'
    
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
    """LinkedIn scraper with SESSION PERSISTENCE - solve CAPTCHA once per week!"""
    
    # Cookie storage location
    COOKIES_DIR = Config.DATA_DIR / 'cookies'
    
    # FIXED selectors for October 2025
    SELECTORS = {
        'login': {
            'email': '#username',
            'password': '#password',
            'submit': 'button[type="submit"]'
        },
        'regular_linkedin': {
            'search_result': 'li.reusable-search__result-container',
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
        Initialize scraper with session persistence
        
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
        
        # Create cookies directory
        self.COOKIES_DIR.mkdir(parents=True, exist_ok=True)
        
        # Cookie file specific to this email
        import hashlib
        email_hash = int(hashlib.md5(email.encode()).hexdigest()[:8], 16)
        self.cookie_file = self.COOKIES_DIR / f'linkedin_session_{email_hash}.pkl'
        
        self.stats = {
            'leads_scraped': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None,
            'using_sales_nav': False,
            'pages_scraped': 0,
            'used_saved_session': False
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
    
    def save_cookies(self):
        """Save session cookies to file"""
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookie_file, 'wb') as f:
                pickle.dump(cookies, f)
            print(f"💾 Session saved! (valid for ~7 days)")
            print(f"   Next run will skip login & CAPTCHA!")
            return True
        except Exception as e:
            print(f"⚠️ Could not save session: {str(e)}")
            return False
    
    def ensure_driver_alive(self):
        """Ensure driver is alive before using it - RECOVERY HELPER"""
        if not self.driver:
            print("⚠️ Driver is None - setting up new driver")
            return self.setup_driver()
        
        try:
            # Test if driver is alive
            _ = self.driver.current_url
            return True
        except Exception as e:
            print(f"⚠️ Driver died: {str(e)}")
            print("   🔄 Attempting recovery...")
            
            # Try to close dead driver
            try:
                self.driver.quit()
            except:
                pass
            
            # Reset driver
            self.driver = None
            self.wait = None
            
            # Recreate driver
            if self.setup_driver():
                print("✅ Driver recovered successfully")
                return True
            else:
                print("❌ Driver recovery failed")
                return False
    
    def is_logged_in(self) -> bool:
        """Check if currently logged into LinkedIn"""
        try:
            current_url = self.driver.current_url
            
            # Check URL indicators
            if any(indicator in current_url for indicator in ['feed', 'mynetwork', 'sales/homepage', 'messaging']):
                return True
            
            # Check for LinkedIn nav bar (only visible when logged in)
            try:
                self.driver.find_element(By.CSS_SELECTOR, 'nav.global-nav')
                return True
            except:
                pass
            
            # Check for login/checkpoint indicators
            if any(indicator in current_url for indicator in ['login', 'checkpoint', 'challenge', 'uas/login']):
                return False
            
            return False
            
        except Exception as e:
            print(f"⚠️ Could not check login status: {str(e)}")
            return False
    
    def load_cookies(self):
        """Load session cookies from file - FIXED VERSION"""
        try:
            if not self.cookie_file.exists():
                print("🔍 No saved session found - will do fresh login")
                return False
            
            # Check cookie age
            age_days = (datetime.now().timestamp() - self.cookie_file.stat().st_mtime) / 86400
            
            if age_days > 7:
                print(f"⚠️ Saved session expired ({age_days:.1f} days old)")
                print("   Will do fresh login")
                self.cookie_file.unlink()
                return False
            
            print(f"🔄 Found saved session ({age_days:.1f} days old)")
            print("   Loading cookies...")
            
            # Ensure driver is alive
            if not self.ensure_driver_alive():
                return False
            
            # Navigate to LinkedIn
            print("   📍 Navigating to LinkedIn...")
            self.driver.get('https://www.linkedin.com')
            time.sleep(3)
            
            # Load cookies
            print("   🍪 Loading cookies...")
            with open(self.cookie_file, 'rb') as f:
                cookies = pickle.load(f)
            
            cookies_loaded = 0
            for cookie in cookies:
                cookie_copy = cookie.copy()
                if 'domain' in cookie_copy:
                    del cookie_copy['domain']
                if 'sameSite' in cookie_copy and cookie_copy['sameSite'] not in ['Strict', 'Lax', 'None']:
                    del cookie_copy['sameSite']
                try:
                    self.driver.add_cookie(cookie_copy)
                    cookies_loaded += 1
                except Exception as e:
                    continue
            
            print(f"   ✅ Loaded {cookies_loaded} cookies")
            
            # Refresh to apply cookies
            print("   🔄 Refreshing page to apply cookies...")
            self.driver.refresh()
            time.sleep(5)
            
            # FIXED: Check if logged in using dedicated method
            if self.is_logged_in():
                current_url = self.driver.current_url
                print(f"✅ Successfully resumed session!")
                print(f"   Current page: {current_url[:60]}...")
                print("   🎉 NO LOGIN NEEDED - NO CAPTCHA!")
                self.stats['used_saved_session'] = True
                return True
            else:
                print("⚠️ Saved session invalid - cookies didn't work")
                self.cookie_file.unlink()
                return False
                
        except Exception as e:
            print(f"⚠️ Could not load session: {str(e)}")
            traceback.print_exc()
            
            if self.cookie_file.exists():
                try:
                    self.cookie_file.unlink()
                except:
                    pass
            return False

    def login(self) -> bool:
        """Login to LinkedIn with extended CAPTCHA handling - FIXED VERSION"""
        try:
            print("\n🔐 Logging into LinkedIn...")
            
            # FIXED: Check if already logged in first
            if self.is_logged_in():
                print("✅ Already logged in! Skipping login.")
                return True
            
            # Try to use saved session
            if self.load_cookies():
                return True
            
            # FIXED: Only do fresh login if not logged in
            if self.is_logged_in():
                print("✅ Logged in after cookie load!")
                return True
            
            # Fresh login required
            print("🆕 Starting fresh login...")
            self.driver.get('https://www.linkedin.com/login')
            
            print("   ⏳ Waiting for login page to load...")
            self.human_delay(4, 6)
            
            # Verify we're on the login page
            current_url = self.driver.current_url
            
            # FIXED: If already logged in after navigation, return success
            if self.is_logged_in():
                print("✅ Already logged in (redirected from login page)!")
                return True
            
            if 'login' not in current_url:
                print(f"   ⚠️ Not on login page! Current URL: {current_url}")
                
                # If we're on a logged-in page, that's actually success
                if self.is_logged_in():
                    print("✅ Already logged in!")
                    return True
                
                print("   📍 Navigating to login page again...")
                self.driver.get('https://www.linkedin.com/login')
                self.human_delay(4, 6)
            
            # Wait for email field
            print("   🔍 Looking for email field...")
            try:
                email_field = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, self.SELECTORS['login']['email']))
                )
                print("   ✅ Email field found!")
            except TimeoutException:
                print("   ❌ Email field not found after 15 seconds")
                
                # Maybe we're already logged in?
                if self.is_logged_in():
                    print("✅ Already logged in!")
                    return True
                
                print(f"   📍 Current URL: {self.driver.current_url}")
                return False
            
            # Enter email
            email_field.clear()
            for char in self.email:
                email_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            self.human_delay(0.5, 1.0)
            
            # Enter password
            try:
                password_field = self.driver.find_element(By.CSS_SELECTOR, self.SELECTORS['login']['password'])
                password_field.clear()
                for char in self.password:
                    password_field.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
            except NoSuchElementException:
                print("   ❌ Password field not found")
                return False
            
            self.human_delay(0.5, 1.0)
            
            # Submit
            try:
                login_btn = self.driver.find_element(By.CSS_SELECTOR, self.SELECTORS['login']['submit'])
                login_btn.click()
            except NoSuchElementException:
                print("   ❌ Login button not found")
                return False
            
            print("  → Waiting for login...")
            self.human_delay(4, 6)
            
            # Check current page
            current_url = self.driver.current_url
            
            # CAPTCHA/Security Challenge detected
            if 'checkpoint' in current_url or 'challenge' in current_url:
                print("\n" + "="*70)
                print("🤖 LINKEDIN SECURITY CHECK DETECTED")
                print("="*70)
                print("⚠️  LinkedIn is asking you to verify you're human!")
                print("")
                print("📋 INSTRUCTIONS:")
                print("   1. Look at the browser window (should be visible)")
                print("   2. Click 'Start Puzzle' or solve the CAPTCHA")
                print("   3. Complete any security challenges")
                print("   4. Wait for LinkedIn feed to load")
                print("")
                print("⏳ I'll wait up to 5 MINUTES for you to complete this...")
                print("   (You can take your time!)")
                print("="*70 + "\n")
                
                # Wait up to 5 minutes for user to solve CAPTCHA
                max_wait = 300
                check_interval = 5
                start_time = time.time()
                
                while time.time() - start_time < max_wait:
                    time.sleep(check_interval)
                    
                    try:
                        elapsed = int(time.time() - start_time)
                        
                        # Check if we're logged in
                        if self.is_logged_in():
                            print(f"\n✅ Verification completed successfully after {elapsed} seconds!")
                            print("✅ You're now logged in!")
                            
                            # Save cookies for next time!
                            self.save_cookies()
                            
                            if USE_DATABASE:
                                db_manager.log_activity(
                                    activity_type='login',
                                    description='Successfully logged into LinkedIn (with CAPTCHA)',
                                    status='success'
                                )
                            return True
                        
                        # Still on checkpoint page
                        current_url = self.driver.current_url
                        if 'checkpoint' in current_url or 'challenge' in current_url:
                            remaining = max_wait - elapsed
                            print(f"  ⏳ Still waiting for verification... ({elapsed}s elapsed, {remaining}s remaining)")
                        
                    except Exception as e:
                        print(f"  ⚠️ Error checking status: {str(e)}")
                        continue
                
                # Timeout
                print(f"\n❌ Verification timeout after {max_wait} seconds")
                print("   Please try running the scraper again.")
                return False
            
            # No CAPTCHA - check if we're logged in
            elif self.is_logged_in():
                print("✅ Successfully logged in! (No CAPTCHA required)")
                
                # Save cookies for next time!
                self.save_cookies()
                
                if USE_DATABASE:
                    db_manager.log_activity(
                        activity_type='login',
                        description='Successfully logged into LinkedIn',
                        status='success'
                    )
                return True
            
            # Login failed for other reason
            else:
                print(f"❌ Login failed")
                print(f"   Current URL: {current_url}")
                
                # Check for error messages
                try:
                    error_msg = self.driver.find_element(By.CSS_SELECTOR, '.alert-error').text
                    print(f"   Error: {error_msg}")
                except:
                    pass
                
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
        """Search for leads using keywords - FIXED WITH DRIVER HEALTH CHECK"""
        try:
            # Verify driver is alive before searching
            if not self.ensure_driver_alive():
                print("❌ Driver died before search")
                return False
            
            # Verify we're actually logged in
            print("\n🔐 Verifying login status...")
            
            if not self.is_logged_in():
                print("❌ Not logged in! Attempting to login...")
                if not self.login():
                    return False
            
            print(f"✅ Logged in - current page: {self.driver.current_url[:60]}...")
            
            # Clean and prepare keywords
            clean_keywords = keywords.strip()
            if not clean_keywords:
                clean_keywords = "CEO founder"
            
            print(f"\n🎯 Search target: {clean_keywords}")
            
            # Try Sales Navigator first if preferred
            if self.sales_nav_preference:
                has_sales_nav = self.detect_sales_nav_access()
                
                if has_sales_nav:
                    print(f"\n🔎 Searching Sales Navigator for: {clean_keywords}")
                    
                    url_keywords = clean_keywords.replace(' ', '%20')
                    search_url = f"https://www.linkedin.com/sales/search/people?keywords={url_keywords}"
                    
                    print(f"   Navigating to: {search_url}")
                    self.driver.get(search_url)
                    self.human_delay(4, 6)
                    
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
                    else:
                        print(f"⚠️ Sales Nav redirect failed, current URL: {self.driver.current_url[:60]}")
            
            # Fallback to regular LinkedIn
            print(f"\n🔎 Searching Regular LinkedIn for: {clean_keywords}")
            url_keywords = clean_keywords.replace(' ', '%20')
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={url_keywords}"
            
            print(f"   Navigating to: {search_url}")
            self.driver.get(search_url)
            self.human_delay(3, 5)
            
            final_url = self.driver.current_url
            print(f"   Final URL: {final_url[:80]}")
            
            if 'search/results/people' in final_url:
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
                print(f"❌ Search failed! Current URL: {final_url}")
                
                # Check if we got logged out
                if not self.is_logged_in():
                    print("❌ Got logged out or hit security checkpoint!")
                
                return False
        
        except Exception as e:
            print(f"❌ Search error: {str(e)}")
            traceback.print_exc()
            return False
    
    def extract_lead_data(self, card_element) -> Optional[Dict]:
        """Extract lead data from search result card - UPDATED FOR OCT 2025"""
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
            
            # Get the full card text for debugging
            try:
                card_text = card_element.text.strip()
            except:
                card_text = ""
            
            # CRITICAL: Find profile link first
            try:
                # Try multiple link selectors
                link_selectors = [
                    'a[href*="/in/"]',
                    '.entity-result__title-text a',
                    '.app-aware-link[href*="/in/"]',
                    'a.app-aware-link'
                ]
                
                profile_link = None
                for selector in link_selectors:
                    try:
                        link_elem = card_element.find_element(By.CSS_SELECTOR, selector)
                        href = link_elem.get_attribute('href')
                        if href and '/in/' in href and 'linkedin.com' in href:
                            profile_link = href
                            break
                    except:
                        continue
                
                if not profile_link:
                    return None
                
                # Clean URL
                if '?' in profile_link:
                    profile_link = profile_link.split('?')[0]
                
                lead['profile_url'] = profile_link
                
            except Exception as e:
                return None
            
            # Extract name from the link or card
            try:
                # Try multiple name selectors
                name_selectors = [
                    '.entity-result__title-text a span[aria-hidden="true"]',
                    '.entity-result__title-text a span:first-child',
                    'span.entity-result__title-text span',
                    '.entity-result__title-text'
                ]
                
                name = None
                for selector in name_selectors:
                    try:
                        name_elem = card_element.find_element(By.CSS_SELECTOR, selector)
                        name_text = name_elem.text.strip()
                        if name_text and len(name_text) > 0:
                            name = name_text
                            break
                    except:
                        continue
                
                # Fallback: extract from card text
                if not name and card_text:
                    lines = [l.strip() for l in card_text.split('\n') if l.strip()]
                    if lines:
                        # First non-button line is usually the name
                        for line in lines:
                            if line and len(line) < 100 and not any(word in line.lower() for word in ['connect', 'message', 'follow', 'view', 'profile']):
                                name = line
                                break
                
                if name:
                    lead['name'] = name
                else:
                    return None
                    
            except:
                return None
            
            # Extract title and company
            try:
                # Try structured selectors first
                title_selectors = [
                    '.entity-result__primary-subtitle',
                    '.entity-result__summary',
                    'div.entity-result__primary-subtitle'
                ]
                
                for selector in title_selectors:
                    try:
                        subtitle_elem = card_element.find_element(By.CSS_SELECTOR, selector)
                        subtitle_text = subtitle_elem.text.strip()
                        
                        if subtitle_text:
                            # Parse "Title at Company" format
                            if ' at ' in subtitle_text:
                                parts = subtitle_text.split(' at ', 1)
                                lead['title'] = parts[0].strip()
                                lead['company'] = parts[1].strip()
                            elif ' | ' in subtitle_text:
                                parts = subtitle_text.split(' | ', 1)
                                lead['title'] = parts[0].strip()
                                if len(parts) > 1:
                                    lead['company'] = parts[1].strip()
                            else:
                                lead['title'] = subtitle_text
                            break
                    except:
                        continue
                
                # Fallback: parse from card text
                if not lead['title'] and card_text:
                    lines = [l.strip() for l in card_text.split('\n') if l.strip()]
                    if len(lines) >= 2:
                        # Second line is usually title
                        title_line = lines[1] if len(lines) > 1 else ""
                        
                        if title_line and not any(word in title_line.lower() for word in ['connect', 'message', 'follow']):
                            if ' at ' in title_line:
                                parts = title_line.split(' at ', 1)
                                lead['title'] = parts[0].strip()
                                lead['company'] = parts[1].strip()
                            else:
                                lead['title'] = title_line
                
            except:
                pass
            
            # Extract location
            try:
                location_selectors = [
                    '.entity-result__secondary-subtitle',
                    'div.entity-result__secondary-subtitle',
                    '.t-black--light.t-12'
                ]
                
                for selector in location_selectors:
                    try:
                        loc_elem = card_element.find_element(By.CSS_SELECTOR, selector)
                        loc_text = loc_elem.text.strip()
                        
                        if loc_text and not any(word in loc_text.lower() for word in ['connect', 'message', 'mutual']):
                            lead['location'] = loc_text
                            break
                    except:
                        continue
                
                # Fallback: third line in card text
                if not lead['location'] and card_text:
                    lines = [l.strip() for l in card_text.split('\n') if l.strip()]
                    if len(lines) >= 3:
                        location_line = lines[2]
                        if location_line and not any(word in location_line.lower() for word in ['connect', 'message', 'mutual', 'follower']):
                            lead['location'] = location_line
                            
            except:
                pass
            
            # Set headline (combination of title and company)
            if lead['title']:
                if lead['company']:
                    lead['headline'] = f"{lead['title']} at {lead['company']}"
                else:
                    lead['headline'] = lead['title']
            
            # Validate - must have name and profile URL
            if not lead['name'] or not lead['profile_url']:
                return None
            
            # Must be a real LinkedIn profile
            if '/in/' not in lead['profile_url']:
                return None
            
            return lead
        except Exception as e:
            return None
    

    def scrape_current_page(self):
        """Scrape leads from current page - FIXED with adaptive selectors for October 2025"""
        leads = []
        
        try:
            print("\n📊 Scraping current page...")
            self.human_delay(3, 5)
            
            # TRY MULTIPLE SELECTORS (LinkedIn changes these frequently)
            if self.stats['using_sales_nav']:
                selectors_to_try = [
                    'li.artdeco-list__item',
                    'li[class*="artdeco-list"]',
                    'div.search-result'
                ]
            else:
                # UPDATED SELECTORS for October 2025
                selectors_to_try = [
                    # Obfuscated classes (change frequently - currently working Oct 2025)
                    'div.b9fd59a4',  # Current working selector
                    'div[class^="b9"]',  # Pattern for obfuscated classes starting with b9
                    'div[class*="reusable-search"]',  # Pattern match
                    # Standard selectors (fallback)
                    'li.reusable-search__result-container',
                    'div.entity-result__item',
                    'li[class*="reusable-search"]',
                    'div.search-result',
                    'li.search-result__occluded-item',
                    # Structural fallback
                    'ul.reusable-search__entity-result-list > li',
                ]
            
            cards = []
            working_selector = None
            
            # Try each selector until we find results
            for selector in selectors_to_try:
                try:
                    test_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(test_cards) > 0:
                        cards = test_cards
                        working_selector = selector
                        print(f"  ✅ Found {len(test_cards)} results with selector: {selector}")
                        break
                except:
                    continue
            
            # If no selectors work, try structural analysis
            if not cards:
                print("  ⚠️ Standard selectors failed, trying structural analysis...")
                cards = self._find_cards_by_structure()
                if cards:
                    working_selector = "structural analysis"
                    print(f"  ✅ Found {len(cards)} results via structural analysis")
            
            if not cards:
                print("  ⚠️ No results found on page with any selector")
                print(f"  💡 Current URL: {self.driver.current_url}")
                return leads
            
            print(f"  → Processing {len(cards)} potential cards")
            
            # Deduplicate and validate
            seen_urls = set()
            valid_cards = []
            for card in cards:
                try:
                    link = card.find_element(By.CSS_SELECTOR, 'a[href*="/in/"]')
                    href = link.get_attribute('href')
                    
                    if href and '/in/' in href and 'linkedin.com/in/' in href:
                        clean_url = href.split('?')[0].rstrip('/')
                        
                        if clean_url not in seen_urls:
                            valid_cards.append(card)
                            seen_urls.add(clean_url)
                except:
                    continue
            
            print(f"  → {len(valid_cards)} unique valid profiles")
            
            # Extract data from valid cards
            for i, card in enumerate(valid_cards, 1):
                try:
                    lead_data = self.extract_lead_data(card)
                    if lead_data:
                        leads.append(lead_data)
                        self.stats['leads_scraped'] += 1
                        print(f"  [{i}/{len(valid_cards)}] ✅ {lead_data['name']}")
                    else:
                        print(f"  [{i}/{len(valid_cards)}] ⚠️  Skipped - missing data")
                except Exception as e:
                    print(f"  [{i}/{len(valid_cards)}] ❌ Error: {str(e)[:50]}")
                    self.stats['errors'] += 1
                    continue
            
            self.stats['pages_scraped'] += 1
            return leads
            
        except Exception as e:
            print(f"  ❌ Error scraping page: {str(e)}")
            return leads


    def _find_cards_by_structure(self):
        """Fallback: Find search result cards by analyzing DOM structure
        
        This method is used when LinkedIn changes their class names and our
        predefined selectors stop working. It analyzes the page structure
        to find the results list dynamically.
        """
        try:
            # Find all UL elements on the page
            all_uls = self.driver.find_elements(By.TAG_NAME, 'ul')
            
            # Find the UL with the most LI children (likely the results list)
            best_ul = None
            max_children = 0
            
            for ul in all_uls:
                try:
                    li_children = ul.find_elements(By.TAG_NAME, 'li')
                    
                    # Only consider ULs with a reasonable number of items (5-100)
                    if len(li_children) > max_children and 5 <= len(li_children) <= 100:
                        # Verify these LI elements contain profile links
                        has_profiles = False
                        profile_count = 0
                        
                        # Check first 5 items to see if they contain LinkedIn profile links
                        for li in li_children[:5]:
                            try:
                                link = li.find_element(By.CSS_SELECTOR, 'a[href*="/in/"]')
                                href = link.get_attribute('href')
                                if '/in/' in href and 'linkedin.com/in/' in href:
                                    profile_count += 1
                            except:
                                continue
                        
                        # If at least 3 out of 5 sampled items have profile links, it's probably the results list
                        if profile_count >= 3:
                            max_children = len(li_children)
                            best_ul = ul
                except:
                    continue
            
            if best_ul:
                print(f"  🔍 Structural analysis found {max_children} potential results")
                return best_ul.find_elements(By.TAG_NAME, 'li')
            
            return []
            
        except Exception as e:
            print(f"  ⚠️ Structural analysis failed: {str(e)}")
            return []
    
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
        """Main scraping function - FIXED WITH DRIVER HEALTH MONITORING"""
        all_leads = []
        self.stats['start_time'] = datetime.now()
        
        try:
            print("\n" + "="*70)
            print("🚀 LINKEDIN LEAD SCRAPER - STARTING (FIXED VERSION)")
            print("="*70)
            
            # Ensure driver is alive at the start
            if not self.ensure_driver_alive():
                print("❌ Cannot start scraping - driver setup failed")
                if USE_DATABASE:
                    db_manager.log_activity(
                        activity_type='scrape',
                        description='Scraping failed - driver initialization error',
                        status='failed',
                        error_message='Driver setup failed'
                    )
                return all_leads
            
            # Setup
            if not self.setup_driver():
                return all_leads
            
            # Login
            print("\n🔐 Checking login status...")
            
            if not self.ensure_driver_alive():
                print("❌ Driver died before login")
                return all_leads
            
            if not self.login():
                print("\n❌ Cannot proceed without login")
                if USE_DATABASE:
                    db_manager.log_activity(
                        activity_type='login',
                        description='Login failed',
                        status='failed',
                        error_message='Login unsuccessful'
                    )
                return all_leads
            
            # Verify driver after login, before search
            print("\n🔐 Verifying driver status before search...")
            if not self.ensure_driver_alive():
                print("❌ Driver died after login, before search")
                if USE_DATABASE:
                    db_manager.log_activity(
                        activity_type='scrape',
                        description='Driver died between login and search',
                        status='failed',
                        error_message='Driver session lost after login'
                    )
                return all_leads
            
            print("✅ Driver is healthy, proceeding to search...")
            
            # Get keywords
            keywords = filters.get('keywords', 'CEO founder')
            print(f"\n🎯 Target Keywords: {keywords}")
            
            # Search
            if not self.search_leads(keywords):
                print("\n❌ Search failed")
                if USE_DATABASE:
                    db_manager.log_activity(
                        activity_type='search',
                        description=f'Search failed for: {keywords}',
                        status='failed',
                        error_message='Could not perform search'
                    )
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
            
            if USE_DATABASE:
                db_manager.log_activity(
                    activity_type='scrape',
                    description=f'Error: {str(e)}',
                    status='failed',
                    error_message=str(e)
                )
        
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
        
        # Session info
        if self.stats['used_saved_session']:
            print(f"🔄 Session: REUSED (no CAPTCHA!)")
        else:
            print(f"🔄 Session: FRESH LOGIN (CAPTCHA solved)")
        
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
    
    parser = argparse.ArgumentParser(description='LinkedIn Lead Scraper - FIXED')
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