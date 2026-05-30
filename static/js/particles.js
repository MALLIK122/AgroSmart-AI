// AgroSmart AI - Futuristic agriculture particle network
(function () {
  const canvas = document.getElementById('particle-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let W, H, particles = [], mouse = { x: -9999, y: -9999 };

  const COLORS = ['#00ffa3', '#00d4ff', '#34d399', '#a3e635', '#fbbf24', '#6ee7b7'];
  const AG_SYMBOLS = ['🌱', '🍃', '💧', '⬡', '◈', '✦', '🌾'];
  const COUNT = 85;

  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  function Particle() {
    this.reset();
  }

  Particle.prototype.reset = function () {
    this.x = Math.random() * W;
    this.y = Math.random() * H;
    this.z = Math.random() * 2 + 0.3;
    this.r = (Math.random() * 2.5 + 1) * this.z;
    this.color = COLORS[Math.floor(Math.random() * COLORS.length)];
    this.symbol = Math.random() > 0.78 ? AG_SYMBOLS[Math.floor(Math.random() * AG_SYMBOLS.length)] : null;
    this.vx = (Math.random() - 0.5) * 0.35 * this.z;
    this.vy = (Math.random() - 0.5) * 0.35 * this.z - 0.12 * this.z;
    this.alpha = Math.random() * 0.45 + 0.12;
    this.pulse = Math.random() * Math.PI * 2;
    this.pulseSpeed = 0.01 + Math.random() * 0.016;
    this.rotation = Math.random() * Math.PI * 2;
    this.rotSpeed = (Math.random() - 0.5) * 0.02;
  };

  Particle.prototype.update = function () {
    this.pulse += this.pulseSpeed;
    this.rotation += this.rotSpeed;
    const pAlpha = this.alpha + Math.sin(this.pulse) * 0.14;

    const dx = this.x - mouse.x;
    const dy = this.y - mouse.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist < 140) {
      const force = (140 - dist) / 140;
      this.x += (dx / dist) * force * 2.2;
      this.y += (dy / dist) * force * 2.2;
    }

    this.x += this.vx;
    this.y += this.vy;

    if (this.x < -30) this.x = W + 30;
    if (this.x > W + 30) this.x = -30;
    if (this.y < -30) this.y = H + 30;
    if (this.y > H + 30) this.reset();

    return pAlpha;
  };

  function drawConnections() {
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const p1 = particles[i];
        const p2 = particles[j];
        const dx = p1.x - p2.x;
        const dy = p1.y - p2.y;
        const d = Math.sqrt(dx * dx + dy * dy);
        if (d < 140) {
          const alpha = (1 - d / 140) * 0.2;
          const grad = ctx.createLinearGradient(p1.x, p1.y, p2.x, p2.y);
          grad.addColorStop(0, `rgba(0,255,163,${alpha})`);
          grad.addColorStop(1, `rgba(0,212,255,${alpha * 0.6})`);
          ctx.beginPath();
          ctx.moveTo(p1.x, p1.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.strokeStyle = grad;
          ctx.lineWidth = 0.7;
          ctx.stroke();
        }
      }
    }
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    drawConnections();
    particles.forEach((p) => {
      const a = p.update();
      ctx.save();
      ctx.globalAlpha = a;
      if (p.symbol) {
        ctx.font = `${p.r * 6}px sans-serif`;
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rotation);
        ctx.fillStyle = p.color;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(p.symbol, 0, 0);
      } else {
        const grad = ctx.createRadialGradient(
          p.x - p.r * 0.3,
          p.y - p.r * 0.3,
          0,
          p.x,
          p.y,
          p.r * 2.2
        );
        grad.addColorStop(0, 'rgba(255,255,255,0.85)');
        grad.addColorStop(0.35, p.color);
        grad.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r * 2.2, 0, Math.PI * 2);
        ctx.fillStyle = grad;
        ctx.fill();
      }
      ctx.restore();
    });
    requestAnimationFrame(draw);
  }

  function init() {
    resize();
    particles = Array.from({ length: COUNT }, () => new Particle());
    draw();
  }

  window.addEventListener('resize', resize);
  window.addEventListener('mousemove', (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
