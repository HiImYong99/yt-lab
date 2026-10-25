// Growth-card demo: the game's own first hand, grade pools and payouts for a
// fresh 17-year-old striker (data/cards-<code>.json, written by soccer-career's
// tool/web_card_demo_test.dart). Every round starts from that same player,
// so each payout is exactly what the app would show.
(function () {
  var root = document.getElementById('demo');
  if (!root || !window.fetch) return;

  var strings = JSON.parse(document.getElementById('demo-strings').textContent);
  var assets = new URL(root.getAttribute('data-assets'), document.baseURI).href;
  function format(text, value) { return text.replace('{0}', value); }

  var GRADES = {
    common: { label: strings.grades.common, ink: '#CDD1DB' },
    rare: { label: strings.grades.rare, ink: '#8DBAFF' },
    epic: { label: strings.grades.epic, ink: '#CEADFF' },
    unique: { label: strings.grades.unique, ink: '#FFC530' },
    legend: { label: strings.grades.legend, ink: '#FF7A7A' }
  };
  var ODDS = [['common', 10], ['rare', 30], ['epic', 44], ['unique', 13], ['legend', 3]];
  var still = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  var data, grade, hand, rerolled, seen, picked;
  var cardsEl = root.querySelector('.demo-cards');
  var badgeEl = root.querySelector('.demo-grade');
  var confirmEl = root.querySelector('.demo-confirm');
  var payoutEl = root.querySelector('.payout');

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function card(id) { return data.cards[id]; }
  function emblem(id, big) {
    var c = card(id);
    var e = el('span', big ? 'emblem big' : 'emblem');
    e.style.setProperty('--ink', GRADES[c.rarity].ink);
    var g = el('span', 'glyph');
    g.style.setProperty('--glyph', 'url(' + assets + 'img/cards/' + c.family + '.webp)');
    e.appendChild(g);
    return e;
  }

  function deal(g, ids) {
    grade = g;
    hand = ids.slice();
    rerolled = [false, false, false];
    seen = {};
    ids.forEach(function (id) { seen[id] = true; });
    picked = -1;
    render();
  }

  function shuffle(a) {
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  // Grade by the game's odds, then three cards of different families.
  function drawRound() {
    var n = Math.random() * 100, g = 'legend';
    for (var i = 0, acc = 0; i < ODDS.length; i++) {
      acc += ODDS[i][1];
      if (n < acc) { g = ODDS[i][0]; break; }
    }
    var fam = {}, out = [];
    shuffle(data.pools[g].slice()).forEach(function (id) {
      var f = card(id).family;
      if (!fam[f] && out.length < 3) { fam[f] = true; out.push(id); }
    });
    deal(g, out);
  }

  // One free redraw per slot: same grade, no family the other two hold,
  // unseen cards first.
  function alternatives(slot) {
    var others = {};
    hand.forEach(function (id, i) { if (i !== slot) others[card(id).family] = true; });
    var pool = data.pools[grade].filter(function (id) {
      return id !== hand[slot] && !others[card(id).family];
    });
    var fresh = pool.filter(function (id) { return !seen[id]; });
    return fresh.length ? fresh : pool;
  }
  function reroll(slot) {
    var alt = alternatives(slot);
    if (rerolled[slot] || !alt.length) return;
    var id = alt[Math.floor(Math.random() * alt.length)];
    hand[slot] = id;
    seen[id] = true;
    rerolled[slot] = true;
    if (picked === slot) picked = -1;
    render(slot);
  }

  function render(changed) {
    var g = GRADES[grade];
    badgeEl.textContent = g.label;
    root.style.setProperty('--ink', g.ink);
    cardsEl.textContent = '';
    hand.forEach(function (id, i) {
      var c = card(id);
      var li = el('li', 'demo-card' + (i === picked ? ' on' : '') + (i === changed && !still ? ' swap' : ''));
      var b = el('button', 'pick');
      b.type = 'button';
      b.setAttribute('aria-pressed', i === picked ? 'true' : 'false');
      b.appendChild(emblem(id));
      var t = el('span', 'txt');
      t.appendChild(el('span', 'nm', c.name));
      t.appendChild(el('span', 'sm', c.summary));
      b.appendChild(t);
      b.addEventListener('click', function () { picked = i; render(); });
      li.appendChild(b);
      var r = el('button', 'reroll');
      r.type = 'button';
      r.disabled = rerolled[i] || !alternatives(i).length;
      r.setAttribute('aria-label', (rerolled[i] ? strings.rerolled_aria : strings.reroll_aria).replace('{name}', c.name));
      r.title = rerolled[i] ? data.ui['gc.rerolled'] : data.ui['gc.reroll'];
      r.addEventListener('click', function () { reroll(i); });
      li.appendChild(r);
      cardsEl.appendChild(li);
    });
    confirmEl.disabled = picked < 0;
    confirmEl.textContent = picked < 0 ? data.ui['gc.select'] : strings.confirm;
  }

  function chip(text, cls) { return el('span', 'chip ' + (cls || ''), text); }
  function signed(n) { return (n > 0 ? '+' : '−') + Math.abs(n); }

  function payout() {
    var id = hand[picked], c = card(id), g = GRADES[c.rarity];
    payoutEl.textContent = '';
    payoutEl.style.setProperty('--ink', g.ink);
    payoutEl.classList.toggle('legend', c.rarity === 'legend');
    var head = el('p', 'got', format(data.ui['gc.reward.got'], g.label));
    head.tabIndex = -1;
    payoutEl.appendChild(head);
    payoutEl.appendChild(emblem(id, true));
    payoutEl.appendChild(el('h3', 'nm', c.name));
    payoutEl.appendChild(el('p', 'sm', c.summary));

    var fills = [];
    if (c.lines.length) {
      var ul = el('ul', 'lines');
      c.lines.forEach(function (l) {
        var li = el('li');
        var top = el('div', 'row');
        top.appendChild(el('span', 'lb', l.label));
        var v = el('span', 'v');
        v.appendChild(el('span', 'from', String(l.from)));
        v.appendChild(el('span', 'arrow', '→'));
        v.appendChild(el('span', 'to', String(l.to)));
        if (l.to !== l.from) v.appendChild(chip(signed(l.to - l.from), l.to < l.from ? 'down' : ''));
        if (l.wall1 != null && l.wall1 !== l.wall0) v.appendChild(chip(format(data.ui['gc.reward.ceil'], l.wall1 - l.wall0), 'wall'));
        top.appendChild(v);
        li.appendChild(top);
        var track = el('div', 'track');
        var base = el('span', 'base');
        var fill = el('span', 'fill');
        var lo = Math.min(l.from, l.to);
        base.style.width = (lo / l.scale * 100) + '%';
        fill.style.left = (lo / l.scale * 100) + '%';
        fill.style.width = '0%';
        track.appendChild(base);
        track.appendChild(fill);
        if (l.to < l.from) fill.classList.add('down');
        var tick = null;
        if (l.wall0 != null) {
          tick = el('span', 'wallmark');
          tick.style.left = (l.wall0 / l.scale * 100) + '%';
          track.appendChild(tick);
        }
        li.appendChild(track);
        ul.appendChild(li);
        fills.push(function () {
          fill.style.width = (Math.abs(l.to - l.from) / l.scale * 100) + '%';
          if (tick) tick.style.left = (l.wall1 / l.scale * 100) + '%';
        });
      });
      payoutEl.appendChild(ul);
    } else {
      payoutEl.appendChild(el('p', 'held', c.seasons
        ? format(strings.held_seasons, c.seasons)
        : strings.held_condition));
    }

    var o = el('div', 'ovr' + (c.ovr[1] > c.ovr[0] ? ' up' : ''));
    o.appendChild(el('span', 'lb', 'OVR'));
    var ov = el('span', 'v');
    ov.appendChild(el('span', 'from', String(c.ovr[0])));
    ov.appendChild(el('span', 'arrow', '→'));
    var to = el('span', 'to', String(c.ovr[0]));
    ov.appendChild(to);
    if (c.ovr[1] !== c.ovr[0]) ov.appendChild(chip(signed(c.ovr[1] - c.ovr[0])));
    o.appendChild(ov);
    payoutEl.appendChild(o);

    var act = el('div', 'acts');
    var again = el('button', 'again', strings.next);
    again.type = 'button';
    again.addEventListener('click', function () {
      root.classList.remove('paid');
      drawRound();
      cardsEl.querySelector('.pick').focus();
    });
    act.appendChild(again);
    var go = el('a', 'go', strings.continue);
    go.href = storeHref();
    act.appendChild(go);
    payoutEl.appendChild(act);

    root.classList.add('paid');
    head.focus({ preventScroll: true });

    var run = function () {
      fills.forEach(function (f, i) { setTimeout(f, still ? 0 : 120 + i * 140); });
      countUp(to, c.ovr[0], c.ovr[1], still ? 0 : 120 + fills.length * 140, function () {
        if (c.ovr[1] >= 99) o.classList.add('max');
      });
    };
    still ? run() : requestAnimationFrame(function () { requestAnimationFrame(run); });
  }

  function countUp(node, from, to, delay, done) {
    if (still || from === to) { node.textContent = String(to); if (done) done(); return; }
    setTimeout(function () {
      var t0 = null;
      (function step(t) {
        if (t0 == null) t0 = t;
        var k = Math.min(1, (t - t0) / 500);
        node.textContent = String(Math.round(from + (to - from) * k));
        if (k < 1) requestAnimationFrame(step);
        else if (done) done();
      })(performance.now());
    }, delay);
  }

  function storeHref() {
    var c = document.documentElement.classList;
    if (c.contains('is-android')) return document.querySelector('[data-store="android"]').href;
    if (c.contains('is-ios')) return document.querySelector('[data-store="ios"]').href;
    return '#get';
  }

  confirmEl.addEventListener('click', function () { if (picked >= 0) payout(); });

  fetch(root.getAttribute('data-cards-url')).then(function (r) { return r.json(); }).then(function (d) {
    data = d;
    Object.keys(GRADES).forEach(function (key) {
      GRADES[key].label = d.ui['gc.' + key] || strings.grades[key];
    });
    deal(d.firstRarity, d.firstHand);
    root.classList.add('live');
  }).catch(function () {});
})();
