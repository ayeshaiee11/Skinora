/* ══════════════════════════════════════════════════════════
   NEUROCURE SMOKE / VAPE TRACKER — JS
   ══════════════════════════════════════════════════════════ */

(function () {

/* ── CONFIG ─────────────────────────────────────────────── */
const STORAGE_KEY = 'nct_data_v2';
const today = () => new Date().toISOString().slice(0, 10);

/* ── LEVELS ─────────────────────────────────────────────── */
const LEVELS = [
    { name: 'Beginner',       xpNeeded: 0   },
    { name: 'Aware',          xpNeeded: 50  },
    { name: 'Cutting Back',   xpNeeded: 150 },
    { name: 'Fighter',        xpNeeded: 300 },
    { name: 'Streak Builder', xpNeeded: 500 },
    { name: 'Lung Cleaner',   xpNeeded: 750 },
    { name: 'Glow Starter',   xpNeeded: 1050},
    { name: 'Brain Healer',   xpNeeded: 1400},
    { name: 'Free Agent',     xpNeeded: 1800},
    { name: 'Nicotine Free',  xpNeeded: 2300},
];

/* ── HEAL ACTIONS — keyed by how many you've smoked today ─ */
const HEAL_ACTIONS = {
    smoke: [
        { icon:'💧', name:'Drink 500ml Water Now',        desc:'Flushes carbon monoxide from blood faster. Do it immediately.' },
        { icon:'🚶', name:'10-Minute Walk',               desc:'Boosts circulation and brings oxygen back to skin cells.' },
        { icon:'🧴', name:'Vitamin C Serum Tonight',      desc:'Counteracts oxidative stress from smoke on your skin.' },
        { icon:'🫁', name:'4-7-8 Breathing (3 rounds)',   desc:'Inhale 4s, hold 7s, exhale 8s. Clears residual aerosol.' },
        { icon:'🍊', name:'Eat Vitamin C–Rich Fruit',     desc:'Oranges, amla, kiwi. Nicotine depletes Vit C by up to 35%.' },
        { icon:'🌿', name:'Green Tea (no sugar)',          desc:'EGCG in green tea has antioxidant activity that counters smoke damage.' },
        { icon:'🛁', name:'Cold-Finish Shower',           desc:'Ends blood vessel constriction caused by nicotine. 30s cold is enough.' },
        { icon:'😴', name:'Sleep Before Midnight',         desc:'Peak skin repair happens 10pm–2am. Nicotine disrupts this window.' },
    ],
    vape: [
        { icon:'💧', name:'Drink 500ml Water Now',        desc:'Aerosol particles dry airways. Hydration thins mucus and helps clear them.' },
        { icon:'🌬️', name:'Diaphragm Breathing',          desc:'Belly breath in 4s, out 6s. Helps clear propylene glycol residue from airways.' },
        { icon:'🍃', name:'Peppermint or Ginger Tea',     desc:'Both soothe inflamed airways and neutralise chemical flavour residue.' },
        { icon:'🏃', name:'Light Cardio (15 min)',         desc:'Increases ventilation, speeds aerosol clearance from lung tissue.' },
        { icon:'🧴', name:'Niacinamide Moisturiser',       desc:'Vaping dehydrates skin. Niacinamide restores barrier function.' },
        { icon:'🫐', name:'Antioxidant-Rich Snack',       desc:'Berries, walnuts, or dark chocolate fight free radicals from vape chemicals.' },
        { icon:'🚫', name:'Avoid Vaping Indoors',         desc:'Secondhand aerosol redeposits on mucous membranes. Go outside or don't.' },
        { icon:'😴', name:'No Screen + Early Sleep',       desc:'Your brain is overstimulated from nicotine spikes. Sleep restores dopamine baseline.' },
    ],
};

/* ── ACHIEVEMENTS ──────────────────────────────────────── */
const ACHIEVEMENTS = [
    { id:'first_log',   icon:'📋', name:'First Log',         condition: d => d.totalLogged >= 1 },
    { id:'zero_day',    icon:'🌿', name:'Zero Day',          condition: d => d.cleanDays >= 1 },
    { id:'streak3',     icon:'🔥', name:'3-Day Streak',      condition: d => d.streak >= 3 },
    { id:'streak7',     icon:'🏆', name:'7-Day Streak',      condition: d => d.streak >= 7 },
    { id:'streak14',    icon:'💎', name:'2-Week Warrior',    condition: d => d.streak >= 14 },
    { id:'streak30',    icon:'🌟', name:'30-Day Hero',       condition: d => d.streak >= 30 },
    { id:'halved',      icon:'📉', name:'Cut in Half',       condition: d => d.lowestDay > 0 && d.lowestDay <= (d.peakDay / 2) },
    { id:'lvl5',        icon:'⚡', name:'Level 5 Reached',  condition: d => d.xp >= 500 },
    { id:'xp1000',      icon:'🧠', name:'1000 XP Brain',     condition: d => d.xp >= 1000 },
];

/* ── STATE ──────────────────────────────────────────────── */
let nctMode = null;  // 'smoke' | 'vape'
let state = {};

function loadState() {
    try { state = JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}; } catch { state = {}; }
    state.log        = state.log        || {};   // { 'YYYY-MM-DD': count }
    state.xp         = state.xp         || 0;
    state.streak     = state.streak     || 0;
    state.cleanDays  = state.cleanDays  || 0;
    state.totalLogged= state.totalLogged|| 0;
    state.peakDay    = state.peakDay    || 0;
    state.lowestDay  = state.lowestDay  || Infinity;
    state.unlocked   = state.unlocked   || [];
    state.lastActive = state.lastActive || null;
    state.mode       = state.mode       || null;
}

function saveState() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

/* ── PUBLIC: called by ncSetMode() in existing script ─── */
window.nctShowTracker = function (mode) {
    loadState();
    nctMode = mode;
    state.mode = mode;
    saveState();

    const wrap = document.getElementById('ncTrackerWrap');
    if (!wrap) return;
    wrap.style.display = 'block';

    // Badge + icon
    document.getElementById('nctBadge').textContent   = mode === 'smoke' ? '🚬 Smoke Tracker' : '💨 Vape Tracker';
    document.getElementById('nctLogIcon').textContent  = mode === 'smoke' ? '🚬' : '💨';

    nctRender();
};

window.nctHideTracker = function () {
    const wrap = document.getElementById('ncTrackerWrap');
    if (wrap) wrap.style.display = 'none';
};

/* ── LOG ONE ─────────────────────────────────────────────── */
window.nctLog = function () {
    loadState();
    const d = today();
    state.log[d]     = (state.log[d] || 0) + 1;
    state.totalLogged++;
    state.peakDay    = Math.max(state.peakDay, state.log[d]);
    if (state.log[d] < state.lowestDay) state.lowestDay = state.log[d];

    // Penalty XP (each log costs 10 XP floor 0)
    state.xp = Math.max(0, state.xp - 10);

    // Streak break if they log today after a clean day
    state.streak     = 0;
    state.lastActive  = d;
    saveState();

    // Shake the button
    const btn = document.getElementById('nctLogBtn');
    btn.classList.remove('nct-shake');
    void btn.offsetWidth;
    btn.classList.add('nct-shake');

    nctCheckAchievements();
    nctRender();
    nctToast(`+1 logged — ${state.log[d]} today. You can still end on a clean note.`);
};

/* ── MARK CLEAN DAY ──────────────────────────────────────── */
window.nctMarkCleanDay = function () {
    loadState();
    const d = today();
    if ((state.log[d] || 0) > 0) {
        nctToast('You already logged some today — tomorrow is your clean day!');
        return;
    }
    // Gain XP
    state.xp += 50;
    state.cleanDays++;

    // Streak logic
    const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0,10);
    if (state.lastActive === yesterday || state.streak === 0) {
        state.streak++;
    } else if (state.lastActive !== d) {
        state.streak = 1;
    }
    state.lastActive = d;
    state.log[d] = 0;
    saveState();

    nctCheckAchievements();
    nctRender();
    nctToast(`✅ Clean day locked in! +50 XP — Streak: ${state.streak} days 🔥`);
};

/* ── RENDER ──────────────────────────────────────────────── */
function nctRender() {
    const d = today();
    const todayCount = state.log[d] || 0;

    // Stats
    document.getElementById('nctToday').textContent  = todayCount;
    document.getElementById('nctStreak').textContent  = state.streak;
    document.getElementById('nctTotal').textContent   = state.totalLogged;

    // XP / level
    let lvlIdx = 0;
    for (let i = LEVELS.length - 1; i >= 0; i--) {
        if (state.xp >= LEVELS[i].xpNeeded) { lvlIdx = i; break; }
    }
    const thisLvl = LEVELS[lvlIdx];
    const nextLvl = LEVELS[Math.min(lvlIdx + 1, LEVELS.length - 1)];
    const xpInLvl = state.xp - thisLvl.xpNeeded;
    const xpRange = nextLvl.xpNeeded - thisLvl.xpNeeded || 1;
    const xpPct   = lvlIdx === LEVELS.length - 1 ? 100 : Math.round((xpInLvl / xpRange) * 100);

    document.getElementById('nctLevelName').textContent = thisLvl.name;
    document.getElementById('nctXpFill').style.width    = xpPct + '%';
    document.getElementById('nctXpVal').textContent     = state.xp;
    document.getElementById('nctXpNext').textContent    = nextLvl.xpNeeded;

    // Damage meter
    const dmgPct = Math.min(100, todayCount * 10);
    document.getElementById('nctDmgFill').style.width = dmgPct + '%';
    document.getElementById('nctDmgPct').textContent  = dmgPct + '%';
    document.getElementById('nctDmgHint').textContent = dmgPct === 0
        ? 'No damage logged today — stay strong.'
        : dmgPct <= 30 ? 'Mild damage — drink water and do some breathing exercises.'
        : dmgPct <= 60 ? 'Moderate damage — your lungs and skin are feeling this.'
        : dmgPct <= 90 ? 'Heavy damage today — start healing now, not later.'
        : 'Maximum damage zone. Your body needs intervention right now.';

    // Heal panel
    const healWrap = document.getElementById('nctHealWrap');
    if (todayCount > 0 && nctMode) {
        healWrap.style.display = 'block';
        renderHealGrid(nctMode, todayCount);
    } else {
        healWrap.style.display = todayCount === 0 ? 'none' : 'block';
    }

    // 7-day chart
    render7DayChart();

    // Achievements
    renderAchievements();
}

function renderHealGrid(mode, count) {
    const pool = HEAL_ACTIONS[mode] || HEAL_ACTIONS.smoke;
    // Show more cards as count rises (up to all 8)
    const show = Math.min(pool.length, 2 + Math.floor(count / 2));
    const cards = pool.slice(0, show);
    document.getElementById('nctHealGrid').innerHTML = cards.map(c => `
        <div class="nct-heal-card">
            <div class="nct-heal-card-icon">${c.icon}</div>
            <div class="nct-heal-card-body">
                <div class="nct-heal-card-name">${c.name}</div>
                <div class="nct-heal-card-desc">${c.desc}</div>
            </div>
        </div>
    `).join('');
}

function render7DayChart() {
    const days = [];
    for (let i = 6; i >= 0; i--) {
        const dt = new Date(Date.now() - i * 86400000);
        const key = dt.toISOString().slice(0, 10);
        const label = dt.toLocaleDateString('en', { weekday: 'short' });
        days.push({ key, label, count: state.log[key] || 0 });
    }
    const max = Math.max(...days.map(d => d.count), 1);
    const barColors = ['#34d399','#34d399','#fbbf24','#fbbf24','#f87171','#f87171','#dc2626'];

    document.getElementById('nctBarChart').innerHTML = days.map((d, i) => {
        const pct = Math.round((d.count / max) * 100);
        const color = d.count === 0 ? '#34d399' : pct <= 30 ? '#fbbf24' : '#f87171';
        return `<div class="nct-bar-col">
            <div class="nct-bar-count">${d.count > 0 ? d.count : ''}</div>
            <div class="nct-bar-inner" style="height:${Math.max(pct,3)}%;background:${color}"></div>
            <div class="nct-bar-label">${d.label}</div>
        </div>`;
    }).join('');
}

function renderAchievements() {
    document.getElementById('nctAchieveGrid').innerHTML = ACHIEVEMENTS.map(a => {
        const unlocked = state.unlocked.includes(a.id);
        return `<div class="nct-achieve ${unlocked ? 'unlocked' : ''}">
            <span class="nct-achieve-icon">${a.icon}</span>
            <span class="nct-achieve-name">${a.name}</span>
        </div>`;
    }).join('');
}

/* ── ACHIEVEMENTS CHECK ──────────────────────────────────── */
function nctCheckAchievements() {
    ACHIEVEMENTS.forEach(a => {
        if (!state.unlocked.includes(a.id) && a.condition(state)) {
            state.unlocked.push(a.id);
            saveState();
            setTimeout(() => nctToast(`🏅 Achievement unlocked: ${a.name}!`), 800);
        }
    });
}

/* ── TOAST ────────────────────────────────────────────────── */
let toastTimer;
function nctToast(msg) {
    const el = document.getElementById('nctToast');
    if (!el) return;
    el.textContent = msg;
    el.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove('show'), 3200);
}
window.nctToast = nctToast;

/* ── HOOK INTO EXISTING ncSetMode ───────────────────────── */
// Wrap the existing ncSetMode if it exists
document.addEventListener('DOMContentLoaded', () => {
    const origSetMode = window.ncSetMode;
    window.ncSetMode = function (mode) {
        if (origSetMode) origSetMode(mode);
        if (mode === 'smoke' || mode === 'vape') {
            nctShowTracker(mode);
        } else {
            nctHideTracker();
        }
    };

    // Auto-restore tracker if mode was previously set
    loadState();
    if (state.mode && (state.mode === 'smoke' || state.mode === 'vape')) {
        // Don't auto-show, user must click mode card
    }
});

})();