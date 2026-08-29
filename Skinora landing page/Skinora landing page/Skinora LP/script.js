/* ==========================================================
   SKINORA — script.js
   All editable content is stored in DATA ARRAYS at the top.
   Search for "SWAP THIS DATA" comments to find every place
   you need to edit text, images, or links.
   ========================================================== */

/** Sign-in page (served by START-SERVER.bat at localhost:8000) */
const LOGIN_URL = '/login/';
 
 
/* ----------------------------------------------------------
   ██████╗  █████╗ ████████╗ █████╗
   ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗
   ██║  ██║███████║   ██║   ███████║
   ██║  ██║██╔══██║   ██║   ██╔══██║
   ██████╔╝██║  ██║   ██║   ██║  ██║
   ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝
 
   ALL EDITABLE CONTENT IS IN THIS SECTION.
   Everything below the DATA section is rendering logic —
   you normally don't need to touch it.
   ---------------------------------------------------------- */
 
 
/* ==========================================================
   1. SOCIAL PROOF / MEDIA LOGOS
   SWAP THIS DATA ↓
   Each item: { name: "Publication Name" }
   You can optionally add an `logoImg` key with a URL to use
   a real image instead of text. Example:
   { name: "Vogue", logoImg: "images/logos/vogue.png" }
   ========================================================== */
const mediaLogos = [
  { name: "Vogue" },
  { name: "Self" },
  { name: "Healthline" },
  { name: "Well+Good" },
  { name: "MindBodyGreen" },
  { name: "Women's Health" },
];
 
 
/* ==========================================================
   2. PLATFORM CORE FEATURES
   SWAP THIS DATA ↓
   Fields:
     icon       — any emoji or unicode character
     title      — feature heading
     description — short paragraph
     tag        — small label shown on the card
   ========================================================== */
const featuresData = [
  {
    icon: "◈",
    title: "Personalised Dashboards",
    description:
      "Gender-specific content, curated wellness metrics, and continuous support tracking — all tailored to your body's unique rhythm and goals.",
    tag: "Core Experience",
  },
  {
    icon: "✦",
    title: "Appearance Intelligence",
    description:
      "Face-detection-assisted hairstyle recommendations, hijab styling guides, jewellery selection, and colour-theory-based wardrobe coaching.",
    tag: "Aesthetic Coaching",
  },
  {
    icon: "❧",
    title: "Nutrition & Gut Health",
    description:
      "Curated hydration juice blends, microbiome-supportive recipes, and meal plans designed to nourish from the inside out.",
    tag: "Preventive Health",
  },
  {
    icon: "◎",
    title: "Hydration & Activity Tracking",
    description:
      "Integrated daily water intake logging and fitness activity trackers that sync with your nutrition and wellness goals seamlessly.",
    tag: "Daily Habits",
  },
];
 
 
/* ==========================================================
   3. DUAL DASHBOARD DATA
   SWAP THIS DATA ↓
   Two keys: "women" and "men".
   Each has:
     eyebrow, headline, description, modules (array of {icon, label}),
     ctaText, ctaHref
   Also: screenTitle, stats (array of {label, value, color}),
          bars (array of {label, pct, color}) — these render the
          decorative "app screen" on the right side.
   ========================================================== */
const dashboardData = {
  women: {
    eyebrow: "Women's Module",
    headline: "<em>MenstHeal</em> — your cycle, understood",
    description:
      "A comprehensive period-tracking and PCOS/PCOD management module that translates your cycle data into actionable health insights, symptom predictions, and specialist-backed guidance.",
    modules: [
      { icon: "🌙", label: "Cycle & ovulation tracking" },
      { icon: "📊", label: "Hormone & symptom logging" },
      { icon: "💊", label: "PCOS/PCOD management plan" },
      { icon: "🥗", label: "Cycle-synced nutrition guide" },
      { icon: "🧘", label: "Mood & energy journaling" },
    ],
    ctaText: "Explore MenstHeal",
    ctaHref: LOGIN_URL,
    screenTitle: "MenstHeal Dashboard",
    stats: [
      { label: "Cycle Day", value: "14", color: "#E8C4B8" },
      { label: "Avg. Cycle", value: "28d", color: "#C9A0A8" },
    ],
    bars: [
      { label: "Hydration goal", pct: 78 },
      { label: "Symptom score", pct: 42 },
      { label: "Activity this week", pct: 60 },
    ],
  },
  men: {
    eyebrow: "Men's Module",
    headline: "<em>NicoCure</em> — break the habit, reclaim your health",
    description:
      "A behavioural support programme for nicotine and substance cessation. NicoCure combines cognitive prompts, craving logs, and milestone rewards to help you build lasting change.",
    modules: [
      { icon: "📅", label: "Daily craving & trigger log" },
      { icon: "🏆", label: "Streak milestones & rewards" },
      { icon: "🧠", label: "CBT-based behavioural prompts" },
      { icon: "💪", label: "Replacement habit builder" },
      { icon: "📈", label: "Progress & health recovery stats" },
    ],
    ctaText: "Explore NicoCure",
    ctaHref: LOGIN_URL,
    screenTitle: "NicoCure Dashboard",
    stats: [
      { label: "Days Clean", value: "31", color: "#7D9B76" },
      { label: "Cravings Logged", value: "6", color: "#B8973E" },
    ],
    bars: [
      { label: "Craving resistance", pct: 85 },
      { label: "Sleep quality", pct: 72 },
      { label: "Physical activity", pct: 55 },
    ],
  },
};
 
 
/* ==========================================================
   4. HOW IT WORKS — STEPS
   SWAP THIS DATA ↓
   Fields: step (number string), title, description
   ========================================================== */
const stepsData = [
  {
    step: "1",
    title: "Create Your Free Account",
    description:
      "Sign up securely in under two minutes. No credit card required. Your data is encrypted and never shared.",
  },
  {
    step: "2",
    title: "Complete Your Personal Profile",
    description:
      "Log your basic metrics, biological sex, lifestyle habits, and key health markers to calibrate your personalised plan.",
  },
  {
    step: "3",
    title: "Access Your Custom Dashboard",
    description:
      "Instantly unlock personalised appearance coaching, nutrition plans, cycle or cessation modules, and interactive trackers.",
  },
];
 
 
/* ==========================================================
   5. SUCCESS STORIES / TESTIMONIALS
   SWAP THIS DATA ↓
   Fields:
     quote      — the testimonial text
     name       — reviewer's name
     meta       — subtitle (location, module used, etc.)
     avatar     — emoji fallback (shown if no avatarImg)
     avatarImg  — (optional) URL to a real avatar photo
                  e.g. "images/avatars/priya.jpg"
     stars      — number 1–5
   ========================================================== */
const testimonialsData = [
  {
    quote:
      "MenstHeal genuinely changed how I understand my body. The cycle syncing with my nutrition plan meant fewer crashes and way more energy during my luteal phase.",
    name: "Priya K.",
    meta: "Mumbai · MenstHeal user",
    avatar: "🌸",
    avatarImg: "",   // SWAP → e.g. "images/avatars/priya.jpg"
    stars: 5,
  },
  {
    quote:
      "The colour-theory coaching in Appearance Intelligence sounds niche but it completely transformed how I shop. I've returned maybe two items in six months. That's a record.",
    name: "Amara O.",
    meta: "London · Appearance Intelligence",
    avatar: "✨",
    avatarImg: "",   // SWAP → e.g. "images/avatars/amara.jpg"
    stars: 5,
  },
  {
    quote:
      "NicoCure's habit-replacement builder is the only thing that's kept me smoke-free past 30 days. The milestone badges sound simple but they work. Day 47 today.",
    name: "Reuben M.",
    meta: "Nairobi · NicoCure user",
    avatar: "💪",
    avatarImg: "",   // SWAP → e.g. "images/avatars/reuben.jpg"
    stars: 5,
  },
  {
    quote:
      "I never thought I'd be logging water intake daily, but the tracker is so frictionless I barely notice. My skin and energy have genuinely improved in four weeks.",
    name: "Sofía L.",
    meta: "Barcelona · Hydration Tracker",
    avatar: "💧",
    avatarImg: "",   // SWAP → e.g. "images/avatars/sofia.jpg"
    stars: 4,
  },
  {
    quote:
      "As someone with PCOD, finding an app that actually addresses the full picture — diet, symptoms, mood — rather than just a calendar was a relief.",
    name: "Ananya R.",
    meta: "Bengaluru · MenstHeal user",
    avatar: "🌿",
    avatarImg: "",   // SWAP → e.g. "images/avatars/ananya.jpg"
    stars: 5,
  },
  {
    quote:
      "The juice blend recipes alone are worth it. I've replaced my afternoon coffee with a microbiome blend and I actually feel the difference — this is not placebo.",
    name: "Jenna T.",
    meta: "Toronto · Nutrition & Gut Health",
    avatar: "🥂",
    avatarImg: "",   // SWAP → e.g. "images/avatars/jenna.jpg"
    stars: 5,
  },
];
 
 
/* ==========================================================
   6. FOOTER QUICK LINKS — MODULES
   SWAP THIS DATA ↓
   Fields: label, href
   ========================================================== */
const footerModules = [
  { label: "MenstHeal",            href: "#dashboards" },
  { label: "NicoCure",             href: "#dashboards" },
  { label: "Appearance Studio",    href: "#features" },
  { label: "Nutrition & Gut",      href: "#features" },
  { label: "Hydration Tracker",    href: "#features" },
];
 
 
/* ==========================================================
   7. SOCIAL MEDIA LINKS
   SWAP THIS DATA ↓
   Fields: icon (emoji), label (screen-reader text), href
   ========================================================== */
const socialLinks = [
  { icon: "𝕏",  label: "Twitter / X",  href: "#" },
  { icon: "in", label: "LinkedIn",       href: "#" },
  { icon: "▶",  label: "YouTube",        href: "#" },
  { icon: "📷", label: "Instagram",      href: "#" },
];
 
 
/* ==========================================================
   END OF EDITABLE DATA SECTION
   ——————————————————————————————————————————————————————
   Rendering logic begins below. Edit with care.
   ========================================================== */
 
 
/* ----------------------------------------------------------
   RENDER: Social Proof Logos
   ---------------------------------------------------------- */
function renderMediaLogos() {
  const container = document.getElementById("proofLogos");
  if (!container) return;
 
  container.innerHTML = mediaLogos.map((logo) => {
    if (logo.logoImg) {
      return `<a href="#" class="proof-logo-item" aria-label="${logo.name}">
                <img src="${logo.logoImg}" alt="${logo.name}" height="22" />
              </a>`;
    }
    return `<span class="proof-logo-item">${logo.name}</span>`;
  }).join("");
}
 
 
/* ----------------------------------------------------------
   RENDER: Core Features Grid
   ---------------------------------------------------------- */
function renderFeatures() {
  const container = document.getElementById("featuresGrid");
  if (!container) return;
 
  container.innerHTML = featuresData.map((f) => `
    <article class="feature-card reveal">
      <div class="feature-icon" aria-hidden="true">${f.icon}</div>
      <h3>${f.title}</h3>
      <p>${f.description}</p>
      <span class="feature-tag">${f.tag}</span>
    </article>
  `).join("");
}
 
 
/* ----------------------------------------------------------
   RENDER: Dashboard Panels
   ---------------------------------------------------------- */
function renderDashboards() {
  const container = document.getElementById("dashboardPanels");
  if (!container) return;
 
  const keys = Object.keys(dashboardData);
 
  container.innerHTML = keys.map((key, i) => {
    const d = dashboardData[key];
 
    const modulesHTML = d.modules.map((m) =>
      `<div class="module-pill">
         <span class="pill-icon" aria-hidden="true">${m.icon}</span>
         ${m.label}
       </div>`
    ).join("");
 
    const statsHTML = d.stats.map((s) =>
      `<div class="screen-stat">
         <span class="stat-label">${s.label}</span>
         <span class="stat-value" style="color:${s.color}">${s.value}</span>
       </div>`
    ).join("");
 
    const barsHTML = d.bars.map((b) =>
      `<div class="screen-bar-block">
         <div class="screen-bar-label">${b.label}</div>
         <div class="screen-bar">
           <div class="screen-bar-fill" style="width:${b.pct}%"></div>
         </div>
       </div>`
    ).join("");
 
    return `
      <div class="dashboard-panel ${i === 0 ? 'active' : ''}" id="panel-${key}" role="tabpanel">
        <div class="dashboard-info">
          <span class="eyebrow">${d.eyebrow}</span>
          <h3>${d.headline}</h3>
          <p>${d.description}</p>
          <div class="dashboard-modules">${modulesHTML}</div>
          <a href="${d.ctaHref}" class="btn btn-outline-sage">${d.ctaText}</a>
        </div>
 
        <div class="dashboard-screen" aria-hidden="true">
          <div class="screen-header">
            <div class="screen-dot"></div>
            <div class="screen-dot"></div>
            <div class="screen-dot"></div>
            <span class="screen-title">${d.screenTitle}</span>
          </div>
          <div class="screen-body">
            <div class="screen-stat-row">${statsHTML}</div>
            ${barsHTML}
          </div>
        </div>
      </div>
    `;
  }).join("");
}
 
 
/* ----------------------------------------------------------
   RENDER: How It Works Steps
   ---------------------------------------------------------- */
function renderSteps() {
  const container = document.getElementById("stepsTimeline");
  if (!container) return;
 
  container.innerHTML = stepsData.map((s) => `
    <div class="step-card reveal">
      <div class="step-number" aria-hidden="true">${s.step}</div>
      <h3>${s.title}</h3>
      <p>${s.description}</p>
    </div>
  `).join("");
}
 
 
/* ----------------------------------------------------------
   RENDER: Testimonials
   ---------------------------------------------------------- */
function renderTestimonials() {
  const container = document.getElementById("testimonialsGrid");
  if (!container) return;
 
  container.innerHTML = testimonialsData.map((t) => {
    const stars = "★".repeat(t.stars) + "☆".repeat(5 - t.stars);
 
    const avatarHTML = t.avatarImg
      ? `<img src="${t.avatarImg}" alt="${t.name}" />`
      : `<span aria-hidden="true">${t.avatar}</span>`;
 
    return `
      <article class="testimonial-card reveal">
        <div class="testimonial-stars" aria-label="${t.stars} out of 5 stars">${stars}</div>
        <blockquote class="testimonial-quote">${t.quote}</blockquote>
        <div class="testimonial-author">
          <div class="author-avatar">${avatarHTML}</div>
          <div>
            <div class="author-name">${t.name}</div>
            <div class="author-meta">${t.meta}</div>
          </div>
        </div>
      </article>
    `;
  }).join("");
}
 
 
/* ----------------------------------------------------------
   RENDER: Footer Module Links
   ---------------------------------------------------------- */
function renderFooterModules() {
  const container = document.getElementById("footerModuleLinks");
  if (!container) return;
 
  container.innerHTML = footerModules.map((m) =>
    `<li><a href="${m.href}">${m.label}</a></li>`
  ).join("");
}
 
 
/* ----------------------------------------------------------
   RENDER: Footer Social Icons
   ---------------------------------------------------------- */
function renderSocialLinks() {
  const container = document.getElementById("footerSocial");
  if (!container) return;
 
  container.innerHTML = socialLinks.map((s) =>
    `<a href="${s.href}" class="social-btn" aria-label="${s.label}" rel="noopener noreferrer">${s.icon}</a>`
  ).join("");
}
 
 
/* ----------------------------------------------------------
   BEHAVIOUR: Dashboard Tab Toggle
   ---------------------------------------------------------- */
function initDashboardTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  const panels  = document.querySelectorAll(".dashboard-panel");
 
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.tab;
 
      tabBtns.forEach((b) => {
        b.classList.remove("active");
        b.setAttribute("aria-pressed", "false");
      });
      btn.classList.add("active");
      btn.setAttribute("aria-pressed", "true");
 
      panels.forEach((p) => {
        p.classList.remove("active");
        if (p.id === `panel-${target}`) {
          p.classList.add("active");
        }
      });
    });
  });
}
 
 
/* ----------------------------------------------------------
   BEHAVIOUR: Sticky Navbar Shadow
   ---------------------------------------------------------- */
function initNavbarScroll() {
  const navbar = document.getElementById("navbar");
  if (!navbar) return;
 
  const onScroll = () => {
    navbar.classList.toggle("scrolled", window.scrollY > 20);
  };
 
  window.addEventListener("scroll", onScroll, { passive: true });
}
 
 
/* ----------------------------------------------------------
   BEHAVIOUR: Mobile Hamburger Menu
   ---------------------------------------------------------- */
function initHamburger() {
  const btn   = document.getElementById("navHamburger");
  const links = document.getElementById("navLinks");
  if (!btn || !links) return;
 
  btn.addEventListener("click", () => {
    const isOpen = links.classList.toggle("nav-open");
    btn.setAttribute("aria-expanded", String(isOpen));
    document.body.style.overflow = isOpen ? "hidden" : "";
  });
 
  // Close menu when a link is clicked
  links.querySelectorAll("a").forEach((a) => {
    a.addEventListener("click", () => {
      links.classList.remove("nav-open");
      btn.setAttribute("aria-expanded", "false");
      document.body.style.overflow = "";
    });
  });
}
 
 
/* ----------------------------------------------------------
   BEHAVIOUR: Scroll-Reveal using IntersectionObserver
   ---------------------------------------------------------- */
function initScrollReveal() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12 }
  );
 
  // Observe all .reveal elements (rendered by JS above)
  const observe = () => {
    document.querySelectorAll(".reveal").forEach((el) => observer.observe(el));
  };
 
  // Run once immediately, then again shortly after JS renders DOM
  observe();
  setTimeout(observe, 100);
}
 
 
/* ----------------------------------------------------------
   BEHAVIOUR: Newsletter Form Validation
   ---------------------------------------------------------- */
function initNewsletter() {
  const form    = document.getElementById("newsletterForm");
  const input   = document.getElementById("newsletterEmail");
  const msg     = document.getElementById("newsletterMsg");
  if (!form || !input || !msg) return;
 
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const email = input.value.trim();
    const valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
 
    if (!valid) {
      msg.textContent = "Please enter a valid email address.";
      msg.className = "newsletter-msg error";
      return;
    }
 
    // SWAP THIS → replace with your real newsletter API call
    msg.textContent = "You're on the list! We'll be in touch soon.";
    msg.className = "newsletter-msg success";
    input.value = "";
  });
}
 
 
/* ----------------------------------------------------------
   UTILITY: Set Footer Copyright Year
   ---------------------------------------------------------- */
function setCurrentYear() {
  const el = document.getElementById("currentYear");
  if (el) el.textContent = new Date().getFullYear();
}
 
 
/* ----------------------------------------------------------
   INIT — Run everything once DOM is ready
   ---------------------------------------------------------- */
document.addEventListener("DOMContentLoaded", () => {
  // 1. Render all dynamic sections
  renderMediaLogos();
  renderFeatures();
  renderDashboards();
  renderSteps();
  renderTestimonials();
  renderFooterModules();
  renderSocialLinks();
  setCurrentYear();
 
  // 2. Wire up interactions
  initDashboardTabs();
  initNavbarScroll();
  initHamburger();
  initScrollReveal();
  initNewsletter();
});