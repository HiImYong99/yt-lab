#!/usr/bin/env python3
"""Tell IndexNow (Bing, Yandex, Seznam...) and Naver about the soccer-career URLs in sitemap.xml.

    python3 soccer-career/_build/indexnow.py            # every /soccer-career/ URL
    python3 soccer-career/_build/indexnow.py goalkeeper # only URLs containing "goalkeeper"
"""
import json, pathlib, re, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
KEY = '9fbef194c38ca2c3883228c7249a113d'
ENDPOINTS = ['https://api.indexnow.org/indexnow', 'https://searchadvisor.naver.com/indexnow']

def main(filters):
    urls = re.findall(r'<loc>(https://ytlab\.site/soccer-career/[^<]+)</loc>', (ROOT / 'sitemap.xml').read_text())
    urls = [u for u in urls if not filters or any(f in u for f in filters)]
    body = json.dumps({'host': 'ytlab.site', 'key': KEY,
                       'keyLocation': f'https://ytlab.site/{KEY}.txt', 'urlList': urls}).encode()
    for ep in ENDPOINTS:
        req = urllib.request.Request(ep, body, {'Content-Type': 'application/json; charset=utf-8'})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                print(ep, r.status, len(urls), 'urls')
        except urllib.error.HTTPError as e:
            print(ep, e.code, e.read()[:200])

if __name__ == '__main__':
    main(sys.argv[1:])
