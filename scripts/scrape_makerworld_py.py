#!/usr/bin/env python3
"""
Simple headless scraper using pyppeteer to capture HTML snapshot and diagnostics
Usage:
  python3 scripts/scrape_makerworld_py.py https://makerworld.com/en/@darionji --out /tmp/result.json

Outputs:
 - JSON saved to --out path
 - screenshot saved to /tmp/mw_screenshot.png
 - diagnostics JSON saved to /tmp/mw_diag.json
 - HTML saved to /tmp/result_py.html

Note: pyppeteer will download a Chromium binary on first run (approx 100-200MB).
"""
import asyncio
import json
import sys
import argparse
from pathlib import Path

async def scrape(url, out_path=None, timeout=60000, wait_selector='[data-trackid]'):
    from pyppeteer import launch
    browser = await launch(headless=True, args=['--no-sandbox'])
    page = await browser.newPage()
    await page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    try:
        await page.goto(url, {'timeout': timeout, 'waitUntil': 'domcontentloaded'})
    except Exception as e:
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
    html_path = Path('/tmp/result_py.html')
    html_path.write_text(html, encoding='utf-8')

    # basic parse: account name, points, models
    out = {
        'sourceUrl': url,
        'accountName': None,
        'points': 0,
        'models': {}
    }
    try:
        # account name heuristics
        h1 = await page.querySelector('h1')
        if h1:
            out['accountName'] = (await page.evaluate('(el) => el.innerText', h1)).strip()
        # points
        pts = 0
        candidates = await page.querySelectorAll('[class*="points"], [class*="reward"], .mw-css-1541sxf')
        for c in candidates:
            try:
                txt = (await page.evaluate('(el)=>el.innerText', c)).strip()
                import re
                m = re.search(r"(\d+[,.]?\d*)", txt.replace('\xa0',''))
                if m:
                    val = m.group(1).replace(',','')
                    pts = int(float(val))
                    break
            except Exception:
                continue
        out['points'] = pts
        # models
        model_nodes = await page.querySelectorAll('[data-trackid]')
        for idx, m in enumerate(model_nodes):
            try:
                trackid = await page.evaluate('(el)=>el.getAttribute("data-trackid")', m)
                title_el = await m.querySelector('h3, h2, .title')
                title = None
                if title_el:
                    title = (await page.evaluate('(el)=>el.innerText', title_el)).strip()
                txt = (await page.evaluate('(el)=>el.innerText', m))
                import re
                nums = re.findall(r"(\d+[,.]?\d*)", txt)
                key = trackid or f'idx-{idx}'
                out['models'][key] = {'id': trackid, 'title': title, 'raw_metrics_numbers': nums}
            except Exception:
                continue
    except Exception as e:
        print('parsing error', e, file=sys.stderr)

    if out_path:
        Path(out_path).write_text(json.dumps(out, indent=2), encoding='utf-8')
    await browser.close()
    return out

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('--out', '-o', help='path to save JSON output', default='result.json')
    args = parser.parse_args()
    try:
        data = asyncio.get_event_loop().run_until_complete(scrape(args.url, args.out))
        print(json.dumps({'status':'ok','models': len(data.get('models',{})), 'points': data.get('points'), 'accountName': data.get('accountName')}))
    except Exception as e:
        print('Error:', e, file=sys.stderr)
        sys.exit(1)
