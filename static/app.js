// SOCRATICA CLIENT LOGIC

// Global state
let currentChart = null;
let lastRequestData = null;

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
    // Initialise Lucide icons
    if (window.lucide) {
        window.lucide.createIcons();
    }
    
    // Setup Navigation Tabs
    setupNavigation();
    
    // Setup Form Submissions
    setupForm();
    
    // Load historical sessions & analytics on start
    refreshData();
});

// Navigation Handling
function setupNavigation() {
    const navWorkspace = document.getElementById("btn-nav-workspace");
    const navAnalytics = document.getElementById("btn-nav-analytics");
    const navHistory = document.getElementById("btn-nav-history");
    
    const viewWorkspace = document.getElementById("view-workspace");
    const viewAnalytics = document.getElementById("view-analytics");
    const viewHistory = document.getElementById("view-history");
    
    const navLinks = [navWorkspace, navAnalytics, navHistory];
    const views = [viewWorkspace, viewAnalytics, viewHistory];
    
    function switchTab(targetIndex) {
        navLinks.forEach((link, idx) => {
            if (idx === targetIndex) {
                link.classList.add("active");
                views[idx].classList.add("active");
            } else {
                link.classList.remove("active");
                views[idx].classList.remove("active");
            }
        });
        
        // Refresh when tabs change to keep charts up to date
        if (targetIndex === 1 || targetIndex === 2) {
            refreshData();
        }
    }
    
    navWorkspace.addEventListener("click", (e) => { e.preventDefault(); switchTab(0); });
    navAnalytics.addEventListener("click", (e) => { e.preventDefault(); switchTab(1); });
    navHistory.addEventListener("click", (e) => { e.preventDefault(); switchTab(2); });
    
    // Deep linking via hash
    const hash = window.location.hash;
    if (hash === "#analytics") switchTab(1);
    if (hash === "#history") switchTab(2);
}

// Form Handling
function setupForm() {
    const form = document.getElementById("predict-form");
    const btnSubmit = document.getElementById("btn-submit");
    const btnLoader = document.getElementById("btn-loader");
    const btnRegenerate = document.getElementById("btn-regenerate");
    
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const field = document.getElementById("field-select").value;
        const problem_text = document.getElementById("problem-text").value;
        const use_ai = document.getElementById("toggle-use-ai").checked;
        const selected_model = document.querySelector('input[name="selected_model"]:checked').value;
        
        lastRequestData = { field, problem_text, use_ai, selected_model };
        
        await runAnalysis(lastRequestData);
    });
    
    btnRegenerate.addEventListener("click", async () => {
        if (!lastRequestData) return;
        
        // Read latest state of toggle & selected model (they might have changed before click)
        lastRequestData.use_ai = document.getElementById("toggle-use-ai").checked;
        lastRequestData.selected_model = document.querySelector('input[name="selected_model"]:checked').value;
        
        // Show local loading state on feedback card only, keep scores visible
        const feedbackBody = document.getElementById("feedback-text");
        feedbackBody.innerHTML = `
            <div style="display: flex; align-items: center; gap: 0.75rem; color: var(--color-text-light); padding: 1.5rem 0;">
                <span class="loader-spinner" style="border-top-color: var(--color-primary);"></span>
                <span>Regenerating response based on ${lastRequestData.selected_model} guidance...</span>
            </div>
        `;
        
        try {
            const response = await fetch("/predict", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(lastRequestData)
            });
            
            if (!response.ok) throw new Error("Server error");
            const data = await response.json();
            
            // Re-render only response block
            renderResponse(data.response);
        } catch (err) {
            console.error(err);
            feedbackBody.innerHTML = `<p style="color: var(--color-frustrated)">Failed to regenerate response. Please try again.</p>`;
        }
    });
}

// Running Predict API
async function runAnalysis(reqData) {
    const btnSubmit = document.getElementById("btn-submit");
    const btnLoader = document.getElementById("btn-loader");
    
    // Loading state ON
    btnSubmit.disabled = true;
    btnLoader.classList.remove("hidden");
    
    try {
        const response = await fetch("/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(reqData)
        });
        
        if (!response.ok) {
            const errBody = await response.json();
            throw new Error(errBody.detail || "Prediction failed");
        }
        
        const data = await response.json();
        
        // Display Results
        document.getElementById("results-empty").classList.add("hidden");
        document.getElementById("results-content").classList.remove("hidden");
        
        // 1. Render Response text
        renderResponse(data.response);
        
        // 2. Render Model A (RoBERTa)
        renderModelResults("model-a", data.model_a);
        
        // 3. Render Model B (BiLSTM)
        renderModelResults("model-b", data.model_b);
        
        // Refresh underlying datasets in background
        refreshData();
        
    } catch (err) {
        console.error(err);
        alert(`Error: ${err.message}`);
    } finally {
        // Loading state OFF
        btnSubmit.disabled = false;
        btnLoader.classList.add("hidden");
    }
}

// Format markdown paragraphs
function renderResponse(text) {
    const body = document.getElementById("feedback-text");
    if (!text) {
        body.innerHTML = "<p>No response generated.</p>";
        return;
    }
    
    // Parse response line breaks and simple styling
    const paragraphs = text.split("\n\n");
    let html = "";
    paragraphs.forEach(p => {
        p = p.trim();
        if (!p) return;
        
        // Render headers if starts with ### or ##
        if (p.startsWith("###")) {
            html += `<h3>${p.replace("###", "").trim()}</h3>`;
        } else if (p.startsWith("##")) {
            html += `<h3>${p.replace("##", "").trim()}</h3>`;
        }
        // Render lists
        else if (p.startsWith("-") || p.startsWith("*")) {
            const items = p.split(/\n[-*]/);
            html += "<ul>";
            items.forEach(item => {
                const cleaned = item.replace(/^[-*\s]+/, "").trim();
                if (cleaned) html += `<li>${cleaned}</li>`;
            });
            html += "</ul>";
        }
        // Normal paragraph
        else {
            // Support simple bolding "**text**" -> "<strong>text</strong>"
            const parsedBold = p.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
            html += `<p>${parsedBold.replace(/\n/g, "<br>")}</p>`;
        }
    });
    
    body.innerHTML = html;
}

// Icon Mapping helper
const EMOTION_ICONS = {
    "Curious": "compass",
    "Confused": "help-circle",
    "Frustrated": "alert-triangle",
    "Confident": "award",
    "Bored": "meh"
};

// Render results inside Model Panel
function renderModelResults(prefix, predData) {
    const primary = predData.primary_emotion;
    const confidence = predData.primary_confidence;
    const all = predData.all_emotions;
    const mixed = predData.mixed_emotions;
    
    // Primary Badge
    const primaryBadge = document.getElementById(`${prefix}-primary-badge`);
    const primaryName = document.getElementById(`${prefix}-primary-name`);
    const primaryConf = document.getElementById(`${prefix}-primary-conf`);
    
    primaryName.textContent = primary;
    primaryConf.textContent = `${Math.round(confidence * 100)}%`;
    
    // Reset background emotion color classes
    primaryBadge.className = "emotion-badge-large";
    primaryBadge.classList.add(`emotion-${primary.toLowerCase()}`);
    
    // Update primary icon
    const iconName = EMOTION_ICONS[primary] || "smile";
    primaryBadge.querySelector("i").setAttribute("data-lucide", iconName);
    
    // Mixed Badges
    const mixedContainer = document.getElementById(`${prefix}-mixed-container`);
    const mixedSection = document.getElementById(`${prefix}-mixed-section`);
    mixedContainer.innerHTML = "";
    
    if (mixed && mixed.length > 0) {
        mixedSection.classList.remove("hidden");
        mixed.forEach(([emotion, val]) => {
            const badge = document.createElement("span");
            badge.className = `emotion-badge-small emotion-${emotion.toLowerCase()}`;
            
            const icon = document.createElement("i");
            icon.setAttribute("data-lucide", EMOTION_ICONS[emotion] || "smile");
            icon.style.width = "13px";
            icon.style.height = "13px";
            
            badge.appendChild(icon);
            badge.appendChild(document.createTextNode(` ${emotion} `));
            
            const scoreSpan = document.createElement("span");
            scoreSpan.className = "score";
            scoreSpan.textContent = `${Math.round(val * 100)}%`;
            badge.appendChild(scoreSpan);
            
            mixedContainer.appendChild(badge);
        });
    } else {
        mixedSection.classList.add("hidden");
    }
    
    // Probability Bars breakdown
    const barsContainer = document.getElementById(`${prefix}-bars`);
    barsContainer.innerHTML = "";
    
    // Sorted by emotion name to maintain alignment between models
    const sortedEmotions = Object.keys(all).sort();
    sortedEmotions.forEach(emotion => {
        const val = all[emotion];
        const barRow = document.createElement("div");
        barRow.className = "bar-row";
        
        const barInfo = document.createElement("div");
        barInfo.className = "bar-info";
        
        const label = document.createElement("span");
        label.className = "bar-label";
        
        const labelIcon = document.createElement("i");
        labelIcon.setAttribute("data-lucide", EMOTION_ICONS[emotion] || "smile");
        
        label.appendChild(labelIcon);
        label.appendChild(document.createTextNode(emotion));
        
        const valSpan = document.createElement("span");
        valSpan.className = "bar-val";
        valSpan.textContent = `${Math.round(val * 100)}%`;
        
        barInfo.appendChild(label);
        barInfo.appendChild(valSpan);
        
        const track = document.createElement("div");
        track.className = "bar-track";
        
        const fill = document.createElement("div");
        fill.className = `bar-fill bg-${emotion.toLowerCase()}`;
        
        track.appendChild(fill);
        barRow.appendChild(barInfo);
        barRow.appendChild(track);
        
        barsContainer.appendChild(barRow);
        
        // Trigger width animation with a small timeout
        setTimeout(() => {
            fill.style.width = `${Math.round(val * 100)}%`;
        }, 50);
    });
    
    // Re-create injected lucide icons
    if (window.lucide) {
        window.lucide.createIcons();
    }
}

// Fetch and refresh session logs & charts
async function refreshData() {
    try {
        const response = await fetch("/history");
        if (!response.ok) throw new Error("Could not fetch history");
        const logs = await response.json();
        
        // Update history UI components
        renderLogsTable(logs);
        renderAnalytics(logs);
    } catch (err) {
        console.error("Error refreshing data:", err);
    }
}

// Render logs table
function renderLogsTable(logs) {
    const tableBody = document.getElementById("history-table-body");
    const emptyState = document.getElementById("table-empty-state");
    const countBadge = document.getElementById("log-count-badge");
    
    countBadge.textContent = `${logs.length} session${logs.length === 1 ? "" : "s"} logged`;
    
    if (logs.length === 0) {
        tableBody.innerHTML = "";
        emptyState.classList.remove("hidden");
        return;
    }
    
    emptyState.classList.add("hidden");
    
    // Sort descending by timestamp (newest first)
    const sortedLogs = [...logs].reverse();
    
    let html = "";
    sortedLogs.forEach(row => {
        const date = new Date(row.timestamp);
        const formattedDate = date.toLocaleDateString(undefined, { 
            month: 'short', 
            day: 'numeric', 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        // Safely retrieve primary emotions
        const modelAPrimary = row.model_a_pred?.primary_emotion || "-";
        const modelBPrimary = row.model_b_pred?.primary_emotion || "-";
        
        // Render row cells
        html += `
            <tr>
                <td><strong>${formattedDate}</strong></td>
                <td><span class="subject-tag">${row.field}</span></td>
                <td title="${escapeHTML(row.problem_text)}">${escapeHTML(row.problem_text)}</td>
                <td><span class="emotion-badge-small emotion-${modelAPrimary.toLowerCase()}">${modelAPrimary}</span></td>
                <td><span class="emotion-badge-small emotion-${modelBPrimary.toLowerCase()}">${modelBPrimary}</span></td>
                <td><strong>${row.selected_model}</strong></td>
                <td>${row.final_response.includes("fallback") || row.final_response.includes("It looks like") || row.final_response.includes("It is completely okay") ? "Template Fallback" : "Gemini AI"}</td>
            </tr>
        `;
    });
    
    tableBody.innerHTML = html;
}

// Helper to escape HTML characters
function escapeHTML(str) {
    if (!str) return "";
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Render Analytics Graph using Chart.js
function renderAnalytics(logs) {
    const totalSessions = document.getElementById("stat-total-sessions");
    const topEmotion = document.getElementById("stat-top-emotion");
    const aiCount = document.getElementById("stat-ai-count");
    
    const chartWrapper = document.querySelector(".chart-wrapper");
    const chartCanvas = document.getElementById("emotionChart");
    const chartEmpty = document.getElementById("chart-empty-state");
    
    totalSessions.textContent = logs.length;
    
    if (logs.length === 0) {
        chartEmpty.classList.remove("hidden");
        chartCanvas.classList.add("hidden");
        topEmotion.textContent = "-";
        aiCount.textContent = "0";
        return;
    }
    
    chartEmpty.classList.add("hidden");
    chartCanvas.classList.remove("hidden");
    
    // Aggregation maps
    const emotionCounts = {
        "Bored": 0,
        "Confident": 0,
        "Confused": 0,
        "Curious": 0,
        "Frustrated": 0
    };
    
    let geminiCount = 0;
    
    logs.forEach(row => {
        // We aggregate by the emotion of the SELECTED model used to guide the assistant
        const selected = row.selected_model === "Model B" ? row.model_b_pred : row.model_a_pred;
        const emotion = selected?.primary_emotion;
        if (emotion in emotionCounts) {
            emotionCounts[emotion]++;
        }
        
        // Count AI versus fallback template
        // Gemini generated prompt texts aren't matching exact fallback substrings
        const isFallback = row.final_response.includes("It looks like") || 
                           row.final_response.includes("It is completely okay") || 
                           row.final_response.includes("Fantastic! You're approaching") ||
                           row.final_response.includes("I love your curiosity") ||
                           row.final_response.includes("I hear you, and it's completely");
        if (!isFallback) {
            geminiCount++;
        }
    });
    
    aiCount.textContent = geminiCount;
    
    // Find most frequent emotion
    let maxCount = -1;
    let popularEmotion = "-";
    for (const [emotion, count] of Object.entries(emotionCounts)) {
        if (count > maxCount && count > 0) {
            maxCount = count;
            popularEmotion = emotion;
        }
    }
    topEmotion.textContent = popularEmotion !== "-" ? popularEmotion : "None";
    
    // Render Chart.js Polar Area Chart
    const emotionsList = Object.keys(emotionCounts);
    const dataValues = emotionsList.map(e => emotionCounts[e]);
    
    // Mapped custom HSL colors for matching branding style
    const bgColors = [
        "rgba(100, 116, 139, 0.7)",  // Bored - Slate Grey
        "rgba(16, 185, 129, 0.7)",   // Confident - Emerald Green
        "rgba(245, 158, 11, 0.7)",   // Confused - Amber Orange
        "rgba(99, 102, 241, 0.7)",   // Curious - Indigo Purple
        "rgba(239, 68, 68, 0.7)"     // Frustrated - Coral Red
    ];
    
    const borderColors = [
        "rgba(100, 116, 139, 1)",
        "rgba(16, 185, 129, 1)",
        "rgba(245, 158, 11, 1)",
        "rgba(99, 102, 241, 1)",
        "rgba(239, 68, 68, 1)"
    ];
    
    if (currentChart) {
        currentChart.destroy();
    }
    
    currentChart = new Chart(chartCanvas, {
        type: 'polarArea',
        data: {
            labels: emotionsList,
            datasets: [{
                data: dataValues,
                backgroundColor: bgColors,
                borderColor: borderColors,
                borderWidth: 1.5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    grid: {
                        color: "rgba(0, 0, 0, 0.05)"
                    },
                    ticks: {
                        backdropColor: "transparent",
                        color: "rgba(0, 0, 0, 0.5)",
                        stepSize: 1
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        font: {
                            family: "'Plus Jakarta Sans', sans-serif",
                            weight: 600
                        },
                        padding: 15
                    }
                }
            }
        }
    });
}
