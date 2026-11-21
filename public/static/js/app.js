async function drawTrendChart() {
  const canvas = document.getElementById('trend-chart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const rows = Array.isArray(window.AQUAGUARD_HISTORY) ? window.AQUAGUARD_HISTORY : [];
  if (!rows.length) return;

  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * window.devicePixelRatio;
  canvas.height = rect.height * window.devicePixelRatio;
  ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
  const w = rect.width, h = rect.height;
  ctx.clearRect(0, 0, w, h);

  ctx.strokeStyle = '#edf1f5'; ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = 10 + i * (h - 30) / 4;
    ctx.beginPath(); ctx.moveTo(34, y); ctx.lineTo(w - 8, y); ctx.stroke();
  }

  function plot(field, color, max) {
    ctx.strokeStyle = color; ctx.lineWidth = 2;
    ctx.beginPath();
    rows.forEach((row, index) => {
      const x = 34 + index * (w - 42) / Math.max(rows.length - 1, 1);
      const value = Number(row[field] || 0);
      const y = h - 20 - (value / max) * (h - 35);
      if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }
  plot('tds_ppm', '#3d86c7', 200);
  plot('turbidity_ntu', '#67b7a3', 20);
}

window.addEventListener('load', drawTrendChart);
window.addEventListener('resize', drawTrendChart);

if (document.querySelector('.workspace')) {
  setInterval(() => window.location.reload(), 30000);
}
