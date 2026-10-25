#!/usr/bin/env python3
"""Build plain HTML using only the standard library. Run from any directory."""
from copy import deepcopy
from html import escape
import json
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET

BUILD = Path(__file__).resolve().parent
SITE = BUILD.parent
ROOT = SITE.parent
ORIGIN = 'https://ytlab.site'
# code: HTML lang, hreflang, OG locale, endonym (lib/l10n/strings.dart)
LANGUAGES = {
    'ko': ('ko', 'ko', 'ko_KR', '한국어'),
    'en': ('en', 'en', 'en_US', 'English'),
    'ja': ('ja', 'ja', 'ja_JP', '日本語'),
    'zh': ('zh-Hans', 'zh-Hans', 'zh_CN', '简体中文'),
    'es': ('es', 'es', 'es_ES', 'Español'),
    'pt': ('pt-BR', 'pt', 'pt_BR', 'Português'),
    'fr': ('fr', 'fr', 'fr_FR', 'Français'),
    'de': ('de', 'de', 'de_DE', 'Deutsch'),
    'it': ('it', 'it', 'it_IT', 'Italiano'),
    'id': ('id', 'id', 'id_ID', 'Indonesia'),
    'tr': ('tr', 'tr', 'tr_TR', 'Türkçe'),
    'ar': ('ar', 'ar', 'ar_AR', 'العربية'),
}
INK = {'common': '#CDD1DB', 'rare': '#8DBAFF', 'epic': '#CEADFF', 'unique': '#FFC530', 'legend': '#FF7A7A'}
TOKEN = re.compile(r'{{\s*([\w.]+)\s*}}')
SM = 'http://www.sitemaps.org/schemas/sitemap/0.9'
XHTML = 'http://www.w3.org/1999/xhtml'


def available_languages():
    return [code for code in LANGUAGES if (BUILD / 'i18n' / f'{code}.json').is_file()]


def page_path(code, guide=False):
    return f'/soccer-career/{code}/' + ('guide/' if guide else '')


def alternates(codes, guide=False):
    links = {LANGUAGES[c][1]: ORIGIN + page_path(c, guide) for c in codes}
    # An absent English translation must never leave a dangling x-default.
    if 'en' in codes:
        links['x-default'] = ORIGIN + page_path('en', guide)
    return links


def script_json(value):
    return json.dumps(value, ensure_ascii=False, indent=2).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')


def store_links(code, guide=False):
    app = 'https://apps.apple.com/' + ('kr/' if code == 'ko' else '') + 'app/id6807107830'
    hl = {'zh': 'zh-CN', 'pt': 'pt-BR'}.get(code, code)
    campaign = 'guide' if guide else 'soccer-career'
    play = ('https://play.google.com/store/apps/details?id=site.ytlab.soccer_career'
            f'&hl={hl}&referrer=utm_source%3Dytlab.site%26utm_medium%3Dweb%26utm_campaign%3D{campaign}-{code}')
    return app, play


def badge_dimensions(path):
    if path.suffix == '.svg':
        box = ET.parse(path).getroot().attrib['viewBox']
        _, _, width, height = map(float, re.split(r'[\s,]+', box.strip()))
    else:
        data = path.read_bytes()
        if data[:8] != b'\x89PNG\r\n\x1a\n':
            raise ValueError(f'Not a PNG: {path}')
        width, height = struct.unpack('>II', data[16:24])
    return width, height


def badge(code, kind, assets, strings):
    file = f'img/badges/{"appstore" if kind == "app" else "gp"}-{code}.{ "svg" if kind == "app" else "png"}'
    width, height = badge_dimensions(SITE / file)
    # Integer HTML dimensions reserve space; CSS uses the exact intrinsic ratio.
    return (f'<img src="{assets}{file}" alt="{escape(strings[f"store.{kind}_alt"], quote=True)}" '
            f'width="{round(width * 52 / height)}" height="52">')


def switcher(code, codes, guide, label):
    links = []
    for other in codes:
        current = ' aria-current="true"' if code == other else ''
        links.append(f'<a href="{page_path(other, guide)}" lang="{LANGUAGES[other][0]}" '
                     f'dir="auto" data-lang="{other}"{current}>{LANGUAGES[other][3]}</a>')
    return (f'<nav class="wrap languages" aria-label="{escape(label, quote=True)}">' + '\n'.join(links) + '</nav>\n'
            '<script>document.querySelectorAll(".languages [data-lang]").forEach(function (a) {\n'
            '  a.addEventListener("click", function () { try { localStorage.setItem("sc-lang", a.dataset.lang); } catch (e) {} });\n'
            '});</script>')


def initial_hand(data, strings, assets):
    cards = []
    for ident in data['firstHand']:
        card = data['cards'][ident]
        ink = INK[card['rarity']]
        aria = strings['demo.reroll_aria'].replace('{name}', card['name'])
        cards.append(
            '<li class="demo-card"><button class="pick" type="button" aria-pressed="false">'
            f'<span class="emblem" style="--ink:{ink}"><span class="glyph" '
            f'style="--glyph:url(/soccer-career/img/cards/{card["family"]}.webp)"></span></span>'
            f'<span class="txt"><span class="nm">{escape(card["name"])}</span>'
            f'<span class="sm">{escape(card["summary"])}</span></span></button>'
            f'<button class="reroll" type="button" aria-label="{escape(aria, quote=True)}" '
            f'title="{escape(data["ui"]["gc.reroll"], quote=True)}"></button></li>')
    return '\n              '.join(cards)


def localize_paths(value, code):
    """Rich translations may contain links; localize these as well as templates."""
    return (value.replace('/soccer-career/guide/', page_path(code, True))
            .replace('/soccer-career/#', page_path(code) + '#')
            .replace('href="/soccer-career/"', f'href="{page_path(code)}"')
            .replace('href="/football-career-privacy/"',
                     'href="/football-career-privacy/' + ('' if code == 'ko' else 'en/') + '"'))


def json_ld(strings, code, guide, image):
    schema = deepcopy(strings['schema.guide' if guide else 'schema.page'])
    app, play = store_links(code, guide)
    def visit(value):
        if isinstance(value, dict):
            result = {key: visit(item) for key, item in value.items()}
            if 'inLanguage' in result:
                result['inLanguage'] = LANGUAGES[code][0]
            return result
        if isinstance(value, list):
            return [visit(item) for item in value]
        if isinstance(value, str):
            if value == ORIGIN + '/soccer-career/guide/': return ORIGIN + page_path(code, True)
            if value == ORIGIN + '/soccer-career/': return ORIGIN + page_path(code)
            if value == ORIGIN + '/soccer-career/#app': return ORIGIN + page_path(code) + '#app'
            if value.startswith(ORIGIN + '/soccer-career/img/og-'): return image
            if value.startswith('https://apps.apple.com/'): return app
            if value.startswith('https://play.google.com/'): return play
        return value
    return script_json(visit(schema))


def render_page(code, codes, strings, guide=False):
    assets = '../../' if guide else '../'
    og = 'og-guide.jpg' if guide and code == 'ko' else 'og-podium.jpg'
    image = ORIGIN + '/soccer-career/img/' + og
    app, play = store_links(code, guide)
    values = {k: localize_paths(v, code) for k, v in strings.items() if isinstance(v, str)}
    values.update(lang=LANGUAGES[code][0], dir='rtl' if code == 'ar' else 'ltr',
                  canonical=ORIGIN + page_path(code, guide), assets=assets,
                  intro_path=page_path(code), guide_path=page_path(code, True),
                  privacy_path='/football-career-privacy/' + ('' if code == 'ko' else 'en/'),
                  og_locale=LANGUAGES[code][2], og_image=image,
                  og_width='1200' if og == 'og-guide.jpg' else '1280',
                  og_height='630' if og == 'og-guide.jpg' else '720',
                  app_store=escape(app, quote=True), google_play=escape(play, quote=True),
                  app_badge=badge(code, 'app', assets, strings),
                  play_badge=badge(code, 'play', assets, strings),
                  json_ld=json_ld(strings, code, guide, image),
                  switcher=switcher(code, codes, guide, strings['switcher.label']),
                  hreflang='\n'.join(f'<link rel="alternate" hreflang="{lang}" href="{url}">'
                                     for lang, url in alternates(codes, guide).items()))
    if not guide:
        data = json.loads((SITE / 'data' / f'cards-{code}.json').read_text())
        player = data['player']
        player_text = strings['demo.player']
        for key in ('age', 'position', 'ovr'):
            player_text = player_text.replace('{' + key + '}', escape(str(player[key])))
        values.update(cards_url=f'{assets}data/cards-{code}.json',
                      initial_hand=initial_hand(data, strings, assets),
                      demo_choose=escape(data['ui']['gc.choose']), demo_one=escape(data['ui']['gc.one']),
                      demo_select=escape(data['ui']['gc.select']),
                      demo_grade=escape(data['ui']['gc.' + data['firstRarity']]), demo_player=player_text,
                      demo_strings=script_json({k.removeprefix('demo.'): v for k, v in strings.items() if k.startswith('demo.')}))
    template = (BUILD / ('guide.html' if guide else 'page.html')).read_text()
    def substitute(match):
        value = values[match[1]]
        # A shared string can appear in both a heading and a meta attribute.
        prefix = template[:match.start()]
        if match[1] in strings and prefix.rfind('<') > prefix.rfind('>'):
            return escape(value, quote=True)
        return value
    result = TOKEN.sub(substitute, template)
    # The H1's second line is a block span; a space keeps the heading's text
    # from running together for crawlers ("…키우기카드").
    result = re.sub(r'(?<=\S)<span class="second">', ' <span class="second">', result)
    if '{{' in result or '}}' in result:
        raise ValueError(f'Unresolved placeholder in {code}, guide={guide}')
    return result


def router(codes, guide=False):
    links = '\n'.join(f'<li><a href="{page_path(code, guide)}" lang="{LANGUAGES[code][0]}" dir="auto">'
                      f'{LANGUAGES[code][3]}</a></li>' for code in codes)
    suffix = 'guide/' if guide else ''
    # Only available translations are valid targets, even for saved preferences.
    return '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, follow">
<title>YT Lab</title>
</head>
<body>
<ul>''' + links + '''</ul>
<script>
(function () {
  var available = ''' + json.dumps(codes) + ''';
  if (!available.length) return;
  var language;
  try { language = localStorage.getItem('sc-lang'); } catch (e) {}
  if (available.indexOf(language) < 0) {
    language = (navigator.languages || [navigator.language || '']).map(function (locale) {
      return locale.toLowerCase().split('-')[0];
    }).find(function (code) { return available.indexOf(code) >= 0; });
  }
  if (!language) language = available.indexOf('en') >= 0 ? 'en' : available[0];
  location.replace('/soccer-career/' + language + '/''' + suffix + "' + location.search + location.hash);" + '''
})();
</script>
</body>
</html>
'''


def sitemap(codes):
    ET.register_namespace('', SM)
    ET.register_namespace('xhtml', XHTML)
    path = ROOT / 'sitemap.xml'
    root = ET.parse(path).getroot()
    for entry in list(root):
        loc = entry.find(f'{{{SM}}}loc')
        if loc is not None and (loc.text or '').startswith(ORIGIN + '/soccer-career/'):
            root.remove(entry)
    for code in codes:
        for guide in (False, True):
            entry = ET.SubElement(root, f'{{{SM}}}url')
            ET.SubElement(entry, f'{{{SM}}}loc').text = ORIGIN + page_path(code, guide)
            for lang, url in alternates(codes, guide).items():
                ET.SubElement(entry, f'{{{XHTML}}}link', rel='alternate', hreflang=lang, href=url)
    ET.indent(root, space='  ')
    return ET.tostring(root, encoding='unicode', xml_declaration=True) + '\n'


def main():
    codes = available_languages()
    reference = json.loads((BUILD / 'i18n' / f'{codes[0]}.json').read_text()) if codes else {}
    outputs = {}
    for code in codes:
        strings = json.loads((BUILD / 'i18n' / f'{code}.json').read_text())
        if set(strings) != set(reference):
            raise ValueError(f'{code}: translation keys differ: {set(strings) ^ set(reference)}')
        for guide in (False, True):
            path = ROOT / page_path(code, guide).lstrip('/') / 'index.html'
            outputs[path] = render_page(code, codes, strings, guide)
    outputs[SITE / 'index.html'] = router(codes)
    outputs[SITE / 'guide/index.html'] = router(codes, True)
    outputs[ROOT / 'sitemap.xml'] = sitemap(codes)
    # Render and validate every input before touching any published file.
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
    print(f'Built {len(codes) * 2} language pages ({", ".join(codes) or "none"}), 2 routers and sitemap.xml')


if __name__ == '__main__':
    main()
