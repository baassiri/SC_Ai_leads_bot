"""
SC AI Lead Generation System - LinkedIn Message Sender
Selenium automation for sending connection requests and messages on LinkedIn
"""

import time
import random
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

try:
    from backend.config import Config
    from backend.database.db_manager import db_manager
    USE_DATABASE = True
except ImportError:
    print("⚠️ Warning: Database modules not available")
    USE_DATABASE = False
    class Config:
        pass


class LinkedInMessageSender:
    """Send connection requests and messages on LinkedIn using Selenium"""
    
    def __init__(self, email: str, password: str, headless: bool = False):
        """
        Initialize LinkedIn message sender
        
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
            'connection_requests_sent': 0,
            'messages_sent': 0,
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
        
        # Anti-detection options
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Initialize driver
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            print(f"⚠️ ChromeDriverManager failed, trying direct install: {str(e)}")
            self.driver = webdriver.Chrome(options=chrome_options)
        
        self.wait = WebDriverWait(self.driver, 20)
        
        if not self.headless:
            self.driver.maximize_window()
        
        print("✅ Chrome WebDriver ready!")
        return True
    
    def human_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def login(self) -> bool:
        """Log into LinkedIn"""
        try:
            print("\n🔐 Logging into LinkedIn...")
            
            self.driver.get('https://www.linkedin.com/login')
            self.human_delay(2, 4)
            
            # Enter credentials
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, 'username')))
            email_field.clear()
            email_field.send_keys(self.email)
            self.human_delay(0.5, 1.5)
            
            password_field = self.driver.find_element(By.ID, 'password')
            password_field.clear()
            password_field.send_keys(self.password)
            self.human_delay(0.5, 1.5)
            
            # Submit
            login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            login_button.click()
            
            print("  → Waiting for login...")
            self.human_delay(3, 5)
            
            # Verify login
            if 'feed' in self.driver.current_url or 'mynetwork' in self.driver.current_url:
                print("✅ Successfully logged in!")
                return True
            else:
                print("❌ Login failed")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return False
    
    def send_connection_request(self, profile_url: str, message: str = None, 
                                lead_name: str = None) -> Dict:
        """
        Send a connection request to a LinkedIn profile
        
        Args:
            profile_url: LinkedIn profile URL
            message: Optional connection message (max 300 chars)
            lead_name: Lead name for logging
            
        Returns:
            Dict with success status and details
        """
        result = {
            'success': False,
            'message': '',
            'sent_at': None,
            'lead_name': lead_name,
            'profile_url': profile_url
        }
        
        try:
            print(f"\n📤 Sending connection request to: {lead_name or profile_url}")
            
            # Navigate to profile
            self.driver.get(profile_url)
            self.human_delay(2, 4)
            
            # Find "Connect" button
            connect_buttons = self.driver.find_elements(By.XPATH, 
                "//button[contains(@aria-label, 'Invite') or contains(., 'Connect')]")
            
            if not connect_buttons:
                result['message'] = "Connect button not found - may already be connected"
                print(f"  ⚠️ {result['message']}")
                return result
            
            # Click Connect button
            connect_button = connect_buttons[0]
            connect_button.click()
            self.human_delay(1, 2)
            
            # Handle "Add a note" if message provided
            if message:
                try:
                    # Click "Add a note" button
                    add_note_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Add a note')]"))
                    )
                    add_note_button.click()
                    self.human_delay(0.5, 1)
                    
                    # Find note textarea
                    note_field = self.wait.until(
                        EC.presence_of_element_located((By.NAME, "message"))
                    )
                    
                    # Validate message length (LinkedIn limit is 300 chars)
                    if len(message) > 300:
                        message = message[:297] + "..."
                        print(f"  ⚠️ Message truncated to 300 characters")
                    
                    # Type message with human-like delays
                    note_field.clear()
                    for char in message:
                        note_field.send_keys(char)
                        time.sleep(random.uniform(0.05, 0.15))
                    
                    print(f"  ✅ Added personalized note ({len(message)} chars)")
                    self.human_delay(1, 2)
                    
                except Exception as e:
                    print(f"  ⚠️ Could not add note: {str(e)}")
            
            # Click "Send" button
            try:
                send_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, 
                        "//button[@aria-label='Send now' or contains(., 'Send') or @aria-label='Send invitation']"))
                )
                send_button.click()
                self.human_delay(2, 3)
                
                # Success!
                result['success'] = True
                result['sent_at'] = datetime.utcnow()
                result['message'] = 'Connection request sent successfully'
                self.stats['connection_requests_sent'] += 1
                
                print(f"  ✅ Connection request sent to {lead_name}!")
                
                if USE_DATABASE:
                    db_manager.log_activity(
                        activity_type='connection_sent',
                        description=f"Sent connection request to {lead_name}",
                        status='success'
                    )
                
            except Exception as e:
                result['message'] = f"Failed to click send: {str(e)}"
                print(f"  ❌ {result['message']}")
                self.stats['errors'] += 1
            
        except Exception as e:
            result['message'] = f"Error: {str(e)}"
            print(f"  ❌ {result['message']}")
            self.stats['errors'] += 1
            
            if USE_DATABASE:
                db_manager.log_activity(
                    activity_type='connection_sent',
                    description=f"Failed to send connection to {lead_name}",
                    status='failed',
                    error_message=str(e)
                )
        
        return result
    
    def send_message(self, profile_url: str, message: str, lead_name: str = None) -> Dict:
        """
        Send a direct message to a LinkedIn connection
        
        Args:
            profile_url: LinkedIn profile URL
            message: Message content
            lead_name: Lead name for logging
            
        Returns:
            Dict with success status and details
        """
        result = {
            'success': False,
            'message': '',
            'sent_at': None,
            'lead_name': lead_name,
            'profile_url': profile_url
        }
        
        try:
            print(f"\n💬 Sending message to: {lead_name or profile_url}")
            
            # Navigate to profile
            self.driver.get(profile_url)
            self.human_delay(2, 4)
            
            # Find "Message" button
            message_buttons = self.driver.find_elements(By.XPATH,
                "//button[contains(@aria-label, 'Message') or contains(., 'Message')]")
            
            if not message_buttons:
                result['message'] = "Message button not found - may not be connected"
                print(f"  ⚠️ {result['message']}")
                return result
            
            # Click Message button
            message_button = message_buttons[0]
            message_button.click()
            self.human_delay(1, 2)
            
            # Find message input field
            try:
                message_field = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 
                        "div[role='textbox'], div.msg-form__contenteditable"))
                )
                
                # Type message with human-like delays
                message_field.click()
                self.human_delay(0.5, 1)
                
                for char in message:
                    message_field.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
                
                print(f"  ✅ Message typed ({len(message)} chars)")
                self.human_delay(1, 2)
                
                # Find and click Send button
                send_button = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR,
                        "button[type='submit'].msg-form__send-button, button.msg-form__send-btn"))
                )
                send_button.click()
                self.human_delay(2, 3)
                
                # Success!
                result['success'] = True
                result['sent_at'] = datetime.utcnow()
                result['message'] = 'Message sent successfully'
                self.stats['messages_sent'] += 1
                
                print(f"  ✅ Message sent to {lead_name}!")
                
                if USE_DATABASE:
                    db_manager.log_activity(
                        activity_type='message_sent',
                        description=f"Sent message to {lead_name}",
                        status='success'
                    )
                
            except Exception as e:
                result['message'] = f"Failed to send message: {str(e)}"
                print(f"  ❌ {result['message']}")
                self.stats['errors'] += 1
            
        except Exception as e:
            result['message'] = f"Error: {str(e)}"
            print(f"  ❌ {result['message']}")
            self.stats['errors'] += 1
            
            if USE_DATABASE:
                db_manager.log_activity(
                    activity_type='message_sent',
                    description=f"Failed to send message to {lead_name}",
                    status='failed',
                    error_message=str(e)
                )
        
        return result
    
    def send_batch_connection_requests(self, leads: List[Dict], 
                                      max_requests: int = 10) -> Dict:
        """
        Send connection requests to multiple leads
        
        Args:
            leads: List of dicts with profile_url, message, name
            max_requests: Maximum requests to send in this batch
            
        Returns:
            Dict with batch statistics
        """
        self.stats['start_time'] = datetime.utcnow()
        
        print(f"\n🚀 Starting batch connection requests")
        print(f"   → Leads to process: {len(leads)}")
        print(f"   → Max requests: {max_requests}")
        print("="*60)
        
        results = []
        sent_count = 0
        
        for i, lead in enumerate(leads[:max_requests], 1):
            if sent_count >= max_requests:
                print(f"\n⚠️ Reached max requests limit ({max_requests})")
                break
            
            print(f"\n[{i}/{min(len(leads), max_requests)}]", end=" ")
            
            result = self.send_connection_request(
                profile_url=lead.get('profile_url'),
                message=lead.get('message'),
                lead_name=lead.get('name')
            )
            
            results.append(result)
            
            if result['success']:
                sent_count += 1
            
            # Human-like delay between requests (important!)
            if i < min(len(leads), max_requests):
                delay = random.uniform(15, 30)  # 15-30 seconds between requests
                print(f"  😴 Waiting {delay:.1f}s before next request...")
                time.sleep(delay)
        
        self.stats['end_time'] = datetime.utcnow()
        
        # Print summary
        self.print_batch_stats(results)
        
        return {
            'total_processed': len(results),
            'successful': sent_count,
            'failed': len(results) - sent_count,
            'results': results,
            'stats': self.stats
        }
    
    def print_batch_stats(self, results: List[Dict]):
        """Print batch statistics"""
        print("\n" + "="*60)
        print("📊 Batch Connection Request Summary")
        print("="*60)
        
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Total Processed: {len(results)}")
        
        if self.stats['start_time'] and self.stats['end_time']:
            duration = (self.stats['end_time'] - self.stats['start_time']).seconds
            print(f"⏱️ Duration: {duration} seconds")
            
            if successful > 0:
                avg_per_request = duration / successful
                print(f"⚡ Average per request: {avg_per_request:.1f}s")
        
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
    
    parser = argparse.ArgumentParser(description='LinkedIn Message Sender')
    parser.add_argument('--email', type=str, required=True, help='LinkedIn email')
    parser.add_argument('--password', type=str, required=True, help='LinkedIn password')
    parser.add_argument('--profile', type=str, help='Profile URL to send connection request')
    parser.add_argument('--message', type=str, help='Connection message')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    args = parser.parse_args()
    
    # Create sender
    sender = LinkedInMessageSender(
        email=args.email,
        password=args.password,
        headless=args.headless
    )
    
    # Setup and login
    sender.setup_driver()
    
    if sender.login():
        if args.profile:
            # Send single connection request
            result = sender.send_connection_request(
                profile_url=args.profile,
                message=args.message,
                lead_name="Test Lead"
            )
            
            if result['success']:
                print("\n🎉 Connection request sent successfully!")
            else:
                print(f"\n❌ Failed: {result['message']}")
        else:
            print("\n⚠️ No profile URL provided. Use --profile flag")
    
    sender.close()