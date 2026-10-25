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
`data/cards-<code>.json`, and both localized badges. All twelve language codes,
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
The twelve-locale smoke checks use an in-memory copy fixture for infrastructure
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
