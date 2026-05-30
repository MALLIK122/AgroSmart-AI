// AgroSmart AI - Futuristic 3D UI animations
(function () {
  'use strict';

  /* Scroll reveal */
  const revealEls = document.querySelectorAll(
    '.glass-card:not(#chat-window):not(#result-card), .feature-card, .stat-card, .section-header, .hero-content, .weather-widget, .chart-card'
  );
  revealEls.forEach((el) => el.classList.add('reveal-on-scroll'));

  const revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed');
          revealObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
  );
  revealEls.forEach((el) => revealObserver.observe(el));

  /* 3D tilt on cards */
  document.querySelectorAll('.glass-card.tilt-3d, .feature-card, .weather-widget, .stat-card').forEach((card) => {
    card.classList.add('tilt-3d');
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      card.style.setProperty('--tilt-x', `${y * -10}deg`);
      card.style.setProperty('--tilt-y', `${x * 10}deg`);
    });
    card.addEventListener('mouseleave', () => {
      card.style.setProperty('--tilt-x', '0deg');
      card.style.setProperty('--tilt-y', '0deg');
    });
  });

  /* Parallax hero mesh */
  const heroMesh = document.querySelector('.hero-mesh');
  const heroOrb = document.querySelector('.hero-orb');
  if (heroMesh || heroOrb) {
    window.addEventListener(
      'scroll',
      () => {
        const y = window.scrollY * 0.35;
        if (heroMesh) heroMesh.style.transform = `translateY(${y}px)`;
        if (heroOrb) heroOrb.style.transform = `translateY(${y * 0.5}px) rotateX(${8 + y * 0.02}deg)`;
      },
      { passive: true }
    );
  }

  /* Stagger feature cards */
  document.querySelectorAll('.features-grid .feature-card').forEach((card, i) => {
    card.style.transitionDelay = `${i * 0.08}s`;
  });

  /* Navbar scroll glow */
  const header = document.querySelector('header');
  if (header) {
    const onScroll = () => header.classList.toggle('scrolled', window.scrollY > 40);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* Smooth anchor scroll */
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', (e) => {
      const id = anchor.getAttribute('href');
      if (!id || id === '#') return;
      const target = document.querySelector(id);
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });

  /* Active nav link on scroll */
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-link[href^="#"]');
  if (sections.length && navLinks.length) {
    const sectionObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const id = entry.target.getAttribute('id');
          navLinks.forEach((link) => {
            link.classList.toggle('active', link.getAttribute('href') === `#${id}`);
          });
        });
      },
      { rootMargin: '-40% 0px -50% 0px', threshold: 0 }
    );
    sections.forEach((s) => sectionObserver.observe(s));
  }

  /* Mobile nav drawer */
  const burgerBtn = document.getElementById('mobile-menu-toggle');
  const navMenu = document.querySelector('.nav-menu');
  if (burgerBtn && navMenu) {
    burgerBtn.addEventListener('click', () => {
      navMenu.classList.toggle('mobile-open');
      burgerBtn.classList.toggle('active');
      const icon = burgerBtn.querySelector('i');
      if (icon) {
        icon.classList.toggle('fa-bars');
        icon.classList.toggle('fa-xmark');
      }
    });
    navMenu.querySelectorAll('.nav-link').forEach((link) => {
      link.addEventListener('click', () => {
        if (window.innerWidth <= 768) {
          navMenu.classList.remove('mobile-open');
          burgerBtn.classList.remove('active');
          const icon = burgerBtn.querySelector('i');
          if (icon) {
            icon.classList.add('fa-bars');
            icon.classList.remove('fa-xmark');
          }
        }
      });
    });
  }

  /* Typing cursor on hero badge (subtle) */
  const heroBadge = document.querySelector('.hero-badge span');
  if (heroBadge && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    heroBadge.classList.add('typing-cursor');
  }
})();
