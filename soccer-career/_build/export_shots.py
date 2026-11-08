#!/usr/bin/env python3
"""Publish an approved store screenshot set on the landing pages.

Usage: export_shots.py <set-dir> <soccer-career>/tool/shots/clean
<set-dir> is tool/aso/store-shots.json's folder. Needs Pillow. Replaces every
image in img/shots/<code>/ and rewrites data/shots.json; then run build.py.
"""
import json, sys
from pathlib import Path
from PIL import Image

SITE = Path(__file__).resolve().parent.parent
WIDTHS = ((600, ''), (300, '-300'))
SEPARATOR = {'ko': ' ', 'ja': ' ', 'zh': ' ', 'zh-hant': ' ', 'ar': '، '}

folder, copy_dir = Path(sys.argv[1]) / 'iphone-69', Path(sys.argv[2])
codes = sorted({path.name.split('_')[0] for path in folder.glob('*_*.png')})
shots = {}
for code in codes:
    copy = json.loads((copy_dir / ('copy.json' if code == 'ko' else f'copy.{code}.json')).read_text())
    output = SITE / 'img/shots' / code
    output.mkdir(parents=True, exist_ok=True)
    for old in output.glob('*.webp'):
        old.unlink()
    shots[code] = []
    for number, item in enumerate(copy['shots'], 1):
        stem = f'{number:02}{item["name"]}'
        image = Image.open(folder / f'{code}_{stem}.png').convert('RGB')
        for width, suffix in WIDTHS:
            scaled = image.resize((width, round(image.height * width / image.width)), Image.LANCZOS)
            scaled.save(output / f'{stem}{suffix}.webp', format='WEBP', quality=82, method=6)
        shots[code].append({'file': stem, 'alt': item['label'] + ': ' + SEPARATOR.get(code, ', ').join(item['lines'])})
(SITE / 'data/shots.json').write_text(json.dumps(shots, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(f'{len(codes)} languages, {sum(map(len, shots.values()))} screenshots')
