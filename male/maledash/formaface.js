/* FormaFace — malemodel integration for Skinora male dashboard */

const FF_API_BASE = window.FORMAFACE_API || (
    location.port === '8000' || location.pathname.startsWith('/male') ? '' : 'http://localhost:8000'
);

const ffState = {
    file: null,
    previewUrl: null,
    cameraStream: null,
    cameraActive: false,
    apiOnline: false,
    pollTimer: null,
};

function $(id) { return document.getElementById(id); }

function apiUrl(path) {
    return FF_API_BASE + path;
}

function setStatus(type, message, showProgress) {
    const el = $('ffStatus');
    if (!el) return;
    el.className = 'ff-status show ' + type;
    el.innerHTML = message + (showProgress
        ? '<div class="ff-progress"><div class="ff-progress-fill" id="ffProgressFill"></div></div>'
        : '');
}

function hideStatus() {
    const el = $('ffStatus');
    if (el) el.classList.remove('show');
}

function formatLabel(value) {
    if (!value) return '—';
    return value.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function ffStopCamera() {
    if (ffState.cameraStream) {
        ffState.cameraStream.getTracks().forEach(t => t.stop());
        ffState.cameraStream = null;
    }
    ffState.cameraActive = false;

    const wrap = $('ffUploadWrap');
    const video = $('ffCamera');
    const placeholder = $('ffUploadPlaceholder');
    const captureBtn = $('ffCaptureBtn');
    const cameraBtn = $('ffCameraBtn');

    if (wrap) wrap.classList.remove('camera-active');
    if (video) { video.style.display = 'none'; video.srcObject = null; }
    if (placeholder) placeholder.style.display = '';
    if (captureBtn) captureBtn.style.display = 'none';
    if (cameraBtn) cameraBtn.style.display = '';
}

async function ffStartCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
            audio: false,
        });
        ffState.cameraStream = stream;
        ffState.cameraActive = true;
        ffState.file = null;

        const wrap = $('ffUploadWrap');
        const video = $('ffCamera');
        const preview = $('ffPreview');
        const placeholder = $('ffUploadPlaceholder');
        const captureBtn = $('ffCaptureBtn');
        const cameraBtn = $('ffCameraBtn');
        const results = $('ffResults');

        if (preview) { preview.src = ''; preview.classList.remove('show'); }
        if (results) { results.classList.remove('show'); results.innerHTML = ''; }
        if (wrap) wrap.classList.add('camera-active');
        if (placeholder) placeholder.style.display = 'none';
        if (video) {
            video.srcObject = stream;
            video.style.display = 'block';
        }
        if (captureBtn) captureBtn.style.display = '';
        if (cameraBtn) cameraBtn.style.display = 'none';

        setStatus('ok', 'Camera on — position your face, then tap Capture.', false);
    } catch (e) {
        setStatus('error', 'Camera access denied or unavailable. Try uploading a photo instead.', false);
    }
}

function ffCaptureFromCamera() {
    const video = $('ffCamera');
    const canvas = $('ffCanvas');
    if (!video || !canvas) return;

    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0);
    ctx.setTransform(1, 0, 0, 1, 0, 0);

    canvas.toBlob(function(blob) {
        if (!blob) return;
        ffStopCamera();
        ffState.file = new File([blob], 'capture.jpg', { type: 'image/jpeg' });
        if (ffState.previewUrl) URL.revokeObjectURL(ffState.previewUrl);
        ffState.previewUrl = URL.createObjectURL(blob);
        ffShowPreview(ffState.previewUrl);
        setStatus('ok', 'Photo captured — tap Analyse My Face.', false);
    }, 'image/jpeg', 0.92);
}

function ffShowPreview(src) {
    const preview = $('ffPreview');
    const placeholder = $('ffUploadPlaceholder');
    if (!preview) return;
    preview.src = src;
    preview.classList.add('show');
    if (placeholder) placeholder.style.display = 'none';
}

function ffHandleFile(file) {
    if (!file || !file.type.startsWith('image/')) return;
    ffStopCamera();
    ffState.file = file;
    if (ffState.previewUrl) URL.revokeObjectURL(ffState.previewUrl);
    ffState.previewUrl = URL.createObjectURL(file);
    ffShowPreview(ffState.previewUrl);
    setStatus('ok', 'Photo ready — tap Analyse My Face.', false);
    const results = $('ffResults');
    if (results) { results.classList.remove('show'); results.innerHTML = ''; }
}

function renderRecSection(title, urls) {
    if (!urls || !urls.length) return '';
    const items = urls.map(url => {
        const src = url.startsWith('http') || url.startsWith('data:') ? url : apiUrl(url);
        return `<div class="ff-rec-item"><img src="${src}" alt="${title}" loading="lazy"></div>`;
    }).join('');
    return `
        <div class="ff-rec-section">
            <div class="ff-rec-title">${title}</div>
            <div class="ff-rec-grid">${items}</div>
        </div>`;
}

function syncToProfile(data) {
    if (!window.skProfile) window.skProfile = {};
    window.skProfile.formaface = {
        face_shape: data.face_shape,
        eye_shape: data.eye_shape,
        undertone: data.undertone,
        contrast: data.contrast,
    };
    window.skProfile.faceShape = data.face_shape;
    window.skProfile.eyeShape = data.eye_shape;
    window.skProfile.mlUndertone = data.undertone;
    window.skProfile.contrast = data.contrast;
    window.skProfile.formafaceScannedAt = new Date().toISOString();
    try {
        localStorage.setItem('skinoraProfileMale', JSON.stringify(window.skProfile));
    } catch (e) { /* ignore */ }
    if (typeof skRunEnhancements === 'function') skRunEnhancements();
    if (typeof skRefreshDashProfile === 'function') skRefreshDashProfile();
}

function renderResults(data) {
    const wrap = $('ffResults');
    if (!wrap) return;

    const ut = data.undertone_info || {};
    const tips = data.tips || {};
    const recs = data.recommendations || {};
    const traits = (tips.traits || []).map(t => `<span class="ff-hero-pill">${t}</span>`).join('');

    wrap.innerHTML = `
        <div class="ff-analysis-grid">
            <div class="ff-annotated-wrap">
                <img src="${data.annotated_image}" alt="Face analysis overlay">
            </div>
            <div class="ff-metrics">
                <div class="ff-metric">
                    <div class="ff-metric-label">Face Shape</div>
                    <div class="ff-metric-val">${formatLabel(data.face_shape)}</div>
                </div>
                <div class="ff-metric">
                    <div class="ff-metric-label">Eye Shape</div>
                    <div class="ff-metric-val">${formatLabel(data.eye_shape)}</div>
                </div>
                <div class="ff-metric">
                    <div class="ff-metric-label">Contrast</div>
                    <div class="ff-metric-val">${formatLabel(data.contrast)}</div>
                </div>
                <div class="ff-metric">
                    <div class="ff-metric-label">Traits</div>
                    <div class="ff-hero-pills" style="justify-content:center;margin-top:4px">${traits || '—'}</div>
                </div>
                <div class="ff-undertone-card">
                    <div class="ff-swatch" style="background:${ut.swatch || '#ccc'}"></div>
                    <div class="ff-undertone-text">
                        <h4>${ut.label || formatLabel(data.undertone)}</h4>
                        <p>${ut.undertone || ''}</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="ff-tips-grid">
            <div class="ff-tip-card"><h4>Hair</h4><p>${tips.hair || '—'}</p></div>
            <div class="ff-tip-card"><h4>Beard</h4><p>${tips.beard || '—'}</p></div>
            <div class="ff-tip-card"><h4>Outfit</h4><p>${tips.outfit || '—'}</p></div>
            <div class="ff-tip-card"><h4>Colours</h4><p>${tips.color || '—'}</p></div>
            <div class="ff-tip-card"><h4>Grooming</h4><p>${tips.grooming || '—'}</p></div>
            <div class="ff-tip-card"><h4>Style</h4><p>${tips.style || '—'}</p></div>
        </div>

        ${renderRecSection('Hairstyles', recs.hairstyles)}
        ${renderRecSection('Beard Styles', recs.beard)}
        ${renderRecSection('Outfit Colours', recs.colours)}
        ${renderRecSection('Outfit Styles', recs.outfit_style)}
        ${renderRecSection('Accessories', recs.accessories)}
    `;

    wrap.classList.add('show');
    syncToProfile(data);
}

function updateConnectionUI() {
    const el = $('ffConnection');
    if (!el) return;
    if (ffState.apiOnline) {
        el.textContent = '● FormaFace ready';
        el.className = 'ff-connection connected';
        el.hidden = false;
    } else {
        el.hidden = true;
    }
}

async function checkApi() {
    try {
        const res = await fetch(apiUrl('/api/health'));
        if (!res.ok) throw new Error('offline');
        const wasOffline = !ffState.apiOnline;
        ffState.apiOnline = true;
        updateConnectionUI();
        if (wasOffline && !ffState.file) {
            setStatus('ok', 'Backend connected — upload or take a photo to begin.', false);
        }
        return true;
    } catch {
        ffState.apiOnline = false;
        updateConnectionUI();
        return false;
    }
}

function startApiPolling() {
    checkApi();
    if (ffState.pollTimer) clearInterval(ffState.pollTimer);
    ffState.pollTimer = setInterval(checkApi, 3000);
}

async function analyze() {
    if (!ffState.file) {
        setStatus('error', 'Please upload or take a photo first.', false);
        return;
    }

    const online = await checkApi();
    if (!online) {
        setStatus('error', 'Backend not reachable yet — start it in your terminal, then try again.', false);
        return;
    }

    const analyzeBtn = $('ffAnalyzeBtn');
    if (analyzeBtn) analyzeBtn.disabled = true;

    setStatus('loading', 'Analysing your face with MediaPipe…', true);
    const progress = $('ffProgressFill');
    if (progress) progress.style.width = '35%';

    const fd = new FormData();
    fd.append('image', ffState.file);

    try {
        if (progress) progress.style.width = '65%';
        const res = await fetch(apiUrl('/api/analyze'), { method: 'POST', body: fd });
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || 'Analysis failed');
        }

        if (progress) progress.style.width = '100%';
        hideStatus();
        renderResults(data);
    } catch (err) {
        setStatus('error', err.message || 'Something went wrong. Use a clear, front-facing photo.', false);
    } finally {
        if (analyzeBtn) analyzeBtn.disabled = false;
    }
}

function resetUpload() {
    ffState.file = null;
    if (ffState.previewUrl) {
        URL.revokeObjectURL(ffState.previewUrl);
        ffState.previewUrl = null;
    }
    ffStopCamera();

    const input = $('ffFileInput');
    const preview = $('ffPreview');
    const results = $('ffResults');
    const placeholder = $('ffUploadPlaceholder');

    if (input) input.value = '';
    if (preview) { preview.src = ''; preview.classList.remove('show'); }
    if (placeholder) placeholder.style.display = '';
    if (results) { results.classList.remove('show'); results.innerHTML = ''; }
    hideStatus();
}

function init() {
    const uploadWrap = $('ffUploadWrap');
    const fileInput = $('ffFileInput');
    const cameraBtn = $('ffCameraBtn');
    const captureBtn = $('ffCaptureBtn');
    const analyzeBtn = $('ffAnalyzeBtn');
    const resetBtn = $('ffResetBtn');

    if (!uploadWrap || !fileInput) return;

    uploadWrap.addEventListener('click', function(e) {
        if (ffState.cameraActive) return;
        if (e.target.closest('video')) return;
        fileInput.click();
    });

    uploadWrap.addEventListener('dragover', e => {
        e.preventDefault();
        if (!ffState.cameraActive) uploadWrap.classList.add('dragover');
    });
    uploadWrap.addEventListener('dragleave', () => uploadWrap.classList.remove('dragover'));
    uploadWrap.addEventListener('drop', e => {
        e.preventDefault();
        uploadWrap.classList.remove('dragover');
        if (ffState.cameraActive) return;
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) ffHandleFile(file);
    });

    fileInput.addEventListener('change', e => {
        const file = e.target.files[0];
        if (file) ffHandleFile(file);
        e.target.value = '';
    });

    if (cameraBtn) cameraBtn.addEventListener('click', e => {
        e.stopPropagation();
        ffStartCamera();
    });
    if (captureBtn) captureBtn.addEventListener('click', e => {
        e.stopPropagation();
        ffCaptureFromCamera();
    });
    if (analyzeBtn) analyzeBtn.addEventListener('click', analyze);
    if (resetBtn) resetBtn.addEventListener('click', resetUpload);

    startApiPolling();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
