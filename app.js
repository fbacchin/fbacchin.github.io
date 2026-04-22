// === ATP Ranking Simulator — Sinner vs Alcaraz 2026 ===

// Current official points (as of March 15, 2026)
const SINNER_BASE = 13360;
const ALCARAZ_BASE = 12960;

// Points distribution by category and result
const POINTS = {
  'Grand Slam': { W: 2000, F: 1300, SF: 800, QF: 400, R16: 200, R32: 100, R64: 50, R128: 10, '-': 0 },
  'Masters 1000': { W: 1000, F: 650, SF: 400, QF: 200, R16: 100, R32: 50, R64: 30, R128: 10, '-': 0 },
  'ATP 500': { W: 500, F: 330, SF: 200, QF: 100, R16: 50, '-': 0 },
  'ATP 250': { W: 250, F: 165, SF: 100, QF: 50, R16: 25, '-': 0 },
  'ATP Finals': { W: 1500, F: 1000, SF: 800, RR: 600, '-': 0 }
};

// Upcoming tournaments to simulate (from March 2026 onwards)
const TOURNAMENTS = [
  {
    name: 'Madrid',
    category: 'Masters 1000',
    dates: 'Apr 27 - Mag 4',
    sinnerDefend: 0,
    alcarazDefend: 0,
    note: ''
  },
  {
    name: 'Roma',
    category: 'Masters 1000',
    dates: 'Mag 8-18',
    sinnerDefend: 650,
    alcarazDefend: 1000,
    note: 'Sinner F, Alcaraz W'
  },
  {
    name: 'Roland Garros',
    category: 'Grand Slam',
    dates: 'Mag 25 - Giu 8',
    sinnerDefend: 1300,
    alcarazDefend: 2000,
    note: 'Sinner F, Alcaraz W'
  },
  {
    name: 'Halle',
    category: 'ATP 500',
    dates: 'Giu 16-22',
    sinnerDefend: 50,
    alcarazDefend: 0,
    note: 'Sinner R16'
  },
  {
    name: "Queen's Club",
    category: 'ATP 500',
    dates: 'Giu 16-22',
    sinnerDefend: 0,
    alcarazDefend: 500,
    note: 'Alcaraz W da difendere'
  },
  {
    name: 'Wimbledon',
    category: 'Grand Slam',
    dates: 'Giu 30 - Lug 13',
    sinnerDefend: 2000,
    alcarazDefend: 1300,
    note: 'Sinner W, Alcaraz F'
  },
  {
    name: 'Toronto/Montreal',
    category: 'Masters 1000',
    dates: 'Ago 4-10',
    sinnerDefend: 0,
    alcarazDefend: 0,
    note: ''
  },
  {
    name: 'Cincinnati',
    category: 'Masters 1000',
    dates: 'Ago 11-17',
    sinnerDefend: 650,
    alcarazDefend: 1000,
    note: 'Sinner F, Alcaraz W'
  },
  {
    name: 'US Open',
    category: 'Grand Slam',
    dates: 'Ago 25 - Set 7',
    sinnerDefend: 1300,
    alcarazDefend: 2000,
    note: 'Sinner F, Alcaraz W'
  },
  {
    name: 'Shanghai',
    category: 'Masters 1000',
    dates: 'Ott 5-12',
    sinnerDefend: 50,
    alcarazDefend: 0,
    note: 'Sinner R32'
  },
  {
    name: 'Parigi-Bercy',
    category: 'Masters 1000',
    dates: 'Ott 27 - Nov 2',
    sinnerDefend: 1000,
    alcarazDefend: 10,
    note: 'Sinner W, Alcaraz R32'
  },
  {
    name: 'ATP Finals',
    category: 'ATP Finals',
    dates: 'Nov 9-16',
    sinnerDefend: 1500,
    alcarazDefend: 1000,
    note: 'Sinner W, Alcaraz F'
  }
];

// Points to defend lists
const SINNER_DEFEND = [
  { tournament: 'Wimbledon', points: 2000, drop: '13 Lug' },
  { tournament: 'ATP Finals', points: 1500, drop: '16 Nov' },
  { tournament: 'Roland Garros', points: 1300, drop: '8 Giu' },
  { tournament: 'US Open', points: 1300, drop: '7 Set' },
  { tournament: 'Parigi-Bercy', points: 1000, drop: '2 Nov' },
  { tournament: 'Roma', points: 650, drop: '18 Mag' },
  { tournament: 'Cincinnati', points: 650, drop: '17 Ago' },
  { tournament: 'Vienna', points: 500, drop: '26 Ott' },
  { tournament: 'Pechino', points: 500, drop: '28 Set' },
  { tournament: 'Halle', points: 50, drop: '22 Giu' },
  { tournament: 'Shanghai', points: 50, drop: '12 Ott' },
];

const ALCARAZ_DEFEND = [
  { tournament: 'Roland Garros', points: 2000, drop: '8 Giu' },
  { tournament: 'US Open', points: 2000, drop: '7 Set' },
  { tournament: 'Wimbledon', points: 1300, drop: '13 Lug' },
  { tournament: 'Monte-Carlo', points: 1000, drop: '13 Apr' },
  { tournament: 'Roma', points: 1000, drop: '18 Mag' },
  { tournament: 'Cincinnati', points: 1000, drop: '17 Ago' },
  { tournament: 'ATP Finals', points: 1000, drop: '16 Nov' },
  { tournament: "Queen's Club", points: 500, drop: '22 Giu' },
  { tournament: 'Tokyo', points: 500, drop: '28 Set' },
  { tournament: 'Indian Wells', points: 400, drop: '16 Mar' },
  { tournament: 'Barcellona', points: 330, drop: '20 Apr' },
  { tournament: 'Miami', points: 10, drop: '30 Mar' },
  { tournament: 'Parigi-Bercy', points: 10, drop: '2 Nov' },
];

// State — values: undefined (not yet set), '-' (not playing), or result string
let state = {
  sinner: {},
  alcaraz: {}
};

function getResults(category) {
  const pts = POINTS[category];
  if (!pts) return ['-'];
  return Object.keys(pts);
}

function formatNumber(n) {
  return n.toLocaleString('it-IT');
}

function calculate() {
  let sinnerDelta = 0;
  let alcarazDelta = 0;

  TOURNAMENTS.forEach((t, i) => {
    const sResult = state.sinner[i];
    const aResult = state.alcaraz[i];
    const pts = POINTS[t.category];

    // Only count tournaments that have been explicitly set by the user
    if (sResult !== undefined) {
      const sGained = pts[sResult] || 0;
      sinnerDelta += sGained - t.sinnerDefend;
    }
    if (aResult !== undefined) {
      const aGained = pts[aResult] || 0;
      alcarazDelta += aGained - t.alcarazDefend;
    }
  });

  const sinnerNew = SINNER_BASE + sinnerDelta;
  const alcarazNew = ALCARAZ_BASE + alcarazDelta;
  const gap = sinnerNew - alcarazNew;

  return { sinnerNew, alcarazNew, gap };
}

function updateUI() {
  const { sinnerNew, alcarazNew, gap } = calculate();

  // Scoreboard
  document.getElementById('sinner-points').textContent = formatNumber(sinnerNew);
  document.getElementById('alcaraz-points').textContent = formatNumber(alcarazNew);

  const sinnerIsNo1 = sinnerNew > alcarazNew;
  document.getElementById('sinner-rank').textContent = sinnerIsNo1 ? '#1' : '#2';
  document.getElementById('alcaraz-rank').textContent = sinnerIsNo1 ? '#2' : '#1';

  // Gap
  const gapEl = document.getElementById('gap-value');
  const absGap = Math.abs(gap);
  if (gap > 0) {
    gapEl.textContent = `+${formatNumber(gap)}`;
    gapEl.style.color = 'var(--sinner-color)';
  } else if (gap < 0) {
    gapEl.textContent = `-${formatNumber(absGap)}`;
    gapEl.style.color = 'var(--alcaraz-color)';
  } else {
    gapEl.textContent = '0';
    gapEl.style.color = 'var(--color-text)';
  }

  // Gap bar
  const maxPts = Math.max(sinnerNew, alcarazNew);
  const barPercent = maxPts > 0 ? (Math.min(sinnerNew, alcarazNew) / maxPts) * 100 : 50;
  const barEl = document.getElementById('gap-bar');
  barEl.style.width = barPercent + '%';
  barEl.style.background = sinnerIsNo1 ? 'var(--sinner-color)' : 'var(--alcaraz-color)';

  // Status
  const statusBar = document.getElementById('status-bar');
  const statusText = document.getElementById('status-text');
  const statusIcon = statusBar.querySelector('.status-icon');

  if (sinnerIsNo1) {
    statusBar.classList.add('status-success');
    statusIcon.textContent = '🏆';
    statusText.textContent = `Sinner diventa N.1 con ${formatNumber(sinnerNew)} punti (+${formatNumber(gap)} su Alcaraz)`;
  } else if (gap === 0) {
    statusBar.classList.remove('status-success');
    statusIcon.textContent = '⚖️';
    statusText.textContent = 'Parità di punti. Sinner ha bisogno di superare Alcaraz per essere N.1';
  } else {
    statusBar.classList.remove('status-success');
    statusIcon.textContent = '⚠️';
    statusText.textContent = `Sinner ha bisogno di recuperare ${formatNumber(absGap)} punti per diventare N.1`;
  }

  // Update per-tournament point changes
  TOURNAMENTS.forEach((t, i) => {
    const sResult = state.sinner[i];
    const aResult = state.alcaraz[i];
    const pts = POINTS[t.category];

    const sPtsEl = document.getElementById(`sinner-pts-${i}`);
    const aPtsEl = document.getElementById(`alcaraz-pts-${i}`);

    if (sPtsEl) {
      if (sResult === undefined) {
        sPtsEl.textContent = '—';
        sPtsEl.className = 'points-change';
      } else if (sResult === '-') {
        sPtsEl.textContent = t.sinnerDefend > 0 ? `−${formatNumber(t.sinnerDefend)}` : '0';
        sPtsEl.className = 'points-change' + (t.sinnerDefend > 0 ? ' negative' : '');
      } else {
        const sGained = pts[sResult] || 0;
        const sNet = sGained - t.sinnerDefend;
        const sign = sNet >= 0 ? '+' : '−';
        sPtsEl.textContent = `${sign}${formatNumber(Math.abs(sNet))}`;
        sPtsEl.className = 'points-change' + (sNet >= 0 ? ' positive' : ' negative');
      }
    }

    if (aPtsEl) {
      if (aResult === undefined) {
        aPtsEl.textContent = '—';
        aPtsEl.className = 'points-change';
      } else if (aResult === '-') {
        aPtsEl.textContent = t.alcarazDefend > 0 ? `−${formatNumber(t.alcarazDefend)}` : '0';
        aPtsEl.className = 'points-change' + (t.alcarazDefend > 0 ? ' negative' : '');
      } else {
        const aGained = pts[aResult] || 0;
        const aNet = aGained - t.alcarazDefend;
        const sign = aNet >= 0 ? '+' : '−';
        aPtsEl.textContent = `${sign}${formatNumber(Math.abs(aNet))}`;
        aPtsEl.className = 'points-change' + (aNet >= 0 ? ' positive' : ' negative');
      }
    }
  });
}

function renderTournaments() {
  const grid = document.getElementById('tournament-grid');
  grid.innerHTML = '';

  TOURNAMENTS.forEach((t, i) => {
    const results = getResults(t.category);

    const row = document.createElement('div');
    row.className = 'tournament-row';

    const catBadge = t.category === 'Grand Slam' ? '🎾 Grand Slam'
      : t.category === 'ATP Finals' ? '🏆 ATP Finals'
      : t.category === 'Masters 1000' ? '🔷 Masters 1000'
      : t.category === 'ATP 500' ? '🔹 ATP 500'
      : '🔸 ATP 250';

    // Build options: placeholder first, then '-' (non gioca), then results
    const resultOptions = results.filter(r => r !== '-').map(r => {
      return `<option value="${r}">${r} (${POINTS[t.category][r] || 0} pt)</option>`;
    }).join('');
    const optionsHtml = `<option value="" selected disabled>— Seleziona —</option><option value="-">Non gioca / Perde presto (0 pt)</option>${resultOptions}`;

    row.innerHTML = `
      <div class="tournament-info">
        <div class="tournament-name">${t.name}</div>
        <div class="tournament-cat">${catBadge}</div>
        <div class="tournament-dates">${t.dates}${t.note ? ' — ' + t.note : ''}</div>
      </div>
      <div class="player-select-group">
        <label class="select-label sinner-label">🇮🇹 Sinner</label>
        <select class="result-select" data-player="sinner" data-index="${i}">
          ${optionsHtml}
        </select>
        <div class="points-change" id="sinner-pts-${i}">—</div>
      </div>
      <div class="player-select-group">
        <label class="select-label alcaraz-label">🇪🇸 Alcaraz</label>
        <select class="result-select" data-player="alcaraz" data-index="${i}">
          ${optionsHtml}
        </select>
        <div class="points-change" id="alcaraz-pts-${i}">—</div>
      </div>
    `;

    grid.appendChild(row);
  });

  // Event listeners
  grid.querySelectorAll('.result-select').forEach(sel => {
    sel.addEventListener('change', (e) => {
      const player = e.target.dataset.player;
      const idx = parseInt(e.target.dataset.index);
      const val = e.target.value;
      if (val === '') {
        delete state[player][idx];
      } else {
        state[player][idx] = val;
      }
      updateUI();
    });
  });
}

function renderDefend() {
  const sinnerList = document.getElementById('sinner-defend');
  const alcarazList = document.getElementById('alcaraz-defend');

  sinnerList.innerHTML = SINNER_DEFEND.map(d => `
    <div class="defend-item">
      <span class="defend-tournament">${d.tournament}</span>
      <div class="defend-info">
        <span class="defend-pts">${formatNumber(d.points)}</span>
        <span class="defend-date">${d.drop}</span>
      </div>
    </div>
  `).join('');

  alcarazList.innerHTML = ALCARAZ_DEFEND.map(d => `
    <div class="defend-item">
      <span class="defend-tournament">${d.tournament}</span>
      <div class="defend-info">
        <span class="defend-pts">${formatNumber(d.points)}</span>
        <span class="defend-date">${d.drop}</span>
      </div>
    </div>
  `).join('');
}

// Theme toggle
(function(){
  const t = document.querySelector('[data-theme-toggle]');
  const r = document.documentElement;
  let d = r.getAttribute('data-theme') || (matchMedia('(prefers-color-scheme:dark)').matches ? 'dark' : 'light');
  r.setAttribute('data-theme', d);
  if (t) {
    t.addEventListener('click', () => {
      d = d === 'dark' ? 'light' : 'dark';
      r.setAttribute('data-theme', d);
      t.setAttribute('aria-label', 'Switch to ' + (d === 'dark' ? 'light' : 'dark') + ' mode');
      t.innerHTML = d === 'dark'
        ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
        : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
    });
  }
})();

// Preset scenarios
function applyPreset(preset) {
  state = { sinner: {}, alcaraz: {} };

  if (preset === 'reset') {
    // Reset all selects to placeholder
    document.querySelectorAll('.result-select').forEach(sel => {
      sel.value = '';
    });
    updateUI();
    return;
  }

  TOURNAMENTS.forEach((t, i) => {
    if (preset === 'sinnerWins') {
      state.sinner[i] = 'W';
      state.alcaraz[i] = 'F';
    } else if (preset === 'alcarazWins') {
      state.sinner[i] = 'F';
      state.alcaraz[i] = 'W';
    } else if (preset === 'splitSlams') {
      // Sinner wins RG, Wimbledon; Alcaraz wins US Open, ATP Finals
      // Masters: they alternate
      if (t.category === 'Grand Slam') {
        if (t.name === 'Roland Garros' || t.name === 'Wimbledon') {
          state.sinner[i] = 'W';
          state.alcaraz[i] = 'F';
        } else {
          state.sinner[i] = 'F';
          state.alcaraz[i] = 'W';
        }
      } else if (t.category === 'Masters 1000') {
        // Alternate: Sinner wins Indian Wells, Madrid, Cincinnati, Paris
        if (['Indian Wells', 'Madrid', 'Cincinnati', 'Parigi-Bercy'].includes(t.name)) {
          state.sinner[i] = 'W';
          state.alcaraz[i] = 'SF';
        } else {
          state.sinner[i] = 'SF';
          state.alcaraz[i] = 'W';
        }
      } else if (t.category === 'ATP Finals') {
        state.sinner[i] = 'W';
        state.alcaraz[i] = 'F';
      } else {
        // ATP 500: both reach SF
        state.sinner[i] = 'SF';
        state.alcaraz[i] = 'SF';
      }
    }
  });

  // Update selects to match
  document.querySelectorAll('.result-select').forEach(sel => {
    const player = sel.dataset.player;
    const idx = parseInt(sel.dataset.index);
    if (state[player][idx] !== undefined) {
      sel.value = state[player][idx];
    }
  });

  updateUI();
}

// Make applyPreset globally available for onclick
window.applyPreset = applyPreset;

// Init
renderTournaments();
renderDefend();
updateUI();
