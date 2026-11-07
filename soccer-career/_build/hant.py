#!/usr/bin/env python3
"""Regenerate Traditional Chinese copy; optionally refresh Apple screenshots."""
import argparse
from io import BytesIO
import json
from pathlib import Path
import re
from urllib.request import urlopen

BUILD = Path(__file__).resolve().parent
SITE = BUILD.parent
FIXES = (('傢俱樂部', '家俱樂部'), ('擴充套件', '擴充'), ('型別', '類型'),
         ('資料', '數據'), ('合同', '合約'), ('程式碼', '代碼'), ('賬號', '帳號'), ('繫結', '綁定'),
         # Taiwan quotes with corner brackets and calls an app an App.
         ('“', '「'), ('”', '」'), ('‘', '『'), ('’', '』'),
         ('應用內購買', 'App 內購買'), ('與應用一致', '與 App 一致'))
FAQS = (
    ('《綠茵人生》是什麼遊戲？', '《綠茵人生》是一款足球員養成模擬遊戲。從17歲的青訓球員開始，透過成長卡、比賽、轉會與續約，培養球員直到退役。'),
    ('台灣、香港可以下載嗎？', '可以。台灣、香港玩家都可以在 App Store 和 Google Play 免費下載，遊戲內含可選購的商品。'),
    ('可以離線玩嗎？', '可以離線推進球員生涯，包括賽季、成長卡與轉會。排行榜、購買、錢包及更換裝置需要網路連線。'),
)


def convert(value, cc):
    # Convert values only: machine keys, URLs and placeholders stay intact.
    if isinstance(value, dict):
        return {key: convert(item, cc) for key, item in value.items()}
    if isinstance(value, list):
        return [convert(item, cc) for item in value]
    if isinstance(value, str):
        value = cc.convert(value)
        for before, after in FIXES:
            value = value.replace(before, after)
    return value


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def refresh_screenshots():
    """Ignore Apple's English fallback when no Traditional localization exists."""
    lookup = 'https://itunes.apple.com/lookup?id=6807107830&country=tw&lang=zh_tw'
    with urlopen(lookup, timeout=30) as response:
        results = json.load(response).get('results', [])
    urls = results[0].get('screenshotUrls', []) if results else []
    names = ('01retired', '02hall', '03titles', '04home', '05ovr99', '06owner', '07archive')
    localized = {name: next((url for url in urls if re.search(
        r'/(?:zh_tw|zh-TW|zh_hant|zh-Hant)_' + name + r'\.', url)), None) for name in names}
    if not all(localized.values()):
        print('Apple returned no complete Traditional screenshot set; using img/shots/zh/.')
        return
    from PIL import Image
    outputs = {}
    for name, url in localized.items():
        url = re.sub(r'/\d+x\d+bb\.(?:jpg|png)$', '/600x0w.webp', url)
        with urlopen(url, timeout=30) as response:
            image = Image.open(BytesIO(response.read())).convert('RGB')
        for width, suffix in ((600, ''), (300, '-300')):
            scaled = image.resize((width, round(image.height * width / image.width)))
            output = BytesIO()
            scaled.save(output, format='WEBP', quality=85)
            outputs[name + suffix + '.webp'] = output.getvalue()
    folder = SITE / 'img/shots/zh-hant'
    folder.mkdir(parents=True, exist_ok=True)
    for name, data in outputs.items():
        (folder / name).write_bytes(data)
    print('Refreshed Traditional screenshots.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--screenshots', action='store_true', help='also look up Taiwan screenshots (requires Pillow)')
    args = parser.parse_args()
    from opencc import OpenCC
    cc = OpenCC('s2twp')
    strings = convert(json.loads((BUILD / 'i18n/zh.json').read_text()), cc)
    strings['schema.page']['@graph'].append({'@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in FAQS]})
    write_json(BUILD / 'i18n/zh-hant.json', strings)
    for source in sorted((SITE / 'data').glob('*-zh.json')):
        write_json(source.with_name(source.name.replace('-zh.json', '-zh-hant.json')),
                   convert(json.loads(source.read_text()), cc))
    if args.screenshots:
        refresh_screenshots()
    print('Regenerated zh-hant copy and data from zh (s2twp + ordered terminology fixes).')


if __name__ == '__main__':
    main()
