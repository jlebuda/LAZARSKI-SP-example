/* Studio Piegus — skrypty strony. Bez zależności. */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var cfg = window.PIEGUS || {};
  window.dataLayer = window.dataLayer || [];
  function track(name, extra) {
    var o = { event: name };
    for (var k in extra) { o[k] = extra[k]; }
    window.dataLayer.push(o);
  }

  /* Menu mobilne */
  var toggle = $('.nav-toggle'), nav = $('#nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  /* UTM — zapamiętujemy źródło wejścia na czas wizyty, żeby trafiło do zapytania */
  var utmKeys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'gclid', 'fbclid'];
  try {
    var qs = new URLSearchParams(location.search);
    utmKeys.forEach(function (k) {
      var v = qs.get(k);
      if (v) { sessionStorage.setItem('pg_' + k, v); }
    });
  } catch (e) { /* brak storage — trudno */ }
  function utmData() {
    var out = {};
    try {
      utmKeys.forEach(function (k) {
        var v = sessionStorage.getItem('pg_' + k);
        if (v) { out[k] = v; }
      });
    } catch (e) {}
    return out;
  }

  /* Pomiar kliknięć w telefon i e-mail */
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href^="tel:"], a[href^="mailto:"]');
    if (!a) { return; }
    track(a.href.indexOf('tel:') === 0 ? 'click_phone' : 'click_email', { page: location.pathname });
  });

  /* Grafik: filtry dni i grup */
  $$('[data-tt]').forEach(function (box) {
    var rows = $$('.tt-row', box), empty = $('.tt-empty', box);
    var state = { day: 'all', group: 'all' };
    function apply() {
      var shown = 0;
      rows.forEach(function (r) {
        var ok = (state.day === 'all' || r.dataset.day === state.day) &&
                 (state.group === 'all' || r.dataset.group === state.group);
        r.hidden = !ok;
        if (ok) { shown++; }
      });
      if (empty) { empty.hidden = shown !== 0; }
    }
    $$('[data-filter]', box).forEach(function (btn) {
      btn.addEventListener('click', function () {
        var kind = btn.dataset.filter;
        $$('[data-filter="' + kind + '"]', box).forEach(function (b) { b.setAttribute('aria-pressed', 'false'); });
        btn.setAttribute('aria-pressed', 'true');
        state[kind] = btn.dataset.value;
        apply();
      });
    });
    apply();
  });

  /* Przycisk „Zapisz się" w wierszu grafiku wybiera grupę w formularzu */
  $$('[data-pick]').forEach(function (a) {
    a.addEventListener('click', function () {
      var sel = $('select[name="grupa"]');
      if (!sel) { return; }
      for (var i = 0; i < sel.options.length; i++) {
        if (sel.options[i].value === a.dataset.pick) { sel.selectedIndex = i; break; }
      }
    });
  });

  /* Wolne terminy: kliknięcie dodaje datę do pola z terminami */
  $$('[data-date]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var input = $('input[name="terminy"]');
      if (!input) { return; }
      var list = input.value ? input.value.split(/\s*;\s*/).filter(Boolean) : [];
      var d = btn.dataset.date, i = list.indexOf(d);
      if (i === -1) { list.push(d); btn.setAttribute('aria-pressed', 'true'); }
      else { list.splice(i, 1); btn.setAttribute('aria-pressed', 'false'); }
      input.value = list.join('; ');
    });
  });

  /* Formularze: wysyłka na endpoint albo gotowy e-mail */
  $$('form[data-form]').forEach(function (f) {
    utmKeys.forEach(function (k) { /* pola ukryte nie są potrzebne — UTM dołączamy przy wysyłce */ });
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      if (f.elements.website && f.elements.website.value) { return; }
      var status = $('.form-status', f);
      var data = {}, lines = [];
      $$('input, select, textarea', f).forEach(function (el) {
        if (!el.name || el.name === 'website' || el.type === 'submit') { return; }
        var v = (el.value || '').trim();
        if (!v) { return; }
        data[el.name] = v;
        var lab = el.closest('.field') && $('label', el.closest('.field'));
        lines.push(((lab ? lab.firstChild.textContent : el.name).trim()) + ': ' + v);
      });
      var utm = utmData();
      for (var k in utm) { data[k] = utm[k]; }
      data.formularz = f.dataset.form;
      data.strona = location.pathname;
      data.jezyk = document.documentElement.lang;
      track('form_submit', { form: f.dataset.form, page: location.pathname });

      if (cfg.endpoint) {
        status.className = 'form-status'; status.textContent = '…';
        fetch(cfg.endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }, body: JSON.stringify(data) })
          .then(function (r) { if (!r.ok) { throw new Error('bad'); } f.reset(); status.className = 'form-status ok'; status.textContent = f.dataset.ok; })
          .catch(function () { status.className = 'form-status err'; status.textContent = f.dataset.err; });
      } else if (cfg.email) {
        var body = lines.join('\n');
        location.href = 'mailto:' + cfg.email + '?subject=' + encodeURIComponent(f.dataset.subject) + '&body=' + encodeURIComponent(body);
        status.className = 'form-status ok'; status.textContent = f.dataset.mail;
      } else {
        status.className = 'form-status err'; status.textContent = f.dataset.err;
      }
    });
  });
})();
