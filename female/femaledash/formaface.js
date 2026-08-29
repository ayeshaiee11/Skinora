/* FormaFace — OpenCV model integration for Skinora dashboard */

const FF_API_BASE = window.FORMAFACE_API || (
    location.port === '8000' || location.pathname.startsWith('/female') ? '' : 'http://localhost:8000'
);

const ffState = {
    file: null,
    previewUrl: null,
    cameraStream: null,
    cameraActive: false,
};

const FF_REC_LABELS = {
    hairstyles: 'Hairstyles',
    hijaab: 'Hijab Styles',
    outfit_styles: 'Outfit Styles',
    colours: 'Colour Palette',
    accessories: 'Accessories',
    eyeliner: 'Eyeliner',
    face_shape: 'Face Shape Guide',
    eye_shape: 'Eye Shape Guide',
};

function ffEl(id) {
    return document.getElementById(id);
}

function ffSetStatus(msg, type) {
    const el = ffEl('ffStatus');
    if (!el) return;
    el.textContent = msg;
    el.className = 'ff-status' + (type ? ' ff-status-' + type : '');
}

function ffSetProgress(show, pct, text) {
    const wrap = ffEl('ffProgress');
    const fill = ffEl('ffProgressFill');
    const label = ffEl('ffProgressText');
    if (wrap) wrap.style.display = show ? 'block' : 'none';
    if (fill) fill.style.width = (pct || 0) + '%';
    if (label && text) label.textContent = text;
}

function ffStopCamera() {
    if (ffState.cameraStream) {
        ffState.cameraStream.getTracks().forEach(function(t) { t.stop(); });
        ffState.cameraStream = null;
    }
    ffState.cameraActive = false;
    const video = ffEl('ffCamera');
    const preview = ffEl('ffPreview');
    const captureBtn = ffEl('ffCaptureBtn');
    if (video) video.style.display = 'none';
    if (preview) preview.style.display = '';
    if (captureBtn) captureBtn.style.display = 'none';
}

function ffShowPreview(src) {
    const preview = ffEl('ffPreview');
    if (!preview) return;
    preview.innerHTML = '<img src="' + src + '" alt="Preview" class="ff-preview-img">';
    preview.style.display = '';
}

function ffEnableAnalyze(enabled) {
    const btn = ffEl('ffAnalyzeBtn');
    if (btn) btn.disabled = !enabled;
}

async function ffCheckApi() {
    try {
        const res = await fetch(FF_API_BASE + '/api/health');
        if (!res.ok) throw new Error('offline');
        const data = await res.json();
        if (data.status === 'ok') {
            ffSetStatus('FormaFace API connected. Upload or capture a photo to begin.', 'ok');
            return true;
        }
    } catch (e) {
        ffSetStatus('FormaFace API offline. Start the Skinora server on port 8000.', 'error');
    }
    return false;
}

function ffHandleFile(file) {
    if (!file || !file.type.startsWith('image/')) return;
    ffStopCamera();
    ffState.file = file;
    if (ffState.previewUrl) URL.revokeObjectURL(ffState.previewUrl);
    ffState.previewUrl = URL.createObjectURL(file);
    ffShowPreview(ffState.previewUrl);
    ffEnableAnalyze(true);
    ffSetStatus('Photo ready — click Analyse Face.', 'ok');
    ffEl('ffResults').style.display = 'none';
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

        const video = ffEl('ffCamera');
        const preview = ffEl('ffPreview');
        const captureBtn = ffEl('ffCaptureBtn');
        video.srcObject = stream;
        video.style.display = 'block';
        preview.style.display = 'none';
        captureBtn.style.display = '';
        ffEnableAnalyze(false);
        ffSetStatus('Camera active — position your face and tap Capture.', 'ok');
        ffEl('ffResults').style.display = 'none';
    } catch (e) {
        ffSetStatus('Camera access denied or unavailable.', 'error');
    }
}

function ffCaptureFromCamera() {
    const video = ffEl('ffCamera');
    const canvas = ffEl('ffCanvas');
    if (!video || !canvas) return;

    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);

    canvas.toBlob(function(blob) {
        if (!blob) return;
        ffStopCamera();
        ffState.file = new File([blob], 'capture.jpg', { type: 'image/jpeg' });
        if (ffState.previewUrl) URL.revokeObjectURL(ffState.previewUrl);
        ffState.previewUrl = URL.createObjectURL(blob);
        ffShowPreview(ffState.previewUrl);
        ffEnableAnalyze(true);
        ffSetStatus('Photo captured — click Analyse Face.', 'ok');
    }, 'image/jpeg', 0.92);
}

function ffCap(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function ffRenderMetrics(data) {
    const el = ffEl('ffMetrics');
    if (!el) return;

    const items = [
        { label: 'Face Shape', value: ffCap(data.face_shape), icon: '◇' },
        { label: 'Eye Shape', value: ffCap(data.eye_shape), icon: '◎' },
        { label: 'Undertone', value: ffCap(data.undertone), icon: '◐' },
        { label: 'Contrast', value: ffCap(data.contrast), icon: '◑' },
    ];

    el.innerHTML = items.map(function(item) {
        return '<div class="ff-metric-card">' +
            '<div class="ff-metric-icon">' + item.icon + '</div>' +
            '<div class="ff-metric-label">' + item.label + '</div>' +
            '<div class="ff-metric-value">' + item.value + '</div>' +
        '</div>';
    }).join('');
}

function ffRenderTips(tips) {
    const el = ffEl('ffTips');
    if (!el || !tips) return;

    const face = tips.face_shape || {};
    const ut = tips.undertone || {};

    el.innerHTML =
        '<div class="sk3d-section-badge">✨ YOUR ANALYSIS</div>' +
        '<h3 class="sk3d-section-title">Personalised Style Insights</h3>' +
        '<div class="ff-tips-grid">' +
            '<div class="ff-tip-card"><h4>👓 Frames</h4><p>' + (face.specs || '') + '</p></div>' +
            '<div class="ff-tip-card"><h4>💇 Hair</h4><p>' + (face.hair || '') + '</p></div>' +
            '<div class="ff-tip-card"><h4>🧕 Hijab</h4><p>' + (face.hijab || '') + '</p></div>' +
            '<div class="ff-tip-card"><h4>👗 Outfit</h4><p>' + (face.outfit || '') + '</p></div>' +
            '<div class="ff-tip-card"><h4>🎨 Colours</h4><p>' + (face.color || '') + '</p></div>' +
            '<div class="ff-tip-card"><h4>✏️ Eyeliner</h4><p>' + (tips.eyeliner || '') + '</p></div>' +
            '<div class="ff-tip-card"><h4>💄 Makeup</h4><p>' + (tips.makeup || '') + '</p></div>' +
            '<div class="ff-tip-card"><h4>🌸 Skincare</h4><p>' + (tips.skin || '') + '</p></div>' +
        '</div>' +
        (ut.label ? '<div class="ff-undertone-bar"><span class="ff-undertone-swatch" style="background:' + (ut.swatch || '#ccc') + '"></span><strong>' + ut.label + '</strong> — ' + (ut.undertone || '') + '</div>' : '');
}

function ffRenderRecommendations(recs) {
    const el = ffEl('ffRecs');
    if (!el || !recs) return;

    let html = '<div class="sk3d-section-badge">🖼️ STYLE PICKS</div><h3 class="sk3d-section-title">Curated For Your Face</h3>';

    Object.keys(FF_REC_LABELS).forEach(function(key) {
        const items = recs[key] || [];
        if (!items.length) return;

        html += '<div class="ff-rec-block">' +
            '<h4>' + FF_REC_LABELS[key] + '</h4>' +
            '<div class="ff-rec-grid">' +
            items.map(function(img) {
                const src = img.url.startsWith('http') ? img.url : FF_API_BASE + img.url;
                return '<div class="ff-rec-item"><img src="' + src + '" alt="' + img.name + '"><span>' + img.name + '</span></div>';
            }).join('') +
            '</div></div>';
    });

    el.innerHTML = html;
}

function ffRenderResults(data) {
    ffRenderMetrics(data);

    const annotated = ffEl('ffAnnotated');
    if (annotated && data.annotated) annotated.src = data.annotated;

    ffRenderTips(data.tips);
    ffRenderRecommendations(data.recommendations);

    ffEl('ffResults').style.display = 'block';
    ffEl('ffResults').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function ffAnalyze() {
    if (!ffState.file) {
        ffSetStatus('Please upload or capture a photo first.', 'error');
        return;
    }

    const analyzeBtn = ffEl('ffAnalyzeBtn');
    if (analyzeBtn) analyzeBtn.disabled = true;

    ffSetProgress(true, 10, 'Uploading photo…');
    ffSetStatus('Analysing your face with OpenCV + MediaPipe…', '');

    const form = new FormData();
    form.append('image', ffState.file);

    try {
        ffSetProgress(true, 40, 'Detecting landmarks…');
        const res = await fetch(FF_API_BASE + '/api/analyze/female', { method: 'POST', body: form });
        const data = await res.json();

        ffSetProgress(true, 90, 'Building recommendations…');

        if (!res.ok) {
            throw new Error(data.error || 'Analysis failed.');
        }

        ffSetProgress(true, 100, 'Done!');
        ffSetStatus('Analysis complete ✨', 'ok');
        ffRenderResults(data);

        if (window.skProfile) {
            window.skProfile.formaface = {
                face_shape: data.face_shape,
                eye_shape: data.eye_shape,
                undertone: data.undertone,
                contrast: data.contrast,
            };
            try {
                localStorage.setItem('skinoraProfile', JSON.stringify(window.skProfile));
                if (window.SkinoraAPI && window.SkinoraAPI.getToken()) {
                    window.SkinoraAPI.saveProfile(window.skProfile).catch(function () {});
                }
            } catch (e) { /* ignore */ }
        }
    } catch (e) {
        ffSetStatus(e.message || 'Could not reach FormaFace API.', 'error');
    } finally {
        setTimeout(function() { ffSetProgress(false, 0, ''); }, 600);
        if (analyzeBtn) analyzeBtn.disabled = !ffState.file;
    }
}

function ffInitFormaFace() {
    const uploadBtn = ffEl('ffUploadBtn');
    const cameraBtn = ffEl('ffCameraBtn');
    const captureBtn = ffEl('ffCaptureBtn');
    const analyzeBtn = ffEl('ffAnalyzeBtn');
    const fileInput = ffEl('ffPhotoInput');

    if (!uploadBtn) return;

    uploadBtn.addEventListener('click', function() { fileInput.click(); });
    cameraBtn.addEventListener('click', ffStartCamera);
    captureBtn.addEventListener('click', ffCaptureFromCamera);
    analyzeBtn.addEventListener('click', ffAnalyze);

    fileInput.addEventListener('change', function(e) {
        const file = e.target.files && e.target.files[0];
        if (file) ffHandleFile(file);
        e.target.value = '';
    });

    ffCheckApi();
}

document.addEventListener('DOMContentLoaded', ffInitFormaFace);
