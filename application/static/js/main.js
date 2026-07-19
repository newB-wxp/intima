/**
 * Intima - Main JavaScript
 * Age Gate, Mobile Menu, Cart Interactions, Lazy Loading
 */

(function () {
  'use strict';

  /* ===== Age Gate ===== */
  var AGE_GATE_KEY = 'intima_age_verified';
  var AGE_GATE_EXPIRY_MS = 24 * 60 * 60 * 1000;

  function initAgeGate() {
    var gate = document.getElementById('age-gate');
    if (!gate) return;

    var stored = localStorage.getItem(AGE_GATE_KEY);
    if (stored) {
      try {
        var data = JSON.parse(stored);
        if (Date.now() - data.timestamp < AGE_GATE_EXPIRY_MS) {
          gate.classList.add('hidden');
          return;
        }
      } catch (e) {}
    }

    var yesBtn = gate.querySelector('.age-gate-yes');
    var noBtn = gate.querySelector('.age-gate-no');

    if (yesBtn) {
      yesBtn.addEventListener('click', function () {
        localStorage.setItem(AGE_GATE_KEY, JSON.stringify({ timestamp: Date.now() }));
        gate.classList.add('hidden');
      });
    }

    if (noBtn) {
      noBtn.addEventListener('click', function () {
        window.location.href = 'https://www.google.com';
      });
    }
  }

  /* ===== Mobile Menu ===== */
  function initMobileMenu() {
    var hamburger = document.getElementById('hamburger');
    var menu = document.getElementById('mobile-menu');
    var overlay = document.getElementById('mobile-overlay');
    if (!hamburger || !menu) return;

    function openMenu() {
      hamburger.classList.add('active');
      hamburger.setAttribute('aria-expanded', 'true');
      menu.classList.add('open');
      if (overlay) overlay.classList.add('open');
      document.body.style.overflow = 'hidden';
    }

    function closeMenu() {
      hamburger.classList.remove('active');
      hamburger.setAttribute('aria-expanded', 'false');
      menu.classList.remove('open');
      if (overlay) overlay.classList.remove('open');
      document.body.style.overflow = '';
    }

    hamburger.addEventListener('click', function () {
      menu.classList.contains('open') ? closeMenu() : openMenu();
    });

    if (overlay) overlay.addEventListener('click', closeMenu);

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && menu.classList.contains('open')) closeMenu();
    });
  }

  /* ===== Filter Sidebar Toggle ===== */
  function initFilterToggle() {
    var toggleBtn = document.getElementById('filter-toggle');
    var closeBtn = document.getElementById('filter-close');
    var sidebar = document.getElementById('filter-sidebar');
    if (!toggleBtn || !sidebar) return;

    toggleBtn.addEventListener('click', function () {
      sidebar.classList.add('open');
      if (closeBtn) closeBtn.style.display = 'flex';
      document.body.style.overflow = 'hidden';
    });

    if (closeBtn) {
      closeBtn.addEventListener('click', function () {
        sidebar.classList.remove('open');
        closeBtn.style.display = 'none';
        document.body.style.overflow = '';
      });
    }

    sidebar.addEventListener('click', function (e) {
      if (e.target === sidebar) {
        sidebar.classList.remove('open');
        if (closeBtn) closeBtn.style.display = 'none';
        document.body.style.overflow = '';
      }
    });
  }

  /* ===== Quantity +/- ===== */
  function initQuantitySelectors() {
    document.addEventListener('click', function (e) {
      var minusBtn = e.target.closest('.quantity-minus');
      var plusBtn = e.target.closest('.quantity-plus');
      if (!minusBtn && !plusBtn) return;

      var container = (minusBtn || plusBtn).closest('.quantity-selector');
      if (!container) return;
      var input = container.querySelector('.quantity-input');
      if (!input) return;

      var current = parseInt(input.value, 10) || 1;
      var min = parseInt(input.min, 10) || 1;
      var max = parseInt(input.max, 10) || 99;

      input.value = minusBtn ? Math.max(min, current - 1) : Math.min(max, current + 1);
      input.dispatchEvent(new Event('change', { bubbles: true }));
    });
  }

  /* ===== AJAX Add to Cart ===== */
  function initAddToCart() {
    document.addEventListener('click', function (e) {
      var btn = e.target.closest('.add-to-cart-btn');
      if (!btn) return;

      e.preventDefault();
      var productId = btn.getAttribute('data-product-id');
      var detailInfo = btn.closest('.product-detail-info');
      var quantity = 1;

      if (detailInfo) {
        var qtyInput = detailInfo.querySelector('.quantity-input');
        if (qtyInput) quantity = parseInt(qtyInput.value, 10) || 1;
      }

      var originalText = btn.textContent;
      btn.disabled = true;
      btn.textContent = 'Adding...';

      var csrfMeta = document.querySelector('meta[name="csrf-token"]');
      var headers = { 'Content-Type': 'application/json' };
      if (csrfMeta && csrfMeta.content) headers['X-CSRFToken'] = csrfMeta.content;

      fetch('/api/cart/add', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({ product_id: productId, quantity: quantity })
      })
        .then(function (resp) {
          if (!resp.ok) throw new Error();
          return resp.json();
        })
        .then(function (data) {
          btn.textContent = 'Added!';
          btn.style.backgroundColor = '#059669';
          btn.style.borderColor = '#059669';
          if (data.cart_count !== undefined) updateCartBadge(data.cart_count);
          setTimeout(function () {
            btn.disabled = false;
            btn.textContent = originalText;
            btn.style.backgroundColor = '';
            btn.style.borderColor = '';
          }, 1500);
        })
        .catch(function () {
          btn.textContent = 'Error - try again';
          btn.style.backgroundColor = '#DC2626';
          btn.style.borderColor = '#DC2626';
          setTimeout(function () {
            btn.disabled = false;
            btn.textContent = originalText;
            btn.style.backgroundColor = '';
            btn.style.borderColor = '';
          }, 2000);
        });
    });
  }

  function updateCartBadge(count) {
    var badge = document.querySelector('.cart-badge');
    if (!badge) {
      var cartIcon = document.querySelector('a[href*="cart"] .nav-icon');
      if (cartIcon && count > 0) {
        var span = document.createElement('span');
        span.className = 'cart-badge';
        span.textContent = count > 99 ? '99+' : count;
        cartIcon.appendChild(span);
      }
      return;
    }
    if (count <= 0) { badge.remove(); return; }
    badge.textContent = count > 99 ? '99+' : count;
  }

  /* ===== Flash Message Dismiss ===== */
  function initFlashMessages() {
    document.addEventListener('click', function (e) {
      var closeBtn = e.target.closest('.flash-close');
      if (!closeBtn) return;
      var msg = closeBtn.closest('.flash-message');
      if (msg) {
        msg.style.opacity = '0';
        msg.style.transition = 'opacity 0.3s ease';
        setTimeout(function () { msg.remove(); }, 300);
      }
    });
  }

  /* ===== Password Strength ===== */
  function initPasswordStrength() {
    var pw = document.getElementById('password');
    var fill = document.getElementById('password-strength-fill');
    var text = document.getElementById('password-strength-text');
    if (!pw || !fill || !text) return;

    pw.addEventListener('input', function () {
      var val = pw.value;
      var score = 0;
      if (val.length >= 8) score++;
      if (val.length >= 12) score++;
      if (/[A-Z]/.test(val)) score++;
      if (/[a-z]/.test(val)) score++;
      if (/[0-9]/.test(val)) score++;
      if (/[^A-Za-z0-9]/.test(val)) score++;

      var levels = [
        { w: '0%', c: '', t: '' },
        { w: '20%', c: '#DC2626', t: 'Very Weak' },
        { w: '40%', c: '#D97706', t: 'Weak' },
        { w: '60%', c: '#D97706', t: 'Fair' },
        { w: '80%', c: '#059669', t: 'Strong' },
        { w: '100%', c: '#059669', t: 'Very Strong' },
        { w: '100%', c: '#059669', t: 'Very Strong' }
      ];
      var l = levels[Math.min(score, 6)];
      fill.style.width = l.w;
      fill.style.backgroundColor = l.c;
      text.textContent = l.t;
    });
  }

  /* ===== Sort Redirect ===== */
  function initSortSelect() {
    var sel = document.getElementById('sort-select');
    if (!sel) return;
    sel.addEventListener('change', function () {
      var url = new URL(window.location.href);
      url.searchParams.set('sort', sel.value);
      url.searchParams.delete('page');
      window.location.href = url.toString();
    });
  }

  /* ===== Price Filter Apply ===== */
  function initPriceFilter() {
    var btn = document.getElementById('apply-price');
    if (!btn) return;
    btn.addEventListener('click', function () {
      var min = document.getElementById('price-min');
      var max = document.getElementById('price-max');
      var url = new URL(window.location.href);
      if (min && min.value) url.searchParams.set('min_price', min.value);
      else url.searchParams.delete('min_price');
      if (max && max.value) url.searchParams.set('max_price', max.value);
      else url.searchParams.delete('max_price');
      url.searchParams.delete('page');
      window.location.href = url.toString();
    });
  }

  /* ===== Filters Apply ===== */
  function initFiltersApply() {
    var btn = document.getElementById('apply-filters');
    if (!btn) return;
    btn.addEventListener('click', function () {
      var url = new URL(window.location.href);
      url.searchParams.delete('page');

      var materials = [];
      document.querySelectorAll('input[name="material"]:checked').forEach(function (cb) {
        materials.push(cb.value);
      });
      if (materials.length) url.searchParams.set('material', materials.join(','));
      else url.searchParams.delete('material');

      var rating = document.querySelector('input[name="rating"]:checked');
      if (rating) url.searchParams.set('rating', rating.value);
      else url.searchParams.delete('rating');

      window.location.href = url.toString();
    });
  }

  /* ===== Lazy Loading ===== */
  function initLazyLoading() {
    if (!('IntersectionObserver' in window)) {
      document.querySelectorAll('img[data-src]').forEach(function (img) {
        img.src = img.getAttribute('data-src');
        img.removeAttribute('data-src');
        img.classList.add('loaded');
      });
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          var img = entry.target;
          img.src = img.getAttribute('data-src');
          img.removeAttribute('data-src');
          img.classList.add('loaded');
          observer.unobserve(img);
        }
      });
    }, { rootMargin: '200px 0px' });

    document.querySelectorAll('img[data-src]').forEach(function (img) {
      observer.observe(img);
    });
  }

  /* ===== Init ===== */
  function init() {
    initAgeGate();
    initMobileMenu();
    initFilterToggle();
    initQuantitySelectors();
    initAddToCart();
    initFlashMessages();
    initPasswordStrength();
    initSortSelect();
    initPriceFilter();
    initFiltersApply();
    initLazyLoading();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
