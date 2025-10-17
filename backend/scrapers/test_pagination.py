"""
Debug script to find LinkedIn pagination buttons
Run this while on a LinkedIn search results page
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# Setup Chrome
options = Options()
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

print("\n🔍 PAGINATION BUTTON FINDER")
print("="*70)
print("\n📋 Instructions:")
print("1. Browser will open")
print("2. Login to LinkedIn manually")
print("3. Search for 'CEO founder' with USA filter")
print("4. Press ENTER in this terminal when ready")
print("="*70)

driver.get('https://www.linkedin.com/login')
input("\n⏸️  Press ENTER when you're on a search results page with pagination...")

print("\n🔍 Analyzing pagination buttons...")

# Scroll to bottom
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(2)

# Method 1: Find ALL buttons on the page
print("\n📊 ALL BUTTONS ON PAGE:")
all_buttons = driver.find_elements(By.TAG_NAME, 'button')
print(f"   Found {len(all_buttons)} total buttons")

pagination_buttons = []
for i, btn in enumerate(all_buttons):
    try:
        text = btn.text.strip()
        aria_label = btn.get_attribute('aria-label')
        classes = btn.get_attribute('class')
        is_displayed = btn.is_displayed()
        is_enabled = btn.is_enabled()
        
        # Look for pagination-related buttons
        if any(keyword in str(text).lower() + str(aria_label).lower() + str(classes).lower() 
               for keyword in ['next', 'page', '2', '3', 'pagination']):
            pagination_buttons.append({
                'index': i,
                'text': text,
                'aria_label': aria_label,
                'classes': classes,
                'displayed': is_displayed,
                'enabled': is_enabled
            })
    except:
        continue

print(f"\n✅ Found {len(pagination_buttons)} pagination-related buttons:\n")

for btn_info in pagination_buttons:
    print(f"Button #{btn_info['index']}:")
    print(f"   Text: '{btn_info['text']}'")
    print(f"   Aria-label: '{btn_info['aria_label']}'")
    print(f"   Classes: '{btn_info['classes'][:100]}...'")
    print(f"   Visible: {btn_info['displayed']}, Enabled: {btn_info['enabled']}")
    print()

# Method 2: Find pagination container
print("\n🔍 Looking for pagination container...")
pagination_selectors = [
    '.artdeco-pagination',
    '[class*="pagination"]',
    'nav[aria-label*="pagination"]',
    'div[class*="search-results__pagination"]'
]

for selector in pagination_selectors:
    try:
        containers = driver.find_elements(By.CSS_SELECTOR, selector)
        if containers:
            print(f"\n✅ Found container with: {selector}")
            container = containers[0]
            html = container.get_attribute('outerHTML')
            print(f"\n📄 HTML (first 500 chars):\n{html[:500]}")
            break
    except:
        continue

print("\n" + "="*70)
print("✅ Debug complete! Use this info to fix the selectors.")
print("="*70)

input("\nPress ENTER to close browser...")
driver.quit()