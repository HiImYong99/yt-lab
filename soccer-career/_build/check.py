#!/usr/bin/env python3
"""Validate generated HTML, local resources, SEO and preserved Korean copy.

The only body-text exclusion is the newly required language switcher. Script
and style contents are not visible text. Both legacy Korean pages are checked.
"""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
import build
from build import (BUILD, SITE, ROOT, ORIGIN, LANGUAGES, SM, XHTML,
                   alternates, available_languages, badge_dimensions, page_path,
                   store_links)

URL = re.compile(r'''url\(\s*(?:"([^"]*)"|'([^']*)'|([^)]*?))\s*\)''', re.I)


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.text = []
        self.refs = []
        self.ids = set()
        self.links = []
        self.metas = {}
        self.scripts = []
        self.script = None
        self.images = []
        self.html = {}
        self.demo = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        hidden = (tag in ('script', 'style') or
                  'languages' in attrs.get('class', '').split() or
                  (bool(self.stack) and self.stack[-1][1]))
        if tag not in ('area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'):
            self.stack.append((tag, hidden))
        if tag == 'html': self.html = attrs
        if tag == 'meta': self.metas[attrs.get('name', attrs.get('property'))] = attrs.get('content')
        if tag == 'link' or tag == 'a': self.links.append((tag, attrs))
        if tag == 'img': self.images.append(attrs)
        if 'id' in attrs: self.ids.add(attrs['id'])
        if attrs.get('id') == 'demo': self.demo = attrs
        for key in ('href', 'src', 'data-cards-url'):
            if key in attrs: self.refs.append(attrs[key])
        if 'style' in attrs:
            self.refs.extend(css_urls(attrs['style']))
        if tag == 'script':
            self.script = [attrs, '']

    def handle_endtag(self, tag):
        if tag == 'script' and self.script is not None:
            self.scripts.append(self.script)
            self.script = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                self.stack = self.stack[:i]
                break

    def handle_data(self, data):
        if self.script is not None:
            self.script[1] += data
        if not self.stack or not self.stack[-1][1]:
            self.text.append(data)

    def visible_text(self):
        return ' '.join(''.join(self.text).split())


def css_urls(text):
    return [next(value for value in match.groups() if value is not None).strip() for match in URL.finditer(text)]


def assert_local(reference, source):
    url = urlsplit(reference)
    if url.scheme not in ('', 'http', 'https') or (url.netloc and url.netloc != urlsplit(ORIGIN).netloc):
        return
    target = (ROOT / unquote(url.path).lstrip('/') if url.path.startswith('/')
              else source.parent / unquote(url.path) if url.path else source)
    target = target.resolve()
    assert target.is_relative_to(ROOT), f'Outside site: {source}: {reference}'
    if target.is_dir(): target /= 'index.html'
    assert target.is_file(), f'Missing local resource: {source.relative_to(ROOT)} -> {reference}'
    if url.fragment and target.suffix == '.html':
        # JSON-LD @id values are not links and intentionally are not collected.
        ids = Page(target.read_text()).ids
        assert unquote(url.fragment) in ids, f'Missing fragment: {reference} in {source}'


def no_placeholders(text, source):
    assert '{{' not in text and '}}' not in text, f'Leftover placeholder in {source}'


def check_subsets():
    """Exercise locale wiring without publishing untranslated fixture pages."""
    codes = available_languages()
    fixture = json.loads((BUILD / 'i18n' / f'{codes[0]}.json').read_text()) if codes else None
    subsets = [[], ['ko'], ['en'], ['ar'], ['zh', 'pt'], list(LANGUAGES)]
    for subset in subsets:
        # Discovery depends only on files present, never on ko/en being mandatory.
        with tempfile.TemporaryDirectory(dir=BUILD) as temp:
            folder = Path(temp)
            (folder / 'i18n').mkdir()
            for code in subset:
                (folder / 'i18n' / f'{code}.json').write_text('{}')
            original = build.BUILD
            try:
                build.BUILD = folder
                assert available_languages() == subset
            finally:
                build.BUILD = original
        for guide in (False, True):
            expected = alternates(subset, guide)
            assert ('x-default' in expected) == ('en' in subset)
            router = Page(build.router(subset, guide))
            assert [a['href'] for tag, a in router.links] == [page_path(c, guide) for c in subset]
            tree = ET.fromstring(build.sitemap(subset))
            actual = {e.find(f'{{{SM}}}loc').text for e in tree}
            assert {url for url in actual if url.startswith(ORIGIN + '/soccer-career/')} == {
                ORIGIN + page_path(c, g) for c in subset for g in (False, True)}
            if fixture:
                for code in subset:
                    text = build.render_page(code, subset, fixture, guide)
                    no_placeholders(text, code)
                    page = Page(text)
                    assert page.html['lang'] == LANGUAGES[code][0]
                    assert page.html['dir'] == ('rtl' if code == 'ar' else 'ltr')
                    assert {a['hreflang']: a['href'] for tag, a in page.links if a.get('rel') == 'alternate'} == expected
                    assert [a['data-lang'] for tag, a in page.links if 'data-lang' in a] == subset
                    for attrs, body in page.scripts:
                        if attrs.get('type') in ('application/json', 'application/ld+json'):
                            json.loads(body)


def main():
    codes = available_languages()
    documents = {}
    for code in codes:
        for guide in (False, True):
            path = ROOT / page_path(code, guide).lstrip('/') / 'index.html'
            text = path.read_text()
            no_placeholders(text, path)
            page = Page(text)
            documents[path] = page
            assert page.html['lang'] == LANGUAGES[code][0]
            assert page.html['dir'] == ('rtl' if code == 'ar' else 'ltr')
            canonical = [a['href'] for tag, a in page.links if a.get('rel') == 'canonical']
            assert canonical == [ORIGIN + page_path(code, guide)]
            found = [(a['hreflang'], a['href']) for tag, a in page.links if a.get('rel') == 'alternate']
            assert len(found) == len(dict(found)), f'Duplicate hreflang: {path}'
            assert dict(found) == alternates(codes, guide), f'Incomplete hreflang: {path}'
            switch = [a for tag, a in page.links if 'data-lang' in a]
            assert [a['data-lang'] for a in switch] == codes
            assert [a['href'] for a in switch] == [page_path(c, guide) for c in codes]
            assert page.metas['og:locale'] == LANGUAGES[code][2]
            assert page.metas['apple-itunes-app'] == 'app-id=6807107830'
            assert page.metas['og:url'] == canonical[0]
            image = 'og-guide.jpg' if code == 'ko' and guide else 'og-podium.jpg'
            assert page.metas['og:image'] == ORIGIN + '/soccer-career/img/' + image
            assert page.metas['twitter:image'] == page.metas['og:image']
            expected_size = ('1200', '630') if image == 'og-guide.jpg' else ('1280', '720')
            assert (page.metas['og:image:width'], page.metas['og:image:height']) == expected_size
            assert_local(page.metas['og:image'], path)
            schemas = [json.loads(body) for attrs, body in page.scripts if attrs.get('type') == 'application/ld+json']
            assert len(schemas) == 1, f'Missing JSON-LD in {path}'
            entities = schemas[0]['@graph']
            assert any(e.get('inLanguage') == LANGUAGES[code][0] for e in entities)
            assert all(e.get('inLanguage', LANGUAGES[code][0]) == LANGUAGES[code][0] for e in entities)
            for tag, a in page.links:
                href = a.get('href', '')
                if href.startswith('https://apps.apple.com/'):
                    assert href == store_links(code, guide)[0]
                if href.startswith('https://play.google.com/'):
                    assert href == store_links(code, guide)[1]
                if href.startswith('/soccer-career/') and 'data-lang' not in a:
                    assert href.startswith(page_path(code)), f'Cross-language internal link: {href}'
            for img in page.images:
                if '/badges/' in img['src']:
                    assert img['height'] == '52'
                    w, h = badge_dimensions((path.parent / img['src']).resolve())
                    assert int(img['width']) == round(w * 52 / h)
            if not guide:
                data = json.loads((SITE / 'data' / f'cards-{code}.json').read_text())
                assert page.demo['data-cards-url'] == f'../data/cards-{code}.json'
                assert_local(page.demo['data-cards-url'], path)
                assert len(re.findall(r'class="demo-card"', text)) == 3
                visible = page.visible_text()
                for ident in data['firstHand']:
                    card = data['cards'][ident]
                    assert card['name'] in visible and card['summary'] in visible
                for key in ('gc.choose', 'gc.one', 'gc.select', 'gc.' + data['firstRarity']):
                    assert data['ui'][key] in visible
                payload = [json.loads(body) for attrs, body in page.scripts if attrs.get('id') == 'demo-strings']
                assert len(payload) == 1 and payload[0]['confirm']
                for card in data['cards'].values():
                    assert_local('../img/cards/' + card['family'] + '.webp', path)
            if code == 'en':
                assert not re.search('[가-힣]', page.visible_text()), f'Untranslated Korean in {path}'
                assert 'Football Career Sim: Be a Pro' in text
            if code == 'ko':
                legacy = BUILD / 'legacy' / ('guide/index.html' if guide else 'index.html')
                before = Page(legacy.read_text()).visible_text()
                after = page.visible_text()
                if before != after:
                    at = next((i for i, pair in enumerate(zip(before, after)) if pair[0] != pair[1]), min(len(before), len(after)))
                    raise AssertionError(f'Korean copy changed at {at}: {before[at:at+100]!r} != {after[at:at+100]!r}')
    # Every hreflang target has the same complete set, including self references.
    for path, page in documents.items():
        links = {a['hreflang']: a['href'] for tag, a in page.links if a.get('rel') == 'alternate'}
        for url in links.values():
            target = ROOT / urlsplit(url).path.lstrip('/') / 'index.html'
            reciprocal = {a['hreflang']: a['href'] for tag, a in documents[target].links if a.get('rel') == 'alternate'}
            assert reciprocal == links, f'Nonreciprocal hreflang: {path} -> {url}'
    for guide in (False, True):
        path = SITE / ('guide/index.html' if guide else 'index.html')
        text = path.read_text()
        no_placeholders(text, path)
        page = Page(text)
        documents[path] = page
        assert page.metas['robots'] == 'noindex, follow'
        assert [a['href'] for tag, a in page.links if tag == 'a'] == [page_path(c, guide) for c in codes]
        assert 'location.search + location.hash' in text and 'try {' in text
    count = 0
    for path, page in documents.items():
        for reference in page.refs:
            assert_local(reference, path)
            count += 1
    for css in SITE.glob('*.css'):
        text = css.read_text()
        no_placeholders(text, css)
        for reference in css_urls(text):
            assert_local(reference, css)
            count += 1
    sitemap = ET.parse(ROOT / 'sitemap.xml').getroot()
    entries = {e.find(f'{{{SM}}}loc').text: e for e in sitemap}
    assert ORIGIN + '/' in entries
    expected = {ORIGIN + page_path(c, g) for c in codes for g in (False, True)}
    assert {url for url in entries if url.startswith(ORIGIN + '/soccer-career/')} == expected
    for code in codes:
        for guide in (False, True):
            entry = entries[ORIGIN + page_path(code, guide)]
            links = entry.findall(f'{{{XHTML}}}link')
            assert len(links) == len(alternates(codes, guide))
            assert {a.attrib['hreflang']: a.attrib['href'] for a in links} == alternates(codes, guide)
    check_subsets()
    print(f'PASS: {len(codes)*2} language pages, 2 routers, {count} resource references, JSON-LD, reciprocal hreflang, sitemap, badges, Korean legacy copy and partial-language/12-locale configurations')


if __name__ == '__main__':
    main()
