import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pickle
import os
from datetime import datetime
from backend.credentials_manager import credentials_manager


class LinkedInSender:
    def __init__(self):
        self.driver = None
        self.cookies_file = "data/linkedin_cookies.pkl"
        self.daily_limit = 100
        self.sent_today = 0
        
    def init_driver(self):
        """Initialize Chrome WebDriver with stealth settings"""
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--start-maximized')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("✅ Chrome driver initialized")
        
    def login_manual(self):
        """AUTO-LOGIN using saved credentials from credentials_manager"""
        if not self.driver:
            self.init_driver()
        
        # Get credentials from credentials_manager
        creds = credentials_manager.get_linkedin_credentials()
        
        if not creds:
            print("❌ No LinkedIn credentials found!")
            print("💡 Please save your credentials in Settings first")
            return False
        
        email = creds['email']
        password = creds['password']
        
        print(f"🔐 Logging in to LinkedIn as: {email}")
        
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        
        try:
            # Fill in email
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.clear()
            email_field.send_keys(email)
            time.sleep(0.5)
            
            # Fill in password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(password)
            time.sleep(0.5)
            
            # Click sign in button
            sign_in_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            sign_in_btn.click()
            
            print("⏳ Waiting for login...")
            print(f"🔍 Current URL: {self.driver.current_url}")
            time.sleep(3)
            
            # Wait for login to complete
            max_wait = 60
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                current_url = self.driver.current_url
                print(f"🔍 Checking URL: {current_url}")
                
                if "/feed" in current_url or "/mynetwork" in current_url:
                    print("✅ Login successful! (Detected feed page)")
                    self.save_cookies()
                    return True
                
                try:
                    self.driver.find_element(By.ID, "global-nav")
                    print("✅ Login successful! (Detected navigation)")
                    self.save_cookies()
                    return True
                except NoSuchElementException:
                    pass
                
                if "checkpoint" in current_url or "challenge" in current_url:
                    print("⚠️ LinkedIn security verification required!")
                    print("👉 Please complete the verification in the browser...")
                    
                    verify_start = time.time()
                    while time.time() - verify_start < 300:
                        current_url = self.driver.current_url
                        
                        if "/feed" in current_url or "/mynetwork" in current_url:
                            print("✅ Verification completed! Login successful!")
                            self.save_cookies()
                            return True
                        
                        try:
                            self.driver.find_element(By.ID, "global-nav")
                            print("✅ Verification completed! Login successful!")
                            self.save_cookies()
                            return True
                        except NoSuchElementException:
                            pass
                        
                        time.sleep(2)
                    
                    print("❌ Verification timeout")
                    return False
                
                if "/login" in current_url:
                    try:
                        error_msg = self.driver.find_element(By.CLASS_NAME, "form__input--error")
                        print(f"❌ Login error: {error_msg.text}")
                        return False
                    except NoSuchElementException:
                        pass
                
                time.sleep(2)
            
            print("❌ Login timeout - page did not load")
            return False
                    
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return False
            
    def save_cookies(self):
        """Save cookies for future sessions"""
        os.makedirs(os.path.dirname(self.cookies_file), exist_ok=True)
        pickle.dump(self.driver.get_cookies(), open(self.cookies_file, "wb"))
        print("💾 Session cookies saved!")
        
    def load_cookies(self):
        """Load saved cookies"""
        if not os.path.exists(self.cookies_file):
            print("ℹ️ No saved cookies found")
            return False
        
        try:
            if not self.driver:
                self.init_driver()
                
            self.driver.get("https://www.linkedin.com")
            time.sleep(1)
            
            cookies = pickle.load(open(self.cookies_file, "rb"))
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            
            self.driver.refresh()
            time.sleep(2)
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "global-nav"))
                )
                print("✅ Logged in using saved session!")
                return True
            except TimeoutException:
                print("⚠️ Session expired. Need fresh login.")
                return False
                
        except Exception as e:
            print(f"⚠️ Error loading cookies: {str(e)}")
            return False
            
    def random_delay(self, min_sec=2, max_sec=5):
        """Random delay to mimic human behavior"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
        
    def send_connection_request(self, profile_url, message):
        """Send connection request with personalized message - HANDLES REDIRECT & POPUP"""
        try:
            print(f"\n📤 Navigating to profile: {profile_url}")
            
            self.driver.get(profile_url)
            self.random_delay(3, 6)
            
            # Try multiple selectors for Connect button
            connect_selectors = [
                "//button[contains(@aria-label, 'Invite') and contains(@aria-label, 'to connect')]",
                "//button[contains(., 'Connect')]",
                "//button[contains(@aria-label, 'Connect')]",
                "//span[text()='Connect']/parent::button"
            ]
            
            connect_button = None
            for selector in connect_selectors:
                try:
                    connect_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    print(f"✅ Found Connect button with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not connect_button:
                print("⚠️ Connect button not found - may already be connected")
                return {"success": False, "error": "Connect button not found"}
            
            connect_button.click()
            print("✅ Clicked Connect button")

            # CRITICAL: Wait and check if LinkedIn redirected us
            time.sleep(3)

            current_url = self.driver.current_url
            target_profile_slug = profile_url.split('/in/')[-1].split('/')[0]

            if target_profile_slug not in current_url:
                print(f"⚠️ LinkedIn redirected away from target profile!")
                print(f"   Current URL: {current_url}")
                print(f"   Expected: {profile_url}")
                print("🔄 Navigating back to target profile...")
                
                self.driver.get(profile_url)
                time.sleep(3)
                
                # Try clicking Connect again
                connect_button = None
                for selector in connect_selectors:
                    try:
                        connect_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        break
                    except TimeoutException:
                        continue
                
                if not connect_button:
                    return {"success": False, "error": "LinkedIn blocked automation - redirect detected"}
                
                connect_button.click()
                print("✅ Clicked Connect button (after redirect fix)")
                time.sleep(3)
            
            # CRITICAL: Wait and check for Sales Navigator popup
            print("⏳ Waiting for modal to load...")
            time.sleep(3)
            
            # Try to close Sales Navigator popup if it appears
            sales_nav_popup_selectors = [
                "//button[@aria-label='Dismiss']",
                "//button[contains(@aria-label, 'Close')]",
                "//button[@data-test-modal-close-btn]",
                "//svg[@data-test-icon='close-small']/parent::button",
                "//button[contains(@class, 'artdeco-modal__dismiss')]"
            ]
            
            popup_closed = False
            for selector in sales_nav_popup_selectors:
                try:
                    close_button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    close_button.click()
                    print("✅ Closed Sales Navigator popup")
                    time.sleep(2)
                    popup_closed = True
                    break
                except TimeoutException:
                    continue
            
            if popup_closed:
                # If popup was closed, we need to click Connect again
                print("🔄 Clicking Connect button again after closing popup...")
                connect_button = None
                for selector in connect_selectors:
                    try:
                        connect_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        break
                    except TimeoutException:
                        continue
                
                if connect_button:
                    connect_button.click()
                    print("✅ Clicked Connect button (second time)")
                    time.sleep(3)
            
            # Now look for the actual connection modal
            # Try to find "Add a note" button
            add_note_selectors = [
                "//button[contains(., 'Add a note')]",
                "//button[contains(@aria-label, 'Add a note')]",
                "//span[text()='Add a note']/parent::button",
                "//button[contains(text(), 'Add a note')]"
            ]
            
            note_added = False
            for selector in add_note_selectors:
                try:
                    add_note_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    add_note_button.click()
                    time.sleep(2)
                    print("✅ Clicked 'Add a note'")
                    
                    # Find and fill message box
                    message_selectors = [
                        "//textarea[@name='message']",
                        "//textarea[contains(@id, 'custom-message')]",
                        "//textarea[@id='custom-message']",
                        "//textarea[contains(@class, 'ember-text-area')]"
                    ]
                    
                    message_box = None
                    for msg_selector in message_selectors:
                        try:
                            message_box = WebDriverWait(self.driver, 3).until(
                                EC.presence_of_element_located((By.XPATH, msg_selector))
                            )
                            print(f"✅ Found message box")
                            break
                        except TimeoutException:
                            continue
                    
                    if message_box:
                        message_box.clear()
                        
                        # Truncate message if too long (LinkedIn limit is 300 chars)
                        if len(message) > 295:
                            message = message[:295] + "..."
                            print(f"⚠️ Message truncated to {len(message)} chars")
                        
                        # Type message
                        for char in message:
                            message_box.send_keys(char)
                            time.sleep(random.uniform(0.03, 0.08))
                        
                        print(f"✅ Typed message ({len(message)} chars)")
                        note_added = True
                        time.sleep(2)
                        break
                    
                except TimeoutException:
                    continue
            
            if not note_added:
                print("⚠️ No 'Add a note' option available - sending without message")
            
            # Find and click Send button
            print("🔍 Looking for Send button...")
            send_selectors = [
                "//button[@aria-label='Send now']",
                "//button[@aria-label='Send invitation']",
                "//button[contains(@aria-label, 'Send')]",
                "//button[contains(text(), 'Send now')]",
                "//button[contains(text(), 'Send')]",
                "//span[text()='Send']/parent::button",
                "//span[text()='Send now']/parent::button",
                "//button[contains(@class, 'artdeco-button--primary') and contains(., 'Send')]"
            ]
            
            send_button = None
            for selector in send_selectors:
                try:
                    send_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    print(f"✅ Found Send button")
                    break
                except TimeoutException:
                    continue
            
            if not send_button:
                print("❌ Could not find Send button!")
                print("📸 Taking screenshot for debugging...")
                try:
                    self.driver.save_screenshot("data/send_button_error.png")
                    print("✅ Screenshot saved to data/send_button_error.png")
                except:
                    pass
                return {"success": False, "error": "Send button not found"}
            
            send_button.click()
            print(f"✅ Connection request sent {'with personalized message' if note_added else 'without note'}!")
            self.sent_today += 1
            
            time.sleep(3)
            
            return {
                "success": True, 
                "message": f"Connection request sent {'with note' if note_added else '(no note option)'}"
            }
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error sending connection request: {error_msg}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": error_msg}
            
    def check_if_connected(self, profile_url):
        """Check if already connected to this person"""
        try:
            self.driver.get(profile_url)
            self.random_delay(2, 4)
            
            try:
                self.driver.find_element(By.XPATH, 
                    "//button[contains(@aria-label, 'Message') or contains(., 'Message')]")
                print("ℹ️ Already connected to this person")
                return True
            except NoSuchElementException:
                return False
                
        except Exception as e:
            print(f"⚠️ Could not check connection status: {e}")
            return False
            
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            print("🔒 Browser closed")


# Global instance
linkedin_sender = LinkedInSender()