/* =========================
   Starfield Background
========================= */
(function() {
  const canvas = document.getElementById("starfield");
  const ctx = canvas.getContext("2d");
  
  const STAR_COUNT = 120;
  const COLORS = ["#6366f1","#8b5cf6","#a855f7","#ffffff","#c4b5fd","#e0e7ff"];
  let stars = [];
  let shootingStars = [];
  let lastShoot = 0;
  let paused = false;
  let lastFrame = 0;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  function initStars() {
    stars = [];
    for (let i = 0; i < STAR_COUNT; i++) {
      stars.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        r: Math.random() * 1.5 + 0.5,
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
        speed: Math.random() * 0.8 + 0.2,
        offset: Math.random() * Math.PI * 2,
        baseAlpha: Math.random() * 0.5 + 0.3
      });
    }
  }

  function spawnShootingStar() {
    const startX = Math.random() * canvas.width * 0.8;
    const startY = Math.random() * canvas.height * 0.4;
    shootingStars.push({
      x: startX,
      y: startY,
      vx: 4 + Math.random() * 4,
      vy: 2 + Math.random() * 3,
      life: 1,
      decay: 0.015 + Math.random() * 0.01,
      len: 40 + Math.random() * 60,
      color: COLORS[Math.floor(Math.random() * 3)]
    });
  }

  function draw(time) {
    if (paused) { requestAnimationFrame(draw); return; }

    // Cap at ~30 FPS
    if (time - lastFrame < 33) { requestAnimationFrame(draw); return; }
    lastFrame = time;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const t = time * 0.001;

    // Draw stars
    for (const s of stars) {
      const alpha = s.baseAlpha + Math.sin(t * s.speed + s.offset) * 0.3;
      ctx.globalAlpha = Math.max(0.05, Math.min(1, alpha));
      ctx.fillStyle = s.color;
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fill();
    }

    // Shooting stars
    if (t - lastShoot > 5 + Math.random() * 3) {
      spawnShootingStar();
      lastShoot = t;
    }

    for (let i = shootingStars.length - 1; i >= 0; i--) {
      const ss = shootingStars[i];
      ss.x += ss.vx;
      ss.y += ss.vy;
      ss.life -= ss.decay;

      if (ss.life <= 0) { shootingStars.splice(i, 1); continue; }

      ctx.globalAlpha = ss.life * 0.8;
      const grad = ctx.createLinearGradient(ss.x, ss.y, ss.x - ss.vx * (ss.len / 5), ss.y - ss.vy * (ss.len / 5));
      grad.addColorStop(0, ss.color);
      grad.addColorStop(1, "transparent");
      ctx.strokeStyle = grad;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(ss.x, ss.y);
      ctx.lineTo(ss.x - ss.vx * (ss.len / 5), ss.y - ss.vy * (ss.len / 5));
      ctx.stroke();
    }

    ctx.globalAlpha = 1;
    requestAnimationFrame(draw);
  }

  window.addEventListener("resize", () => { resize(); initStars(); });
  document.addEventListener("visibilitychange", () => { paused = document.hidden; });

  resize();
  initStars();
  requestAnimationFrame(draw);
})();
