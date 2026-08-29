/* Skinora API client — auth + MongoDB profile sync */

(function () {
    'use strict';

    const API = window.SKINORA_API || '';

    function getToken() {
        try { return localStorage.getItem('skinoraToken'); } catch (e) { return null; }
    }

    function setToken(token) {
        try { localStorage.setItem('skinoraToken', token); } catch (e) { /* ignore */ }
    }

    function clearAuth() {
        try {
            localStorage.removeItem('skinoraToken');
            localStorage.removeItem('skinoraGender');
        } catch (e) { /* ignore */ }
    }

    function authHeaders() {
        const token = getToken();
        return token ? { Authorization: 'Bearer ' + token } : {};
    }

    async function apiFetch(path, options) {
        const res = await fetch(API + path, Object.assign({
            headers: Object.assign({ 'Content-Type': 'application/json' }, authHeaders(), (options && options.headers) || {}),
        }, options || {}));
        const data = await res.json().catch(function () { return {}; });
        if (!res.ok) {
            const err = new Error(data.detail || data.message || 'Request failed');
            err.status = res.status;
            throw err;
        }
        return data;
    }

    function dashboardPath(gender) {
        if (gender === 'female') return '/female/';
        return '/male/';
    }

    function requireAuth(loginPath) {
        loginPath = loginPath || '/login/';
        if (!getToken()) {
            window.location.replace(loginPath);
            return false;
        }
        return true;
    }

    function logout() {
        clearAuth();
        window.location.href = '/';
    }

    async function loadProfile() {
        const data = await apiFetch('/api/profile');
        return data.profile || {};
    }

    async function saveProfile(profile) {
        await apiFetch('/api/profile', {
            method: 'PUT',
            body: JSON.stringify(profile),
        });
    }

    async function fetchMe() {
        return apiFetch('/api/auth/me');
    }

    function localProfileKey(gender) {
        return gender === 'female' ? 'skinoraProfile' : 'skinoraProfileMale';
    }

    function isProfileComplete(gender, p) {
        if (!p || !p.skinType || !p.undertone || !p.age || !p.height || !p.weight) return false;
        if (gender === 'female') return !!(p.period && p.pcos);
        return !!p.smoking;
    }

    async function initDashboard(gender) {
        if (!getToken()) return;

        var justLoggedIn = false;
        try {
            justLoggedIn = sessionStorage.getItem('skinoraJustLoggedIn') === '1';
            if (justLoggedIn) sessionStorage.removeItem('skinoraJustLoggedIn');
        } catch (e) { /* ignore */ }

        try {
            var profile = await loadProfile();
            if (profile && typeof window.skProfile !== 'undefined') {
                Object.assign(window.skProfile, profile);
                window.skProfile = window.skProfile;
                try {
                    localStorage.setItem(localProfileKey(gender), JSON.stringify(window.skProfile));
                } catch (e) { /* ignore */ }
            }

            var complete = isProfileComplete(gender, window.skProfile);
            var overlay = document.getElementById('skOnboarding');

            if (complete) {
                if (overlay) overlay.classList.add('sk-hidden');
                if (typeof window.skPopulateProfile === 'function') {
                    window.skPopulateProfile();
                }
                if (justLoggedIn && typeof window.skWelcomeBack === 'function') {
                    window.skWelcomeBack();
                }
            } else if (typeof window.skShowOnboarding === 'function') {
                window.skShowOnboarding();
            }

            if (typeof window.skRunEnhancements === 'function') {
                setTimeout(window.skRunEnhancements, 200);
            }
        } catch (e) {
            console.warn('Skinora profile sync:', e);
            if (justLoggedIn && typeof window.skShowOnboarding === 'function') {
                window.skShowOnboarding();
            }
        }

        hookProfileSave();
    }

    function hookProfileSave() {
        if (window._skinoraSaveHooked) return;
        window._skinoraSaveHooked = true;

        var origEnter = window.skEnter;
        window.skEnter = function () {
            if (origEnter) origEnter();
            if (window.skProfile && getToken()) {
                saveProfile(window.skProfile).catch(function (e) {
                    console.warn('Skinora save failed:', e);
                });
            }
        };

        var origPopulate = window.skPopulateProfile;
        if (origPopulate) {
            window.skPopulateProfile = function () {
                origPopulate();
                if (window.skProfile && getToken()) {
                    saveProfile(window.skProfile).catch(function () { /* ignore */ });
                }
            };
        }
    }

    window.SkinoraAPI = {
        getToken: getToken,
        setToken: setToken,
        clearAuth: clearAuth,
        requireAuth: requireAuth,
        dashboardPath: dashboardPath,
        loadProfile: loadProfile,
        saveProfile: saveProfile,
        fetchMe: fetchMe,
        initDashboard: initDashboard,
        hookProfileSave: hookProfileSave,
        logout: logout,
        login: function (email, password) {
            return apiFetch('/api/auth/login', {
                method: 'POST',
                body: JSON.stringify({ email: email, password: password }),
            });
        },
        register: function (email, password) {
            return apiFetch('/api/auth/register', {
                method: 'POST',
                body: JSON.stringify({ email: email, password: password }),
            });
        },
        setGender: function (gender) {
            return apiFetch('/api/auth/gender', {
                method: 'PATCH',
                body: JSON.stringify({ gender: gender }),
            });
        },
    };
})();
