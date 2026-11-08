#!/usr/bin/env python3
"""Rebuild img/fonts/ytlab-sans-ko.woff2 from the glyphs on the Korean main page.

Pretendard is OFL with a Reserved Font Name, so the subset carries another name.

Run after changing Korean main-page copy or re-exporting cards-ko.json. Needs
fonttools + brotli and network access. build.py itself stays standard-library.
Writes font-glyphs.txt so check.py can catch copy the font does not cover.
"""
import json, subprocess, tempfile, urllib.request
from pathlib import Path
from fontTools.ttLib import TTFont

BUILD = Path(__file__).resolve().parent
SITE = BUILD.parent
FAMILY = 'YT Lab Sans KO'
URL = 'https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/packages/pretendard/dist/web/variable/woff2/PretendardVariable.woff2'

strings = json.loads((BUILD / 'i18n/ko.json').read_text())
page = ''.join(v for k, v in strings.items() if isinstance(v, str) and k.startswith(('page.', 'demo.', 'shared.', 'topics.nav.', 'topics.more', 'switcher.')))
cards = (SITE / 'data/cards-ko.json').read_text()
latin = ''.join(chr(c) for c in range(0x20, 0x7f)) + '·…–—−→’‘“”×%+'
glyphs = ''.join(sorted(set(page + json.dumps(json.loads(cards), ensure_ascii=False) + latin) - set('\n\r\t')))
(BUILD / 'font-glyphs.txt').write_text(glyphs, encoding='utf-8')
out = SITE / 'img/fonts/ytlab-sans-ko.woff2'
out.parent.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory() as tmp:
    source = Path(tmp) / 'PretendardVariable.woff2'
    urllib.request.urlretrieve(URL, source)
    subprocess.run(['pyftsubset', str(source), '--text-file=' + str(BUILD / 'font-glyphs.txt'),
                    '--flavor=woff2', '--layout-features=*', '--output-file=' + str(out)], check=True)
font = TTFont(out)
names = font['name']
names.names = [n for n in names.names if n.nameID in (0, 13, 14)]
for ident, value in ((1, FAMILY), (2, 'Regular'), (3, FAMILY), (4, FAMILY), (6, FAMILY.replace(' ', ''))):
    names.setName(value, ident, 3, 1, 0x409)
font.flavor = 'woff2'
font.save(out)
print(f'{len(glyphs)} glyphs, {out.stat().st_size // 1024} KB')
