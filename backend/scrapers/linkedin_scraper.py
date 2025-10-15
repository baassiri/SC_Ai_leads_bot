"""
SC AI Lead Generation System - LinkedIn Scraper
OCTOBER 2025 - TEXT PARSING VERSION
This version uses TEXT-BASED PARSING instead of CSS selectors
Works even when LinkedIn changes their class names!
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
    """LinkedIn scraper with TEXT-BASED PARSING"""
    
    # Cookie storage location
    COOKIES_DIR = Config.DATA_DIR / 'cookies'
    
    # FIXED selectors for October 2025
    SELECTORS = {
        'login': {
            'email': '#username',
            'password': '#password',
            'submit': 'button[type="submit"]'
        }
    }
    
    def __init__(self, email: str, password: str, headless: bool = False, sales_nav_preference: bool = True):
        """Initialize scraper with session persistence"""
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
        """Ensure driver is alive before using it"""
        if not self.driver:
            print("⚠️ Driver is None - setting up new driver")
            return self.setup_driver()
        
        try:
            _ = self.driver.current_url
            return True
        except Exception as e:
            print(f"⚠️ Driver died: {str(e)}")
            print("   🔄 Attempting recovery...")
            
            try:
                self.driver.quit()
            except:
                pass
            
            self.driver = None
            self.wait = None
            
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
            
            if any(indicator in current_url for indicator in ['feed', 'mynetwork', 'sales/homepage', 'messaging']):
                return True
            
            try:
                self.driver.find_element(By.CSS_SELECTOR, 'nav.global-nav')
                return True
            except:
                pass
            
            if any(indicator in current_url for indicator in ['login', 'checkpoint', 'challenge', 'uas/login']):
                return False
            
            return False
            
        except Exception as e:
            print(f"⚠️ Could not check login status: {str(e)}")
            return False
    
    def load_cookies(self):
        """Load session cookies from file"""
        try:
            if not self.cookie_file.exists():
                print("🔎 No saved session found - will do fresh login")
                return False
            
            age_days = (datetime.now().timestamp() - self.cookie_file.stat().st_mtime) / 86400
            
            if age_days > 7:
                print(f"⚠️ Saved session expired ({age_days:.1f} days old)")
                print("   Will do fresh login")
                self.cookie_file.unlink()
                return False
            
            print(f"📄 Found saved session ({age_days:.1f} days old)")
            print("   Loading cookies...")
            
            if not self.ensure_driver_alive():
                return False
            
            print("   🔑 Navigating to LinkedIn...")
            self.driver.get('https://www.linkedin.com')
            time.sleep(3)
            
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
            
            print("   🔄 Refreshing page to apply cookies...")
            self.driver.refresh()
            time.sleep(5)
            
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
        """Login to LinkedIn with extended CAPTCHA handling"""
        try:
            print("\n🔓 Logging into LinkedIn...")
            
            if self.is_logged_in():
                print("✅ Already logged in! Skipping login.")
                return True
            
            if self.load_cookies():
                return True
            
            if self.is_logged_in():
                print("✅ Logged in after cookie load!")
                return True
            
            print("🆕 Starting fresh login...")
            self.driver.get('https://www.linkedin.com/login')
            
            print("   ⏳ Waiting for login page to load...")
            self.human_delay(4, 6)
            
            current_url = self.driver.current_url
            
            if self.is_logged_in():
                print("✅ Already logged in (redirected from login page)!")
                return True
            
            if 'login' not in current_url:
                print(f"   ⚠️ Not on login page! Current URL: {current_url}")
                
                if self.is_logged_in():
                    print("✅ Already logged in!")
                    return True
                
                print("   🔎 Navigating to login page again...")
                self.driver.get('https://www.linkedin.com/login')
                self.human_delay(4, 6)
            
            print("   🔎 Looking for email field...")
            try:
                email_field = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, self.SELECTORS['login']['email']))
                )
                print("   ✅ Email field found!")
            except TimeoutException:
                print("   ❌ Email field not found after 15 seconds")
                
                if self.is_logged_in():
                    print("✅ Already logged in!")
                    return True
                
                print(f"   🔎 Current URL: {self.driver.current_url}")
                return False
            
            email_field.clear()
            for char in self.email:
                email_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            self.human_delay(0.5, 1.0)
            
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
            
            try:
                login_btn = self.driver.find_element(By.CSS_SELECTOR, self.SELECTORS['login']['submit'])
                login_btn.click()
            except NoSuchElementException:
                print("   ❌ Login button not found")
                return False
            
            print("  → Waiting for login...")
            self.human_delay(4, 6)
            
            current_url = self.driver.current_url
            
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
                
                max_wait = 300
                check_interval = 5
                start_time = time.time()
                
                while time.time() - start_time < max_wait:
                    time.sleep(check_interval)
                    
                    try:
                        elapsed = int(time.time() - start_time)
                        
                        if self.is_logged_in():
                            print(f"\n✅ Verification completed successfully after {elapsed} seconds!")
                            print("✅ You're now logged in!")
                            
                            self.save_cookies()
                            
                            if USE_DATABASE:
                                db_manager.log_activity(
                                    activity_type='login',
                                    description='Successfully logged into LinkedIn (with CAPTCHA)',
                                    status='success'
                                )
                            return True
                        
                        current_url = self.driver.current_url
                        if 'checkpoint' in current_url or 'challenge' in current_url:
                            remaining = max_wait - elapsed
                            print(f"  ⏳ Still waiting for verification... ({elapsed}s elapsed, {remaining}s remaining)")
                        
                    except Exception as e:
                        print(f"  ⚠️ Error checking status: {str(e)}")
                        continue
                
                print(f"\n❌ Verification timeout after {max_wait} seconds")
                print("   Please try running the scraper again.")
                return False
            
            elif self.is_logged_in():
                print("✅ Successfully logged in! (No CAPTCHA required)")
                
                self.save_cookies()
                
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
        """Search for leads using keywords"""
        try:
            if not self.ensure_driver_alive():
                print("❌ Driver died before search")
                return False
            
            print("\n🔎 Verifying login status...")
            
            if not self.is_logged_in():
                print("❌ Not logged in! Attempting to login...")
                if not self.login():
                    return False
            
            print(f"✅ Logged in - current page: {self.driver.current_url[:60]}...")
            
            clean_keywords = keywords.strip()
            if not clean_keywords:
                clean_keywords = "CEO founder"
            
            print(f"\n🎯 Search target: {clean_keywords}")
            
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
                
                if not self.is_logged_in():
                    print("❌ Got logged out or hit security checkpoint!")
                
                return False
        
        except Exception as e:
            print(f"❌ Search error: {str(e)}")
            traceback.print_exc()
            return False
    
    def extract_lead_data(self, card_element) -> Optional[Dict]:
        """Extract lead data from search result card - TEXT PARSING METHOD"""
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
            
            # STEP 1: Extract profile URL (CRITICAL)
            profile_link = None
            try:
                all_links = card_element.find_elements(By.TAG_NAME, 'a')
                
                for link in all_links:
                    try:
                        href = link.get_attribute('href')
                        if href and '/in/' in href and 'linkedin.com/in/' in href:
                            clean_url = href.split('?')[0].rstrip('/')
                            profile_link = clean_url
                            break
                    except:
                        continue
                
                if not profile_link:
                    return None
                
                lead['profile_url'] = profile_link
                
            except:
                return None
            
            # STEP 2: Get card text and parse it
            try:
                card_text = card_element.text.strip()
            except:
                card_text = ""
            
            if not card_text:
                return None
            
            # Split into lines and clean
            lines = [l.strip() for l in card_text.split('\n') if l.strip()]
            
            # Filter out button text and irrelevant lines
            filtered_lines = []
            button_words = ['connect', 'message', 'follow', 'view', 'save', 'more', 'profile', 'mutual']
            
            for line in lines:
                line_lower = line.lower()
                # Skip button text
                if any(btn in line_lower for btn in button_words):
                    continue
                # Skip lines that are too long (likely descriptions)
                if len(line) > 200:
                    continue
                # Skip lines with just numbers (connection count)
                if line.replace(',', '').replace(' ', '').isdigit():
                    continue
                # Keep valid lines
                if len(line) > 0:
                    filtered_lines.append(line)
            
            print(f"      DEBUG - Card has {len(filtered_lines)} parsed lines")
            
            # Parse based on line position
            if len(filtered_lines) >= 1:
                # Line 1: Name
                lead['name'] = filtered_lines[0]
                print(f"      Name: {lead['name']}")
            
            if len(filtered_lines) >= 2:
                # Line 2: Title (possibly with company)
                title_line = filtered_lines[1]
                
                # Check for "Title at Company" format
                if ' at ' in title_line:
                    parts = title_line.split(' at ', 1)
                    lead['title'] = parts[0].strip()
                    lead['company'] = parts[1].strip()
                    print(f"      Title: {lead['title']}")
                    print(f"      Company: {lead['company']}")
                # Check for "Title | Company" format
                elif ' | ' in title_line:
                    parts = title_line.split(' | ', 1)
                    lead['title'] = parts[0].strip()
                    lead['company'] = parts[1].strip() if len(parts) > 1 else None
                    print(f"      Title: {lead['title']}")
                    print(f"      Company: {lead['company']}")
                else:
                    lead['title'] = title_line
                    print(f"      Title: {lead['title']}")
            
            if len(filtered_lines) >= 3:
                # Line 3: Could be location OR additional title/company info
                line3 = filtered_lines[2]
                
                # Check if it looks like a location
                location_indicators = ['Governorate', ', ', 'Lebanon', 'Beirut', 'Area', 'District', 'Region']
                is_location = any(indicator in line3 for indicator in location_indicators)
                
                if is_location:
                    lead['location'] = line3
                    print(f"      Location: {lead['location']}")
                # Otherwise it might be company info if we don't have it yet
                elif not lead['company']:
                    # Check if it has company-like patterns
                    if ' at ' in line3:
                        parts = line3.split(' at ', 1)
                        if not lead['title']:
                            lead['title'] = parts[0].strip()
                        lead['company'] = parts[1].strip()
                        print(f"      Company (from line3): {lead['company']}")
            
            # Check line 4 for location if we haven't found it yet
            if not lead['location'] and len(filtered_lines) >= 4:
                line4 = filtered_lines[3]
                location_indicators = ['Governorate', ', ', 'Lebanon', 'Beirut', 'Area', 'District', 'Region']
                if any(indicator in line4 for indicator in location_indicators):
                    lead['location'] = line4
                    print(f"      Location (from line4): {lead['location']}")
            
            # Build headline
            if lead['title']:
                if lead['company']:
                    lead['headline'] = f"{lead['title']} at {lead['company']}"
                else:
                    lead['headline'] = lead['title']
            
            # Validation: Must have name and profile URL at minimum
            if not lead['name'] or not lead['profile_url']:
                print(f"      ❌ Missing required fields - name: {lead['name']}, url: {lead['profile_url']}")
                return None
            
            # Clean up name (remove duplicates if present)
            if lead['name'] and '\n' in lead['name']:
                name_parts = lead['name'].split('\n')
                if len(name_parts) > 1 and name_parts[0] == name_parts[1]:
                    lead['name'] = name_parts[0]
            
            print(f"      ✅ Successfully extracted lead: {lead['name']}")
            return lead
            
        except Exception as e:
            print(f"      ❌ Extraction error: {str(e)}")
            traceback.print_exc()
            return None
    
    def scrape_current_page(self):
        """Scrape leads from current page - DYNAMIC DETECTION"""
        leads = []
        
        try:
            print("\n📊 Scraping current page...")
            self.human_delay(3, 5)
            
            print("  🔍 Finding search result cards...")
            
            # Find ALL profile links on the page
            all_profile_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/in/"]')
            print(f"  📊 Found {len(all_profile_links)} profile links")
            
            if len(all_profile_links) == 0:
                print("  ❌ No profile links found on page")
                return leads
            
            # Find the parent containers (cards) that contain these links
            cards_found = []
            seen_cards = set()
            
            for link in all_profile_links:
                try:
                    # Walk up the DOM to find the card container
                    current = link
                    for level in range(15):
                        try:
                            parent = current.find_element(By.XPATH, '..')
                            links_in_parent = parent.find_elements(By.CSS_SELECTOR, 'a[href*="/in/"]')
                            link_count = len(links_in_parent)
                            
                            # If this parent has 1-5 profile links, it's likely the card
                            if 1 <= link_count <= 5:
                                element_id = parent.id
                                
                                if element_id not in seen_cards:
                                    cards_found.append(parent)
                                    seen_cards.add(element_id)
                                break
                            
                            current = parent
                        except:
                            break
                except:
                    continue
            
            print(f"  🎯 Found {len(cards_found)} unique result cards")
            
            if len(cards_found) == 0:
                print("  ❌ Could not identify result cards")
                return leads
            
            # Extract data from each card
            for i, card in enumerate(cards_found, 1):
                try:
                    print(f"\n  [{i}/{len(cards_found)}] Extracting card data...")
                    lead_data = self.extract_lead_data(card)
                    
                    if lead_data:
                        leads.append(lead_data)
                        self.stats['leads_scraped'] += 1
                        print(f"  [{i}/{len(cards_found)}] ✅ {lead_data['name']}")
                    else:
                        print(f"  [{i}/{len(cards_found)}] ⚠️  Skipped - could not extract data")
                except Exception as e:
                    print(f"  [{i}/{len(cards_found)}] ❌ Error: {str(e)[:50]}")
                    self.stats['errors'] += 1
                    continue
            
            self.stats['pages_scraped'] += 1
            print(f"\n✅ Page scraping complete - found {len(leads)} leads")
            return leads
            
        except Exception as e:
            print(f"  ❌ Error scraping page: {str(e)}")
            traceback.print_exc()
            return leads
    
    def go_to_next_page(self) -> bool:
        """Navigate to next page"""
        try:
            print("\n➡️ Going to next page...")
            
            # Find next button (try multiple selectors)
            next_selectors = [
                'button[aria-label="Next"]',
                'button[aria-label="View next page"]',
                '.artdeco-pagination__button--next',
                'button.artdeco-pagination__button.artdeco-pagination__button--next'
            ]
            
            next_btn = None
            for selector in next_selectors:
                try:
                    btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if btn.is_enabled():
                        next_btn = btn
                        break
                except:
                    continue
            
            if not next_btn:
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
        """Main scraping function"""
        all_leads = []
        self.stats['start_time'] = datetime.now()
        
        try:
            print("\n" + "="*70)
            print("🚀 LINKEDIN LEAD SCRAPER - TEXT PARSING VERSION")
            print("="*70)
            
            if not self.ensure_driver_alive():
                print("❌ Cannot start scraping - driver setup failed")
                return all_leads
            
            if not self.setup_driver():
                return all_leads
            
            print("\n🔓 Checking login status...")
            
            if not self.ensure_driver_alive():
                print("❌ Driver died before login")
                return all_leads
            
            if not self.login():
                print("\n❌ Cannot proceed without login")
                return all_leads
            
            print("\n🔎 Verifying driver status before search...")
            if not self.ensure_driver_alive():
                print("❌ Driver died after login, before search")
                return all_leads
            
            print("✅ Driver is healthy, proceeding to search...")
            
            keywords = filters.get('keywords', 'CEO founder')
            print(f"\n🎯 Target Keywords: {keywords}")
            
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
        
        if self.stats['used_saved_session']:
            print(f"📄 Session: REUSED (no CAPTCHA!)")
        else:
            print(f"📄 Session: FRESH LOGIN (CAPTCHA solved)")
        
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
    
    parser = argparse.ArgumentParser(description='LinkedIn Lead Scraper - TEXT PARSING VERSION')
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