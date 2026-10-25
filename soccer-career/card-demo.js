// Growth-card demo: the game's own first hand, grade pools and payouts for a
// fresh 17-year-old striker (cards.json, written by soccer-career's
// tool/web_card_demo_test.dart). Every round starts from that same player,
// so each payout is exactly what the app would show.
(function () {
  var root = document.getElementById('demo');
  if (!root || !window.fetch) return;

  var GRADES = {
    common: { label: '일반', ink: '#CDD1DB' },
    rare: { label: '레어', ink: '#8DBAFF' },
    epic: { label: '에픽', ink: '#CEADFF' },
    unique: { label: '유니크', ink: '#FFC530' }
  };
  var ODDS = [['common', 10], ['rare', 30], ['epic', 45], ['unique', 15]];
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
    g.style.setProperty('--glyph', 'url(img/cards/' + c.family + '.webp)');
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
    var n = Math.random() * 100, g = 'unique';
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
      r.setAttribute('aria-label', rerolled[i] ? c.name + ' 다시 뽑음' : c.name + ' 다시 뽑기');
      r.title = rerolled[i] ? '다시 뽑음' : '이 카드 다시 뽑기';
      r.addEventListener('click', function () { reroll(i); });
      li.appendChild(r);
      cardsEl.appendChild(li);
    });
    confirmEl.disabled = picked < 0;
    confirmEl.textContent = picked < 0 ? '카드를 선택하세요' : '이 카드 받기';
  }

  function chip(text, cls) { return el('span', 'chip ' + (cls || ''), text); }
  function signed(n) { return (n > 0 ? '+' : '−') + Math.abs(n); }

  function payout() {
    var id = hand[picked], c = card(id), g = GRADES[c.rarity];
    payoutEl.textContent = '';
    payoutEl.style.setProperty('--ink', g.ink);
    var head = el('p', 'got', g.label + ' 카드 획득');
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
        if (l.wall1 != null && l.wall1 !== l.wall0) v.appendChild(chip('한계 ' + signed(l.wall1 - l.wall0), 'wall'));
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
        ? '보유 중. 앞으로 ' + c.seasons + '시즌 동안 적용됩니다.'
        : '보유 중. 조건을 채우는 순간 보상이 들어옵니다.'));
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
    var again = el('button', 'again', '다음 카드 뽑기');
    again.type = 'button';
    again.addEventListener('click', function () {
      root.classList.remove('paid');
      drawRound();
      cardsEl.querySelector('.pick').focus();
    });
    act.appendChild(again);
    var go = el('a', 'go', '앱에서 이어 키우기');
    go.href = storeHref();
    act.appendChild(go);
    payoutEl.appendChild(act);

    root.classList.add('paid');
    head.focus({ preventScroll: true });

    var run = function () {
      fills.forEach(function (f, i) { setTimeout(f, still ? 0 : 120 + i * 140); });
      countUp(to, c.ovr[0], c.ovr[1], still ? 0 : 120 + fills.length * 140);
    };
    still ? run() : requestAnimationFrame(function () { requestAnimationFrame(run); });
  }

  function countUp(node, from, to, delay) {
    if (still || from === to) { node.textContent = String(to); return; }
    setTimeout(function () {
      var t0 = null;
      (function step(t) {
        if (t0 == null) t0 = t;
        var k = Math.min(1, (t - t0) / 500);
        node.textContent = String(Math.round(from + (to - from) * k));
        if (k < 1) requestAnimationFrame(step);
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

  fetch('cards.json').then(function (r) { return r.json(); }).then(function (d) {
    data = d;
    deal(d.firstRarity, d.firstHand);
    root.classList.add('live');
  }).catch(function () {});
})();
