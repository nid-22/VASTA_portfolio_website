(() => {
  'use strict';
  const CONFIG = { mobileInitial: 4, mobileBatch: 4, interval: 7000 };
  const hero = document.querySelector('.hero');
  const slidesRoot = document.querySelector('#carousel-slides');
  if (hero && slidesRoot) {
    const slides = [...slidesRoot.querySelectorAll('.hero-slide')];
    const dots = document.querySelector('.carousel-dots');
    const pause = document.querySelector('#carousel-pause');
    const reduced = matchMedia('(prefers-reduced-motion: reduce)');
    let active = 0, timer, playing = !reduced.matches, hovering = false, focused = false;

    const schedule = () => {
      clearInterval(timer);
      if (playing && !hovering && !focused && !document.hidden && slides.length > 1) {
        timer = setInterval(() => show(active + 1, false), CONFIG.interval);
      }
    };
    const updatePause = () => {
      pause.textContent = playing ? 'Ⅱ' : '▶';
      pause.setAttribute('aria-label', playing ? 'Pause slideshow' : 'Play slideshow');
    };
    const show = (index, announce = true) => {
      if (!slides.length) return;
      active = (index + slides.length) % slides.length;
      slides.forEach((slide, i) => { slide.hidden = i !== active; });
      [...dots.children].forEach((dot, i) => dot.setAttribute('aria-current', String(i === active)));
      document.querySelector('#carousel-count').textContent = `${String(active + 1).padStart(2, '0')} of ${String(slides.length).padStart(2, '0')}`;
      if (announce) {
        const name = slides[active].querySelector('h2')?.textContent || 'Featured project';
        document.querySelector('#carousel-status').textContent = `${name}, project ${active + 1} of ${slides.length}`;
      }
      schedule();
    };

    dots.replaceChildren();
    slides.forEach((slide, i) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.setAttribute('aria-label', `Show project ${i + 1}: ${slide.querySelector('h2')?.textContent || ''}`);
      button.addEventListener('click', () => show(i));
      dots.append(button);
    });
    document.querySelector('.carousel-controls').hidden = false;
    document.querySelector('#carousel-prev').addEventListener('click', () => show(active - 1));
    document.querySelector('#carousel-next').addEventListener('click', () => show(active + 1));
    pause.addEventListener('click', () => { playing = !playing; updatePause(); schedule(); });
    hero.addEventListener('mouseenter', () => { hovering = true; schedule(); });
    hero.addEventListener('mouseleave', () => { hovering = false; schedule(); });
    hero.addEventListener('focusin', () => { focused = true; schedule(); });
    hero.addEventListener('focusout', e => { if (!hero.contains(e.relatedTarget)) { focused = false; schedule(); } });
    hero.addEventListener('keydown', e => {
      if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
        e.preventDefault();
        show(active + (e.key === 'ArrowRight' ? 1 : -1));
      }
    });
    let touch;
    hero.addEventListener('touchstart', e => { touch = e.touches[0]; }, { passive: true });
    hero.addEventListener('touchend', e => {
      if (!touch) return;
      const dx = e.changedTouches[0].clientX - touch.clientX;
      const dy = e.changedTouches[0].clientY - touch.clientY;
      if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.5) show(active + (dx < 0 ? 1 : -1));
      touch = null;
    }, { passive: true });
    reduced.addEventListener('change', () => {
      if (reduced.matches) { playing = false; updatePause(); schedule(); }
    });
    document.addEventListener('visibilitychange', schedule);
    window.addEventListener('pagehide', () => clearInterval(timer));
    show(0, false);
    updatePause();
  }

  const mobile = matchMedia('(max-width:600px)');
  const grid = document.querySelector('#project-grid');
  const scroll = document.querySelector('#project-scroll');
  const more = document.querySelector('#see-more');
  if (!grid || !scroll || !more) return;
  const cards = [...grid.children];
  let visible = CONFIG.mobileInitial;
  const updateGrid = () => {
    cards.forEach((card, i) => { card.hidden = mobile.matches && i >= visible; });
    more.hidden = !mobile.matches || visible >= cards.length;
    scroll.tabIndex = mobile.matches ? -1 : 0;
    scroll.setAttribute('aria-label', mobile.matches ? 'Project gallery' : 'Project gallery. Scroll here for more projects.');
    document.querySelector('#grid-count').textContent = mobile.matches ? `${Math.min(visible, cards.length)} of ${cards.length} projects` : `${cards.length} projects`;
    if (!mobile.matches && cards.length) {
      const gap = parseFloat(getComputedStyle(grid).rowGap);
      scroll.style.height = `${cards[0].getBoundingClientRect().height * 3 + gap * 2}px`;
    } else {
      scroll.style.height = 'auto';
    }
  };
  more.addEventListener('click', () => {
    const firstNew = cards[visible];
    visible += CONFIG.mobileBatch;
    updateGrid();
    if (firstNew) firstNew.focus({ preventScroll: true });
  });
  mobile.addEventListener('change', updateGrid);
  new ResizeObserver(updateGrid).observe(grid);
  updateGrid();
})();
