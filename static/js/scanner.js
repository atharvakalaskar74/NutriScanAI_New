/**
 * NutriScan AI — Scanner Module
 * Camera streaming, file uploading, AI scanning, interactive weight recalculation, and meal saving.
 */

let activeStream = null;
let currentBlob = null;
let currentScanData = null;

// DOM Elements
const videoEl = document.getElementById("camera-video");
const previewImg = document.getElementById("preview-image");
const placeholderEl = document.getElementById("viewport-placeholder");
const overlayEl = document.getElementById("scanner-overlay");
const scanBeamEl = document.getElementById("scan-beam");
const cameraControls = document.getElementById("camera-controls");
const analysisActions = document.getElementById("analysis-actions");
const scanningStatus = document.getElementById("scanning-status");
const rejectionBox = document.getElementById("rejection-box");
const rejectionText = document.getElementById("rejection-reason-text");
const resultsBox = document.getElementById("results-box");
const foodItemsContainer = document.getElementById("food-items-container");
const fileInput = document.getElementById("file-input");

// Buttons
const btnOpenCamera = document.getElementById("btn-open-camera");
const btnTriggerUpload = document.getElementById("btn-trigger-upload");
const btnCapture = document.getElementById("btn-capture");
const btnCloseCamera = document.getElementById("btn-close-camera");
const btnAnalyze = document.getElementById("btn-analyze");
const btnRetake = document.getElementById("btn-retake");
const btnSaveMeal = document.getElementById("btn-save-meal");

// --- Camera Handling ---

async function startCamera() {
    stopCamera();
    hideResults();

    try {
        const constraints = {
            video: {
                facingMode: { ideal: "environment" },
                width: { ideal: 1280 },
                height: { ideal: 720 }
            },
            audio: false
        };

        activeStream = await navigator.mediaDevices.getUserMedia(constraints);
        videoEl.srcObject = activeStream;
        videoEl.style.display = "block";
        previewImg.style.display = "none";
        placeholderEl.style.display = "none";
        overlayEl.style.display = "flex";
        cameraControls.style.display = "flex";
        analysisActions.style.display = "none";
    } catch (err) {
        console.error("Camera access error:", err);
        alert("Camera permission denied or camera device not available. You can upload an image file instead.");
        stopCamera();
    }
}

function stopCamera() {
    if (activeStream) {
        activeStream.getTracks().forEach(track => track.stop());
        activeStream = null;
    }
    videoEl.style.display = "none";
    cameraControls.style.display = "none";
    overlayEl.style.display = "none";
}

function captureFrame() {
    if (!videoEl || !videoEl.videoWidth) return;

    const canvas = document.createElement("canvas");
    canvas.width = videoEl.videoWidth;
    canvas.height = videoEl.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
        currentBlob = blob;
        const imageUrl = URL.createObjectURL(blob);
        previewImg.src = imageUrl;
        previewImg.style.display = "block";

        stopCamera();
        analysisActions.style.display = "block";
    }, "image/jpeg", 0.92);
}

// --- File Upload Handling ---

function handleFileSelect(file) {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
        alert("Please select a valid image file (JPG, PNG, WEBP).");
        return;
    }

    stopCamera();
    hideResults();

    currentBlob = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImg.src = e.target.result;
        previewImg.style.display = "block";
        placeholderEl.style.display = "none";
        overlayEl.style.display = "none";
        analysisActions.style.display = "block";
    };
    reader.readAsDataURL(file);
}

// --- AI Analysis Execution ---

async function runAnalysis() {
    if (!currentBlob) {
        alert("No food image selected. Please capture or upload a picture first.");
        return;
    }

    hideResults();
    analysisActions.style.display = "none";
    scanningStatus.style.display = "block";
    overlayEl.style.display = "flex";
    scanBeamEl.style.display = "block";

    const formData = new FormData();
    formData.append("image", currentBlob, "scan.jpg");

    try {
        const resp = await fetch("/api/scan", {
            method: "POST",
            body: formData
        });

        const data = await resp.json();
        scanningStatus.style.display = "none";
        scanBeamEl.style.display = "none";
        analysisActions.style.display = "block";

        if (!data.success) {
            alert(data.message || "Failed to analyze image. Please try again.");
            return;
        }

        // STEP 1: Food vs Non-Food Check
        if (data.is_food === false) {
            showRejection(data.rejection_reason || "This image does not appear to contain food. Please point your camera at an edible food item.");
            return;
        }

        // STEP 2: Food Detected
        currentScanData = data;
        showFoodResults(data);

    } catch (err) {
        console.error("Analysis network error:", err);
        scanningStatus.style.display = "none";
        scanBeamEl.style.display = "none";
        analysisActions.style.display = "block";
        alert("Network or server error during scanning: " + err.message);
    }
}

function showRejection(reason) {
    rejectionText.textContent = reason;
    rejectionBox.style.display = "block";
    resultsBox.style.display = "none";
}

function hideResults() {
    rejectionBox.style.display = "none";
    resultsBox.style.display = "none";
}

// --- Render Food Results & Interactive Weight Adjustment ---

function showFoodResults(data) {
    rejectionBox.style.display = "none";
    resultsBox.style.display = "block";

    const confidencePct = Math.round((data.confidence || 0.9) * 100);
    document.getElementById("detection-confidence").textContent = `${confidencePct}% AI Confidence`;

    renderFoodItems(data.foods);
    updateTotalsUI(data.totals);
}

function renderFoodItems(foods) {
    foodItemsContainer.innerHTML = "";

    foods.forEach((item, index) => {
        const scaled = item.scaled_nutrition;
        const sourceBadgeClass = item.source === "local_db" ? "badge-source-db" : "badge-source-ai";
        const sourceLabel = item.source === "local_db" ? "Verified Nutrition" : "AI Estimated";

        const card = document.createElement("div");
        card.className = "card";
        card.style.background = "rgba(11, 17, 32, 0.6)";
        card.style.border = "1px solid var(--border-color)";
        card.style.padding = "1.25rem";

        card.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.75rem;">
                <div>
                    <h4 style="font-size: 1.15rem; color: var(--text-main); margin-bottom: 0.2rem;">${item.name}</h4>
                    <span class="badge ${sourceBadgeClass}">${sourceLabel}</span>
                    <span style="font-size: 0.8rem; color: var(--text-dim); margin-left: 0.5rem;">${item.serving_description || ''}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <label style="font-size: 0.85rem; color: var(--text-muted); font-weight: 500;">Serving Weight:</label>
                    <div style="display: flex; align-items: center; background: rgba(0,0,0,0.4); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 0.2rem 0.5rem;">
                        <input type="number" 
                               class="item-weight-input" 
                               data-index="${index}" 
                               value="${Math.round(item.estimated_weight_g)}" 
                               min="5" max="2500" step="5" 
                               style="width: 70px; background: transparent; border: none; color: var(--text-main); font-size: 1rem; font-weight: 700; text-align: right; outline: none;">
                        <span style="color: var(--text-dim); font-size: 0.85rem; margin-left: 0.3rem;">g</span>
                    </div>
                </div>
            </div>

            <!-- Scaled Nutrition Badges for this item -->
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; text-align: center; background: rgba(255,255,255,0.02); padding: 0.6rem; border-radius: var(--radius-sm);">
                <div>
                    <div id="item-${index}-cal" style="font-weight: 700; color: var(--primary-light); font-size: 1rem;">${Math.round(scaled.calories)} kcal</div>
                    <div style="font-size: 0.7rem; color: var(--text-dim);">Calories</div>
                </div>
                <div>
                    <div id="item-${index}-pro" style="font-weight: 700; color: var(--accent-blue); font-size: 1rem;">${scaled.protein_g}g</div>
                    <div style="font-size: 0.7rem; color: var(--text-dim);">Protein</div>
                </div>
                <div>
                    <div id="item-${index}-carb" style="font-weight: 700; color: var(--accent-amber); font-size: 1rem;">${scaled.carbs_g}g</div>
                    <div style="font-size: 0.7rem; color: var(--text-dim);">Carbs</div>
                </div>
                <div>
                    <div id="item-${index}-fat" style="font-weight: 700; color: #f43f5e; font-size: 1rem;">${scaled.fat_g}g</div>
                    <div style="font-size: 0.7rem; color: var(--text-dim);">Fat</div>
                </div>
            </div>
        `;

        foodItemsContainer.appendChild(card);
    });

    // Attach real-time weight change listeners
    document.querySelectorAll(".item-weight-input").forEach(input => {
        input.addEventListener("input", onWeightChange);
    });
}

// When user changes weight of an item
async function onWeightChange(e) {
    const index = parseInt(e.target.dataset.index, 10);
    const newWeight = parseFloat(e.target.value) || 0;

    if (!currentScanData || !currentScanData.foods[index]) return;

    // Update weight in client state
    currentScanData.foods[index].estimated_weight_g = newWeight;
    currentScanData.foods[index].weight_g = newWeight;

    // Request recalculation from backend nutrition service
    try {
        const payload = {
            items: currentScanData.foods.map(f => ({
                food_id: f.food_id,
                name: f.name,
                weight_g: f.estimated_weight_g,
                source: f.source,
                nutrition_per_100g: f.nutrition_per_100g
            }))
        };

        const resp = await fetch("/api/nutrition/recalculate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const resData = await resp.json();
        if (resData.success) {
            // Update individual item displays
            resData.items.forEach((item, idx) => {
                const s = item.scaled_nutrition;
                const calEl = document.getElementById(`item-${idx}-cal`);
                const proEl = document.getElementById(`item-${idx}-pro`);
                const carbEl = document.getElementById(`item-${idx}-carb`);
                const fatEl = document.getElementById(`item-${idx}-fat`);

                if (calEl) calEl.textContent = `${Math.round(s.calories)} kcal`;
                if (proEl) proEl.textContent = `${s.protein_g}g`;
                if (carbEl) carbEl.textContent = `${s.carbs_g}g`;
                if (fatEl) fatEl.textContent = `${s.fat_g}g`;

                // Update state
                currentScanData.foods[idx].scaled_nutrition = s;
            });

            // Update grand totals
            updateTotalsUI(resData.totals);
            currentScanData.totals = resData.totals;
        }
    } catch (err) {
        console.error("Recalculation error:", err);
    }
}

function updateTotalsUI(totals) {
    if (!totals) return;
    document.getElementById("total-calories-val").textContent = Math.round(totals.calories || 0);
    document.getElementById("total-protein-val").textContent = `${totals.protein_g || 0}g`;
    document.getElementById("total-carbs-val").textContent = `${totals.carbs_g || 0}g`;
    document.getElementById("total-fat-val").textContent = `${totals.fat_g || 0}g`;
    document.getElementById("total-fiber-val").textContent = `${totals.fiber_g || 0}g`;
    document.getElementById("total-sugar-val").textContent = `${totals.sugar_g || 0}g`;
}

// --- Save Meal ---

async function saveMeal() {
    if (!currentScanData || !currentScanData.foods || !currentScanData.foods.length) {
        alert("No analyzed food available to save.");
        return;
    }

    const mealType = document.getElementById("save-meal-type").value;
    const notes = document.getElementById("save-meal-notes").value;

    const payload = {
        meal_type: mealType,
        notes: notes,
        image_url: currentScanData.image_url,
        items: currentScanData.foods.map(f => ({
            food_name: f.name,
            food_id: f.food_id,
            weight_g: f.estimated_weight_g,
            calories: f.scaled_nutrition.calories,
            protein_g: f.scaled_nutrition.protein_g,
            carbs_g: f.scaled_nutrition.carbs_g,
            fat_g: f.scaled_nutrition.fat_g,
            fiber_g: f.scaled_nutrition.fiber_g,
            sugar_g: f.scaled_nutrition.sugar_g,
            source: f.source
        }))
    };

    btnSaveMeal.disabled = true;
    btnSaveMeal.textContent = "Saving Meal...";

    try {
        const resp = await fetch("/api/meals", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const res = await resp.json();
        btnSaveMeal.disabled = false;
        btnSaveMeal.textContent = "✅ Save Meal to Log";

        if (res.success) {
            alert("Meal successfully logged to your daily tracker!");
            window.location.href = "/dashboard";
        } else {
            alert(res.message || "Failed to save meal.");
        }
    } catch (err) {
        btnSaveMeal.disabled = false;
        btnSaveMeal.textContent = "✅ Save Meal to Log";
        alert("Network error saving meal: " + err.message);
    }
}

// --- Event Listeners Setup ---

if (btnOpenCamera) btnOpenCamera.addEventListener("click", startCamera);
if (btnCloseCamera) btnCloseCamera.addEventListener("click", stopCamera);
if (btnCapture) btnCapture.addEventListener("click", captureFrame);

if (btnTriggerUpload) {
    btnTriggerUpload.addEventListener("click", () => fileInput.click());
}

if (fileInput) {
    fileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files[0]) {
            handleFileSelect(e.target.files[0]);
        }
    });
}

if (btnAnalyze) btnAnalyze.addEventListener("click", runAnalysis);
if (btnRetake) {
    btnRetake.addEventListener("click", () => {
        previewImg.style.display = "none";
        analysisActions.style.display = "none";
        hideResults();
        startCamera();
    });
}

if (btnSaveMeal) btnSaveMeal.addEventListener("click", saveMeal);
