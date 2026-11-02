#!/usr/bin/env python3
"""Build plain HTML using only the standard library. Run from any directory."""
from copy import deepcopy
from html import escape
import json
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET
from datetime import date

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
TOPICS = ('goalkeeper', 'awards', 'positions', 'offline')


def available_languages():
    return [code for code in LANGUAGES if (BUILD / 'i18n' / f'{code}.json').is_file()]


def page_path(code, guide=False):
    return f'/soccer-career/{code}/' + ((guide if isinstance(guide, str) else 'guide') + '/' if guide else '')


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


MONTHS = {
    'en': 'January February March April May June July August September October November December',
    'es': 'enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre',
    'pt': 'janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro',
    'fr': 'janvier février mars avril mai juin juillet août septembre octobre novembre décembre',
    'de': 'Januar Februar März April Mai Juni Juli August September Oktober November Dezember',
    'it': 'gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre',
    'id': 'Januari Februari Maret April Mei Juni Juli Agustus September Oktober November Desember',
    'tr': 'Ocak Şubat Mart Nisan Mayıs Haziran Temmuz Ağustos Eylül Ekim Kasım Aralık',
    'ar': 'يناير فبراير مارس أبريل مايو يونيو يوليو أغسطس سبتمبر أكتوبر نوفمبر ديسمبر',
}


def format_number(value, code):
    group = '\u202f' if code == 'fr' else '.' if code in ('es', 'pt', 'de', 'it', 'id', 'tr') else ','
    decimal = ',' if code in ('es', 'pt', 'fr', 'de', 'it', 'id', 'tr') else '.'
    whole, dot, fraction = f'{value:,}'.partition('.')
    return whole.replace(',', group) + (decimal + fraction if dot else '')


def format_date(value, code):
    d = date.fromisoformat(value)
    if code == 'ko': return f'{d.year}년 {d.month}월 {d.day}일'
    if code in ('ja', 'zh'): return f'{d.year}年{d.month}月{d.day}日'
    month = MONTHS[code].split()[d.month - 1]
    if code == 'en': return f'{month} {d.day}, {d.year}'
    if code in ('es', 'pt'): return f'{d.day} de {month} de {d.year}'
    if code == 'de': return f'{d.day}. {month} {d.year}'
    return f'{d.day} {month} {d.year}'


def fill_stats(value, stats, code):
    def replace(match):
        key = match[1]
        item = stats
        for part in key.split('.'):
            item = item[part]
        return format_date(item, code) if key == 'asOf' else format_number(item, code)
    result = re.sub(r'\{stat:([^{}]+)\}', replace, value)
    if '{stat:' in result: raise ValueError(f'Invalid stat placeholder: {value}')
    return result


def topics_nav(strings, current):
    links = []
    for slug in ('guide',) + TOPICS:
        if slug == current: continue
        # All pages are one level below the language directory except the main page.
        prefix = '' if current is None else '../'
        links.append(f'<li><a href="{prefix}{slug}/">{escape(strings["topics.nav." + slug])}</a></li>')
    return '<nav class="wrap topics-nav"><h2>' + escape(strings['topics.more']) + '</h2><ul>' + ''.join(links) + '</ul></nav>'


def render_topic(code, codes, strings, slug, stats):
    text = {k: fill_stats(localize_paths(v, code), stats, code) for k, v in strings.items() if isinstance(v, str)}
    sections = []
    for n in range(1, 100):
        base = f'{slug}.s{n}.'
        if base + 'h2' not in text: break
        body = [f'<h2>{text[base + "h2"]}</h2>']
        if slug == 'positions' and n == 1:
            heads = ''.join(f'<th scope="col">{escape(text["positions.th." + k])}</th>' for k in ('pos', 'peak', 'seasons', 'age', 'record'))
            rows = []
            for pos, peak, fields in [('striker', 27, ('goals',)), ('winger', 26, ('goals', 'assists')), ('midfielder', 28, ('assists',)), ('defender', 29, ('cs',)), ('keeper', 31, ('cs',))]:
                fmt = lambda key, v: escape(text[key].replace('{0}', format_number(v, code)))
                record = ' + '.join(fmt('positions.rec.' + f, stats[pos][f]) for f in fields)
                rows.append(f'<tr><th scope="row">{escape(text["positions.pos." + pos])}</th><td>{fmt("positions.peak", peak)}</td><td>{format_number(stats[pos]["seasons"], code)}</td><td>{fmt("positions.age", stats[pos]["age"])}</td><td>{record}</td></tr>')
            body.append('<div class="table-scroll"><table class="table"><thead><tr>' + heads + '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>')
        in_list = False
        for key, value in text.items():
            if not key.startswith(base): continue
            part = key[len(base):]
            if re.fullmatch(r'li\d+', part):
                if not in_list: body.append('<ul>'); in_list = True
                body.append('<li>' + value + '</li>')
            elif re.fullmatch(r'p\d+', part):
                if in_list: body.append('</ul>'); in_list = False
                body.append('<p>' + value + '</p>')
        if in_list: body.append('</ul>')
        sections.append('<section><div class="wrap prose">' + ''.join(body) + '</div></section>')
    faqs = []
    for n in range(1, 100):
        q, a = f'{slug}.faq{n}.q', f'{slug}.faq{n}.a'
        if q not in text: break
        faqs.append((text[q], text[a]))
    url = ORIGIN + page_path(code, slug)
    plain = lambda s: re.sub(r'<[^>]*>', '', s)
    graph = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': i, 'name': name, 'item': link} for i, (name, link) in enumerate([('YT Lab', ORIGIN + '/'), (text['topics.home'], ORIGIN + page_path(code)), (text[slug + '.h1'], url)], 1)]},
        {'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': plain(q), 'acceptedAnswer': {'@type': 'Answer', 'text': plain(a)}} for q, a in faqs]},
        {'@type': 'Article', 'headline': plain(text[slug + '.h1']), 'inLanguage': LANGUAGES[code][0], 'dateModified': stats['asOf'], 'author': {'@id': ORIGIN + '/#org'}, 'publisher': {'@id': ORIGIN + '/#org'}}]}
    app, play = store_links(code)
    values = dict(lang=LANGUAGES[code][0], dir='rtl' if code == 'ar' else 'ltr', assets='../../', intro_path=page_path(code), guide_path=page_path(code, True), canonical=url, og_locale=LANGUAGES[code][2], og_image=ORIGIN + '/soccer-career/img/og-podium.jpg', og_width='1280', og_height='720', title=escape(text[slug + '.title']), desc=escape(text[slug + '.desc'], quote=True), h1=escape(text[slug + '.h1']), lede=text[slug + '.lede'], byline=text['topics.byline'], home=escape(text['topics.home']), sections=''.join(sections), faq_heading=escape(text['topics.faq']), faq=''.join('<h3>' + q + '</h3><p>' + a + '</p>' for q, a in faqs), cta=escape(text['topics.cta']), app_store=escape(app, quote=True), google_play=escape(play, quote=True), app_badge=badge(code, 'app', '../../', strings), play_badge=badge(code, 'play', '../../', strings), json_ld=script_json(graph), switcher=switcher(code, codes, slug, strings['switcher.label']), hreflang='\n'.join(f'<link rel="alternate" hreflang="{lang}" href="{link}">' for lang, link in alternates(codes, slug).items()), topics_nav=topics_nav(text, slug))
    for k, v in text.items():
        if k not in values:
            values[k] = v
    result = TOKEN.sub(lambda m: values[m[1]], (BUILD / 'topic.html').read_text())
    if '{{' in result or '{stat:' in result or '{0}' in result: raise ValueError(f'Unresolved topic placeholder: {code}/{slug}')
    return result


def render_page(code, codes, strings, guide=False):
    assets = '../../' if guide else '../'
    og = 'og-guide.jpg' if guide and code == 'ko' else 'og-podium.jpg'
    image = ORIGIN + '/soccer-career/img/' + og
    app, play = store_links(code, guide)
    values = {k: localize_paths(v, code) for k, v in strings.items() if isinstance(v, str)}
    values.update(lang=LANGUAGES[code][0], dir='rtl' if code == 'ar' else 'ltr',
                  canonical=ORIGIN + page_path(code, guide), assets=assets,
                  shots=f'{assets}img/shots/{code}/',
                  intro_path=page_path(code), guide_path=page_path(code, True),
                  privacy_path='/football-career-privacy/' + ('' if code == 'ko' else 'en/'),
                  og_locale=LANGUAGES[code][2], og_image=image,
                  og_width='1200' if og == 'og-guide.jpg' else '1280',
                  og_height='630' if og == 'og-guide.jpg' else '720',
                  app_store=escape(app, quote=True), google_play=escape(play, quote=True),
                  app_badge=badge(code, 'app', assets, strings),
                  play_badge=badge(code, 'play', assets, strings),
                  json_ld=json_ld(strings, code, guide, image),
                  topics_nav=topics_nav(strings, 'guide' if guide else None),
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
        for guide in (False, True, *TOPICS):
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
    stats = json.loads((SITE / 'data' / 'stats.json').read_text())
    for code in codes:
        strings = json.loads((BUILD / 'i18n' / f'{code}.json').read_text())
        if set(strings) != set(reference):
            raise ValueError(f'{code}: translation keys differ: {set(strings) ^ set(reference)}')
        for guide in (False, True):
            path = ROOT / page_path(code, guide).lstrip('/') / 'index.html'
            outputs[path] = render_page(code, codes, strings, guide)
        for slug in TOPICS:
            path = ROOT / page_path(code, slug).lstrip('/') / 'index.html'
            outputs[path] = render_topic(code, codes, strings, slug, stats)
    outputs[SITE / 'index.html'] = router(codes)
    outputs[SITE / 'guide/index.html'] = router(codes, True)
    outputs[ROOT / 'sitemap.xml'] = sitemap(codes)
    # Render and validate every input before touching any published file.
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
    print(f'Built {len(codes) * 6} language pages ({", ".join(codes) or "none"}), 2 routers and sitemap.xml')


if __name__ == '__main__':
    main()
