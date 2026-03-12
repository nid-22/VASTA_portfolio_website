/**
* Template Name: MyPortfolio
* Updated: Jan 29 2024 with Bootstrap v5.3.2
* Template URL: https://bootstrapmade.com/myportfolio-bootstrap-portfolio-website-template/
* Author: BootstrapMade.com
* License: https://bootstrapmade.com/license/
*/
(function() {
  "use strict";

  /**
   * Easy selector helper function
   */
  const select = (el, all = false) => {
    el = el.trim()
    if (all) {
      return [...document.querySelectorAll(el)]
    } else {
      return document.querySelector(el)
    }
  }

  /**
   * Easy event listener function
   */
  const on = (type, el, listener, all = false) => {
    let selectEl = select(el, all)
    if (selectEl) {
      if (all) {
        selectEl.forEach(e => e.addEventListener(type, listener))
      } else {
        selectEl.addEventListener(type, listener)
      }
    }
  }

  /**
   * Easy on scroll event listener 
   */
  const onscroll = (el, listener) => {
    el.addEventListener('scroll', listener)
  }

  /**
   * burgerMenu
   */
  const burgerMenu = select('.burger')
  on('click', '.burger', function(e) {
    burgerMenu.classList.toggle('active');
  })

  /**
   * Porfolio isotope and filter
   */
  window.addEventListener('load', () => {
    let portfolioContainer = select('#portfolio-grid');
    if (portfolioContainer) {
      let portfolioIsotope = new Isotope(portfolioContainer, {
        itemSelector: '.item',
      });

      let portfolioFilters = select('#filters a', true);

      on('click', '#filters a', function(e) {
        e.preventDefault();
        portfolioFilters.forEach(function(el) {
          el.classList.remove('active');
        });
        this.classList.add('active');

        portfolioIsotope.arrange({
          filter: this.getAttribute('data-filter')
        });
        portfolioIsotope.on('arrangeComplete', function() {
          AOS.refresh()
        });
      }, true);
    }

  });

  /**
   * Testimonials slider
   */
  new Swiper('.testimonials-slider', {
    speed: 600,
    loop: true,
    autoplay: {
      delay: 5000,
      disableOnInteraction: false
    },
    slidesPerView: 'auto',
    pagination: {
      el: '.swiper-pagination',
      type: 'bullets',
      clickable: true
    }
  });

  /**
   * Animation on scroll
   */
  window.addEventListener('load', () => {
    AOS.init({
      duration: 1000,
      easing: 'ease-in-out',
      once: true,
      mirror: false
    })
  });
  })();

  /* Gallery lightbox: open clicked thumbnail or main photo fullscreen */
  (function(){
    const gallery = document.querySelector('[data-gallery]');
    if (!gallery) return;

  const mainImg = gallery.querySelector('.gallery-main .main-photo');
  // include all .thumb images (visible and hidden) so the lightbox can navigate every image
  const thumbs = Array.from(gallery.querySelectorAll('.thumb img'));

    // create lightbox DOM
    let lightbox = document.querySelector('.gallery-lightbox');
    if (!lightbox) {
      lightbox = document.createElement('div');
      lightbox.className = 'gallery-lightbox';
      lightbox.innerHTML = '\n      <button class="gb-close" aria-label="Close">✕</button>\n      <button class="gb-prev" aria-label="Previous">◀</button>\n      <img src="" alt="" class="gb-image">\n      <button class="gb-next" aria-label="Next">▶</button>\n    ';
      document.body.appendChild(lightbox);
    }

    const lbImage = lightbox.querySelector('.gb-image');
    const btnClose = lightbox.querySelector('.gb-close');
    const btnPrev = lightbox.querySelector('.gb-prev');
    const btnNext = lightbox.querySelector('.gb-next');

    const imageUrls = [];
    if (mainImg) imageUrls.push(mainImg.getAttribute('src'));
    thumbs.forEach(t => imageUrls.push(t.getAttribute('src')));

    // Immediately preload hidden images (the ones represented by +N) so navigation to them is instant.
    try {
      const hiddenImgs = Array.from(gallery.querySelectorAll('.gallery-hidden img'));
      if (hiddenImgs.length) {
        hiddenImgs.forEach(h => {
          const url = h.getAttribute('src');
          if (!url) return;
          // hint browser to prioritize the image
          try {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.as = 'image';
            link.href = url;
            document.head.appendChild(link);
          } catch (e) {
            // ignore failures creating preload link
          }
          // also create an Image to start the fetch immediately
          try {
            const img = new Image();
            img.decoding = 'async';
            img.src = url;
          } catch (e) {}
        });
      }
    } catch (e) {
      // defensive: if DOM queries fail, ignore and continue to background preload
    }

    // Secondary background preloader (non-blocking) for all images if any remain uncached.
    // Use requestIdleCallback when available, otherwise stagger requests.
    const backgroundPreload = () => {
      imageUrls.forEach((url) => {
        try {
          const img = new Image();
          img.decoding = 'async';
          img.src = url;
        } catch (e) {
          // ignore
        }
      });
    };

    if ('requestIdleCallback' in window) {
      try {
        requestIdleCallback(backgroundPreload, { timeout: 2000 });
      } catch (e) {
        backgroundPreload();
      }
    } else {
      // stagger loads so the browser isn't saturated immediately
      imageUrls.forEach((url, i) => {
        setTimeout(() => {
          try {
            const img = new Image();
            img.decoding = 'async';
            img.src = url;
          } catch (e) {}
        }, i * 150);
      });
    }

    let currentIndex = 0;

    function openAt(index){
      if (index < 0 || index >= imageUrls.length) return;
      currentIndex = index;
      lbImage.src = imageUrls[currentIndex];
      lightbox.classList.add('open');
      document.documentElement.style.overflow = 'hidden';
    }

    function close(){
      lightbox.classList.remove('open');
      document.documentElement.style.overflow = '';
    }

    function next(){
      currentIndex = (currentIndex + 1) % imageUrls.length;
      lbImage.src = imageUrls[currentIndex];
    }

    function prev(){
      currentIndex = (currentIndex - 1 + imageUrls.length) % imageUrls.length;
      lbImage.src = imageUrls[currentIndex];
    }

    if (mainImg) mainImg.addEventListener('click', ()=> openAt(0));
  thumbs.forEach((t, i) => t.addEventListener('click', ()=> openAt(i + (mainImg ? 1 : 0))));

    btnClose.addEventListener('click', close);
    btnNext.addEventListener('click', next);
    btnPrev.addEventListener('click', prev);

    lightbox.addEventListener('click', (e)=>{ if (e.target === lightbox) close(); });
    window.addEventListener('keydown', (e)=>{
      if (!lightbox.classList.contains('open')) return;
      if (e.key === 'Escape') close();
      if (e.key === 'ArrowRight') next();
      if (e.key === 'ArrowLeft') prev();
    });

  })();