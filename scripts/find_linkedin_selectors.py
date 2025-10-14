"""
LinkedIn Selector Finder
This script helps you find the current LinkedIn selectors by testing various options
"""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
from dotenv import load_dotenv

load_dotenv()

def find_selectors():
    """Test various selectors to find which ones work"""
    
    print("🔍 LinkedIn Selector Finder")
    print("="*60)
    
    email = os.getenv('LINKEDIN_EMAIL')
    password = os.getenv('LINKEDIN_PASSWORD')
    
    # Setup Chrome
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        # Login
        print("🔐 Logging in...")
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
        
        print("\n" + "="*60)
        print("Testing Different Selectors:")
        print("="*60)
        
        # Test various container selectors
        container_selectors = [
            'li.reusable-search__result-container',
            'div.entity-result',
            'li.entity-result',
            'div[class*="search-result"]',
            'li[class*="search-result"]',
            'div.search-results-container li',
            'ul.reusable-search__entity-result-list li',
            'div[data-chameleon-result-urn]',
            'li[data-chameleon-result-urn]',
        ]
        
        print("\n1️⃣ Testing CONTAINER selectors:")
        working_container = None
        for selector in container_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and len(elements) > 0:
                    print(f"   ✅ FOUND: '{selector}' ({len(elements)} results)")
                    if not working_container:
                        working_container = selector
                else:
                    print(f"   ❌ Empty: '{selector}'")
            except Exception as e:
                print(f"   ❌ Error: '{selector}' - {str(e)[:50]}")
        
        if not working_container:
            print("\n⚠️ Could not find any working container selector!")
            print("🔍 Let me try to find ANY list items...")
            
            # Try to find any li or div elements
            all_li = driver.find_elements(By.TAG_NAME, 'li')
            all_divs = driver.find_elements(By.TAG_NAME, 'div')
            print(f"   Found {len(all_li)} <li> elements total")
            print(f"   Found {len(all_divs)} <div> elements total")
            
            # Print first few li classes
            print("\n   First 10 <li> elements with classes:")
            for i, li in enumerate(all_li[:10]):
                class_name = li.get_attribute('class')
                if class_name:
                    print(f"      [{i+1}] {class_name[:100]}")
        
        else:
            print(f"\n✅ Best container: '{working_container}'")
            
            # Now test selectors within that container
            print(f"\n2️⃣ Testing selectors INSIDE container:")
            
            first_result = driver.find_elements(By.CSS_SELECTOR, working_container)[0]
            
            # Test name selectors
            name_selectors = [
                'span.entity-result__title-text',
                'a.app-aware-link span[aria-hidden="true"]',
                'span[dir="ltr"] span[aria-hidden="true"]',
                'div.entity-result__title-text a',
                'a[href*="/in/"] span',
                '.entity-result__title-line a span',
                'span.entity-result__title-text a span',
            ]
            
            print("\n   NAME selectors:")
            for selector in name_selectors:
                try:
                    elem = first_result.find_element(By.CSS_SELECTOR, selector)
                    text = elem.text.strip()
                    if text:
                        print(f"      ✅ '{selector}' → '{text}'")
                except:
                    print(f"      ❌ '{selector}'")
            
            # Test title selectors
            title_selectors = [
                '.entity-result__primary-subtitle',
                'div.entity-result__primary-subtitle',
                'div[class*="primary-subtitle"]',
                '.entity-result__summary',
            ]
            
            print("\n   TITLE/POSITION selectors:")
            for selector in title_selectors:
                try:
                    elem = first_result.find_element(By.CSS_SELECTOR, selector)
                    text = elem.text.strip()
                    if text:
                        print(f"      ✅ '{selector}' → '{text[:50]}'")
                except:
                    print(f"      ❌ '{selector}'")
            
            # Test profile link selectors
            link_selectors = [
                'a.app-aware-link[href*="/in/"]',
                'a[href*="/in/"]',
                '.entity-result__title-line a',
                'a.entity-result__title-link',
            ]
            
            print("\n   PROFILE LINK selectors:")
            for selector in link_selectors:
                try:
                    elem = first_result.find_element(By.CSS_SELECTOR, selector)
                    href = elem.get_attribute('href')
                    if href and '/in/' in href:
                        print(f"      ✅ '{selector}' → '{href[:60]}'")
                except:
                    print(f"      ❌ '{selector}'")
        
        print("\n" + "="*60)
        print("🔍 Browser will stay open for manual inspection")
        print("="*60)
        input("\nPress Enter to close browser...")
        
    finally:
        driver.quit()

if __name__ == '__main__':
    find_selectors()
