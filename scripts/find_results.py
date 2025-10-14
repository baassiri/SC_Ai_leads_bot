"""
Find LinkedIn Search Results - Final Version
Specifically targets the actual search result cards, not pagination
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

def find_results():
    print("🔍 Finding LinkedIn Search Results")
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
        print("🔐 Logging in...")
        driver.get('https://www.linkedin.com/login')
        time.sleep(2)
        
        driver.find_element(By.ID, 'username').send_keys(email)
        driver.find_element(By.ID, 'password').send_keys(password)
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        time.sleep(5)
        
        print("🔍 Navigating to search...")
        driver.get('https://www.linkedin.com/search/results/people/?keywords=CEO')
        time.sleep(4)
        
        print("\n" + "="*60)
        print("Strategy 1: Find all links with /in/ (profile links)")
        print("="*60)
        
        profile_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/in/"]')
        print(f"Found {len(profile_links)} profile links")
        
        if profile_links:
            print("\nFirst 5 profile links:")
            for i, link in enumerate(profile_links[:5], 1):
                href = link.get_attribute('href')
                text = link.text.strip()
                parent = link.find_element(By.XPATH, '..')
                parent_tag = parent.tag_name
                parent_class = parent.get_attribute('class')
                
                print(f"\n[{i}] {href[:50]}")
                print(f"    Text: '{text}'")
                print(f"    Parent: <{parent_tag} class='{parent_class[:50]}'>")
        
        print("\n" + "="*60)
        print("Strategy 2: Find parent containers of profile links")
        print("="*60)
        
        if profile_links:
            first_link = profile_links[0]
            
            # Go up the DOM tree to find the card container
            current = first_link
            for level in range(1, 8):
                try:
                    current = current.find_element(By.XPATH, '..')
                    tag = current.tag_name
                    classes = current.get_attribute('class')
                    
                    # Check if this looks like a card container
                    if tag in ['li', 'div']:
                        # Count children
                        children = current.find_elements(By.XPATH, './*')
                        print(f"\nLevel {level}: <{tag}> with {len(children)} children")
                        print(f"  Classes: {classes[:80]}")
                        
                        # Check if it has multiple text spans (name, title, etc)
                        spans = current.find_elements(By.TAG_NAME, 'span')
                        texts = [s.text.strip() for s in spans if s.text.strip() and len(s.text.strip()) > 2]
                        if len(texts) > 2:
                            print(f"  ✅ Found {len(texts)} text elements:")
                            for t in texts[:5]:
                                print(f"     - '{t[:40]}'")
                            
                            # This is likely our container!
                            if classes:
                                first_class = classes.split()[0]
                                selector = f'{tag}.{first_class}'
                                print(f"\n  🎯 SUGGESTED SELECTOR: '{selector}'")
                                
                                # Test if this selector finds multiple results
                                test_results = driver.find_elements(By.CSS_SELECTOR, selector)
                                print(f"  ✅ This selector finds {len(test_results)} results!")
                                
                                if len(test_results) >= 5:
                                    print(f"\n  🎉 THIS IS LIKELY THE CORRECT CONTAINER!")
                                    break
                except:
                    break
        
        print("\n" + "="*60)
        print("Strategy 3: JavaScript page analysis")
        print("="*60)
        
        # Use JavaScript to find elements with profile URLs
        script = """
        const links = Array.from(document.querySelectorAll('a[href*="/in/"]'));
        const uniqueParents = new Set();
        
        links.forEach(link => {
            let parent = link.parentElement;
            for(let i = 0; i < 5; i++) {
                if(parent && (parent.tagName === 'LI' || parent.tagName === 'DIV')) {
                    const classes = parent.className;
                    if(classes && classes.trim()) {
                        uniqueParents.add(classes.split(' ')[0]);
                    }
                }
                parent = parent?.parentElement;
            }
        });
        
        return Array.from(uniqueParents);
        """
        
        unique_classes = driver.execute_script(script)
        print(f"Found {len(unique_classes)} unique parent classes:")
        
        for cls in unique_classes[:10]:
            test_selector = f'.{cls}'
            elements = driver.find_elements(By.CSS_SELECTOR, test_selector)
            if len(elements) >= 5 and len(elements) <= 20:
                print(f"  ✅ '.{cls}' finds {len(elements)} elements (LIKELY RESULTS!)")
            elif len(elements) > 0:
                print(f"     '.{cls}' finds {len(elements)} elements")
        
        print("\n" + "="*60)
        print("🔍 Browser staying open for inspection")
        print("="*60)
        print("\nYou can now:")
        print("1. Inspect the page manually")
        print("2. Look at the Elements tab in DevTools")
        print("3. Find the container that wraps each person card")
        input("\nPress Enter to close...")
        
    finally:
        driver.quit()

if __name__ == '__main__':
    find_results()
