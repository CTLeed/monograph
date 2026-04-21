/* Monograph — progressive enhancements. No third-party code. */
(function () {
  'use strict';

  // Reveal on scroll
  var els = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && els.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-in');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    els.forEach(function (el) { io.observe(el); });
  } else {
    els.forEach(function (el) { el.classList.add('is-in'); });
  }

  // Footer year
  var y = document.querySelectorAll('[data-year]');
  var now = String(new Date().getFullYear());
  y.forEach(function (node) { node.textContent = now; });
})();
