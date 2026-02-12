#!/usr/bin/env python3
"""
Simple headless scraper using pyppeteer to capture HTML snapshot and diagnostics
Usage:
  python3 scripts/py_scrape_makerworld.py https://makerworld.com/en/@darionji --out /tmp/mw.html

Outputs:
 - HTML saved to --out path (or printed to stdout if not provided)
 - screenshot saved to /tmp/mw_screenshot.png
 - diagnostics JSON saved to /tmp/mw_diag.json

Note: pyppeteer will download a Chromium binary on first run (approx 100MB). If running in a locked container without network or privileges, prefer running via Docker or CI.
"""
import asyncio
import json
import sys
import argparse
from pathlib import Path

async def scrape(url, out_path=None, timeout=30000, wait_selector='[data-trackid]'):
    from pyppeteer import launch
    browser = await launch(headless=True, args=['--no-sandbox'])
    page = await browser.newPage()
    await page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    try:
        await page.goto(url, {'timeout': timeout, 'waitUntil': 'domcontentloaded'})
    except Exception as e:
        # still proceed to capture whatever is available
        print(f"navigation error: {e}", file=sys.stderr)
    # try to wait for selector briefly
    found = False
    try:
        await page.waitForSelector(wait_selector, {'timeout': 30000})
        found = True
    except Exception:
        found = False
    html = await page.content()
    screenshot_path = Path('/tmp/mw_screenshot.png')
    await page.screenshot({'path': str(screenshot_path), 'fullPage': True})
    diag = {
        'url': url,
        'found_selector': found,
        'selector': wait_selector,
        'length_html': len(html)
    }
    diag_path = Path('/tmp/mw_diag.json')
    diag_path.write_text(json.dumps(diag, indent=2))
    if out_path:
        Path(out_path).write_text(html)
        print(f'HTML saved to {out_path}')
    else:
        print(html)
    await browser.close()
    return diag

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('--out', '-o', help='path to save HTML')
    args = parser.parse_args()
    try:
        diag = asyncio.get_event_loop().run_until_complete(scrape(args.url, args.out))
        print('Diagnostics:', json.dumps(diag))
    except Exception as e:
        print('Error:', e, file=sys.stderr)
        sys.exit(1)
