// ══════════════════════════════════════════════════════════
//  Agentic Career Counseling Companion — Main JS
// ══════════════════════════════════════════════════════════

// ── Theme (Dark / Light) ──────────────────────────────────
const THEME_KEY = 'acc_theme';
function initTheme() {
  const saved = localStorage.getItem(THEME_KEY) || 'light';
  document.documentElement.setAttribute('data-theme', saved);
  updateThemeBtn(saved);
}
function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem(THEME_KEY, next);
  updateThemeBtn(next);
}
function updateThemeBtn(theme) {
  const btn = document.getElementById('themeToggle');
  if (btn) btn.textContent = theme === 'dark' ? '☀️' : '🌙';
}

// ── Sidebar toggle (mobile) ───────────────────────────────
function initSidebar() {
  const menuBtn = document.getElementById('menuBtn');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  if (!menuBtn || !sidebar) return;
  menuBtn.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    overlay.classList.toggle('active');
  });
  if (overlay) {
    overlay.addEventListener('click', () => {
      sidebar.classList.remove('open');
      overlay.classList.remove('active');
    });
  }
}

// ── Tab system ────────────────────────────────────────────
function initTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const group = this.closest('[data-tab-group]') || this.closest('.tab-nav').parentElement;
      group.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      group.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
      this.classList.add('active');
      const target = this.dataset.tab;
      const pane = group.querySelector(`#${target}`);
      if (pane) pane.classList.add('active');
    });
  });
}

// ── Animate progress bars ─────────────────────────────────
function initProgressBars() {
  const bars = document.querySelectorAll('.progress-fill[data-value]');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        const bar = e.target;
        const val = parseFloat(bar.dataset.value) || 0;
        bar.style.width = '0%';
        setTimeout(() => { bar.style.width = val + '%'; }, 100);
        observer.unobserve(bar);
      }
    });
  }, { threshold: 0.2 });
  bars.forEach(b => observer.observe(b));
}

// ── Number counter animation ─────────────────────────────
function animateCounter(el, target, duration = 1200) {
  const start = 0;
  const startTime = performance.now();
  function tick(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(start + (target - start) * ease);
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}
function initCounters() {
  document.querySelectorAll('[data-counter]').forEach(el => {
    const target = parseFloat(el.dataset.counter);
    const observer = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) {
        animateCounter(el, target);
        observer.disconnect();
      }
    });
    observer.observe(el);
  });
}

// ── Profile form helper ───────────────────────────────────
function initProfileForm() {
  const form = document.getElementById('profileForm');
  if (!form) return;
  form.addEventListener('submit', function (e) {
    const name = form.querySelector('[name="full_name"]').value.trim();
    if (!name) { e.preventDefault(); alert('Please enter your full name.'); }
  });
}

// ── Dashboard charts (Chart.js) ───────────────────────────
function initDashboardCharts() {
  // Career Readiness Doughnut
  const radarCtx = document.getElementById('radarChart');
  if (radarCtx) {
    new Chart(radarCtx, {
      type: 'radar',
      data: {
        labels: ['Technical', 'Analytical', 'Communication', 'Problem Solving', 'Teamwork', 'Leadership'],
        datasets: [{
          label: 'Your Profile',
          data: radarCtx.dataset.values ? JSON.parse(radarCtx.dataset.values) : [70, 65, 60, 80, 75, 55],
          backgroundColor: 'rgba(15,98,254,0.15)',
          borderColor: '#0f62fe',
          borderWidth: 2,
          pointBackgroundColor: '#0f62fe',
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          r: {
            grid: { color: getComputedStyle(document.documentElement).getPropertyValue('--border-color').trim() || '#e0e0e0' },
            ticks: { display: false },
            min: 0, max: 100,
          }
        }
      }
    });
  }

  // Skills Bar Chart
  const skillsCtx = document.getElementById('skillsChart');
  if (skillsCtx) {
    const labels = skillsCtx.dataset.labels ? JSON.parse(skillsCtx.dataset.labels) : ['Python','SQL','Git','Cloud','APIs'];
    const values = skillsCtx.dataset.values ? JSON.parse(skillsCtx.dataset.values) : [80, 60, 75, 50, 65];
    new Chart(skillsCtx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Proficiency %',
          data: values,
          backgroundColor: '#0f62fe',
          borderRadius: 4,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { max: 100, ticks: { callback: v => v + '%' }, grid: { color: '#e0e0e030' } },
          x: { grid: { display: false } }
        }
      }
    });
  }

  // Career Growth Timeline / Line Chart
  const growthCtx = document.getElementById('growthChart');
  if (growthCtx) {
    new Chart(growthCtx, {
      type: 'line',
      data: {
        labels: ['Month 1','Month 3','Month 6','Month 9','Year 1','Year 2','Year 3'],
        datasets: [{
          label: 'Career Score',
          data: [30, 45, 58, 68, 75, 85, 95],
          borderColor: '#0f62fe',
          backgroundColor: 'rgba(15,98,254,0.08)',
          tension: 0.4,
          fill: true,
          pointBackgroundColor: '#0f62fe',
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { max: 100, grid: { color: '#e0e0e030' } },
          x: { grid: { display: false } }
        }
      }
    });
  }

  // Skill Gap Doughnut
  const gapCtx = document.getElementById('skillGapChart');
  if (gapCtx) {
    const existing = parseInt(gapCtx.dataset.existing || 3);
    const missing  = parseInt(gapCtx.dataset.missing  || 5);
    new Chart(gapCtx, {
      type: 'doughnut',
      data: {
        labels: ['Skills Acquired', 'Skills Missing'],
        datasets: [{
          data: [existing, missing],
          backgroundColor: ['#24a148', '#da1e28'],
          borderWidth: 0,
        }]
      },
      options: {
        responsive: true,
        cutout: '70%',
        plugins: {
          legend: { position: 'bottom', labels: { padding: 16, font: { size: 12 } } }
        }
      }
    });
  }

  // Industry Trends Bar
  const trendCtx = document.getElementById('trendChart');
  if (trendCtx) {
    new Chart(trendCtx, {
      type: 'bar',
      data: {
        labels: ['AI/ML', 'Cloud', 'Cybersecurity', 'Data Science', 'Web3', 'IoT', 'DevOps'],
        datasets: [{
          label: 'Demand Index',
          data: [95, 88, 82, 85, 60, 65, 80],
          backgroundColor: ['#0f62fe','#009d9a','#da1e28','#7c3aed','#ff832b','#24a148','#1192e8'],
          borderRadius: 4,
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { max: 100, grid: { color: '#e0e0e030' } },
          y: { grid: { display: false } }
        }
      }
    });
  }
}

// ── Reports PDF print ─────────────────────────────────────
function printReport() {
  window.print();
}

// ── Tooltip ───────────────────────────────────────────────
function initTooltips() {
  document.querySelectorAll('[data-tooltip]').forEach(el => {
    el.addEventListener('mouseenter', function () {
      const tip = document.createElement('div');
      tip.className = 'tooltip-bubble';
      tip.textContent = this.dataset.tooltip;
      tip.style.cssText = `
        position:fixed; background:#161616; color:#fff;
        padding:6px 10px; border-radius:4px; font-size:12px;
        pointer-events:none; z-index:9999; max-width:200px;
      `;
      document.body.appendChild(tip);
      const rect = this.getBoundingClientRect();
      tip.style.top  = (rect.top - tip.offsetHeight - 6) + 'px';
      tip.style.left = (rect.left + rect.width / 2 - tip.offsetWidth / 2) + 'px';
      this._tooltip = tip;
    });
    el.addEventListener('mouseleave', function () {
      if (this._tooltip) { this._tooltip.remove(); this._tooltip = null; }
    });
  });
}

// ── Init ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  initTheme();
  initSidebar();
  initTabs();
  initProgressBars();
  initCounters();
  initProfileForm();
  initDashboardCharts();
  initTooltips();
});
