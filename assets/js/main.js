/* Parsik — interactions: header state, mobile menu, scroll-spy,
   reveal-on-scroll, counters, portfolio filter, contact form. */
(function () {
  'use strict';

  var header = document.getElementById('siteHeader');
  var menuToggle = document.getElementById('menuToggle');
  var mobileMenu = document.getElementById('mobileMenu');
  var navLinks = Array.prototype.slice.call(document.querySelectorAll('.nav-link'));
  var sections = ['hero', 'services', 'portfolio', 'about', 'contact']
    .map(function (id) { return document.getElementById(id); })
    .filter(Boolean);

  /* ── Header background on scroll ── */
  function syncHeader() {
    header.classList.toggle('scrolled', window.scrollY > 40);
  }
  syncHeader();
  window.addEventListener('scroll', syncHeader, { passive: true });

  /* ── Mobile menu ── */
  function closeMenu() {
    mobileMenu.classList.remove('open');
    menuToggle.classList.remove('open');
    menuToggle.setAttribute('aria-expanded', 'false');
    mobileMenu.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }
  menuToggle.addEventListener('click', function () {
    var open = mobileMenu.classList.toggle('open');
    menuToggle.classList.toggle('open', open);
    menuToggle.setAttribute('aria-expanded', String(open));
    mobileMenu.setAttribute('aria-hidden', String(!open));
    document.body.style.overflow = open ? 'hidden' : '';
  });
  mobileMenu.querySelectorAll('a').forEach(function (a) {
    a.addEventListener('click', closeMenu);
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeMenu();
  });

  /* ── Scroll-spy: active nav link ── */
  var spy = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      var id = entry.target.id;
      navLinks.forEach(function (link) {
        link.classList.toggle('is-active', link.getAttribute('href') === '#' + id);
      });
    });
  }, { rootMargin: '-45% 0px -50% 0px' });
  sections.forEach(function (s) { spy.observe(s); });

  /* ── Reveal on scroll ── */
  var reveal = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        reveal.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  document.querySelectorAll('.reveal').forEach(function (el) { reveal.observe(el); });

  /* ── Animated counters (Persian digits) ── */
  var FA_DIGITS = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
  function toFa(n) { return String(n).replace(/\d/g, function (d) { return FA_DIGITS[+d]; }); }

  var counter = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      counter.unobserve(entry.target);
      var el = entry.target;
      var target = parseInt(el.dataset.count, 10);
      var suffix = el.dataset.suffix || '';
      var t0 = null, DUR = 1600;
      function tick(ts) {
        if (!t0) t0 = ts;
        var p = Math.min((ts - t0) / DUR, 1);
        var eased = 1 - Math.pow(1 - p, 3);
        el.textContent = toFa(Math.round(target * eased)) + suffix;
        if (p < 1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    });
  }, { threshold: 0.4 });
  document.querySelectorAll('.stat-num').forEach(function (el) { counter.observe(el); });

  /* ── Portfolio filter ── */
  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip'));
  var cards = Array.prototype.slice.call(document.querySelectorAll('.work-card'));
  chips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      chips.forEach(function (c) { c.classList.remove('is-active'); });
      chip.classList.add('is-active');
      var f = chip.dataset.filter;
      cards.forEach(function (card) {
        var show = f === 'all' || card.dataset.category === f;
        card.classList.toggle('is-hidden', !show);
        if (show) {
          card.classList.remove('is-visible');
          requestAnimationFrame(function () {
            requestAnimationFrame(function () { card.classList.add('is-visible'); });
          });
        }
      });
    });
  });

  /* ── Contact form ── */
  var form = document.getElementById('contactForm');
  var statusEl = document.getElementById('formStatus');
  var submitBtn = document.getElementById('formSubmit');

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var name = form.elements.name, phone = form.elements.phone;
    [name, phone].forEach(function (f) { f.classList.remove('is-invalid'); });
    if (!name.value.trim()) { name.classList.add('is-invalid'); name.focus(); return; }
    if (!phone.value.trim()) { phone.classList.add('is-invalid'); phone.focus(); return; }

    statusEl.className = 'form-status';
    statusEl.innerHTML = '<span class="spinner"></span>در حال ارسال…';
    submitBtn.disabled = true;
    submitBtn.style.opacity = '.65';

    fetch('/api/contact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: name.value.trim(),
        phone: phone.value.trim(),
        service: form.elements.service.value,
        message: form.elements.message.value.trim()
      })
    })
      .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
      .then(function (res) {
        if (res.ok && res.data.ok) {
          statusEl.className = 'form-status ok';
          statusEl.textContent = 'درخواست شما ثبت شد؛ به‌زودی با شما تماس می‌گیریم.';
          form.reset();
        } else {
          throw new Error(res.data.error || 'خطا در ارسال');
        }
      })
      .catch(function () {
        statusEl.className = 'form-status err';
        statusEl.textContent = 'ارسال ناموفق بود؛ لطفاً دوباره تلاش کنید یا تلفنی تماس بگیرید.';
      })
      .finally(function () {
        submitBtn.disabled = false;
        submitBtn.style.opacity = '';
      });
  });
})();
