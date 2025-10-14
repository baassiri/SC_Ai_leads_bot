"""
Advanced LinkedIn Selector Finder
Handles obfuscated class names
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

def find_selectors_advanced():
    """Find selectors using structural analysis"""
    
    print("🔍 Advanced LinkedIn Selector Finder")
    print("="*60)
    
    email = os.getenv('LINKEDIN_EMAIL')
    password = os.getenv('LINKEDIN_PASSWORD')
    
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
        print("Analyzing Page Structure:")
        print("="*60)
        
        # Find UL elements
        all_uls = driver.find_elements(By.TAG_NAME, 'ul')
        print(f"\n📋 Found {len(all_uls)} <ul> elements")
        
        best_ul = None
        max_children = 0
        
        for i, ul in enumerate(all_uls):
            try:
                children = ul.find_elements(By.TAG_NAME, 'li')
                num_children = len(children)
                
                if num_children > max_children and num_children > 5:
                    max_children = num_children
                    best_ul = ul
                    print(f"   [{i+1}] <ul> with {num_children} <li> children ✅")
            except:
                pass
        
        if best_ul:
            print(f"\n✅ Found results container with {max_children} items!")
            
            result_items = best_ul.find_elements(By.TAG_NAME, 'li')
            
            print(f"\n🔍 Analyzing first result item...")
            first_item = result_items[0]
            
            links = first_item.find_elements(By.TAG_NAME, 'a')
            print(f"\n   Found {len(links)} links in first result")
            
            for i, link in enumerate(links[:5], 1):
                href = link.get_attribute('href')
                text = link.text.strip()
                
                if '/in/' in href:
                    print(f"   [{i}] Profile link: {href[:60]}")
                    if text:
                        print(f"       Text: '{text}'")
                
            spans = first_item.find_elements(By.TAG_NAME, 'span')
            print(f"\n   Found {len(spans)} spans in first result")
            
            print("\n   Spans with text:")
            for i, span in enumerate(spans[:10], 1):
                text = span.text.strip()
                if text and len(text) > 2:
                    classes = span.get_attribute('class')
                    print(f"   [{i}] '{text[:50]}' (classes: {classes[:50]})")
            
            outer_html = first_item.get_attribute('outerHTML')
            
            import re
            class_match = re.search(r'<li class="([^"]+)"', outer_html)
            if class_match:
                li_classes = class_match.group(1)
                print(f"\n✅ LI container classes: '{li_classes}'")
                
                selector = f'li.{li_classes.split()[0]}'
                print(f"✅ Suggested container selector: '{selector}'")
            
            print("\n🔗 Testing profile link extraction:")
            try:
                profile_link = first_item.find_element(By.CSS_SELECTOR, 'a[href*="/in/"]')
                href = profile_link.get_attribute('href')
                print(f"   ✅ Found profile link: {href[:60]}")
                print(f"   ✅ Selector: 'a[href*=\"/in/\"]'")
                
                name_text = profile_link.text.strip()
                if name_text:
                    print(f"   ✅ Name from link: '{name_text}'")
            except Exception as e:
                print(f"   ❌ Could not find profile link: {str(e)[:50]}")
            
            print("\n📄 First 500 chars of first result HTML:")
            print(outer_html[:500])
            
        else:
            print("\n❌ Could not find results container")
        
        print("\n" + "="*60)
        print("🔍 Browser staying open - inspect manually if needed")
        print("="*60)
        input("\nPress Enter to close...")
        
    finally:
        driver.quit()

if __name__ == '__main__':
    find_selectors_advanced()
