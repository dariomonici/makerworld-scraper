import requests, sys, json, time
url = 'https://makerworld.com/en/@darionji'
try:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    ts = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    out_html = f'results/makerworld_profile_{ts}.html'
    open(out_html,'wb').write(r.content)
    print('Saved', out_html)
except Exception as e:
    print('ERROR', e)
    sys.exit(1)
