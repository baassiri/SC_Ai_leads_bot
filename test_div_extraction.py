"""
Find Correct Selectors Inside div.b9fd59a4 Cards
This will tell us exactly what selectors to use
"""

import sys
from pathlib import Path
import time

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
from dotenv import load_dotenv

load_dotenv()

def find_working_selectors():
    """Find what selectors actually work inside div.b9fd59a4"""
    
    print("="*70)
    print("🔍 FINDING CORRECT SELECTORS FOR div.b9fd59a4 CARDS")
    print("="*70)
    
    email = os.getenv('LINKEDIN_EMAIL')
    password = os.getenv('LINKEDIN_PASSWORD')
    
    if not email or not password:
        print("❌ Missing credentials in .env file")
        return
    
    # Setup Chrome
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        # Login
        print("\n🔐 Logging in...")
        driver.get('https://www.linkedin.com/login')
        time.sleep(2)
        
        driver.find_element(By.ID, 'username').send_keys(email)
        driver.find_element(By.ID, 'password').send_keys(password)
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        time.sleep(5)
        
        # Navigate to search
        print("🔍 Navigating to search...")
        driver.get('https://www.linkedin.com/search/results/people/?keywords=CEO')
        time.sleep(3)
        
        # Find the cards
        cards = driver.find_elements(By.CSS_SELECTOR, 'div.b9fd59a4')
        
        if not cards:
            print("❌ No div.b9fd59a4 cards found!")
            return
        
        print(f"✅ Found {len(cards)} cards with div.b9fd59a4")
        print("\n" + "="*70)
        print("ANALYZING FIRST CARD")
        print("="*70)
        
        first_card = cards[0]
        
        # Test NAME selectors
        print("\n1️⃣ Testing NAME selectors:")
        name_selectors = [
            'span.entity-result__title-text a span[aria-hidden="true"]',
            'a span[aria-hidden="true"]',
            'a[href*="/in/"] span[aria-hidden="true"]',
            'span[dir="ltr"]',
            'a span[dir="ltr"]',
            'a[href*="/in/"]',  # Just get the link text
        ]
        
        working_name_selector = None
        for selector in name_selectors:
            try:
                elem = first_card.find_element(By.CSS_SELECTOR, selector)
                text = elem.text.strip()
                if text and len(text) > 2:
                    print(f"   ✅ '{selector}' → '{text}'")
                    if not working_name_selector:
                        working_name_selector = selector
            except:
                print(f"   ❌ '{selector}' - failed")
        
        # Test TITLE selectors
        print("\n2️⃣ Testing TITLE/POSITION selectors:")
        title_selectors = [
            '.entity-result__primary-subtitle',
            'div.entity-result__primary-subtitle',
            'div[class*="primary-subtitle"]',
            '[class*="subtitle"]',
        ]
        
        working_title_selector = None
        for selector in title_selectors:
            try:
                elem = first_card.find_element(By.CSS_SELECTOR, selector)
                text = elem.text.strip()
                if text and len(text) > 2:
                    print(f"   ✅ '{selector}' → '{text[:60]}'")
                    if not working_title_selector:
                        working_title_selector = selector
            except:
                print(f"   ❌ '{selector}' - failed")
        
        # Test LOCATION selectors
        print("\n3️⃣ Testing LOCATION selectors:")
        location_selectors = [
            '.entity-result__secondary-subtitle',
            'div.entity-result__secondary-subtitle',
            '[class*="secondary-subtitle"]',
        ]
        
        working_location_selector = None
        for selector in location_selectors:
            try:
                elem = first_card.find_element(By.CSS_SELECTOR, selector)
                text = elem.text.strip()
                if text and len(text) > 2:
                    print(f"   ✅ '{selector}' → '{text[:60]}'")
                    if not working_location_selector:
                        working_location_selector = selector
            except:
                print(f"   ❌ '{selector}' - failed")
        
        # Test PROFILE LINK selectors
        print("\n4️⃣ Testing PROFILE LINK selectors:")
        link_selectors = [
            'a.app-aware-link[href*="/in/"]',
            'a[href*="/in/"]',
            '.entity-result__title-line a',
            'a',
        ]
        
        working_link_selector = None
        for selector in link_selectors:
            try:
                elem = first_card.find_element(By.CSS_SELECTOR, selector)
                href = elem.get_attribute('href')
                if href and '/in/' in href:
                    print(f"   ✅ '{selector}' → '{href[:60]}'")
                    if not working_link_selector:
                        working_link_selector = selector
            except:
                print(f"   ❌ '{selector}' - failed")
        
        # Print summary
        print("\n" + "="*70)
        print("📋 RECOMMENDED SELECTORS")
        print("="*70)
        
        print("\nCopy these into your linkedin_scraper.py SELECTORS dictionary:")
        print("\n'regular_linkedin': {")
        print(f"    'search_result': 'div.b9fd59a4',")
        
        if working_name_selector:
            print(f"    'name': '{working_name_selector}',")
        else:
            print("    'name': '❌ NO WORKING SELECTOR FOUND',")
        
        if working_title_selector:
            print(f"    'title': '{working_title_selector}',")
        else:
            print("    'title': '❌ NO WORKING SELECTOR FOUND',")
        
        if working_location_selector:
            print(f"    'location': '{working_location_selector}',")
        else:
            print("    'location': '❌ NO WORKING SELECTOR FOUND',")
        
        if working_link_selector:
            print(f"    'profile_link': '{working_link_selector}',")
        else:
            print("    'profile_link': '❌ NO WORKING SELECTOR FOUND',")
        
        print("    'next_button': 'button[aria-label=\"Next\"]'")
        print("}")
        
        # Print HTML for manual inspection
        print("\n" + "="*70)
        print("📄 FIRST CARD HTML (for manual inspection)")
        print("="*70)
        print(first_card.get_attribute('outerHTML')[:1000])
        
        print("\n" + "="*70)
        print("🔍 Browser staying open for manual inspection")
        print("="*70)
        input("\nPress Enter to close...")
        
    finally:
        driver.quit()

if __name__ == '__main__':
    find_working_selectors()