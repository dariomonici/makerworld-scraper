#!/usr/bin/env python3
"""
MakerWorld Profile Scraper - Extracts user profile data

Usage:
  python3 scripts/scrape_profile.py https://makerworld.com/en/@darionji
  python3 scripts/scrape_profile.py https://makerworld.com/en/@darionji --out my_profile.json

Outputs (saved in ./output/ directory):
 - profile_data.json - Structured profile data
 - page.html - Full HTML of the page (for debugging)

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
            await page.goto(url, timeout=timeout, wait_until='domcontentloaded')
        except Exception as e:
            print(f"⚠️  Navigation error: {e}", file=sys.stderr)
            await browser.close()
            return None
        
        # Wait for the user_base_info section to load
        print('⏳ Waiting for profile data to load...')
        try:
            await page.wait_for_selector('div.user_base_info', timeout=30000)
        except Exception as e:
            print(f"⚠️  Could not find user_base_info section: {e}", file=sys.stderr)
        
        # Save HTML for debugging
        html = await page.content()
        html_path = output_dir / 'page.html'
        html_path.write_text(html, encoding='utf-8')
        print(f'💾 HTML saved to {html_path}')
        
        # Extract profile data
        profile_data = {
            'url': url,
            'scraped_at': datetime.utcnow().isoformat() + 'Z',
            'username': None,
            'user_level': None,
            'points': None,
            'boost_tokens': None,
            'followers': None,
            'following': None,
            'boosts': None,
            'likes': None,
            'model_downloads': None,
            'model_prints': None,
            'achievements': []
        }
        
        print('🔍 Extracting profile data...')
        
        try:
            # Extract username from span.mw-css-1v58zuy
            username_elem = await page.query_selector('span.mw-css-1v58zuy')
            if username_elem:
                profile_data['username'] = (await username_elem.inner_text()).strip()
                print(f'  ✓ Username: {profile_data["username"]}')
            
            # Extract user level from div.level-icon-size-96
            level_elem = await page.query_selector('div.level-icon-size-96.mw-css-12k4syt')
            if level_elem:
                level_text = await level_elem.inner_text()
                level_match = re.search(r'(\d+)', level_text)
                if level_match:
                    profile_data['user_level'] = int(level_match.group(1))
                    print(f'  ✓ User Level: {profile_data["user_level"]}')
            
            # Extract points from span.mw-css-yyek0l
            points_elem = await page.query_selector('span.mw-css-yyek0l')
            if points_elem:
                points_text = await points_elem.inner_text()
                points_match = re.search(r'([\d,]+)', points_text)
                if points_match:
                    profile_data['points'] = int(points_match.group(1).replace(',', ''))
                    print(f'  ✓ Points: {profile_data["points"]}')
            
            # Extract boost tokens from a.mw-css-1pqes8k
            boost_tokens_elem = await page.query_selector('a.mw-css-1pqes8k')
            if boost_tokens_elem:
                boost_text = await boost_tokens_elem.inner_text()
                boost_match = re.search(r'([\d,]+)', boost_text)
                if boost_match:
                    profile_data['boost_tokens'] = int(boost_match.group(1).replace(',', ''))
                    print(f'  ✓ Boost Tokens: {profile_data["boost_tokens"]}')
            
            # Extract followers and following from div.MuiStack-root.mw-css-qn1esg
            follow_elems = await page.query_selector_all('div.MuiStack-root.mw-css-qn1esg')
            for elem in follow_elems:
                text = await elem.inner_text()
                if 'Followers' in text or 'Follower' in text:
                    match = re.search(r'([\d,]+)', text)
                    if match:
                        profile_data['followers'] = int(match.group(1).replace(',', ''))
                        print(f'  ✓ Followers: {profile_data["followers"]}')
                elif 'Following' in text:
                    match = re.search(r'([\d,]+)', text)
                    if match:
                        profile_data['following'] = int(match.group(1).replace(',', ''))
                        print(f'  ✓ Following: {profile_data["following"]}')
            
            # Extract boosts, likes, model downloads, model prints from div.MuiStack-root.mw-css-7ddqqi
            stats_elem = await page.query_selector('div.MuiStack-root.mw-css-7ddqqi')
            if stats_elem:
                stats_text = await stats_elem.inner_text()
                lines = stats_text.split('\n')
                
                for i, line in enumerate(lines):
                    line_lower = line.lower()
                    if 'boost' in line_lower and i > 0:
                        match = re.search(r'([\d,]+)', lines[i-1])
                        if match:
                            profile_data['boosts'] = int(match.group(1).replace(',', ''))
                            print(f'  ✓ Boosts: {profile_data["boosts"]}')
                    elif 'like' in line_lower and i > 0:
                        match = re.search(r'([\d,]+)', lines[i-1])
                        if match:
                            profile_data['likes'] = int(match.group(1).replace(',', ''))
                            print(f'  ✓ Likes: {profile_data["likes"]}')
                    elif 'download' in line_lower and i > 0:
                        match = re.search(r'([\d,]+)', lines[i-1])
                        if match:
                            profile_data['model_downloads'] = int(match.group(1).replace(',', ''))
                            print(f'  ✓ Model Downloads: {profile_data["model_downloads"]}')
                    elif 'print' in line_lower and 'profile' not in line_lower and i > 0:
                        match = re.search(r'([\d,]+)', lines[i-1])
                        if match:
                            profile_data['model_prints'] = int(match.group(1).replace(',', ''))
                            print(f'  ✓ Model Prints: {profile_data["model_prints"]}')
            
            # Extract achievements from div.MuiStack-root.border.mw-css-kodck9
            achievements_elem = await page.query_selector('div.MuiStack-root.border.mw-css-kodck9')
            if achievements_elem:
                achievement_items = await achievements_elem.query_selector_all('[class*="achievement"], img[alt]')
                for item in achievement_items:
                    try:
                        # Try to get alt text from images or title
                        alt = await item.get_attribute('alt')
                        if alt and alt not in profile_data['achievements']:
                            profile_data['achievements'].append(alt)
                    except:
                        pass
                if profile_data['achievements']:
                    print(f'  ✓ Achievements: {len(profile_data["achievements"])} found')
            
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
        print(f'\n📊 Extracted data:')
        for key, value in profile_data.items():
            if key not in ['url', 'scraped_at'] and value is not None:
                print(f'  {key}: {value}')
        
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

# Made with Bob
