/* ======================================
   SOC Lite – CSV Upload Controller
   ====================================== */

const API_BASE = window.location.origin;

let selectedFile = null;

// DOM Elements
const fileInput = document.getElementById("fileInput");
const uploadArea = document.getElementById("uploadArea");
const fileInfo = document.getElementById("fileInfo");
const fileNameSpan = document.getElementById("fileName");
const progressSection = document.getElementById("analysisProgress");
const progressFill = document.getElementById("progressFill");
const progressText = document.getElementById("progressText");
const viewDashboardSection = document.getElementById("viewDashboardSection");

// ==============================
// Drag & Drop Support
// ==============================

uploadArea.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadArea.classList.add("drag-over");
});

uploadArea.addEventListener("dragleave", () => {
    uploadArea.classList.remove("drag-over");
});

uploadArea.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadArea.classList.remove("drag-over");

    if (e.dataTransfer.files.length > 0) {
        selectedFile = e.dataTransfer.files[0];
        fileInput.files = e.dataTransfer.files;
        showFileInfo();
    }
});

fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
        selectedFile = fileInput.files[0];
        showFileInfo();
    }
});

function showFileInfo() {
    if (!selectedFile) return;
    fileNameSpan.textContent = selectedFile.name;
    fileInfo.style.display = "block";
}

// ==============================
// ANALYZE FILE
// ==============================

async function analyzeFile() {

    if (!selectedFile) {
        alert("Please select a CSV file.");
        return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    progressSection.style.display = "block";
    progressFill.style.width = "20%";
    progressText.textContent = "Uploading file...";

    try {

        const response = await fetch(`${API_BASE}/analyze/csv`, {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error("Server error");
        }

        progressFill.style.width = "60%";
        progressText.textContent = "Analyzing with AI model...";

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || "Analysis failed");
        }

        progressFill.style.width = "100%";
        progressText.textContent = "Analysis complete.";

        // 🔥 IMPORTANT: Backend already stores this in memory
        // We do NOT rely on localStorage anymore

        // Show dashboard button
        viewDashboardSection.style.display = "block";

    } catch (error) {
        console.error("Analysis error:", error);
        alert("Backend not running or CSV invalid.");
        progressSection.style.display = "none";
    }
}

// ==============================
// Redirect to Dashboard
// ==============================

function goToDashboard() {
    window.location.href = "dashboard.html";
}