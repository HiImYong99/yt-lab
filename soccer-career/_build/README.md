# Soccer Career static pages

Run from the repository root (Python 3.9+, standard library only):

```sh
python3 soccer-career/_build/build.py
python3 soccer-career/_build/check.py
```

`page.html` and `guide.html` preserve the original page structure. Edit copy in
`i18n/<code>.json`, then rebuild. Keys are shared between locales; values can
include inline HTML. Preserve links, classes, placeholders such as `{0}`, and
all factual numbers. `schema.page` and `schema.guide` contain localized JSON-LD;
the builder supplies canonical URLs, store URLs, images and `inLanguage`.
Do not edit generated language pages or the two root routers directly.

To add a language, provide its complete translation JSON with the same keys,
`data/cards-<code>.json`, and both localized badges. All thirteen language codes,
endonyms and metadata mappings are already configured. The build never falls
back to Korean copy for a missing translation. It fails on incomplete inputs
before writing output. Missing translation files are omitted from routers,
hreflang, sitemap and switchers. With no English file, `x-default` is omitted
and the router's last fallback is the first available language; with no
translations, routers display an empty list without redirecting. Old files
are not deleted, including previously generated languages no longer enabled.

The initial cards and picker/reward terms come from the app's localized data.
Page-only demo strings live under `demo.*`. The existing shorter reroll note
remains page copy (rather than the longer `gc.next`) to preserve Korean text.
Inline card mask URLs are site-root-relative: CSS custom-property URLs may
resolve against the stylesheet rather than the HTML document. Other shared
assets use paths relative to each generated page. The original Korean game
screenshots are retained in both languages. Non-Korean privacy links use the
existing English privacy page.

`legacy/` is the untouched Korean source captured before routing was added.
`check.py` compares both Korean pages against it, excluding only the new
language switcher and non-visible script/style contents, and normalizing
whitespace. It also checks every local HTML/CSS resource reference, JSON-LD,
canonical/hreflang reciprocity, sitemap, badges and partial-language builds.
The thirteen-locale smoke checks use an in-memory copy fixture for infrastructure
validation; they do not write or claim completed translations.

Optional browser check (requires an existing Playwright installation and a
local HTTP server serving the repository root):

```sh
SITE_URL=http://127.0.0.1:8765 node soccer-career/_build/browser-check.cjs
```

Set `PLAYWRIGHT_MODULE` to the module's path if it is not on Node's module
search path. This checks ko/en mobile and desktop layouts, actual demo
interaction, RTL payout bars, navigation, routers and JavaScript-free fallback.
The build and standard checker do not require Node or Playwright.

## Topic pages (programmatic SEO)

`topic.html` renders `/<code>/{goalkeeper,awards,positions,offline}/` from the
`topics.*` and `<slug>.*` keys. Numbers come from `data/stats.json`
(`{stat:keeper.seasons}` placeholders), a snapshot of finished careers in the
live ranking database. Refresh it now and then, rebuild, push, then ping
search engines:

```sh
python3 soccer-career/_build/stats.py ~/Desktop/soccer-career/server
python3 soccer-career/_build/build.py && python3 soccer-career/_build/check.py
python3 soccer-career/_build/indexnow.py   # IndexNow + Naver, after the push is live
```

## Browser trial (`/soccer-career/play/`)

A Flutter web build of the app with `WEB_TRIAL=true` (first five seasons,
no purchases/ads/server, store buttons at the end). Rebuild from any app
checkout that contains `lib/web_trial.dart`, then rebuild the pages:

```sh
soccer-career/_build/play.sh ~/worktrees/soccer-career/<lane>
python3 soccer-career/_build/build.py && python3 soccer-career/_build/check.py
```

## Traditional Chinese

`zh` is Simplified Chinese (`zh-Hans`); `zh-hant` serves Taiwan, Hong Kong and
Macau (`zh-Hant`, with `zh-TW` and `zh-HK` hreflang aliases). To update it after
editing Simplified Chinese copy or data:

```sh
python3 -m pip install opencc-python-reimplemented
python3 soccer-career/_build/hant.py
python3 soccer-career/_build/build.py && python3 soccer-career/_build/check.py
```

`hant.py` converts JSON values with OpenCC `s2twp`, then applies the ordered
terminology fixes in `FIXES`. It regenerates `i18n/zh-hant.json` and every
`data/*-zh.json` counterpart, and adds the three Traditional intro FAQs.
Do not hand-edit these generated inputs. Intro FAQ JSON-LD uses the same copy
as the visible FAQ; other locale names are supplied by the builder.

Optional screenshot refresh (requires Pillow):

```sh
python3 -m pip install Pillow
python3 soccer-career/_build/hant.py --screenshots
```

This queries Apple with `country=tw&lang=zh_tw`. Only a complete Traditional
screenshot set is saved to `img/shots/zh-hant/`; empty or English fallback
results use the existing `img/shots/zh/` set. The regular build is offline and
uses the available local set. Traditional store badges come from Apple's
`https://tools.applemediaservices.com/api/badges/download-on-the-app-store/black/zh-tw?size=250x83` and Google Play's
`zh-tw_badge_web_generic.png` official badge assets.
