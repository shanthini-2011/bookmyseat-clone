/* ============================================
   BookMySeat - Premium Animation Engine
   GSAP + Lenis + AOS + VanillaTilt
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {

  // ============================================
  // 1. AOS (Animate on Scroll) Init
  // ============================================
  if (typeof AOS !== 'undefined') {
    AOS.init({
      duration: 700,
      easing: 'ease-out-cubic',
      once: true,
      offset: 60,
      delay: 0,
    });
  }

  // ============================================
  // 2. LENIS SMOOTH SCROLLING
  // ============================================
  let lenisInstance = null;
  if (typeof Lenis !== 'undefined') {
    lenisInstance = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: 'vertical',
      gestureOrientation: 'vertical',
      smoothWheel: true,
      wheelMultiplier: 0.8,
      touchMultiplier: 1.5,
      infinite: false,
    });

    function raf(time) {
      lenisInstance.raf(time);
      requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);
  }

  // ============================================
  // 3. FALLING SPARKS / PARTICLES
  // ============================================
  function createParticles() {
    const container = document.createElement('div');
    container.className = 'particles-container';
    container.setAttribute('aria-hidden', 'true');
    document.body.appendChild(container);

    const isLight = document.documentElement.getAttribute('data-theme') === 'light';
    const colors = isLight
      ? [
          'rgba(245, 158, 11, 0.7)',  // Amber/Gold
          'rgba(239, 68, 68, 0.6)',   // Red
          'rgba(236, 72, 153, 0.6)',  // Pink
          'rgba(139, 92, 246, 0.5)',  // Violet
        ]
      : [
          'rgba(245, 158, 11, 0.6)',  // Amber
          'rgba(139, 92, 246, 0.8)',  // Violet
          'rgba(6, 182, 212, 0.8)',   // Cyan
        ];

    // Increased particle count for better visibility
    for (let i = 0; i < 40; i++) {
      const particle = document.createElement('div');
      particle.className = 'particle';
      const size = Math.random() * 4 + 2; // Slightly larger
      const color = colors[Math.floor(Math.random() * colors.length)];
      const duration = Math.random() * 10 + 6; // Fall faster (6-16s)
      const delay = Math.random() * 10;

      particle.style.cssText = `
        width: ${size}px;
        height: ${size}px;
        background: ${color};
        left: ${Math.random() * 100}%;
        animation-duration: ${duration}s;
        animation-delay: -${delay}s;
        box-shadow: 0 0 ${size * 3}px ${color};
      `;
      container.appendChild(particle);
    }
  }
  createParticles();

  // ============================================
  // 4. NAVBAR SCROLL EFFECT
  // ============================================
  const navbar = document.querySelector('.navbar-custom');
  if (navbar) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
      } else {
        navbar.classList.remove('scrolled');
      }
    }, { passive: true });
  }

  // ============================================
  // 5. GSAP ANIMATIONS
  // ============================================
  if (typeof gsap !== 'undefined') {

    if (typeof ScrollTrigger !== 'undefined') {
      gsap.registerPlugin(ScrollTrigger);
    }

    // Navbar entrance
    gsap.from('.navbar-custom', {
      y: -60,
      opacity: 0,
      duration: 0.8,
      ease: 'power3.out',
    });

    // Main content
    gsap.from('main', {
      opacity: 0,
      y: 15,
      duration: 0.5,
      ease: 'power2.out',
      delay: 0.2,
    });

    // Footer
    gsap.from('.footer-custom', {
      y: 30,
      opacity: 0,
      duration: 0.6,
      ease: 'power2.out',
      delay: 0.3,
    });

    // Movie card stagger
    const movieCards = document.querySelectorAll('.card-movie');
    if (movieCards.length > 0) {
      gsap.from('.card-movie', {
        y: 40,
        opacity: 0,
        duration: 0.7,
        stagger: { each: 0.1, from: 'start' },
        ease: 'power3.out',
        clearProps: 'all',
        delay: 0.3,
      });
    }

    // Glass panels with ScrollTrigger
    if (typeof ScrollTrigger !== 'undefined') {
      gsap.utils.toArray('.glass-panel').forEach((panel) => {
        gsap.from(panel, {
          scrollTrigger: {
            trigger: panel,
            start: 'top 88%',
            toggleActions: 'play none none none',
          },
          y: 30,
          opacity: 0,
          duration: 0.6,
          ease: 'power2.out',
        });
      });
    }

    // Section titles
    document.querySelectorAll('.section-title').forEach(el => {
      gsap.from(el, {
        x: -30,
        opacity: 0,
        duration: 0.6,
        ease: 'power2.out',
        scrollTrigger: typeof ScrollTrigger !== 'undefined' ? {
          trigger: el,
          start: 'top 88%',
        } : undefined,
      });
    });

    // Hero carousel
    const heroCarousel = document.querySelector('#heroCarousel, .swiper');
    if (heroCarousel) {
      gsap.from(heroCarousel, {
        scale: 0.95,
        y: 30,
        opacity: 0,
        duration: 1,
        ease: 'power3.out',
      });
    }

    // Metric card counter animation
    document.querySelectorAll('.metric-card h2, .metric-card h3').forEach(el => {
      const text = el.textContent;
      const match = text.match(/[\d,.]+/);
      if (match) {
        const target = parseFloat(match[0].replace(/,/g, ''));
        if (!isNaN(target) && target > 0) {
          const prefix = text.substring(0, text.indexOf(match[0]));
          const suffix = text.substring(text.indexOf(match[0]) + match[0].length);
          const obj = { val: 0 };
          gsap.to(obj, {
            val: target,
            duration: 2,
            ease: 'power2.out',
            delay: 0.5,
            onUpdate: () => {
              el.textContent = prefix + obj.val.toLocaleString('en-IN', {
                minimumFractionDigits: match[0].includes('.') ? 2 : 0,
                maximumFractionDigits: 2,
              }) + suffix;
            },
          });
        }
      }
    });
  }

  // ============================================
  // 6. 3D TILT EFFECT (VanillaTilt)
  // ============================================
  if (typeof VanillaTilt !== 'undefined') {
    const tiltCards = document.querySelectorAll('.card-movie');
    if (tiltCards.length > 0) {
      VanillaTilt.init(tiltCards, {
        max: 5,
        speed: 400,
        glare: true,
        'max-glare': 0.08,
        scale: 1.01,
        perspective: 1200,
      });
    }
  }

  // ============================================
  // 7. PAGE TRANSITIONS
  // ============================================
  function initPageTransitions() {
    const overlay = document.createElement('div');
    overlay.className = 'page-transition-overlay';
    overlay.setAttribute('aria-hidden', 'true');
    for (let i = 0; i < 5; i++) {
      const slice = document.createElement('div');
      slice.className = 'transition-slice';
      overlay.appendChild(slice);
    }
    document.body.appendChild(overlay);

    document.querySelectorAll('a[href]').forEach(link => {
      const href = link.getAttribute('href');
      if (!href || href.startsWith('#') || href.startsWith('javascript') ||
          href.startsWith('http') || href.startsWith('mailto') ||
          link.hasAttribute('download') || link.getAttribute('target') === '_blank') {
        return;
      }

      link.addEventListener('click', (e) => {
        if (e.ctrlKey || e.metaKey || e.shiftKey) return;
        e.preventDefault();
        const targetUrl = href;

        if (typeof gsap !== 'undefined') {
          const slices = overlay.querySelectorAll('.transition-slice');
          gsap.to(slices, {
            scaleY: 1,
            transformOrigin: 'bottom',
            duration: 0.35,
            stagger: 0.05,
            ease: 'power2.inOut',
            onComplete: () => {
              window.location.href = targetUrl;
            },
          });
        } else {
          window.location.href = targetUrl;
        }
      });
    });

    // Entry animation
    const playEntry = () => {
      if (typeof gsap !== 'undefined') {
        const slices = overlay.querySelectorAll('.transition-slice');
        gsap.set(slices, { scaleY: 1, transformOrigin: 'top' });
        gsap.to(slices, {
          scaleY: 0,
          duration: 0.4,
          stagger: 0.05,
          ease: 'power2.inOut',
          delay: 0.1,
        });
      }
    };
    playEntry();

    window.addEventListener('pageshow', (event) => {
      if (event.persisted) playEntry();
    });
  }
  initPageTransitions();

  // ============================================
  // 8. REVEAL ON SCROLL (Intersection Observer)
  // ============================================
  const revealElements = document.querySelectorAll('.reveal-up, .reveal-scale');
  if (revealElements.length > 0 && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    revealElements.forEach(el => observer.observe(el));
  }

  // ============================================
  // 9. CARD GLOW FOLLOW
  // ============================================
  document.querySelectorAll('.card-movie').forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      card.style.setProperty('--glow-x', x + '%');
      card.style.setProperty('--glow-y', y + '%');
    });
  });

});
