/**
 * Intima Wellness — Main JavaScript
 * All vanilla JS, no frameworks.
 */
(function () {
  'use strict';

  /* ======================================================================
     Age Gate
     ====================================================================== */
  function initAgeGate() {
    if (localStorage.getItem('age_verified') === 'true') {
      var el = document.getElementById('age-gate');
      if (el) el.remove();
      return;
    }

    var gate = document.getElementById('age-gate');
    if (!gate) return;

    var btnYes = gate.querySelector('.age-gate__yes');
    var btnNo = gate.querySelector('.age-gate__no');

    if (btnYes) {
      btnYes.addEventListener('click', function () {
        var expires = new Date();
        expires.setHours(expires.getHours() + 24);
        localStorage.setItem('age_verified', 'true');
        localStorage.setItem('age_verified_expires', expires.toISOString());
        gate.style.display = 'none';
        document.body.classList.remove('age-gate--active');
      });
    }

    if (btnNo) {
      btnNo.addEventListener('click', function () {
        window.location.href = 'https://www.google.com';
      });
    }
  }

  /* ======================================================================
     Hamburger Menu
     ====================================================================== */
  function initHamburger() {
    var btn = document.querySelector('.header__hamburger');
    var menu = document.querySelector('.mobile-menu');
    if (!btn || !menu) return;

    btn.addEventListener('click', function () {
      document.body.classList.toggle('nav-open');
    });

    // Close on link click
    var links = menu.querySelectorAll('a');
    links.forEach(function (link) {
      link.addEventListener('click', function () {
        document.body.classList.remove('nav-open');
      });
    });
  }

  /* ======================================================================
     Cart Quantity +/-
     ====================================================================== */
  function initCartQuantity() {
    document.addEventListener('click', function (e) {
      var btn = e.target.closest('.cart__qty-btn');
      if (!btn) return;

      var container = btn.closest('.cart__qty');
      if (!container) return;

      var input = container.querySelector('.cart__qty-input');
      if (!input) return;

      var val = parseInt(input.value, 10) || 1;
      var isPlus = btn.classList.contains('cart__qty-btn--plus');

      if (isPlus) {
        val = Math.min(val + 1, 99);
      } else {
        val = Math.max(val - 1, 1);
      }

      input.value = val;
      input.dispatchEvent(new Event('change', { bubbles: true }));
    });
  }

  /* ======================================================================
     AJAX Add to Cart
     ====================================================================== */
  function initAddToCart() {
    document.addEventListener('click', function (e) {
      var btn = e.target.closest('.add-to-cart');
      if (!btn) return;

      e.preventDefault();

      var productId = btn.getAttribute('data-product-id');
      var quantityEl = document.querySelector('.product-detail__qty-input');
      var quantity = quantityEl ? parseInt(quantityEl.value, 10) || 1 : 1;

      btn.disabled = true;
      btn.textContent = 'Adding...';

      fetch('/api/cart/add', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
          product_id: productId,
          quantity: quantity
        })
      })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          if (data.success) {
            updateCartBadge(data.cart_count);
            showToast(data.message || 'Added to cart', 'success');
          } else {
            showToast(data.message || 'Failed to add item', 'error');
          }
        })
        .catch(function () {
          showToast('Something went wrong. Please try again.', 'error');
        })
        .finally(function () {
          btn.disabled = false;
          btn.textContent = btn.getAttribute('data-original-text') || 'Add to Cart';
        });
    });
  }

  function updateCartBadge(count) {
    var badge = document.querySelector('.header__badge');
    if (!badge) return;
    badge.textContent = count || 0;
    if (count > 0) {
      badge.style.display = 'flex';
    } else {
      badge.style.display = 'none';
    }
  }

  /* ======================================================================
     Toast Notification
     ====================================================================== */
  function showToast(message, type) {
    type = type || 'info';

    var container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    var toast = document.createElement('div');
    toast.className = 'toast toast--' + type;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(function () {
      toast.classList.add('toast--hide');
      toast.addEventListener('animationend', function () {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      });
    }, 3000);
  }

  // Expose globally for inline usage
  window.showToast = showToast;

  /* ======================================================================
     Lazy Loading (Intersection Observer)
     ====================================================================== */
  function initLazyLoad() {
    if (!('IntersectionObserver' in window)) {
      // Fallback: load all immediately
      var imgs = document.querySelectorAll('img[data-src]');
      imgs.forEach(function (img) {
        img.src = img.getAttribute('data-src');
        img.removeAttribute('data-src');
        img.classList.add('lazy-loaded');
      });
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var img = entry.target;
        img.src = img.getAttribute('data-src');
        img.removeAttribute('data-src');
        img.classList.add('lazy-loaded');
        observer.unobserve(img);
      });
    }, {
      rootMargin: '200px 0px',
      threshold: 0.01
    });

    var imgs = document.querySelectorAll('img[data-src]');
    imgs.forEach(function (img) { observer.observe(img); });
  }

  /* ======================================================================
     Flash Message Auto-Dismiss
     ====================================================================== */
  function initFlashAutoDismiss() {
    var msgs = document.querySelectorAll('.flash-message');
    msgs.forEach(function (msg) {
      setTimeout(function () {
        msg.style.opacity = '0';
        msg.style.transform = 'translateX(100%)';
        msg.style.transition = 'all 0.3s ease';
        setTimeout(function () {
          if (msg.parentNode) msg.parentNode.removeChild(msg);
        }, 300);
      }, 5000);
    });

    // Close button
    document.addEventListener('click', function (e) {
      var closeBtn = e.target.closest('.flash-message__close');
      if (!closeBtn) return;
      var msg = closeBtn.closest('.flash-message');
      if (msg) msg.remove();
    });
  }

  /* ======================================================================
     Init
     ====================================================================== */
  document.addEventListener('DOMContentLoaded', function () {
    initAgeGate();
    initHamburger();
    initCartQuantity();
    initAddToCart();
    initLazyLoad();
    initFlashAutoDismiss();
  });
})();
