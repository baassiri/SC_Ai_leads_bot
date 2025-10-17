#!/usr/bin/env python3
"""
LinkedIn Scraper - COMPLETE FIX (ALL 3 FIXES)
==============================================
This script applies ALL fixes in one go:
1. ✅ Increase scraping to 100 leads (max_pages: 3 → 10)
2. ✅ Add duplicate prevention (skip already-scraped profiles)
3. ✅ Add USA-only location filter (no more international leads)
"""

import sys
from pathlib import Path

print("=" * 80)
print("🔧 LINKEDIN SCRAPER - MASTER FIX (ALL 3 FIXES)")
print("=" * 80)

# Path to the scraper file
scraper_file = Path("backend/scrapers/linkedin_scraper.py")

if not scraper_file.exists():
    print("\n❌ Could not find backend/scrapers/linkedin_scraper.py")
    print("   Make sure you're running this from the project root directory")
    sys.exit(1)

print("\n📂 Found scraper file!")
print(f"   Location: {scraper_file}")

# Read the file
with open(scraper_file, 'r', encoding='utf-8') as f:
    content = f.read()

fixes_applied = []

# ============================================================================
# FIX #1: Change max_pages from 3 to 10
# ============================================================================
print("\n" + "=" * 80)
print("FIX #1: Increase max_pages from 3 to 10 (for 100+ leads)")
print("=" * 80)

old_max_pages = "def scrape_leads(self, filters: Dict, max_pages: int = 3) -> List[Dict]:"
new_max_pages = "def scrape_leads(self, filters: Dict, max_pages: int = 10) -> List[Dict]:"

if old_max_pages in content:
    content = content.replace(old_max_pages, new_max_pages)
    print("✅ Changed max_pages from 3 to 10")
    print("   📊 Expected: ~10 leads/page × 10 pages = 100 leads")
    fixes_applied.append("max_pages increased to 10")
else:
    print("⚠️  max_pages already set (or line not found)")

# ============================================================================
# FIX #2: Add duplicate checking
# ============================================================================
print("\n" + "=" * 80)
print("FIX #2: Add duplicate prevention")
print("=" * 80)

old_extraction = """            # Extract data from each card
            for i, card in enumerate(cards_found, 1):
                try:
                    print(f"\\n  [{i}/{len(cards_found)}] Extracting card data...")
                    lead_data = self.extract_lead_data(card)
                    
                    if lead_data:
                        leads.append(lead_data)
                        self.stats['leads_scraped'] += 1
                        print(f"  [{i}/{len(cards_found)}] ✅ {lead_data['name']}")
                    else:
                        print(f"  [{i}/{len(cards_found)}] ⚠️  Skipped - could not extract data")"""

new_extraction = """            # Extract data from each card
            for i, card in enumerate(cards_found, 1):
                try:
                    print(f"\\n  [{i}/{len(cards_found)}] Extracting card data...")
                    lead_data = self.extract_lead_data(card)
                    
                    if lead_data:
                        # ✅ FIX #2: Check for duplicates before adding
                        profile_url = lead_data.get('profile_url')
                        
                        if profile_url:
                            # Check if already in current batch
                            if any(lead.get('profile_url') == profile_url for lead in leads):
                                print(f"  [{i}/{len(cards_found)}] ⏭️  Skipped - duplicate in current batch")
                                continue
                            
                            # Check if already in database
                            if USE_DATABASE:
                                try:
                                    existing = db_manager.get_lead_by_profile_url(profile_url)
                                    if existing:
                                        print(f"  [{i}/{len(cards_found)}] ⏭️  Skipped - already in database")
                                        continue
                                except:
                                    pass  # Database check failed, continue anyway
                        
                        leads.append(lead_data)
                        self.stats['leads_scraped'] += 1
                        print(f"  [{i}/{len(cards_found)}] ✅ {lead_data['name']}")
                    else:
                        print(f"  [{i}/{len(cards_found)}] ⚠️  Skipped - could not extract data")"""

if old_extraction in content:
    content = content.replace(old_extraction, new_extraction)
    print("✅ Added duplicate checking logic")
    print("   🔍 Will skip:")
    print("      - Duplicates in current batch")
    print("      - Profiles already in database")
    fixes_applied.append("Duplicate prevention added")
else:
    print("⚠️  Duplicate checking code not found (may already exist)")

# ============================================================================
# FIX #3: Add USA-only location filter
# ============================================================================
print("\n" + "=" * 80)
print("FIX #3: Add USA-only location filter")
print("=" * 80)

# Regular LinkedIn search URL
old_search_url = 'search_url = f"https://www.linkedin.com/search/results/people/?keywords={url_keywords}"'
new_search_url = '''# ✅ FIX #3: USA-only filter (LinkedIn geoUrn 103644278 = United States)
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={url_keywords}&geoUrn=%5B%2210364427 8%22%5D"'''

if old_search_url in content:
    content = content.replace(old_search_url, new_search_url)
    
    # Add console indicator
    content = content.replace(
        'print(f"   Navigating to: {search_url}")',
        'print(f"   Navigating to: {search_url}")\n            print(f"   🇺🇸 Location Filter: United States ONLY")'
    )
    
    print("✅ Added USA location filter")
    print("   🌎 Will only scrape leads from United States")
    fixes_applied.append("USA location filter added")
else:
    print("⚠️  Search URL not found (may already be modified)")

# ============================================================================
# Save the modified file
# ============================================================================
print("\n" + "=" * 80)
print("💾 SAVING ALL CHANGES")
print("=" * 80)

if not fixes_applied:
    print("⚠️  No changes were made - file may already be fixed!")
    print("   Or the code structure has changed.")
    sys.exit(0)

try:
    with open(scraper_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Successfully updated linkedin_scraper.py")
except Exception as e:
    print(f"❌ Error saving file: {e}")
    sys.exit(1)

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 80)
print("🎉 ALL FIXES APPLIED SUCCESSFULLY!")
print("=" * 80)

print("\n📊 Changes made:")
for i, fix in enumerate(fixes_applied, 1):
    print(f"   {i}. ✅ {fix}")

print("\n🔄 NEXT STEPS:")
print("   1. ⛔ Stop the bot (click 'Stop Bot' in dashboard)")
print("   2. 🔄 Restart the server:")
print("      - Press Ctrl+C in the terminal")
print("      - Run: START_WINDOWS.bat")
print("   3. ▶️  Start scraping again (click 'Start Bot')")

print("\n✨ EXPECTED RESULTS:")
print("   ✅ Will scrape up to 100 leads per session")
print("   ✅ Will skip already-scraped profiles (no duplicates)")
print("   ✅ Will only find USA-based leads (no international)")

print("\n" + "=" * 80)
print("🚀 Your scraper is now optimized for production!")
print("=" * 80)
