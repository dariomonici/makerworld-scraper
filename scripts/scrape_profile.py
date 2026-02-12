#!/usr/bin/env python3
"""
MakerWorld Profile Scraper - Extracts user profile data

Usage:
  python3 scripts/scrape_profile.py https://makerworld.com/en/@darionji
  python3 scripts/scrape_profile.py https://makerworld.com/en/@darionji --out my_profile.json

Outputs (saved in ./output/ directory):
 - profile_data.json - Structured profile data
 - page.html - Full HTML of the page (for debugging)
 - debug_elements.json - Debug info about found elements

Installation:
  pip install playwright
  playwright install chromium
"""
import asyncio
import json
import sys
import argparse
import re
from pathlib import Path
from datetime import datetime

async def scrape_profile(url, out_path=None, timeout=60000):
    from playwright.async_api import async_playwright
    
    # Create output directory
    output_dir = Path(__file__).parent.parent / 'output'
    output_dir.mkdir(exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        print(f'🌐 Navigating to {url}...')
        try:
            # Use 'load' instead of 'networkidle' - much more reliable
            await page.goto(url, timeout=timeout, wait_until='load')
            print('✓ Page loaded')
        except Exception as e:
            print(f"⚠️  Navigation error: {e}", file=sys.stderr)
            await browser.close()
            return None
        
        # Wait for the user_base_info section to load
        print('⏳ Waiting for profile data to load...')
        try:
            await page.wait_for_selector('div.user_base_info', timeout=30000)
            print('✓ User info section found')
        except Exception as e:
            print(f"⚠️  Could not find user_base_info section: {e}", file=sys.stderr)
        
        # Wait for dynamic content to render
        print('⏳ Waiting for dynamic content...')
        try:
            # Wait for one of the key elements that contains data
            await page.wait_for_selector('span.mw-css-1v58zuy, div.level-icon-size-96', timeout=10000)
            print('✓ Content elements found')
        except Exception as e:
            print(f"⚠️  Some content may not be fully loaded: {e}", file=sys.stderr)
        
        # Scroll the page to trigger lazy loading
        print('⏳ Scrolling page to trigger lazy loading...')
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(2)
        await page.evaluate('window.scrollTo(0, 0)')
        await asyncio.sleep(1)
        
        # Give extra time for any remaining dynamic content
        print('⏳ Waiting for all content to load...')
        await asyncio.sleep(5)  # Increased from 3 to 5 seconds
        print('✓ Ready to extract data')
        
        # Save HTML for debugging AFTER scrolling and waiting
        html = await page.content()
        html_path = output_dir / 'page.html'
        html_path.write_text(html, encoding='utf-8')
        print(f'💾 HTML saved to {html_path}')
        
        # Create minimal debug file (removed detailed debug_info)
        # We still keep track of some basic info for troubleshooting
        
        # Extract profile data - only public fields
        profile_data = {
            'url': url,
            'scraped_at': datetime.utcnow().isoformat() + 'Z',
            'username': None,
            'followers': None,
            'following': None,
            'likes': None,
            'model_downloads': None,
            'model_prints': None
        }
        
        print('🔍 Extracting profile data...')
        
        try:
            # Extract username
            username_elem = await page.query_selector('span.mw-css-1v58zuy')
            if username_elem:
                profile_data['username'] = (await username_elem.inner_text()).strip()
                print(f'  ✓ Username: {profile_data["username"]}')
            else:
                # Fallback: try h1
                h1_elem = await page.query_selector('h1')
                if h1_elem:
                    profile_data['username'] = (await h1_elem.inner_text()).strip()
                    print(f'  ✓ Username (fallback): {profile_data["username"]}')
            
            # Extract followers and following
            follow_elems = await page.query_selector_all('div.MuiStack-root.mw-css-qn1esg')
            print(f'  📊 Found {len(follow_elems)} follow elements')
            for i, elem in enumerate(follow_elems):
                text = await elem.inner_text()
                
                # Look for numbers followed by "Followers" or "Following"
                followers_match = re.search(r'([\d,]+)\s*Followers?', text, re.IGNORECASE)
                following_match = re.search(r'([\d,]+)\s*Following', text, re.IGNORECASE)
                
                if followers_match:
                    profile_data['followers'] = int(followers_match.group(1).replace(',', ''))
                    print(f'  ✓ Followers: {profile_data["followers"]}')
                if following_match:
                    profile_data['following'] = int(following_match.group(1).replace(',', ''))
                    print(f'  ✓ Following: {profile_data["following"]}')
            
            # Extract stats (likes, downloads, prints) - REMOVED BOOSTS
            stats_elem = await page.query_selector('div.MuiStack-root.mw-css-7ddqqi')
            if stats_elem:
                stats_text = await stats_elem.inner_text()
                
                # Try to match numbers with labels
                numbers = re.findall(r'\b(\d+)\b', stats_text)
                print(f'  📊 Numbers found in stats: {numbers}')
                
                # Assuming the order is: likes, downloads, prints (without boosts since it's private)
                # We need to identify which numbers are which
                # Let's try to find the labels
                
                # Try pattern matching first
                likes_match = re.search(r'([\d,]+)\s*Likes?', stats_text, re.IGNORECASE)
                downloads_match = re.search(r'([\d,]+)\s*(?:Model\s*)?Downloads?', stats_text, re.IGNORECASE)
                prints_match = re.search(r'([\d,]+)\s*(?:Model\s*)?Prints?', stats_text, re.IGNORECASE)
                
                if likes_match:
                    profile_data['likes'] = int(likes_match.group(1).replace(',', ''))
                    print(f'  ✓ Likes: {profile_data["likes"]}')
                if downloads_match:
                    profile_data['model_downloads'] = int(downloads_match.group(1).replace(',', ''))
                    print(f'  ✓ Model Downloads: {profile_data["model_downloads"]}')
                if prints_match:
                    profile_data['model_prints'] = int(prints_match.group(1).replace(',', ''))
                    print(f'  ✓ Model Prints: {profile_data["model_prints"]}')
                
                # If pattern matching didn't work, try assuming order based on number count
                if not all([likes_match, downloads_match, prints_match]):
                    print(f'  ⚠️  Pattern matching incomplete, trying positional extraction...')
                    # Since we found 4 numbers before (boosts, likes, downloads, prints)
                    # and boosts is private, we might now find 3 numbers
                    if len(numbers) == 3 and profile_data['likes'] is None:
                        profile_data['likes'] = int(numbers[0])
                        profile_data['model_downloads'] = int(numbers[1])
                        profile_data['model_prints'] = int(numbers[2])
                        print(f'  ✓ Stats extracted (assumed order):')
                        print(f'    Likes: {profile_data["likes"]}')
                        print(f'    Downloads: {profile_data["model_downloads"]}')
                        print(f'    Prints: {profile_data["model_prints"]}')
                    elif len(numbers) == 4:
                        # If still showing 4 numbers, skip first (boosts is private but maybe shows 0)
                        profile_data['likes'] = int(numbers[1])
                        profile_data['model_downloads'] = int(numbers[2])
                        profile_data['model_prints'] = int(numbers[3])
                        print(f'  ✓ Stats extracted (skipping first number):')
                        print(f'    Likes: {profile_data["likes"]}')
                        print(f'    Downloads: {profile_data["model_downloads"]}')
                        print(f'    Prints: {profile_data["model_prints"]}')
            
        except Exception as e:
            print(f'⚠️  Error extracting profile data: {e}', file=sys.stderr)
            import traceback
            traceback.print_exc()
        
        # Save profile data
        if out_path:
            out_file = Path(out_path)
        else:
            out_file = output_dir / 'profile_data.json'
        
        out_file.write_text(json.dumps(profile_data, indent=2), encoding='utf-8')
        
        print(f'\n✅ Profile data saved to {out_file}')
        print(f'\n📊 Extracted data summary:')
        for key, value in profile_data.items():
            if key not in ['url', 'scraped_at']:
                if value is not None and value != []:
                    if isinstance(value, list):
                        print(f'  {key}: {len(value)} items')
                    else:
                        print(f'  {key}: {value}')
                else:
                    print(f'  {key}: ❌ NOT FOUND')
        
        await browser.close()
        return profile_data

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape MakerWorld user profile data')
    parser.add_argument('url', help='Profile URL (e.g., https://makerworld.com/en/@username)')
    parser.add_argument('--out', '-o', help='Output JSON file path (default: output/profile_data.json)')
    args = parser.parse_args()
    
    try:
        data = asyncio.run(scrape_profile(args.url, args.out))
        if data:
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print('\n\n⚠️  Interrupted by user')
        sys.exit(130)
    except Exception as e:
        print(f'\n❌ Error: {e}', file=sys.stderr)
        sys.exit(1)
