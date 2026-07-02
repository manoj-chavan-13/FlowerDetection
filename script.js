// AWS FloraSense AI Frontend Controller (Robust Camera & Mobile Fallback)

let currentSelectedFile = null;
let currentImageId = null;
let pollingInterval = null;
let videoStream = null;

// DOM Elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const nativeCameraInput = document.getElementById('native-camera-input');
const uploadPrompt = document.getElementById('upload-prompt');
const filePreviewState = document.getElementById('file-preview-state');
const previewImage = document.getElementById('preview-image');
const fileNameDisplay = document.getElementById('file-name-display');
const fileSizeDisplay = document.getElementById('file-size-display');
const uploadBtn = document.getElementById('upload-btn');

// Camera Elements
const cameraContainer = document.getElementById('camera-container');
const cameraVideoState = document.getElementById('camera-video-state');
const cameraPermissionState = document.getElementById('camera-permission-state');
const liveVideo = document.getElementById('live-video');
const snapshotCanvas = document.getElementById('snapshot-canvas');
const tabFileBtn = document.getElementById('tab-file-btn');
const tabCamBtn = document.getElementById('tab-cam-btn');

// Views
const viewUpload = document.getElementById('view-upload');
const viewLoader = document.getElementById('view-loader');
const viewResults = document.getElementById('view-results');

// Initialize events on DOM load
document.addEventListener('DOMContentLoaded', () => {
    initDragAndDrop();
    initNativeCameraInput();
});

// Switch Views inside Single Card
function switchView(targetView) {
    stopCameraStream();
    viewUpload.classList.add('hidden');
    viewLoader.classList.add('hidden');
    viewResults.classList.add('hidden');
    targetView.classList.remove('hidden');
}

// Reset back to Upload Phase
function resetToUpload() {
    if (pollingInterval) clearInterval(pollingInterval);
    clearSelectedFile();
    showDropZoneMode();
    switchView(viewUpload);
}

// Mode Selection: File Upload vs Camera
function showDropZoneMode() {
    stopCameraStream();
    cameraContainer.classList.add('hidden');
    dropZone.classList.remove('hidden');
    
    tabFileBtn.className = "py-3 px-3 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-bold text-xs shadow-md shadow-emerald-500/25 flex items-center justify-center space-x-2 transition";
    tabCamBtn.className = "py-3 px-3 rounded-2xl text-slate-500 hover:text-slate-800 font-bold text-xs flex items-center justify-center space-x-2 transition";
}

async function startCameraMode() {
    dropZone.classList.add('hidden');
    cameraContainer.classList.remove('hidden');
    
    tabCamBtn.className = "py-3 px-3 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-bold text-xs shadow-md shadow-emerald-500/25 flex items-center justify-center space-x-2 transition";
    tabFileBtn.className = "py-3 px-3 rounded-2xl text-slate-500 hover:text-slate-800 font-bold text-xs flex items-center justify-center space-x-2 transition";

    // Check if getUserMedia is supported (requires HTTPS or Localhost)
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        cameraVideoState.classList.add('hidden');
        cameraPermissionState.classList.remove('hidden');
        document.getElementById('cam-perm-title').textContent = "Security Notice (HTTP Local Access)";
        document.getElementById('cam-perm-msg').textContent = "Browser security blocks live stream over non-HTTPS local IP. Please tap below to launch your phone's native camera app directly.";
        return;
    }

    try {
        videoStream = await navigator.mediaDevices.getUserMedia({ 
            video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } } 
        });
        cameraPermissionState.classList.add('hidden');
        cameraVideoState.classList.remove('hidden');
        liveVideo.srcObject = videoStream;
    } catch (err) {
        // Handle Permission Denied or Not Allowed gracefully
        cameraVideoState.classList.add('hidden');
        cameraPermissionState.classList.remove('hidden');
        document.getElementById('cam-perm-title').textContent = "Camera Access Restricted";
        document.getElementById('cam-perm-msg').textContent = "Permission denied or unavailable. Tap below to use your phone's native camera app directly.";
    }
}

function openNativePhoneCamera() {
    nativeCameraInput.click();
}

function retryCameraAccess() {
    startCameraMode();
}

function initNativeCameraInput() {
    nativeCameraInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            stopCameraMode();
            handleFileSelection(e.target.files[0]);
        }
    });
}

function stopCameraStream() {
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }
}

function stopCameraMode() {
    showDropZoneMode();
}

// Snap Photo from Video Stream
function capturePhoto() {
    if (!liveVideo.videoWidth) return;

    snapshotCanvas.width = liveVideo.videoWidth;
    snapshotCanvas.height = liveVideo.videoHeight;
    const ctx = snapshotCanvas.getContext('2d');
    ctx.drawImage(liveVideo, 0, 0, snapshotCanvas.width, snapshotCanvas.height);

    snapshotCanvas.toBlob((blob) => {
        if (!blob) return;
        const timestamp = Math.floor(Date.now() / 1000);
        const file = new File([blob], `camera_snapshot_${timestamp}.jpg`, { type: 'image/jpeg' });
        
        stopCameraStream();
        showDropZoneMode();
        handleFileSelection(file);
    }, 'image/jpeg', 0.92);
}

// Drag & Drop Setup
function initDragAndDrop() {
    dropZone.addEventListener('click', (e) => {
        if (e.target.id !== 'clear-file-btn' && !e.target.closest('#clear-file-btn')) {
            fileInput.click();
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            handleFileSelection(e.target.files[0]);
        }
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('border-emerald-500', 'bg-emerald-50/50');
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-emerald-500', 'bg-emerald-50/50');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-emerald-500', 'bg-emerald-50/50');
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileSelection(e.dataTransfer.files[0]);
        }
    });
}

// Handle File Selection & Preview
function handleFileSelection(file) {
    if (!file.type.startsWith('image/')) {
        alert('Please select a valid botanical image file (JPEG, PNG, WEBP).');
        return;
    }

    currentSelectedFile = file;
    fileNameDisplay.textContent = file.name;
    fileSizeDisplay.textContent = `${(file.size / 1024).toFixed(1)} KB`;

    const reader = new FileReader();
    reader.onload = (e) => {
        previewImage.src = e.target.result;
        uploadPrompt.classList.add('hidden');
        filePreviewState.classList.remove('hidden');
        
        uploadBtn.disabled = false;
        uploadBtn.className = "w-full py-4 px-6 rounded-2xl bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 active:brightness-95 text-white font-extrabold text-xs sm:text-sm shadow-lg shadow-emerald-600/30 transition-all duration-300 flex items-center justify-center space-x-2 cursor-pointer";
    };
    reader.readAsDataURL(file);
}

// Clear Selected File
function clearSelectedFile(e) {
    if (e) e.stopPropagation();
    currentSelectedFile = null;
    fileInput.value = '';
    nativeCameraInput.value = '';
    uploadPrompt.classList.remove('hidden');
    filePreviewState.classList.add('hidden');
    
    uploadBtn.disabled = true;
    uploadBtn.className = "w-full py-4 px-6 rounded-2xl bg-slate-200 text-slate-400 font-extrabold text-xs sm:text-sm transition-all duration-300 flex items-center justify-center space-x-2 cursor-not-allowed";
}

// Upload Image & Transition to Animated Loader Card
async function handleImageUpload() {
    if (!currentSelectedFile) return;

    switchView(viewLoader);
    
    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById('loader-preview-image').src = e.target.result;
    };
    reader.readAsDataURL(currentSelectedFile);

    updateLoaderStep('Uploading flower photo...', 'Connecting to cloud model...', 35);

    const formData = new FormData();
    formData.append('file', currentSelectedFile);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            currentImageId = data.imageId;
            updateLoaderStep('Analyzing Blooms...', 'Scanning botanical features...', 65);
            startPollingResults(data.imageId);
        } else {
            alert('Upload failed: ' + (data.error || 'Unknown error'));
            resetToUpload();
        }
    } catch (err) {
        alert('Network error during upload: ' + err.message);
        resetToUpload();
    }
}

// Update Animated Loader Text and Progress
function updateLoaderStep(title, subtitle, progressPercent) {
    document.getElementById('loader-title').textContent = title;
    document.getElementById('loader-subtitle').textContent = subtitle;
    document.getElementById('loader-bar').style.width = `${progressPercent}%`;
}

// Poll DynamoDB Table populated by AWS Lambda
function startPollingResults(imageId) {
    if (pollingInterval) clearInterval(pollingInterval);
    
    let attempts = 0;
    const maxAttempts = 30;
    
    pollingInterval = setInterval(async () => {
        attempts++;
        if (attempts === 2) {
            updateLoaderStep('Identifying Species & Counting...', 'Querying DynamoDB record...', 85);
        }

        try {
            const res = await fetch(`/api/results/${encodeURIComponent(imageId)}`);
            const data = await res.json();

            if (data.success && data.status === 'completed' && data.data) {
                clearInterval(pollingInterval);
                updateLoaderStep('Detection Verified!', 'Rendering output...', 100);
                setTimeout(() => {
                    displayAnalysisResults(data.data);
                }, 350);
            } else if (attempts >= maxAttempts) {
                updateLoaderStep('Cloud Processing Delayed', 'Still checking AWS Lambda...', 90);
            }
        } catch (err) {
            console.error('Polling error:', err);
        }
    }, 2000);
}

// Display Analysis Results in Single Card
function displayAnalysisResults(item) {
    switchView(viewResults);

    // Populate exact 4 requested output attributes
    document.getElementById('out-flower-name').textContent = item.flowerName || 'Detected Flower';
    document.getElementById('out-flower-count').textContent = item.flowerCount !== undefined ? item.flowerCount : 1;
    document.getElementById('out-confidence').textContent = `${parseFloat(item.confidence || 100.0).toFixed(1)}%`;
    document.getElementById('out-image-id').textContent = item.imageId || currentImageId;
    
    // Display the uploaded image cleanly
    const imgEl = document.getElementById('res-image-display');
    imgEl.src = `/api/image/${encodeURIComponent(item.imageId || currentImageId)}`;
}
