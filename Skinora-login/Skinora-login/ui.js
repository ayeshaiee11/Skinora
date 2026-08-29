/* ═══════════════════════════════════════════════════════════════════
   SKINORA — ui.js
   Login / register → gender → dashboard redirect (MongoDB API)
════════════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  var SITE_BASE = (location.port === '8000') ? '' : 'http://localhost:8000';
  var API_BASE = window.SKINORA_API || SITE_BASE;

  function apiFetch(path, options) {
    return fetch(API_BASE + path, Object.assign({
      headers: { 'Content-Type': 'application/json' },
    }, options || {})).then(function (res) {
      return res.json().then(function (data) {
        if (!res.ok) {
          var err = new Error(data.detail || 'Request failed');
          err.status = res.status;
          throw err;
        }
        return data;
      });
    });
  }

  function saveToken(token) {
    try { localStorage.setItem('skinoraToken', token); } catch (e) { /* ignore */ }
  }

  function dashboardUrl(gender) {
    var base = SITE_BASE;
    if (gender === 'female') return base + '/female/';
    if (gender === 'male') return base + '/male/';
    return base + '/male/';
  }

  function markFreshLogin() {
    try { sessionStorage.setItem('skinoraJustLoggedIn', '1'); } catch (e) { /* ignore */ }
  }

  function redirectToDashboard(gender) {
    try { localStorage.setItem('skinoraGender', gender || 'male'); } catch (e) { /* ignore */ }
    markFreshLogin();
    window.location.href = dashboardUrl(gender);
  }

  /* ── Password toggle ── */
  var pwInput  = document.getElementById('password-input');
  var pwToggle = document.getElementById('pw-toggle');
  var pwIcon   = document.getElementById('pw-icon');

  pwToggle.addEventListener('click', function () {
    var isHidden     = pwInput.type === 'password';
    pwInput.type     = isHidden ? 'text' : 'password';
    pwIcon.className = isHidden ? 'fa-regular fa-eye-slash' : 'fa-regular fa-eye';
  });

  /* ── 3D card tilt ── */
  var card     = document.getElementById('login-card');
  var MAX_TILT = 10;
  var targetRX = 0, targetRY = 0, currentRX = 0, currentRY = 0;

  function lerp(a, b, t) { return a + (b - a) * t; }

  card.addEventListener('mousemove', function (e) {
    var rect = card.getBoundingClientRect();
    var cx   = rect.left + rect.width  / 2;
    var cy   = rect.top  + rect.height / 2;
    var dx   = (e.clientX - cx) / (rect.width  / 2);
    var dy   = (e.clientY - cy) / (rect.height / 2);
    targetRY =  dx * MAX_TILT;
    targetRX = -dy * MAX_TILT * 0.65;
  });

  card.addEventListener('mouseleave', function () {
    targetRX = 0;
    targetRY = 0;
  });

  (function tiltLoop() {
    currentRX = lerp(currentRX, targetRX, 0.10);
    currentRY = lerp(currentRY, targetRY, 0.10);
    card.style.transform =
      'perspective(900px) rotateX(' + currentRX + 'deg) rotateY(' + currentRY + 'deg)';
    requestAnimationFrame(tiltLoop);
  })();

  /* ── Gender modal ── */
  var genderOverlay = document.getElementById('gender-overlay');
  var optFemale     = document.getElementById('opt-female');
  var optMale       = document.getElementById('opt-male');
  var genderSkip    = document.getElementById('gender-skip');
  var btnContinue   = document.getElementById('btn-gender-continue');

  var selectedGender = null;
  var pendingToken   = null;

  function openGenderModal() {
    genderOverlay.classList.add('is-visible');
    setTimeout(function () { optFemale.focus(); }, 80);
  }

  function closeGenderModal() {
    genderOverlay.classList.remove('is-visible');
  }

  function selectGender(gender) {
    selectedGender = gender;
    [optFemale, optMale].forEach(function (btn) {
      var isThis = btn.dataset.gender === gender;
      btn.classList.toggle('is-selected', isThis);
      btn.setAttribute('aria-pressed', isThis ? 'true' : 'false');
    });
    btnContinue.disabled = false;
  }

  optFemale.addEventListener('click', function () { selectGender('female'); });
  optMale.addEventListener('click', function () { selectGender('male'); });

  genderSkip.addEventListener('click', function () {
    selectedGender = 'skip';
    proceedAfterGender();
  });

  btnContinue.addEventListener('click', function () {
    if (!selectedGender) return;
    proceedAfterGender();
  });

  function proceedAfterGender() {
    var gender = selectedGender || 'skip';
    btnContinue.textContent = 'Opening your dashboard…';
    btnContinue.disabled = true;

    apiFetch('/api/auth/gender', {
      method: 'PATCH',
      headers: { Authorization: 'Bearer ' + pendingToken },
      body: JSON.stringify({ gender: gender }),
    }).then(function () {
      redirectToDashboard(gender === 'skip' ? 'male' : gender);
    }).catch(function () {
      redirectToDashboard(gender === 'female' ? 'female' : 'male');
    });
  }

  genderOverlay.addEventListener('click', function (e) {
    if (e.target === genderOverlay) closeGenderModal();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && genderOverlay.classList.contains('is-visible')) {
      closeGenderModal();
    }
  });

  /* ── Login / Register ── */
  var loginBtn      = document.getElementById('login-btn');
  var emailInput    = document.getElementById('email-input');
  var passwordInput = document.getElementById('password-input');
  var signinLabel   = document.querySelector('.signin-label');
  var cardTitle     = document.querySelector('.card-header-custom h1');
  var footerLink    = document.querySelector('.card-footer-custom a');
  var footerText    = document.querySelector('.card-footer-custom p');

  var isRegisterMode = false;
  var BTN_GRADIENT_ERROR = 'linear-gradient(135deg, #B0A59A 0%, #979E8D 100%)';

  function resetLoginButton() {
    loginBtn.textContent   = isRegisterMode ? 'Create Account' : 'Log In';
    loginBtn.style.background = '';
    loginBtn.disabled      = false;
    loginBtn.style.opacity = '1';
  }

  function setRegisterMode(on) {
    isRegisterMode = on;
    if (signinLabel) signinLabel.textContent = on ? 'Join Skinora' : 'Welcome Back';
    if (cardTitle) cardTitle.textContent = on ? 'Sign Up' : 'Sign In';
    if (footerText) {
      footerText.innerHTML = on
        ? 'Already have an account? <a href="#" id="toggle-auth">Log in</a>'
        : 'Don\'t have an account? <a href="#" id="toggle-auth">Create one</a>';
      bindAuthToggle();
    }
    resetLoginButton();
  }

  function bindAuthToggle() {
    var toggle = document.getElementById('toggle-auth');
    if (toggle) {
      toggle.addEventListener('click', function (e) {
        e.preventDefault();
        setRegisterMode(!isRegisterMode);
      });
    }
  }

  bindAuthToggle();

  /* Hint when opened via Live Server instead of port 8000 */
  if (location.port && location.port !== '8000') {
    var hint = document.getElementById('server-hint');
    if (hint) hint.classList.add('show');
  }

  function handleAuthSuccess(data) {
    pendingToken = data.access_token;
    saveToken(data.access_token);
    markFreshLogin();

    loginBtn.textContent = 'Authenticated  ✦';
    loginBtn.style.background = 'linear-gradient(135deg, #727C6C 0%, #979E8D 100%)';

    setTimeout(function () {
      var gender = data.user && data.user.gender;
      if (gender === 'female' || gender === 'male') {
        redirectToDashboard(gender);
      } else {
        resetLoginButton();
        openGenderModal();
      }
    }, 600);
  }

  function attemptLogin() {
    var email = emailInput.value.trim();
    var pass  = passwordInput.value;

    if (!email || !pass) {
      loginBtn.textContent = 'Enter email & password';
      loginBtn.style.background = BTN_GRADIENT_ERROR;
      if (!email && emailInput) emailInput.focus();
      else if (passwordInput) passwordInput.focus();
      setTimeout(resetLoginButton, 2200);
      return;
    }

    if (isRegisterMode && pass.length < 6) {
      loginBtn.textContent = 'Password min 6 chars';
      loginBtn.style.background = BTN_GRADIENT_ERROR;
      setTimeout(resetLoginButton, 2200);
      return;
    }

    loginBtn.textContent   = isRegisterMode ? 'Creating account…' : 'Authenticating…';
    loginBtn.disabled      = true;
    loginBtn.style.opacity = '0.75';

    var path = isRegisterMode ? '/api/auth/register' : '/api/auth/login';

    apiFetch(path, {
      method: 'POST',
      body: JSON.stringify({ email: email, password: pass }),
    }).then(handleAuthSuccess).catch(function (err) {
      var msg = err.message || 'Login failed';
      if (msg === 'Failed to fetch') {
        msg = 'Server offline — run START-SERVER.bat';
      }
      loginBtn.textContent = msg.slice(0, 42);
      loginBtn.style.background = BTN_GRADIENT_ERROR;
      loginBtn.disabled = false;
      loginBtn.style.opacity = '1';
      setTimeout(resetLoginButton, 3200);
    });
  }

  loginBtn.addEventListener('click', attemptLogin);

  [emailInput, passwordInput].forEach(function (field) {
    field.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') attemptLogin();
    });
  });


})();
