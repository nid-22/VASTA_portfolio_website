(() => {
  'use strict';
  if (!navigator.sendBeacon) return;
  document.querySelectorAll('[data-track-nav]').forEach(link => {
    link.addEventListener('click', () => {
      const body = new URLSearchParams({ label: link.dataset.trackNav });
      navigator.sendBeacon('/analytics/navigation/', body);
    });
  });
})();
