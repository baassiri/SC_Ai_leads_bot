import sqlite3
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import random

class LinkedInMessenger:
    def __init__(self, db_path='database.db'):
        self.db_path = db_path
        self.driver = None
        self.wait = None
        
    def init_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def login(self, email, password):
        try:
            self.driver.get('https://www.linkedin.com/login')
            time.sleep(random.uniform(2, 4))
            
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, 'username')))
            email_field.send_keys(email)
            
            password_field = self.driver.find_element(By.ID, 'password')
            password_field.send_keys(password)
            
            login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            login_button.click()
            
            time.sleep(random.uniform(3, 5))
            return True
        except Exception as e:
            print(f"Login error: {e}")
            return False
            
    def send_message(self, profile_url, message):
        try:
            self.driver.get(profile_url)
            time.sleep(random.uniform(2, 4))
            
            message_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Message')]"))
            )
            message_button.click()
            time.sleep(random.uniform(1, 2))
            
            message_box = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.msg-form__contenteditable"))
            )
            message_box.send_keys(message)
            time.sleep(random.uniform(1, 2))
            
            send_button = self.driver.find_element(By.CSS_SELECTOR, "button.msg-form__send-button")
            send_button.click()
            
            time.sleep(random.uniform(2, 3))
            self.log_message(profile_url, message, 'sent')
            return True
        except Exception as e:
            print(f"Message send error: {e}")
            self.log_message(profile_url, message, 'failed')
            return False
            
    def log_message(self, profile_url, message, status):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (profile_url, message, status, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (profile_url, message, status, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
    def get_conversation_history(self, profile_url):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT message, status, timestamp FROM messages
            WHERE profile_url = ?
            ORDER BY timestamp DESC
        ''', (profile_url,))
        results = cursor.fetchall()
        conn.close()
        return results
        
    def close(self):
        if self.driver:
            self.driver.quit()