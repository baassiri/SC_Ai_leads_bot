"""
LinkedIn Message Sender - FIXED
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import random


class LinkedInMessageSender:
    
    def __init__(self, email: str, password: str, headless: bool = False):
        self.email = email
        self.password = password
        self.driver = None
        self.headless = headless
        self.is_logged_in = False
        
    def start_session(self):
        print("🚀 Starting LinkedIn session...")
        
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(10)
        
        self._login()
        
    def _login(self):
        print("🔐 Logging into LinkedIn...")
        
        try:
            self.driver.get('https://www.linkedin.com/login')
            time.sleep(2)
            
            email_field = self.driver.find_element(By.ID, 'username')
            password_field = self.driver.find_element(By.ID, 'password')
            
            email_field.send_keys(self.email)
            time.sleep(0.5)
            password_field.send_keys(self.password)
            time.sleep(0.5)
            
            login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            login_button.click()
            
            time.sleep(5)
            
            if '/feed' in self.driver.current_url or '/mynetwork' in self.driver.current_url:
                self.is_logged_in = True
                print("✅ Logged in successfully!")
            else:
                print("⚠️  Login may have failed - check for CAPTCHA or 2FA")
                input("Press Enter after solving CAPTCHA...")
                self.is_logged_in = True
                
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            raise
    
    def send_connection_request(self, profile_url: str, message: str, lead_name: str = None) -> dict:
        if not self.is_logged_in:
            return {
                'success': False,
                'message': 'Not logged in',
                'error': 'Session not started'
            }
        
        print(f"\n📤 Sending connection request to {lead_name or 'lead'}...")
        print(f"   URL: {profile_url}")
        
        try:
            self.driver.get(profile_url)
            self._random_delay(3, 5)
            
            # Scroll to top first
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            connect_button = self._find_connect_button()
            
            if not connect_button:
                return {
                    'success': False,
                    'message': 'Connect button not found',
                    'error': 'Already connected or button missing'
                }
            
            # Scroll button into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", connect_button)
            time.sleep(1)
            
            # Try JS click (more reliable)
            try:
                self.driver.execute_script("arguments[0].click();", connect_button)
            except:
                # Fallback to normal click
                connect_button.click()
            
            self._random_delay(2, 3)
            
            # Try to add note
            try:
                # Wait for modal
                add_note_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[contains(., "Add a note")]'))
                )
                
                # Scroll and click
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_note_button)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", add_note_button)
                self._random_delay(1, 2)
                
                # Type message
                message_box = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, 'custom-message'))
                )
                message_box.clear()
                
                for char in message:
                    message_box.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
                
                self._random_delay(1, 2)
                
                # Send
                send_button = self.driver.find_element(By.XPATH, '//button[contains(@aria-label, "Send")]')
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", send_button)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", send_button)
                
                print(f"✅ Connection request sent with note!")
                self._random_delay(3, 5)
                
                return {
                    'success': True,
                    'message': 'Connection request sent',
                    'error': None
                }
                
            except (TimeoutException, NoSuchElementException):
                print("⚠️  No note option - sending without message")
                
                try:
                    send_button = self.driver.find_element(By.XPATH, '//button[contains(@aria-label, "Send") or contains(., "Send")]')
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", send_button)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", send_button)
                    self._random_delay(3, 5)
                    
                    return {
                        'success': True,
                        'message': 'Connection sent without note',
                        'error': None
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'message': 'Could not send',
                        'error': str(e)
                    }
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return {
                'success': False,
                'message': 'Error sending request',
                'error': str(e)
            }
    
    def _find_connect_button(self):
        # Try aria-label
        try:
            return self.driver.find_element(By.CSS_SELECTOR, 'button[aria-label*="Connect"]')
        except NoSuchElementException:
            pass
        
        # Try XPath
        try:
            return self.driver.find_element(By.XPATH, '//button[contains(., "Connect")]')
        except NoSuchElementException:
            pass
        
        # Search all buttons
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, 'button')
            for btn in buttons:
                if 'connect' in btn.text.lower():
                    return btn
        except:
            pass
        
        return None
    
    def _random_delay(self, min_seconds: float, max_seconds: float):
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def close_session(self):
        if self.driver:
            self.driver.quit()
            print("👋 Session closed")


if __name__ == '__main__':
    sender = LinkedInMessageSender(
        email='your-email@example.com',
        password='your-password',
        headless=False
    )
    
    sender.start_session()
    
    result = sender.send_connection_request(
        profile_url='https://linkedin.com/in/test-profile',
        message='Hi! I came across your profile and would love to connect.',
        lead_name='Test Lead'
    )
    
    print(f"\nResult: {result}")
    
    sender.close_session()