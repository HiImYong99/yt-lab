// Optional real-browser smoke check. Build/check.py themselves need only Python.
// Run against python3 -m http.server; PLAYWRIGHT_MODULE may point to an existing installation.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const base = process.env.SITE_URL || 'http://127.0.0.1:8765';
(async () => {
  const browser = await chromium.launch({headless: true});
  try {
    const errors = [];
    const context = await browser.newContext({reducedMotion: 'reduce'});
    const page = await context.newPage();
    page.on('pageerror', error => errors.push(error.message));
    page.on('response', response => {
      if (response.url().startsWith(base) && response.status() >= 400) errors.push(`${response.status()} ${response.url()}`);
    });
    for (const code of ['ko', 'en']) {
      const data = JSON.parse(fs.readFileSync(path.join(root, 'data', `cards-${code}.json`)));
      const strings = JSON.parse(fs.readFileSync(path.join(__dirname, 'i18n', `${code}.json`)));
      for (const width of [390, 1280]) {
        await page.setViewportSize({width, height: 900});
        await page.goto(`${base}/soccer-career/${code}/`, {waitUntil: 'networkidle'});
        await page.locator('#demo.live').waitFor();
        assert.equal(await page.locator('.demo-card .nm').allTextContents().then(v => v.join('|')), data.firstHand.map(id => data.cards[id].name).join('|'));
        assert.equal(await page.locator('.demo-confirm').isDisabled(), true);
        const layout = await page.evaluate(() => ({width: innerWidth, scroll: document.documentElement.scrollWidth}));
        assert.ok(layout.scroll <= layout.width, `${code}/${width}: page overflow ${JSON.stringify(layout)}`);
        if (width === 390 && process.env.QA_SCREENSHOTS) {
          await page.screenshot({path: path.join(__dirname, `qa-${code}.png`), fullPage: false});
        }
        await page.locator('.pick').nth(0).click();
        assert.equal(await page.locator('.demo-confirm').textContent(), strings['demo.confirm']);
        await page.locator('.demo-confirm').click();
        await page.locator('#demo.paid').waitFor();
        assert.equal(await page.locator('.payout .got').textContent(), data.ui['gc.reward.got'].replace('{0}', data.ui['gc.epic']));
        assert.equal(await page.locator('.ovr .to').textContent(), String(data.cards[data.firstHand[0]].ovr[1]));
        assert.equal(await page.locator('.acts .go').getAttribute('href'), '#get');
        await page.locator('.again').click();
        assert.equal(await page.locator('.demo-card').count(), 3);
        const rarity = await page.locator('.demo-grade').textContent();
        const oldName = await page.locator('.demo-card .nm').nth(0).textContent();
        await page.locator('.reroll').nth(0).click();
        assert.equal(await page.locator('.reroll').nth(0).isDisabled(), true);
        assert.notEqual(await page.locator('.demo-card .nm').nth(0).textContent(), oldName);
        assert.equal(await page.locator('.demo-grade').textContent(), rarity);
        // Initial held card, then the same payout under RTL: bars must remain LTR.
        await page.reload({waitUntil: 'networkidle'});
        await page.locator('#demo.live').waitFor();
        await page.locator('.pick').nth(1).click();
        await page.locator('.demo-confirm').click();
        assert.equal(await page.locator('.held').textContent(), strings['demo.held_seasons'].replace('{0}', data.cards[data.firstHand[1]].seasons));
        await page.reload({waitUntil: 'networkidle'});
        await page.locator('#demo.live').waitFor();
        await page.evaluate(() => { document.documentElement.dir = 'rtl'; });
        const rtl = await page.locator('.reroll').first().evaluate(el => getComputedStyle(el).left);
        assert.equal(rtl, '12px');
        await page.locator('.pick').first().click();
        await page.locator('.demo-confirm').click();
        assert.equal(await page.locator('.track').first().evaluate(el => getComputedStyle(el).direction), 'ltr');
        await page.goto(`${base}/soccer-career/${code}/guide/`, {waitUntil: 'networkidle'});
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `guide ${code}/${width}: overflow`);
        assert.equal(await page.locator('a[href$="#demo"]').getAttribute('href'), `/soccer-career/${code}/#demo`);
      }
    }
    // Switcher stays on the same kind of page and stores the preference.
    await page.goto(`${base}/soccer-career/ko/guide/`, {waitUntil: 'networkidle'});
    await page.locator('.languages [data-lang="en"]').click();
    await page.waitForURL('**/soccer-career/en/guide/');
    assert.equal(await page.evaluate(() => localStorage.getItem('sc-lang')), 'en');
    await page.goto(`${base}/soccer-career/guide/?source=test#cards`);
    await page.waitForURL('**/soccer-career/en/guide/?source=test#cards');
    // Browser language order and inaccessible storage, without page navigation races.
    const router = fs.readFileSync(path.join(root, 'index.html'), 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
    const vm = require('node:vm');
    for (const [stored, languages, expected, blocked] of [
      ['ko', ['en-US'], 'ko', false], [null, ['fr-FR', 'ko-KR', 'en'], 'ko', false],
      [null, ['fr-FR'], 'en', false], ['missing', ['en-US'], 'en', false],
      [null, ['ko-KR'], 'ko', true]
    ]) {
      let target;
      vm.runInNewContext(router, {localStorage: {getItem() { if (blocked) throw Error('blocked'); return stored; }}, navigator: {languages}, location: {search: '?a=1', hash: '#demo', replace(url) { target = url; }}});
      assert.equal(target, `/soccer-career/${expected}/?a=1#demo`);
    }
    // No JavaScript still exposes all three cards and both language links.
    const plain = await browser.newContext({javaScriptEnabled: false});
    const staticPage = await plain.newPage();
    await staticPage.goto(`${base}/soccer-career/en/`);
    assert.equal(await staticPage.locator('.demo-card').count(), 3);
    await staticPage.goto(`${base}/soccer-career/`);
    assert.equal(await staticPage.locator('a').count(), 2);
    await plain.close();
    assert.deepEqual(errors, []);
    console.log('PASS: ko/en desktop/mobile, demo picks/rerolls/payouts/held cards, RTL bars, guide links, switcher, router and no-JS fallback');
    await context.close();
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
