// ==========================================
// GLOBAL APPLICATION STATE
// ==========================================
var currentTab = "dashboard";
var currentSelectedPatient = null;
var authToken = localStorage.getItem("health_auth_token") || null;
var currentActiveReportData = null;
var pendingReportId = null;
var reportToDeleteId = null;
var trendChartInstance = null;
var allReportsCache = [];
var allTrendsData = null;
var currentUserData = null;

// ==========================================
// REAL-TIME NOTIFICATIONS & TOAST ENGINE
// ==========================================

function showAppToast(title, message, iconType = "bell") {
  const container = document.getElementById("appToastContainer");
  if (!container) return;

  const toastId = "toast_" + Date.now();
  const icons = {
    bell: "🔔",
    check: "✅",
    pill: "💊",
    utensils: "🍳",
    walk: "🏃",
    zap: "⚡"
  };
  const icon = icons[iconType] || "🔔";

  const toastEl = document.createElement("div");
  toastEl.id = toastId;
  toastEl.className = "pointer-events-auto bg-slate-900 text-white rounded-2xl p-4 shadow-2xl border border-slate-700 flex items-start space-x-3 transform transition-all duration-300 translate-y-4 opacity-0";
  toastEl.innerHTML = `
    <div class="text-xl flex-shrink-0">${icon}</div>
    <div class="flex-1 min-w-0">
      <h5 class="font-extrabold text-xs text-white">${title}</h5>
      <p class="text-[11px] text-slate-300 mt-0.5 leading-relaxed">${message}</p>
    </div>
    <button onclick="document.getElementById('${toastId}').remove()" class="text-slate-400 hover:text-white text-xs">&times;</button>
  `;

  container.appendChild(toastEl);

  // Animate in
  setTimeout(() => {
    toastEl.classList.remove("translate-y-4", "opacity-0");
  }, 50);

  // Auto-remove after 5 seconds
  setTimeout(() => {
    if (document.getElementById(toastId)) {
      toastEl.classList.add("translate-y-4", "opacity-0");
      setTimeout(() => toastEl.remove(), 300);
    }
  }, 5000);
}

async function requestBrowserNotificationPermission() {
  if (!("Notification" in window)) {
    showAppToast("Notifications Unsupported", "Your browser does not support desktop notifications.", "bell");
    return;
  }

  try {
    const perm = await Notification.requestPermission();
    if (perm === "granted") {
      showAppToast("Notifications Enabled!", "You will now receive timely health reminders.", "check");
      new Notification("Antigravity Health Assistant", {
        body: "✓ Browser alerts are now active and working!",
        icon: "https://img.icons8.com/color/96/medical-heart.png"
      });
    } else {
      showAppToast("Permission Notice", "Notification permission was " + perm, "bell");
    }
  } catch (e) {
    console.error(e);
  }
}

async function sendTestNotification() {
  try {
    const res = await fetch("/api/v1/wellness/notifications/send-test", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${authToken}` },
      body: JSON.stringify({
        title: "🔔 Antigravity Health Assistant Alert",
        body: "Your daily reminders and clinical notifications are fully active and working!"
      })
    });
    const data = await res.json();

    // Show toast
    showAppToast(data.title, data.body, "zap");

    // Show native browser notification if permitted
    if ("Notification" in window && Notification.permission === "granted") {
      new Notification(data.title, {
        body: data.body,
        icon: "https://img.icons8.com/color/96/medical-heart.png"
      });
    }
  } catch (e) {
    console.error(e);
  }
}

function toggleNotificationDropdown() {
  const dropdown = document.getElementById("headerNotificationDropdown");
  if (!dropdown) return;
  const isHidden = dropdown.classList.contains("hidden");
  if (isHidden) {
    dropdown.classList.remove("hidden");
    loadNotificationFeed();
  } else {
    dropdown.classList.add("hidden");
  }
}

async function loadNotificationFeed() {
  try {
    const res = await fetch("/api/v1/wellness/notifications/feed", {
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    if (!res.ok) return;

    const data = await res.json();
    const notifs = data.notifications || [];

    // Update Header Badge
    const badge = document.getElementById("headerNotificationBadge");
    if (badge) {
      badge.innerText = notifs.length;
      badge.style.display = notifs.length > 0 ? "flex" : "none";
    }

    // Render Dropdown List
    const headerList = document.getElementById("headerNotificationList");
    if (headerList) {
      if (notifs.length === 0) {
        headerList.innerHTML = `<p class="text-slate-400 py-3 text-center">No active notifications</p>`;
      } else {
        headerList.innerHTML = notifs.map(n => `
          <div class="p-3 bg-slate-50 hover:bg-slate-100 rounded-2xl border border-slate-100 transition space-y-1">
            <div class="flex items-center justify-between">
              <span class="font-extrabold text-slate-900 text-xs">${n.title}</span>
              <span class="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.2 rounded-full">${n.time}</span>
            </div>
            <p class="text-[11px] text-slate-600">${n.body}</p>
          </div>
        `).join("");
      }
    }

    // Render Full Page Feed
    const fullFeed = document.getElementById("fullNotificationFeedContainer");
    if (fullFeed) {
      if (notifs.length === 0) {
        fullFeed.innerHTML = `<p class="text-slate-400 py-4 text-center">No notifications recorded.</p>`;
      } else {
        fullFeed.innerHTML = notifs.map(n => `
          <div class="p-4 bg-slate-50/80 rounded-2xl border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div class="flex items-center space-x-3">
              <div class="w-9 h-9 rounded-xl bg-white border border-slate-200 flex items-center justify-center font-bold text-sm shadow-2xs">
                ${n.category === 'meal' ? '🍳' : n.category === 'movement' ? '🏃' : '📄'}
              </div>
              <div>
                <div class="flex items-center space-x-2">
                  <h4 class="font-extrabold text-slate-900 text-xs">${n.title}</h4>
                  <span class="text-[10px] bg-slate-200 text-slate-700 font-bold px-2 py-0.2 rounded-full">${n.badge}</span>
                </div>
                <p class="text-xs text-slate-600 mt-0.5">${n.body}</p>
              </div>
            </div>
            <span class="text-xs font-extrabold text-slate-500 bg-white px-3 py-1 rounded-xl border border-slate-200 self-start sm:self-auto">${n.time}</span>
          </div>
        `).join("");
      }
    }

    lucide.createIcons();
  } catch (e) {
    console.error("Notification feed error:", e);
  }
}

async function saveMovementReminder() {
  const chk = document.getElementById("exRemCheck");
  const timeInput = document.getElementById("exRemTime");
  const payload = {
    enabled: chk ? chk.checked : true,
    time: timeInput ? timeInput.value : "06:00 PM",
    label: "Daily Movement Reminder"
  };

  try {
    const res = await fetch("/api/v1/wellness/reminders/movement", {
      method: "PUT",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${authToken}` },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      showAppToast("Movement Reminder Saved", `Daily walk reminder set for ${payload.time}.`, "walk");
      loadNotificationFeed();
    }
  } catch (e) {
    console.error(e);
  }
}

// Background Reminder Checker - checks every 30 seconds
function startBackgroundReminderChecker() {
  setInterval(async () => {
    if (!authToken) return;
    try {
      const now = new Date();
      let hours = now.getHours();
      const minutes = now.getMinutes();
      const ampm = hours >= 12 ? 'PM' : 'AM';
      hours = hours % 12;
      hours = hours ? hours : 12;
      const curTimeStr = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')} ${ampm}`;

      // Check against meal reminders
      const mealRes = await fetch("/api/v1/wellness/reminders/diet", { headers: { "Authorization": `Bearer ${authToken}` } });
      if (mealRes.ok) {
        const meals = await mealRes.json();
        meals.forEach(m => {
          if (m.enabled && m.time === curTimeStr) {
            showAppToast(`⏰ Time for ${m.name}`, "Check your personalized meal guide for healthy suggestions.", "utensils");
            if ("Notification" in window && Notification.permission === "granted") {
              new Notification(`Antigravity Health: ${m.name}`, {
                body: `It is ${m.time}. Time for your scheduled meal!`,
                icon: "https://img.icons8.com/color/96/medical-heart.png"
              });
            }
          }
        });
      }
    } catch (e) {}
  }, 30000);
}

function setDashboardTheme(themeName) {
  document.body.classList.remove('theme-emerald', 'theme-sapphire', 'theme-amethyst', 'theme-sunset', 'theme-dark');
  document.body.classList.add(`theme-${themeName}`);
  localStorage.setItem('health_dashboard_theme', themeName);

  // Update ring indicator on top bar
  ['emerald', 'sapphire', 'amethyst', 'sunset', 'dark'].forEach(t => {
    const btn = document.getElementById(`themeBtn_${t}`);
    if (btn) {
      if (t === themeName) {
        btn.classList.add('ring-2', 'ring-white', 'scale-125');
      } else {
        btn.classList.remove('ring-2', 'ring-white', 'scale-125');
      }
    }
  });

  if (currentTab === 'dashboard') {
    loadDashboard();
  loadNotificationFeed();
  startBackgroundReminderChecker();
  }
}

// Initialize saved theme
const savedTheme = localStorage.getItem('health_dashboard_theme') || 'emerald';
document.addEventListener('DOMContentLoaded', () => {
  setDashboardTheme(savedTheme);
});

async function loadSampleReport(type) {
  let sampleText = "";
  let sampleTitle = "";

  if (type === "glucose") {
    sampleTitle = "Metabolic Checkup (Glucose & HbA1c)";
    sampleText = `LABORATORY DIAGNOSTIC REPORT
Patient Name: Eleanor Vance
Age: 42 Years | Gender: Female | Weight: 68.5 kg
Date: 2026-08-26
Doctor: Dr. Mark Taylor

Fasting Blood Glucose: 118.0 mg/dL (70.0 - 99.0 mg/dL)
HbA1c: 6.2 % (4.0 - 5.6 %)
Total Cholesterol: 195.0 mg/dL (125.0 - 200.0 mg/dL)
Vitamin D (25-Hydroxy): 26.0 ng/mL (30.0 - 100.0 ng/mL)
`;
  } else {
    sampleTitle = "Cardiovascular Lipid Profile";
    sampleText = `LABORATORY DIAGNOSTIC REPORT
Patient Name: Marcus Kane
Age: 51 Years | Gender: Male | Weight: 84.0 kg
Date: 2026-08-26
Doctor: Dr. Sarah Jenkins

Total Cholesterol: 240.0 mg/dL (125.0 - 200.0 mg/dL)
LDL Cholesterol: 155.0 mg/dL (0.0 - 100.0 mg/dL)
HDL Cholesterol: 38.0 mg/dL (40.0 - 60.0 mg/dL)
Triglycerides: 220.0 mg/dL (0.0 - 150.0 mg/dL)
`;
  }

  const blob = new Blob([sampleText], { type: "text/plain" });
  const file = new File([blob], `${type}_sample_report.txt`, { type: "text/plain" });
  await uploadSelectedFile(file);
}

function renderPatientFilterBar(containerId, availablePatients, activePatient, onSelectCallbackName) {
  const container = document.getElementById(containerId);
  if (!container || !availablePatients || availablePatients.length <= 1) {
    if (container) container.innerHTML = "";
    return;
  }

  const isAllActive = !activePatient || activePatient === "All";
  let html = `
    <div class="bg-slate-100 dark:bg-slate-800 p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 flex flex-wrap items-center gap-2 mb-4 text-xs">
      <span class="font-bold text-slate-500 uppercase tracking-wider text-[10px] flex items-center mr-1">
        <i data-lucide="users" class="w-3.5 h-3.5 mr-1 text-sky-600"></i> Patient Filter:
      </span>
      <button onclick="${onSelectCallbackName}('All')" class="px-3 py-1 rounded-lg font-bold transition flex items-center space-x-1 ${isAllActive ? 'bg-sky-600 text-white shadow-sm' : 'bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200'}">
        <span>All Patients</span>
      </button>
  `;

  availablePatients.forEach(p => {
    const isSelected = activePatient === p.patient_name;
    html += `
      <button onclick="${onSelectCallbackName}('${p.patient_name.replace(/'/g, "\\'")}')" class="px-3 py-1 rounded-lg font-bold transition flex items-center space-x-1.5 ${isSelected ? 'bg-emerald-600 text-white shadow-sm' : 'bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200'}">
        <span>🩺 ${p.patient_name}</span>
        <span class="text-[10px] bg-black/15 dark:bg-white/15 px-1.5 py-0.2 rounded-full font-mono font-normal">${p.report_count}</span>
      </button>
    `;
  });

  html += `</div>`;
  container.innerHTML = html;
  if (window.lucide) lucide.createIcons();
}

function selectPatientFilter(patientName) {
  currentSelectedPatient = (patientName === "All") ? null : patientName;
  if (currentTab === "history") {
    loadPatientHistory();
  } else if (currentTab === "trends") {
    loadBiomarkerTrends();
  } else if (currentTab === "dashboard") {
    loadDashboard();
  loadNotificationFeed();
  startBackgroundReminderChecker();
  }
}


/**
 * Frontend Controller for Personalized, Report-Driven Healthcare Assistant.
 * Built with clear, friendly, everyday language across all 10 views.
 */










document.addEventListener("DOMContentLoaded", async () => {
  setupDragAndDrop();
  await initAuthSession();
  await loadDashboard();
  loadNotificationFeed();
  startBackgroundReminderChecker();
  lucide.createIcons();
});

async function initAuthSession() {
  if (!authToken) {
    await autoLoginDemo();
  } else {
    try {
      const res = await fetch("/api/v1/auth/me", { headers: { "Authorization": `Bearer ${authToken}` } });
      if (res.ok) {
        currentUserData = await res.json();
        updateHeaderUserDisplay();
      } else {
        await autoLoginDemo();
      }
    } catch (e) {
      await autoLoginDemo();
    }
  }
}

async function autoLoginDemo() {
  try {
    const res = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier: "demo@healthcare.ai", password: "DemoPassword123!" })
    });
    if (res.ok) {
      const data = await res.json();
      authToken = data.access_token;
      currentUserData = data;
      localStorage.setItem("health_auth_token", authToken);
      updateHeaderUserDisplay();
    }
  } catch (e) {
    console.error("Auto login error:", e);
  }
}

function updateHeaderUserDisplay() {
  const btnSignIn = document.getElementById("btnSignInHeader");
  const loggedInBox = document.getElementById("loggedInUserBox");
  const userNameEl = document.getElementById("headerUserName");

  if (currentUserData && authToken) {
    if (btnSignIn) btnSignIn.classList.add("hidden");
    if (loggedInBox) loggedInBox.classList.remove("hidden");
    if (userNameEl) {
      const displayName = currentUserData.full_name || currentUserData.email || currentUserData.phone_number || "Patient Account";
      userNameEl.innerText = displayName;
    }
  } else {
    if (btnSignIn) btnSignIn.classList.remove("hidden");
    if (loggedInBox) loggedInBox.classList.add("hidden");
  }
  lucide.createIcons();
}

function openAuthModal(tab = 'signin') {
  const modal = document.getElementById("authModal");
  if (modal) modal.classList.remove("hidden");
  switchAuthTab(tab);
  lucide.createIcons();
}

function closeAuthModal() {
  const modal = document.getElementById("authModal");
  if (modal) modal.classList.add("hidden");
}

function switchAuthTab(tab) {
  const tabSignIn = document.getElementById("authTabSignIn");
  const tabRegister = document.getElementById("authTabRegister");
  const panelSignIn = document.getElementById("authSignInPanel");
  const panelRegister = document.getElementById("authRegisterPanel");

  if (tab === 'signin') {
    if (tabSignIn) { tabSignIn.classList.add("bg-white", "text-slate-900", "shadow-sm"); tabSignIn.classList.remove("text-slate-500"); }
    if (tabRegister) { tabRegister.classList.remove("bg-white", "text-slate-900", "shadow-sm"); tabRegister.classList.add("text-slate-500"); }
    if (panelSignIn) panelSignIn.classList.remove("hidden");
    if (panelRegister) panelRegister.classList.add("hidden");
  } else {
    if (tabRegister) { tabRegister.classList.add("bg-white", "text-slate-900", "shadow-sm"); tabRegister.classList.remove("text-slate-500"); }
    if (tabSignIn) { tabSignIn.classList.remove("bg-white", "text-slate-900", "shadow-sm"); tabSignIn.classList.add("text-slate-500"); }
    if (panelRegister) panelRegister.classList.remove("hidden");
    if (panelSignIn) panelSignIn.classList.add("hidden");
  }
  lucide.createIcons();
}

async function handleUserLogin() {
  const ident = document.getElementById("loginIdentifier").value.trim();
  const pass = document.getElementById("loginPassword").value;
  const errBox = document.getElementById("loginErrorContainer");
  const errText = document.getElementById("loginErrorText");

  if (!ident || !pass) {
    if (errBox && errText) {
      errText.innerText = "Please enter your Gmail / Mobile number and password.";
      errBox.classList.remove("hidden");
    }
    return;
  }

  try {
    const res = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier: ident, password: pass })
    });

    if (res.ok) {
      const data = await res.json();
      authToken = data.access_token;
      currentUserData = data;
      localStorage.setItem("health_auth_token", authToken);
      if (errBox) errBox.classList.add("hidden");
      closeAuthModal();
      updateHeaderUserDisplay();
      await loadDashboard();
  loadNotificationFeed();
  startBackgroundReminderChecker();
      alert(`✓ Welcome back, ${data.full_name || 'Patient'}!`);
    } else {
      const err = await res.json();
      if (errBox && errText) {
        errText.innerText = err.detail || "Incorrect Gmail / Mobile number or password.";
        errBox.classList.remove("hidden");
      }
    }
  } catch (e) {
    console.error("Login error:", e);
    if (errBox && errText) {
      errText.innerText = "Connection error. Please try again.";
      errBox.classList.remove("hidden");
    }
  }
}

async function handleUserRegister() {
  const name = document.getElementById("regFullName").value.trim();
  const email = document.getElementById("regEmail").value.trim();
  const phone = document.getElementById("regPhone").value.trim();
  const pass = document.getElementById("regPassword").value;
  const errBox = document.getElementById("regErrorContainer");
  const errText = document.getElementById("regErrorText");

  if (!email && !phone) {
    if (errBox && errText) {
      errText.innerText = "Please provide either a Gmail address or a Mobile number.";
      errBox.classList.remove("hidden");
    }
    return;
  }

  if (!pass || pass.length < 6) {
    if (errBox && errText) {
      errText.innerText = "Please enter a password with at least 6 characters.";
      errBox.classList.remove("hidden");
    }
    return;
  }

  try {
    const res = await fetch("/api/v1/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ full_name: name || "Patient", email: email || null, phone_number: phone || null, password: pass })
    });

    if (res.ok) {
      const data = await res.json();
      authToken = data.access_token;
      currentUserData = data;
      localStorage.setItem("health_auth_token", authToken);
      if (errBox) errBox.classList.add("hidden");
      closeAuthModal();
      updateHeaderUserDisplay();
      await loadDashboard();
  loadNotificationFeed();
  startBackgroundReminderChecker();
      alert(`✓ Account created successfully! Welcome, ${data.full_name || 'Patient'}!`);
    } else {
      const err = await res.json();
      if (errBox && errText) {
        errText.innerText = err.detail || "Unable to register account.";
        errBox.classList.remove("hidden");
      }
    }
  } catch (e) {
    console.error("Register error:", e);
    if (errBox && errText) {
      errText.innerText = "Connection error. Please try again.";
      errBox.classList.remove("hidden");
    }
  }
}

async function handleDemoQuickLogin() {
  await autoLoginDemo();
  closeAuthModal();
  await loadDashboard();
  loadNotificationFeed();
  startBackgroundReminderChecker();
  alert("✓ Switched to Demo Patient Account.");
}

async function handleUserLogout() {
  authToken = null;
  currentUserData = null;
  localStorage.removeItem("health_auth_token");
  updateHeaderUserDisplay();
  openAuthModal('signin');
}

function switchTab(tabId) {
  document.querySelectorAll(".tab-view").forEach(el => el.classList.add("hidden"));
  document.querySelectorAll(".nav-item").forEach(el => el.classList.remove("active"));

  const targetView = document.getElementById(`view-${tabId}`);
  const targetNav = document.getElementById(`nav-${tabId}`);
  if (targetView) targetView.classList.remove("hidden");
  if (targetNav) targetNav.classList.add("active");

  lucide.createIcons();

  if (tabId === "dashboard") loadDashboard();
  loadNotificationFeed();
  startBackgroundReminderChecker();
  if (tabId === "history") loadPatientHistory();
  if (tabId === "trends") loadTrends();
  if (tabId === "medications") loadMedications();
  if (tabId === "diet") loadDiet();
  if (tabId === "exercise") loadExercise();
  if (tabId === "notifications") loadNotificationsView();
  if (tabId === "profile") loadPatientProfile();
  if (tabId === "settings") loadSettings();
}

function setupDragAndDrop() {
  const dropzone = document.getElementById("reportDropzone");
  if (!dropzone) return;

  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => { e.preventDefault(); e.stopPropagation(); }, false);
  });

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, () => dropzone.classList.add('border-sky-500', 'bg-sky-50/50'), false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, () => dropzone.classList.remove('border-sky-500', 'bg-sky-50/50'), false);
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length) uploadSelectedFile(files[0]);
  }, false);
}

async function handleFileUpload(event) {
  const file = event.target.files[0];
  if (!file) return;
  await uploadSelectedFile(file);
  event.target.value = "";
}

async function uploadSelectedFile(file) {
  if (!authToken) await autoLoginDemo();

  const statusEl = document.getElementById("uploadStatusBanner");
  if (statusEl) {
    statusEl.classList.remove("hidden");
    statusEl.innerHTML = `
      <div class="flex items-center space-x-3 text-sky-800 bg-sky-50 border border-sky-200 p-4 rounded-xl text-xs font-semibold animate-pulse shadow-sm">
        <i data-lucide="loader-2" class="w-5 h-5 animate-spin text-sky-600"></i>
        <div>
          <p class="font-bold">Reading "${file.name}" in plain English...</p>
          <p class="font-normal text-slate-500">Checking your test results, calculating healthy ranges, and preparing easy-to-read food and movement tips.</p>
        </div>
      </div>
    `;
    lucide.createIcons();
  }

  const formData = new FormData();
  formData.append("file", file);
  formData.append("title", file.name.replace(/\.[^/.]+$/, ""));
  formData.append("report_type", "Laboratory Report");

  try {
    const res = await fetch("/api/v1/reports/upload", {
      method: "POST",
      headers: { "Authorization": `Bearer ${authToken}` },
      body: formData
    });

    if (res.ok) {
      const data = await res.json();
      currentActiveReportData = data;
      pendingReportId = data.report_id;

      if (statusEl) {
        statusEl.innerHTML = `
          <div class="flex items-center justify-between text-emerald-800 bg-emerald-50 border border-emerald-200 p-4 rounded-xl text-xs font-semibold shadow-sm">
            <span class="flex items-center space-x-2">
              <i data-lucide="check-circle-2" class="w-4 h-4 text-emerald-600"></i>
              <span>Report ready! Found <strong>${data.results_extracted_count}</strong> health measurement(s). Opening your simple breakdown...</span>
            </span>
          </div>
        `;
        lucide.createIcons();
      }

      switchTab("analysis");
      await render14StepAnalysis(data);
    } else {
      const err = await res.json();
      const errMsg = err.detail || "Please upload medical reports (such as blood tests, lab panels, or clinical diagnostics).";
      if (statusEl) {
        statusEl.innerHTML = `
          <div class="bg-amber-50 border-2 border-amber-300 rounded-2xl p-6 text-amber-950 shadow-md space-y-3">
            <div class="flex items-start space-x-3.5">
              <div class="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center flex-shrink-0 font-bold border border-amber-200">
                <i data-lucide="file-warning" class="w-6 h-6"></i>
              </div>
              <div class="space-y-1">
                <h4 class="font-bold text-base text-amber-900">Please Upload Medical Reports</h4>
                <p class="text-xs text-amber-800 leading-relaxed font-medium">
                  The document you selected does not contain medical, laboratory, or clinical diagnostic results.
                </p>
                <div class="pt-2 flex flex-wrap gap-2 text-[11px] font-semibold text-amber-900">
                  <span class="bg-white border border-amber-200 px-2.5 py-1 rounded-md shadow-2xs">✓ Blood Tests & CBC</span>
                  <span class="bg-white border border-amber-200 px-2.5 py-1 rounded-md shadow-2xs">✓ Blood Sugar & HbA1c</span>
                  <span class="bg-white border border-amber-200 px-2.5 py-1 rounded-md shadow-2xs">✓ Cholesterol / Lipid Panels</span>
                  <span class="bg-white border border-amber-200 px-2.5 py-1 rounded-md shadow-2xs">✓ Kidney & Liver Function</span>
                  <span class="bg-white border border-amber-200 px-2.5 py-1 rounded-md shadow-2xs">✓ Vitamins & Thyroid</span>
                </div>
              </div>
            </div>
            <div class="flex justify-end pt-1">
              <button onclick="document.getElementById('uploadStatusBanner').classList.add('hidden')" class="px-4 py-1.5 bg-amber-200 hover:bg-amber-300 text-amber-950 rounded-xl text-xs font-bold transition shadow-sm">
                Try Another Medical Report
              </button>
            </div>
          </div>
        `;
        lucide.createIcons();
        statusEl.classList.remove("hidden");
      }
    }
  } catch (e) {
    console.error("Upload error:", e);
    if (statusEl) {
      statusEl.innerHTML = `
        <div class="bg-rose-50 border border-rose-200 rounded-2xl p-5 text-rose-900 shadow-sm flex items-center space-x-3">
          <i data-lucide="alert-triangle" class="w-6 h-6 text-rose-600 flex-shrink-0"></i>
          <div>
            <p class="font-bold text-xs">Error reading document</p>
            <p class="text-xs text-rose-700">Please upload a medical report or lab document in PDF, image, or text format.</p>
          </div>
        </div>
      `;
      lucide.createIcons();
      statusEl.classList.remove("hidden");
    }
  }
}

// 14-Step Report Analysis Workspace in Plain Language
async function render14StepAnalysis(data) {
  const emptyNotice = document.getElementById("analysisEmptyNotice");
  const container = document.getElementById("analysisSequentialContainer");
  if (!container) return;

  if (emptyNotice) emptyNotice.classList.add("hidden");
  container.classList.remove("hidden");

  const insights = data.ai_insights || {};
  const results = data.results || [];

  // STEP 1: REPORT HEADER (WITH DIFFERENTIATED PATIENT NAME)
  const reportPtName = (data.patient_demographics && data.patient_demographics.name) || (insights.patient_demographics && insights.patient_demographics.name) || "Not Specified in Report";
  if (reportPtName && reportPtName !== "Not Specified in Report") {
    currentSelectedPatient = reportPtName;
  }
  document.getElementById("seq1ReportTitle").innerText = data.title;
  document.getElementById("seq1ReportMeta").innerHTML = `
    <strong>🩺 Report Patient:</strong> ${reportPtName} • 
    <strong>📅 Date:</strong> ${data.report_date} • 
    <strong>📄 File:</strong> ${data.file_name} • 
    <strong>🔬 Tests:</strong> ${data.results_extracted_count || results.length} Health Numbers
  `;

  // STEP 2: REPORT DESCRIPTION
  document.getElementById("seq2ReportDesc").innerText = insights.report_description || "A simple breakdown of the health numbers measured in your report.";

  // STEP 3: EXTRACTION VERIFICATION
  const ver = insights.extraction_verification || { total_extracted: results.length, auto_verified_count: results.length, requires_review_count: 0 };
  document.getElementById("seq3VerificationStats").innerHTML = `
    <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center space-x-2">
      <i data-lucide="file-check" class="w-4 h-4 text-sky-600"></i>
      <span><strong>${ver.total_extracted}</strong> Tests Checked</span>
    </div>
    <div class="p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-emerald-900 flex items-center space-x-2">
      <i data-lucide="check-circle-2" class="w-4 h-4 text-emerald-600"></i>
      <span><strong>${ver.auto_verified_count}</strong> Verified Accurate</span>
    </div>
    <div class="p-3 ${ver.requires_review_count > 0 ? 'bg-amber-50 border-amber-200 text-amber-900' : 'bg-slate-50 border-slate-200'} rounded-xl border flex items-center space-x-2">
      <i data-lucide="alert-circle" class="w-4 h-4 text-amber-600"></i>
      <span><strong>${ver.requires_review_count}</strong> Need Quick Look</span>
    </div>
  `;

  // STEP 4: BIOMARKER RESULTS TABLE & PERSONAL TRAINER CARE OPTIONS
  const tbody = document.getElementById("seq4ResultsTableBody");
  tbody.innerHTML = results.map((r, idx) => {
    let careVal = r.care_level || (r.status_flag === 'within_range' ? 'Optimal (Maintain Routine)' : 'Needs Extra Care (Trainer Focus)');
    let defaultAction = r.trainer_action || (
      r.status_flag === 'within_range' 
        ? 'Great job! Maintain your current healthy routine and daily movement.' 
        : 'Focus on 20-min daily walks, wholesome nutrition, and plenty of hydration.'
    );

    return `
      <tr class="hover:bg-slate-50/70 transition">
        <td class="p-3 min-w-[200px]">
          <input type="text" class="w-full border border-slate-200 rounded px-2 py-1 text-xs font-semibold text-slate-800" value="${r.biomarker_name}" id="seqEditName_${idx}">
          <p class="text-[11px] text-slate-500 mt-0.5">${r.friendly_name ? r.friendly_name + ' • ' : ''}${r.explanation_simple || ''}</p>
        </td>
        <td class="p-3"><input type="number" step="0.1" class="w-24 border border-slate-200 rounded px-2 py-1 text-xs font-bold text-slate-900" value="${r.numeric_value}" id="seqEditVal_${idx}"></td>
        <td class="p-3"><input type="text" class="w-20 border border-slate-200 rounded px-2 py-1 text-xs" value="${r.unit || ''}" id="seqEditUnit_${idx}"></td>
        <td class="p-3"><input type="text" class="w-32 border border-slate-200 rounded px-2 py-1 text-xs text-slate-600 font-medium" value="${r.ref_range_raw || ''}" id="seqEditRef_${idx}"></td>
        <td class="p-3 min-w-[180px]">
          <select id="seqEditCare_${idx}" class="w-full border border-slate-300 rounded-lg px-2.5 py-1 text-xs font-bold bg-white text-slate-800 shadow-sm focus:ring-1 focus:ring-emerald-500">
            <option value="Optimal (Maintain Routine)" ${careVal.includes('Optimal') ? 'selected' : ''}>🟢 Optimal (Maintain Routine)</option>
            <option value="Needs Extra Care (Trainer Focus)" ${careVal.includes('Extra Care') || careVal.includes('above_range') ? 'selected' : ''}>🟠 Needs Extra Care (Trainer Priority)</option>
            <option value="Needs Daily Boost (Nutrition Focus)" ${careVal.includes('Boost') || careVal.includes('below_range') ? 'selected' : ''}>🔵 Needs Daily Boost (Nutrition Focus)</option>
            <option value="High Alert (Needs Extra Care)" ${careVal.includes('Alert') || careVal.includes('critical') ? 'selected' : ''}>🔴 High Alert (Needs Extra Care)</option>
          </select>
        </td>
        <td class="p-3 min-w-[240px]">
          <textarea id="seqEditAction_${idx}" rows="2" class="w-full border border-slate-200 rounded-lg p-2 text-xs text-slate-700 bg-emerald-50/30 font-medium">${defaultAction}</textarea>
        </td>
      </tr>
    `;
  }).join("");

  // STEP 5: GRAPHICAL REPRESENTATION
  const gContainer = document.getElementById("seq5GaugesContainer");
  if (results.length) {
    gContainer.innerHTML = results.map(r => {
      const isElevated = r.status_flag === 'above_range' || r.status_flag === 'critical';
      const isLow = r.status_flag === 'below_range';
      const badgeClass = isElevated ? 'badge-elevated' : isLow ? 'badge-low' : 'badge-normal';
      const statusText = isElevated ? 'Higher Than Normal' : isLow ? 'Lower Than Normal' : 'Healthy Normal';
      const gaugePct = Math.min(100, Math.max(0, r.gauge_percentage || 50));

      return `
        <div class="p-4 rounded-xl border border-slate-200 bg-slate-50/60 space-y-3">
          <div class="flex items-center justify-between">
            <div>
              <h4 class="font-bold text-slate-900 text-sm">${r.biomarker_name}</h4>
              <p class="text-xs text-slate-500">${r.category || 'Health Test'} • Healthy Range: <strong>${r.ref_range_raw || 'Standard'}</strong></p>
            </div>
            <span class="text-xs px-2.5 py-0.5 rounded-full font-semibold ${badgeClass}">${statusText}</span>
          </div>
          <div class="space-y-1">
            <div class="range-meter-track">
              <div class="range-meter-pointer" style="left: ${gaugePct}%;"></div>
            </div>
            <div class="flex justify-between text-[10px] text-slate-400 font-medium pt-1">
              <span>Low (< ${r.ref_min || 'Min'})</span>
              <span class="font-bold text-slate-700">Your Number: ${r.numeric_value} ${r.unit || ''}</span>
              <span>High (> ${r.ref_max || 'Max'})</span>
            </div>
          </div>
        </div>
      `;
    }).join("");
  } else {
    gContainer.innerHTML = `<p class="text-xs text-slate-400 col-span-2 text-center py-4">No numbers to chart for this report.</p>`;
  }

  // STEP 6: ABNORMAL / IMPORTANT FINDINGS ("Why This Matters")
  const whyContainer = document.getElementById("seq6WhyThisMattersContainer");
  const whyList = insights.why_this_matters || [];
  if (whyList.length) {
    whyContainer.innerHTML = whyList.map(w => `
      <div class="p-4 rounded-xl border border-amber-200 bg-amber-50/40 text-xs space-y-2">
        <div class="flex items-center justify-between">
          <h4 class="font-bold text-amber-950 text-sm">${w.biomarker_name}: <span class="font-extrabold">${w.value}</span></h4>
          <span class="badge-elevated text-[10px] px-2.5 py-0.5 rounded-full font-bold">Standard Healthy Range: ${w.reference_range}</span>
        </div>
        <p class="text-amber-900"><strong>What it is:</strong> ${w.what_it_means}</p>
        <p class="text-amber-900"><strong>Why it matters for your body:</strong> ${w.why_it_matters}</p>
        <div class="bg-white/80 p-3 rounded-lg border border-amber-100">
          <p class="font-bold text-amber-950">Helpful questions to ask your doctor:</p>
          <ul class="list-disc list-inside mt-1 space-y-0.5 text-amber-900">
            ${w.what_to_discuss.map(d => `<li>${d}</li>`).join("")}
          </ul>
        </div>
      </div>
    `).join("");
  } else {
    whyContainer.innerHTML = `
      <div class="p-3.5 rounded-xl border border-emerald-200 bg-emerald-50 text-xs text-emerald-800 font-medium flex items-center space-x-2">
        <i data-lucide="check-circle" class="w-4 h-4 text-emerald-600"></i>
        <span>All your tested numbers fall comfortably within the healthy normal zone!</span>
      </div>
    `;
  }

  // STEP 7: OVERALL ANALYSIS SUMMARY
  const card = insights.overall_summary_card || {};
  document.getElementById("seq7Headline").innerText = card.headline || "Summary ready.";
  const normList = card.normal_parameters || [];
  document.getElementById("seq7NormalList").innerHTML = normList.length ? normList.map(n => `<span>✓ ${n}</span>`).join("<br>") : `<span class="italic text-slate-400">None detected</span>`;
  const attList = card.attention_parameters || [];
  document.getElementById("seq7AttentionList").innerHTML = attList.length ? attList.map(a => `<span>⚠ ${a}</span>`).join("<br>") : `<span class="italic text-slate-400">All tests are in the healthy zone!</span>`;
  document.getElementById("seq7Synthesis").innerText = card.synthesis || insights.layer_1_simple_explanation || "Summary ready.";

  // STEP 8: PREVIOUS REPORT COMPARISON
  const prevContainer = document.getElementById("seq8ComparisonContainer");
  try {
    const histRes = await fetch("/api/v1/reports/", { headers: { "Authorization": `Bearer ${authToken}` } });
    if (histRes.ok) {
      const histReports = await histRes.json();
      const otherReports = histReports.filter(r => r.id !== data.report_id);
      if (otherReports.length) {
        const prevRep = otherReports[0];
        const compRes = await fetch(`/api/v1/reports/compare?report_id_1=${prevRep.id}&report_id_2=${data.report_id}`, {
          headers: { "Authorization": `Bearer ${authToken}` }
        });
        if (compRes.ok) {
          const compData = await compRes.json();
          prevContainer.innerHTML = `
            <p class="text-xs text-slate-500 mb-2">Comparing against your last visit: <strong>${prevRep.title} (${prevRep.report_date})</strong></p>
            <div class="overflow-x-auto border border-slate-200 rounded-xl">
              <table class="w-full text-xs text-left">
                <thead class="bg-slate-100 text-slate-700 font-semibold">
                  <tr>
                    <th class="p-2.5">Health Test</th>
                    <th class="p-2.5">Previous Visit (${prevRep.report_date})</th>
                    <th class="p-2.5">Current Visit (${data.report_date})</th>
                    <th class="p-2.5">Difference</th>
                    <th class="p-2.5">Direction</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-100">
                  ${compData.comparison_table.map(row => `
                    <tr>
                      <td class="p-2.5 font-bold">${row.parameter}</td>
                      <td class="p-2.5">${row.report_1_value !== null ? row.report_1_value + ' ' + row.unit : '--'}</td>
                      <td class="p-2.5 font-semibold">${row.report_2_value !== null ? row.report_2_value + ' ' + row.unit : '--'}</td>
                      <td class="p-2.5 font-bold ${row.delta > 0 ? 'text-rose-600' : row.delta < 0 ? 'text-emerald-600' : 'text-slate-500'}">
                        ${row.delta !== null ? (row.delta > 0 ? '+' : '') + row.delta + ' ' + row.unit : '--'}
                      </td>
                      <td class="p-2.5">
                        <span class="text-[10px] font-semibold px-2 py-0.5 rounded-full ${row.trend === 'Increased' ? 'bg-amber-50 text-amber-800' : row.trend === 'Decreased' ? 'bg-sky-50 text-sky-800' : 'bg-slate-100 text-slate-700'}">
                          ${row.trend === 'Increased' ? '📈 Higher' : row.trend === 'Decreased' ? '📉 Lower' : '➡️ Stable'}
                        </span>
                      </td>
                    </tr>
                  `).join("")}
                </tbody>
              </table>
            </div>
          `;
        }
      } else {
        prevContainer.innerHTML = `
          <p class="text-xs text-slate-500 bg-slate-50 p-3.5 rounded-xl border border-slate-200">
            This is your first saved report. When you upload your next report, we will automatically show you a side-by-side comparison of your improvements here!
          </p>
        `;
      }
    }
  } catch (e) {
    console.error(e);
  }

  // STEP 10: DIET GUIDANCE
  const sugg = insights.personalized_suggestions || {};
  const dietList = sugg.diet || [];
  document.getElementById("seq10DietGuidance").innerHTML = dietList.map(d => `<p>• ${d}</p>`).join("");

  // STEP 11: EXERCISE GUIDANCE
  const actList = sugg.physical_activity || [];
  document.getElementById("seq11ExerciseGuidance").innerHTML = actList.map(a => `<p>• ${a}</p>`).join("");

  // STEP 12: MEDICATION NOTE
  document.getElementById("seq12MedicationNote").innerText = sugg.medication_treatment || "Never start, stop, or change any medication on your own. Always consult directly with your doctor.";

  // STEP 13: PHYSICIAN QUESTIONS
  const docQuestions = insights.layer_5_questions_for_doctor || [];
  document.getElementById("seq13PhysicianQuestions").innerHTML = docQuestions.map(q => `<li>• ${q}</li>`).join("");

  // STEP 14: DISCLAIMER
  document.getElementById("seq14Disclaimer").innerText = insights.disclaimer || "A friendly note: Always discuss your test results directly with your healthcare provider.";

  lucide.createIcons();
}

function discardAnalysis() {
  document.getElementById("analysisSequentialContainer").classList.add("hidden");
  document.getElementById("analysisEmptyNotice").classList.remove("hidden");
  currentActiveReportData = null;
  pendingReportId = null;
}

// Confirm & Save
async function confirmAndSaveCurrentReport() {
  if (!pendingReportId) return;

  const rows = document.querySelectorAll("#seq4ResultsTableBody tr");
  const results = [];
  rows.forEach((row, idx) => {
    const nameEl = document.getElementById(`seqEditName_${idx}`);
    const valEl = document.getElementById(`seqEditVal_${idx}`);
    const unitEl = document.getElementById(`seqEditUnit_${idx}`);
    const refEl = document.getElementById(`seqEditRef_${idx}`);

    if (nameEl && valEl) {
      results.push({
        biomarker_name: nameEl.value,
        numeric_value: parseFloat(valEl.value) || null,
        unit: unitEl.value,
        ref_range_raw: refEl.value,
        status_flag: "within_range"
      });
    }
  });

  try {
    const res = await fetch(`/api/v1/reports/${pendingReportId}/verify`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${authToken}` },
      body: JSON.stringify({ results: results })
    });

    if (res.ok) {
      alert("✓ Report saved to your personal health timeline!");
      discardAnalysis();
      switchTab("history");
    }
  } catch (e) {
    console.error("Save error:", e);
    alert("Error saving report.");
  }
}

// Patient History Loader
async function loadPatientHistory() {
  try {
    const searchVal = (document.getElementById("historySearchInput") || {}).value || "";
    const sortVal = (document.getElementById("historySortOrder") || {}).value || "desc";

    const res = await fetch(`/api/v1/reports/?search=${encodeURIComponent(searchVal)}&sort_order=${sortVal}`, {
      headers: { "Authorization": `Bearer ${authToken}` }
    });

    const container = document.getElementById("patientHistoryListContainer");
    if (!container) return;

    if (!res.ok) {
      container.innerHTML = `<p class="text-xs text-rose-500 py-4">Error loading past reports.</p>`;
      return;
    }

    const reports = await res.json();
    allReportsCache = reports;

    if (!reports.length) {
      container.innerHTML = `
        <div class="text-center py-16 bg-white rounded-2xl border border-dashed border-slate-200 space-y-3">
          <i data-lucide="folder" class="w-12 h-12 text-slate-300 mx-auto"></i>
          <h4 class="font-bold text-slate-800 text-base">Your saved reports will appear here after you upload them.</h4>
          <p class="text-xs text-slate-400 max-w-sm mx-auto">Upload any blood test, lipid panel, or doctor prescription to start building your personal health timeline.</p>
          <button onclick="switchTab('upload')" class="px-5 py-2.5 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-bold shadow-sm">
            Upload Your First Report
          </button>
        </div>
      `;
      lucide.createIcons();
      return;
    }

    container.innerHTML = reports.map((r, index) => {
      const ext = (r.file_type || 'TXT').toUpperCase();
      const extClass = ext === 'PDF' ? 'bg-rose-50 text-rose-700 border-rose-200' : 'bg-sky-50 text-sky-700 border-sky-200';
      const hasPrev = index < reports.length - 1;
      const prevId = hasPrev ? reports[index + 1].id : null;

      return `
        <div class="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4 hover:border-sky-300 transition" id="reportCard_${r.id}">
          <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 pb-3 border-b border-slate-100">
            <div class="flex items-start space-x-3.5">
              <div class="w-11 h-11 rounded-xl border ${extClass} flex flex-col items-center justify-center flex-shrink-0 font-bold">
                <i data-lucide="file-text" class="w-4 h-4 mb-0.5"></i>
                <span class="text-[9px]">${ext}</span>
              </div>
              <div>
                <div class="flex flex-wrap items-center gap-2">
                  <h4 class="font-bold text-slate-900 text-base">${r.title}</h4>
                  <span class="badge-normal text-[11px] px-2.5 py-0.5 rounded-full font-semibold">✓ Saved in Timeline</span>
                </div>
                <p class="text-xs text-slate-500 mt-1 flex flex-wrap items-center gap-x-3 gap-y-1">
                  <span><strong>Date:</strong> ${r.report_date}</span>
                  <span>•</span>
                  <span><strong>Testing Lab:</strong> ${r.laboratory_name || 'Diagnostic Laboratory'}</span>
                  <span>•</span>
                  <span><strong>File:</strong> <code class="text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded text-[11px]">${r.file_name || 'document'}</code> (${r.file_size_kb || 4.2} KB)</span>
                </p>
              </div>
            </div>

            <!-- Actions -->
            <div class="flex flex-wrap items-center gap-2">
              <button onclick="viewOriginalDocument('${r.id}')" class="px-3 py-2 bg-sky-50 hover:bg-sky-100 text-sky-700 font-semibold text-xs rounded-xl border border-sky-200 transition flex items-center space-x-1.5 shadow-sm">
                <i data-lucide="eye" class="w-3.5 h-3.5"></i>
                <span>View Document</span>
              </button>

              <button onclick="viewReportAnalysisWorkspaceDirectly('${r.id}')" class="px-3 py-2 bg-purple-50 hover:bg-purple-100 text-purple-700 font-semibold text-xs rounded-xl border border-purple-200 transition flex items-center space-x-1.5 shadow-sm">
                <i data-lucide="sparkles" class="w-3.5 h-3.5 text-purple-600"></i>
                <span>Plain Breakdown</span>
              </button>

              <button onclick="viewReportGauges('${r.id}')" class="px-3 py-2 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 font-semibold text-xs rounded-xl border border-emerald-200 transition flex items-center space-x-1.5 shadow-sm">
                <i data-lucide="bar-chart-3" class="w-3.5 h-3.5 text-emerald-600"></i>
                <span>Visual Meters</span>
              </button>

              ${hasPrev ? `
                <button onclick="compareTwoSpecificReports('${r.id}', '${prevId}')" class="px-3 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-semibold text-xs rounded-xl border border-indigo-200 transition flex items-center space-x-1.5 shadow-sm">
                  <i data-lucide="git-compare" class="w-3.5 h-3.5 text-indigo-600"></i>
                  <span>Compare Changes</span>
                </button>
              ` : ''}

              <button onclick="openDeleteConfirmModal('${r.id}', '${r.title.replace(/'/g, "\\'")}')" class="px-3 py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 font-semibold text-xs rounded-xl border border-rose-200 transition flex items-center space-x-1 shadow-sm">
                <i data-lucide="trash-2" class="w-3.5 h-3.5 text-rose-600"></i>
                <span>Delete</span>
              </button>
            </div>
          </div>

          <!-- Biomarkers Grid -->
          <div>
            <p class="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">Tested Numbers in This Report (${r.results.length}):</p>
            <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2.5">
              ${r.results.map(res => `
                <div class="p-2.5 rounded-xl border text-xs ${res.status_flag === 'above_range' ? 'badge-elevated' : res.status_flag === 'below_range' ? 'badge-low' : 'badge-normal'} space-y-0.5">
                  <p class="font-bold truncate text-slate-900">${res.biomarker_name}</p>
                  <p class="font-extrabold text-sm">${res.numeric_value || 'N/A'} <span class="font-normal text-xs text-slate-500">${res.unit || ''}</span></p>
                  <p class="text-[10px] opacity-75 font-medium">${res.ref_range_raw || 'Healthy Range'}</p>
                </div>
              `).join("")}
            </div>
          </div>
        </div>
      `;
    }).join("");
    lucide.createIcons();
  } catch (e) {
    console.error(e);
  }
}

function filterPatientHistory() {
  loadPatientHistory();
}

async function viewReportAnalysisWorkspaceDirectly(reportId) {
  try {
    const res = await fetch(`/api/v1/reports/${reportId}`, { headers: { "Authorization": `Bearer ${authToken}` } });
    if (!res.ok) return;
    const r = await res.json();
    currentActiveReportData = {
      report_id: r.id,
      title: r.title,
      report_date: r.report_date,
      file_name: r.file_name,
      results_extracted_count: r.results.length,
      results: r.results,
      ai_insights: r.ai_summary_layers
    };
    pendingReportId = r.id;
    switchTab("analysis");
    await render14StepAnalysis(currentActiveReportData);
  } catch (e) {
    console.error(e);
  }
}

// View Graphs Modal
async function viewReportGauges(reportId) {
  try {
    const res = await fetch(`/api/v1/reports/${reportId}`, { headers: { "Authorization": `Bearer ${authToken}` } });
    if (!res.ok) return;
    const r = await res.json();

    document.getElementById("reportGaugesTitle").innerText = `Visual Range Meters • ${r.title}`;
    document.getElementById("reportGaugesMeta").innerText = `Date: ${r.report_date} • ${r.results.length} Health Tests Checked`;

    const list = document.getElementById("reportGaugesList");
    list.innerHTML = r.results.map(b => {
      const isElevated = b.status_flag === 'above_range' || b.status_flag === 'critical';
      const isLow = b.status_flag === 'below_range';
      const badgeClass = isElevated ? 'badge-elevated' : isLow ? 'badge-low' : 'badge-normal';
      const statusText = isElevated ? 'Higher Than Normal' : isLow ? 'Lower Than Normal' : 'Healthy Normal';
      const gaugePct = b.status_flag === 'above_range' ? 95 : b.status_flag === 'below_range' ? 10 : 50;

      return `
        <div class="p-4 rounded-xl border border-slate-200 bg-slate-50/60 space-y-3">
          <div class="flex items-center justify-between">
            <div>
              <h4 class="font-bold text-slate-900 text-sm">${b.biomarker_name}</h4>
              <p class="text-xs text-slate-500">Healthy Standard: <strong>${b.ref_range_raw || 'Standard Range'}</strong></p>
            </div>
            <span class="text-xs px-2.5 py-0.5 rounded-full font-semibold ${badgeClass}">${statusText}</span>
          </div>
          <div class="space-y-1">
            <div class="range-meter-track">
              <div class="range-meter-pointer" style="left: ${gaugePct}%;"></div>
            </div>
            <div class="flex justify-between text-[10px] text-slate-400 font-medium pt-1">
              <span>Low Range</span>
              <span class="font-bold text-slate-700">Your Number: ${b.numeric_value} ${b.unit || ''}</span>
              <span>High Range</span>
            </div>
          </div>
        </div>
      `;
    }).join("");

    document.getElementById("reportGaugesModal").classList.remove("hidden");
    lucide.createIcons();
  } catch (e) {
    console.error(e);
  }
}

// Delete Handlers
function openDeleteConfirmModal(reportId, reportTitle) {
  reportToDeleteId = reportId;
  document.getElementById("deleteModalReportTitle").innerText = reportTitle || "Medical Report";
  document.getElementById("deleteConfirmModal").classList.remove("hidden");
  lucide.createIcons();
}

function closeDeleteConfirmModal() {
  reportToDeleteId = null;
  document.getElementById("deleteConfirmModal").classList.add("hidden");
}

async function executeReportDeletion() {
  if (!reportToDeleteId) return;
  try {
    const res = await fetch(`/api/v1/reports/${reportToDeleteId}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${authToken}` }
    });

    if (res.ok) {
      closeDeleteConfirmModal();
      await loadPatientHistory();
      await loadDashboard();
  loadNotificationFeed();
  startBackgroundReminderChecker();
      await loadTrends();
      alert("✓ Report permanently deleted.");
    } else {
      alert("Failed to delete report.");
    }
  } catch (e) {
    console.error("Delete error:", e);
  }
}

function openDeleteAllConfirmModal() {
  document.getElementById("deleteAllConfirmModal").classList.remove("hidden");
  lucide.createIcons();
}

function closeDeleteAllConfirmModal() {
  document.getElementById("deleteAllConfirmModal").classList.add("hidden");
}

async function executeDeleteAllHistory() {
  try {
    const res = await fetch("/api/v1/reports/clear-all", {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${authToken}` }
    });

    if (res.ok) {
      closeDeleteAllConfirmModal();
      await loadPatientHistory();
      await loadDashboard();
  loadNotificationFeed();
  startBackgroundReminderChecker();
      await loadTrends();
      alert("✓ All medical history has been cleared.");
    } else {
      alert("Failed to clear history.");
    }
  } catch (e) {
    console.error("Delete all error:", e);
  }
}

// Dynamic Dashboard Loader in Plain Language
async function loadDashboard() {
  if (!authToken) await autoLoginDemo();
  try {
    const [dashRes, repRes] = await Promise.all([
      fetch("/api/v1/wellness/dashboard-summary", { headers: { "Authorization": `Bearer ${authToken}` } }),
      fetch("/api/v1/reports/", { headers: { "Authorization": `Bearer ${authToken}` } })
    ]);

    const container = document.getElementById("dashboardDynamicContent");
    if (!container) return;

    let dashData = dashRes.ok ? await dashRes.json() : { has_data: false };
    let reports = repRes.ok ? await repRes.json() : [];

    if (!dashData.has_data && reports.length === 0) {
      container.innerHTML = `
        <div class="space-y-6">
          <!-- HERO WELCOME BANNER WITH COLOR ACCENTS -->
          <div class="bg-gradient-to-r from-emerald-950 via-teal-900 to-slate-950 rounded-3xl p-8 text-white shadow-xl border border-emerald-700/40 relative overflow-hidden">
            <div class="absolute -right-10 -bottom-10 w-72 h-72 bg-emerald-500/20 rounded-full blur-3xl pointer-events-none"></div>
            <div class="relative z-10 flex flex-col md:flex-row items-center justify-between gap-6">
              <div class="space-y-3 max-w-xl text-center md:text-left">
                <div class="inline-flex items-center space-x-2 bg-emerald-400/20 text-emerald-300 border border-emerald-400/30 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">
                  <i data-lucide="sparkles" class="w-3.5 h-3.5"></i>
                  <span>Ready for Your Health Reports</span>
                </div>
                <h2 class="text-3xl sm:text-4xl font-black tracking-tight text-white">Welcome to Your Personal Health Guide</h2>
                <p class="text-teal-100 text-sm leading-relaxed">
                  Upload any blood test, lab panel, or prescription to instantly turn complex medical numbers into clear, plain-English explanations with custom nutrition and movement guidance.
                </p>
                <div class="pt-2 flex flex-wrap items-center justify-center md:justify-start gap-3">
                  <button onclick="switchTab('upload')" class="px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-400 hover:from-emerald-600 hover:to-teal-500 text-white rounded-2xl font-black text-sm shadow-lg shadow-emerald-950/40 transition-all flex items-center space-x-2">
                    <i data-lucide="upload-cloud" class="w-4 h-4"></i>
                    <span>UPLOAD YOUR FIRST MEDICAL REPORT</span>
                  </button>
                  <button onclick="loadSampleReport('glucose')" class="px-5 py-3 bg-white/10 hover:bg-white/20 text-white border border-white/20 rounded-2xl font-bold text-xs transition flex items-center space-x-2">
                    <i data-lucide="zap" class="w-4 h-4 text-amber-300"></i>
                    <span>Try 1-Click Blood Sugar Demo</span>
                  </button>
                </div>
              </div>

              <!-- Quick Demo Card Pill -->
              <div class="bg-white/10 backdrop-blur-md border border-white/20 p-5 rounded-2xl text-xs space-y-3 min-w-[280px]">
                <span class="text-teal-200 font-bold uppercase tracking-wider text-[10px] block">What You Get Instantly</span>
                <div class="space-y-2 text-teal-50 font-medium">
                  <div class="flex items-center space-x-2"><i data-lucide="check-circle" class="w-4 h-4 text-emerald-400"></i><span>Plain-English translations</span></div>
                  <div class="flex items-center space-x-2"><i data-lucide="check-circle" class="w-4 h-4 text-emerald-400"></i><span>Visual Green Zone meters</span></div>
                  <div class="flex items-center space-x-2"><i data-lucide="check-circle" class="w-4 h-4 text-emerald-400"></i><span>5-meal targeted food guide</span></div>
                  <div class="flex items-center space-x-2"><i data-lucide="check-circle" class="w-4 h-4 text-emerald-400"></i><span>Easy daily movement plan</span></div>
                </div>
              </div>
            </div>
          </div>

          <!-- 4 VIBRANT FEATURE HIGHLIGHT CARDS -->
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="p-6 rounded-2xl bg-gradient-to-br from-sky-50 to-blue-50/60 border border-sky-200/80 shadow-sm space-y-2 hover-lift">
              <div class="w-10 h-10 rounded-xl bg-sky-500 text-white flex items-center justify-center shadow-md shadow-sky-200">
                <i data-lucide="file-text" class="w-5 h-5"></i>
              </div>
              <h4 class="font-black text-sky-950 text-base">Simple Language</h4>
              <p class="text-xs text-sky-800 leading-relaxed font-medium">No confusing medical jargon. Understand what Fasting Glucose, HbA1c, and Lipids mean in everyday terms.</p>
            </div>

            <div class="p-6 rounded-2xl bg-gradient-to-br from-emerald-50 to-teal-50/60 border border-emerald-200/80 shadow-sm space-y-2 hover-lift">
              <div class="w-10 h-10 rounded-xl bg-emerald-500 text-white flex items-center justify-center shadow-md shadow-emerald-200">
                <i data-lucide="bar-chart-2" class="w-5 h-5"></i>
              </div>
              <h4 class="font-black text-emerald-950 text-base">Visual Gauge Meters</h4>
              <p class="text-xs text-emerald-800 leading-relaxed font-medium">Clear color-coded meters show immediately whether you are in the safe green zone or need extra care.</p>
            </div>

            <div class="p-6 rounded-2xl bg-gradient-to-br from-indigo-50 to-purple-50/60 border border-indigo-200/80 shadow-sm space-y-2 hover-lift">
              <div class="w-10 h-10 rounded-xl bg-indigo-500 text-white flex items-center justify-center shadow-md shadow-indigo-200">
                <i data-lucide="utensils" class="w-5 h-5"></i>
              </div>
              <h4 class="font-black text-indigo-950 text-base">Report-Driven Meals</h4>
              <p class="text-xs text-indigo-800 leading-relaxed font-medium">5 daily meal ideas tailored specifically to your tested blood results with transparent reasons why.</p>
            </div>

            <div class="p-6 rounded-2xl bg-gradient-to-br from-amber-50 to-orange-50/60 border border-amber-200/80 shadow-sm space-y-2 hover-lift">
              <div class="w-10 h-10 rounded-xl bg-amber-500 text-white flex items-center justify-center shadow-md shadow-amber-200">
                <i data-lucide="activity" class="w-5 h-5"></i>
              </div>
              <h4 class="font-black text-amber-950 text-base">Personal Trainer Care</h4>
              <p class="text-xs text-amber-800 leading-relaxed font-medium">Daily self-care movement options and gentle walking routines customized to your health levels.</p>
            </div>
          </div>
        </div>
      `;
      lucide.createIcons();
      return;
    }

    const lr = dashData.latest_report || reports[0];
    const impFindings = dashData.important_findings || [];
    const reminders = (dashData.today_overview && dashData.today_overview.upcoming_reminders) || [];

    const demo = dashData.patient_demographics || {};
    const patientName = demo.patient_name || demo.name || "Not Specified in Report";
    const accountName = demo.account_holder_name || (currentUserData && (currentUserData.full_name || currentUserData.email || currentUserData.phone_number)) || "Account Profile";
    const patientAge = demo.age || "Not Specified in Report";
    const patientWeight = demo.weight || "Not Specified in Report";
    const patientGender = demo.gender || "Not Specified in Report";
    const demoSource = demo.source || "Extracted from Latest Medical Report";

    const topBadge = document.getElementById("userBadge");
    if (topBadge) {
      topBadge.innerHTML = `<i data-lucide="activity" class="w-3.5 h-3.5 mr-1 text-emerald-400"></i> Report Patient: <strong>${patientName}</strong>`;
    }

    container.innerHTML = `
      <!-- VIBRANT MODERN CLINICAL HERO BANNER -->
      <div class="bg-gradient-to-r from-emerald-950 via-teal-950 to-slate-950 rounded-3xl p-7 text-white shadow-xl border border-emerald-800/50 space-y-5 relative overflow-hidden">
        <div class="absolute -right-10 -bottom-10 w-60 h-60 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>
        <div class="absolute -left-10 -top-10 w-60 h-60 bg-teal-500/10 rounded-full blur-3xl pointer-events-none"></div>

        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-6 relative z-10">
          <div class="flex items-start space-x-4.5">
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-400 text-white flex items-center justify-center text-3xl font-black shadow-lg shadow-emerald-900/50 flex-shrink-0">
              🩺
            </div>
            <div>
              <div class="flex items-center space-x-2">
                <span class="text-[10px] bg-emerald-400/20 text-emerald-300 font-extrabold px-3 py-0.5 rounded-full border border-emerald-400/40 uppercase tracking-wider">REPORT PATIENT NAME</span>
                <span class="text-[11px] text-teal-200 font-medium">• ${demoSource}</span>
              </div>
              <h2 class="text-2xl sm:text-3xl font-black text-white mt-1.5 tracking-tight">${patientName}</h2>
              <div class="flex items-center space-x-3 mt-1.5 text-xs text-teal-200">
                <span class="flex items-center bg-white/10 px-2.5 py-0.5 rounded-lg border border-white/10">
                  <i data-lucide="user-check" class="w-3.5 h-3.5 mr-1.5 text-emerald-400"></i> Account Profile: <strong class="ml-1 text-white">${accountName}</strong>
                </span>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-3 gap-3 text-xs bg-white/10 backdrop-blur-md p-4 rounded-2xl border border-white/15 min-w-[320px]">
            <div class="text-center sm:text-left">
              <span class="text-teal-300 text-[10px] uppercase font-bold tracking-wider block">Patient Age</span>
              <p class="font-extrabold text-white text-base mt-0.5">${patientAge}</p>
            </div>
            <div class="text-center sm:text-left border-x border-white/15 px-2">
              <span class="text-teal-300 text-[10px] uppercase font-bold tracking-wider block">Patient Weight</span>
              <p class="font-extrabold text-white text-base mt-0.5">${patientWeight}</p>
            </div>
            <div class="text-center sm:text-left">
              <span class="text-teal-300 text-[10px] uppercase font-bold tracking-wider block">Patient Gender</span>
              <p class="font-extrabold text-white text-base mt-0.5">${patientGender}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- VIBRANT STAT TILES WITH REFINED ACCENT COLORS -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="glass-card hover-lift p-5 rounded-2xl border border-sky-100 bg-gradient-to-br from-sky-50/80 to-white shadow-sm space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold text-sky-800 uppercase tracking-wider">Reports on File</span>
            <div class="w-8 h-8 rounded-xl bg-sky-500 text-white flex items-center justify-center shadow-sm">
              <i data-lucide="folder-check" class="w-4 h-4"></i>
            </div>
          </div>
          <p class="text-3xl font-black text-sky-950">${dashData.total_reports || reports.length}</p>
          <p class="text-[11px] text-sky-700 font-semibold flex items-center">
            <i data-lucide="check" class="w-3 h-3 mr-1 text-sky-600"></i> Saved in timeline
          </p>
        </div>

        <div class="glass-card hover-lift p-5 rounded-2xl border border-emerald-100 bg-gradient-to-br from-emerald-50/80 to-white shadow-sm space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold text-emerald-800 uppercase tracking-wider">Health Numbers Checked</span>
            <div class="w-8 h-8 rounded-xl bg-emerald-500 text-white flex items-center justify-center shadow-sm">
              <i data-lucide="microscope" class="w-4 h-4"></i>
            </div>
          </div>
          <p class="text-3xl font-black text-emerald-950">${dashData.total_biomarkers_extracted || 0}</p>
          <p class="text-[11px] text-emerald-700 font-semibold flex items-center">
            <i data-lucide="sparkles" class="w-3 h-3 mr-1 text-emerald-600"></i> From blood tests
          </p>
        </div>

        <div class="glass-card hover-lift p-5 rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50/80 to-white shadow-sm space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold text-indigo-800 uppercase tracking-wider">Active Medicines</span>
            <div class="w-8 h-8 rounded-xl bg-indigo-500 text-white flex items-center justify-center shadow-sm">
              <i data-lucide="pill" class="w-4 h-4"></i>
            </div>
          </div>
          <p class="text-3xl font-black text-indigo-950">${dashData.active_medications_count || 0}</p>
          <p class="text-[11px] text-indigo-700 font-semibold flex items-center">
            <i data-lucide="clock" class="w-3 h-3 mr-1 text-indigo-600"></i> Daily reminders
          </p>
        </div>

        <div class="glass-card hover-lift p-5 rounded-2xl border border-cyan-100 bg-gradient-to-br from-cyan-50/80 to-white shadow-sm space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold text-cyan-800 uppercase tracking-wider">Today's Water</span>
            <div class="w-8 h-8 rounded-xl bg-cyan-500 text-white flex items-center justify-center shadow-sm">
              <i data-lucide="droplet" class="w-4 h-4"></i>
            </div>
          </div>
          <p class="text-3xl font-black text-cyan-950">${(dashData.today_overview && dashData.today_overview.water_logged_liters) || 0} <span class="text-base font-bold text-cyan-800">L</span></p>
          <button onclick="openMetricModal('water')" class="text-[11px] text-cyan-700 font-bold hover:text-cyan-900 bg-cyan-100/70 hover:bg-cyan-100 px-2.5 py-1 rounded-lg transition inline-flex items-center space-x-1">
            <span>+ Log 1 Glass (250ml)</span>
          </button>
        </div>
      </div>

      <!-- MAIN DASHBOARD CONTENT (LATEST REPORT & TODAY'S SCHEDULE) -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2 glass-card rounded-3xl border border-slate-200/80 p-6 sm:p-7 shadow-sm space-y-5 bg-white">
          <div class="flex items-center justify-between border-b border-slate-100 pb-4">
            <div class="flex items-center space-x-2.5">
              <div class="w-8 h-8 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
                <i data-lucide="file-spreadsheet" class="w-4 h-4"></i>
              </div>
              <h3 class="font-extrabold text-slate-900 text-base">Your Latest Medical Report</h3>
            </div>
            ${lr ? `<span class="badge-normal text-xs px-3 py-1 rounded-full font-bold">✓ Verified & Analyzed</span>` : ''}
          </div>

          ${lr ? `
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl bg-gradient-to-r from-emerald-50/50 via-teal-50/30 to-slate-50 border border-emerald-100/80">
              <div>
                <h4 class="font-black text-slate-900 text-lg">${lr.title}</h4>
                <p class="text-xs text-slate-600 mt-1 flex flex-wrap items-center gap-x-3 gap-y-1">
                  <span>📅 <strong>Date:</strong> ${lr.report_date}</span>
                  <span>•</span>
                  <span>🏥 <strong>Lab:</strong> ${lr.laboratory_name || 'Diagnostic Laboratory'}</span>
                </p>
              </div>
              <div class="flex items-center space-x-2">
                <button onclick="viewOriginalDocument('${lr.id}')" class="px-3.5 py-2 bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 rounded-xl text-xs font-bold flex items-center space-x-1.5 shadow-sm transition">
                  <i data-lucide="eye" class="w-3.5 h-3.5 text-slate-500"></i>
                  <span>View Doc</span>
                </button>
                <button onclick="viewReportAnalysisWorkspaceDirectly('${lr.id}')" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-md shadow-emerald-200 transition flex items-center space-x-1.5">
                  <i data-lucide="sparkles" class="w-3.5 h-3.5"></i>
                  <span>Plain Breakdown</span>
                </button>
              </div>
            </div>
          ` : `<p class="text-xs text-slate-400 py-6 text-center">No report on file yet. Upload your first report to see a plain-English breakdown.</p>`}

          <div>
            <h4 class="font-bold text-slate-900 text-xs uppercase tracking-wider mb-3">Key Biomarkers from Your Report:</h4>
            ${impFindings.length ? `
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                ${impFindings.map(f => `
                  <div class="p-3.5 rounded-2xl border ${f.status === 'above_range' ? 'bg-rose-50/80 border-rose-200 text-rose-950' : 'bg-amber-50/80 border-amber-200 text-amber-950'} text-xs space-y-1 hover-lift">
                    <div class="flex items-center justify-between">
                      <p class="font-extrabold text-slate-900">${f.biomarker_name}</p>
                      <span class="text-[10px] font-bold px-2 py-0.5 rounded-full ${f.status === 'above_range' ? 'bg-rose-200/60 text-rose-800' : 'bg-amber-200/60 text-amber-800'}">
                        ${f.status === 'above_range' ? 'Higher than normal' : 'Lower than normal'}
                      </span>
                    </div>
                    <p class="font-black text-base">${f.value} <span class="font-semibold text-xs text-slate-500">(Healthy: ${f.reference_range})</span></p>
                  </div>
                `).join("")}
              </div>
            ` : `
              <div class="text-xs text-emerald-900 bg-emerald-50 border border-emerald-200 p-4 rounded-2xl font-semibold flex items-center space-x-2">
                <i data-lucide="check-circle" class="w-4 h-4 text-emerald-600"></i>
                <span>All tested parameters fall comfortably within healthy reference intervals.</span>
              </div>
            `}
          </div>
        </div>

        <div class="glass-card rounded-3xl border border-slate-200/80 p-6 sm:p-7 shadow-sm space-y-5 bg-white flex flex-col justify-between">
          <div class="space-y-4">
            <div class="flex items-center justify-between border-b border-slate-100 pb-4">
              <div class="flex items-center space-x-2.5">
                <div class="w-8 h-8 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center">
                  <i data-lucide="calendar-check" class="w-4 h-4"></i>
                </div>
                <h3 class="font-extrabold text-slate-900 text-base">Today's Care Routine</h3>
              </div>
              <span class="text-xs font-bold text-slate-400 bg-slate-100 px-2.5 py-1 rounded-full">${new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
            </div>

            <div class="space-y-2.5 text-xs max-h-[280px] overflow-y-auto pr-1">
              ${reminders.length ? reminders.map(r => `
                <div class="flex items-center justify-between p-3 rounded-2xl border border-slate-100 bg-slate-50/80 hover:bg-slate-100/60 transition">
                  <div class="flex items-center space-x-3">
                    <div class="w-8 h-8 rounded-xl ${r.type === 'MEDICATION' ? 'bg-indigo-100 text-indigo-700' : 'bg-amber-100 text-amber-700'} flex items-center justify-center flex-shrink-0 font-bold">
                      <i data-lucide="${r.icon || 'bell'}" class="w-4 h-4"></i>
                    </div>
                    <div>
                      <p class="font-bold text-slate-900">${r.title}</p>
                      <p class="text-[10px] text-slate-400 font-semibold">${r.type === 'MEDICATION' ? 'Medicine Reminder' : 'Nutritional Timing'}</p>
                    </div>
                  </div>
                  <span class="font-extrabold text-slate-800 bg-white px-2.5 py-1 rounded-lg border border-slate-200/80 shadow-2xs">${r.time}</span>
                </div>
              `).join("") : `
                <div class="text-center py-8 space-y-1">
                  <p class="text-xs text-slate-400 font-medium">No active reminders scheduled for today.</p>
                  <p class="text-[11px] text-slate-400">Timers automatically sync from your medical plan.</p>
                </div>
              `}
            </div>
          </div>

          <button onclick="switchTab('notifications')" class="w-full py-2.5 bg-slate-100 hover:bg-emerald-50 hover:text-emerald-800 text-slate-700 rounded-xl text-xs font-bold border border-slate-200 transition shadow-2xs">
            ⚙ Manage Daily Reminders
          </button>
        </div>
      </div>
    `;
    lucide.createIcons();
  } catch (e) {
    console.error("Dashboard error:", e);
  }
}

// Comparison Modal in Plain Language
async function compareTwoSpecificReports(r1Id, r2Id) {
  try {
    const res = await fetch(`/api/v1/reports/compare?report_id_1=${r1Id}&report_id_2=${r2Id}`, {
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    if (!res.ok) return;

    const data = await res.json();
    document.getElementById("compareTitle").innerText = `How Your Numbers Changed: ${data.report_1.title} vs ${data.report_2.title}`;
    document.getElementById("compareMeta").innerText = `Comparing ${data.report_1.date} to ${data.report_2.date}`;
    document.getElementById("compCol1").innerText = `Earlier Visit (${data.report_1.date})`;
    document.getElementById("compCol2").innerText = `Later Visit (${data.report_2.date})`;

    const tbody = document.getElementById("comparisonTableBody");
    tbody.innerHTML = data.comparison_table.map(row => {
      const isDeltaPositive = row.delta > 0;
      const isDeltaNegative = row.delta < 0;
      const deltaClass = isDeltaPositive ? 'text-rose-600 font-bold' : isDeltaNegative ? 'text-emerald-600 font-bold' : 'text-slate-500';

      return `
        <tr>
          <td class="p-3 font-bold text-slate-900">${row.parameter}</td>
          <td class="p-3">${row.report_1_value !== null ? row.report_1_value + ' ' + row.unit : '<span class="text-slate-400">Not Tested</span>'}</td>
          <td class="p-3 font-semibold">${row.report_2_value !== null ? row.report_2_value + ' ' + row.unit : '<span class="text-slate-400">Not Tested</span>'}</td>
          <td class="p-3 ${deltaClass}">${row.delta !== null ? (row.delta > 0 ? '+' : '') + row.delta + ' ' + row.unit : '--'}</td>
          <td class="p-3 ${deltaClass}">${row.percent_change !== null ? (row.percent_change > 0 ? '+' : '') + row.percent_change + '%' : '--'}</td>
          <td class="p-3">
            <span class="text-[11px] font-semibold px-2 py-0.5 rounded-full ${row.trend === 'Increased' ? 'bg-amber-50 text-amber-800' : row.trend === 'Decreased' ? 'bg-sky-50 text-sky-800' : 'bg-slate-100 text-slate-700'}">
              ${row.trend === 'Increased' ? '📈 Higher' : row.trend === 'Decreased' ? '📉 Lower' : '➡️ Stable'}
            </span>
          </td>
        </tr>
      `;
    }).join("");

    document.getElementById("comparisonModal").classList.remove("hidden");
    lucide.createIcons();
  } catch (e) {
    console.error(e);
  }
}

function closeComparisonModal() {
  document.getElementById("comparisonModal").classList.add("hidden");
}

// Health Trends Loader
async function loadTrends() {
  try {
    const res = await fetch("/api/v1/trends/biomarkers", { headers: { "Authorization": `Bearer ${authToken}` } });
    if (!res.ok) return;

    const data = await res.json();
    allTrendsData = data;

    const container = document.getElementById("trendsDynamicContent");
    if (!container) return;

    if (!data.has_sufficient_data || !data.trends.length) {
      container.innerHTML = `
        <div class="bg-white rounded-2xl border border-dashed border-slate-200 p-12 text-center space-y-3">
          <i data-lucide="trending-up" class="w-12 h-12 text-slate-300 mx-auto"></i>
          <h4 class="font-bold text-slate-800 text-base">More reports needed to show your health progress line.</h4>
          <p class="text-xs text-slate-400 max-w-md mx-auto">Upload at least 2 reports containing matching tests (like Fasting Blood Sugar, HbA1c, or Cholesterol) to see your progress chart over time.</p>
          <button onclick="switchTab('upload')" class="px-5 py-2.5 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-bold shadow-sm">
            Upload Follow-up Report
          </button>
        </div>
      `;
      lucide.createIcons();
      return;
    }

    const select = document.getElementById("trendBiomarkerSelect");
    select.innerHTML = `<option value="ALL">All Tracked Tests (${data.total_biomarkers_tracked})</option>` +
      data.trends.map(t => `<option value="${t.biomarker_code}">${t.biomarker_name}</option>`).join("");

    container.innerHTML = `
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        ${data.trends.map(t => `
          <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-2">
            <div class="flex items-center justify-between">
              <h4 class="font-bold text-slate-900 text-sm truncate">${t.biomarker_name}</h4>
              <span class="text-[11px] font-semibold px-2 py-0.5 rounded-full ${t.trend_direction === 'Increasing' ? 'bg-amber-50 text-amber-800 border border-amber-200' : t.trend_direction === 'Decreasing' ? 'bg-sky-50 text-sky-800 border border-sky-200' : 'bg-slate-100 text-slate-700'}">
                ${t.trend_direction === 'Increasing' ? '📈 Higher' : t.trend_direction === 'Decreasing' ? '📉 Lower' : '➡️ Stable'}
              </span>
            </div>
            <p class="text-xs text-slate-600 leading-relaxed">${t.trend_summary}</p>
          </div>
        `).join("")}
      </div>

      <div class="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <h3 class="font-bold text-slate-900 text-base">Your Health Numbers Across Doctor Visits</h3>
        <div class="h-80 relative">
          <canvas id="trendChart"></canvas>
        </div>
      </div>
    `;
    lucide.createIcons();
    renderTrendChartFromData(data.trends);
  } catch (e) {
    console.error("Trends error:", e);
  }
}

function updateTrendChartSelection() {
  if (!allTrendsData) return;
  const selVal = document.getElementById("trendBiomarkerSelect").value;
  let filtered = allTrendsData.trends;
  if (selVal !== "ALL") {
    filtered = allTrendsData.trends.filter(t => t.biomarker_code === selVal);
  }
  renderTrendChartFromData(filtered);
}

function renderTrendChartFromData(trendsList) {
  const ctx = document.getElementById("trendChart");
  if (!ctx) return;
  if (trendChartInstance) trendChartInstance.destroy();

  const dateSet = new Set();
  trendsList.forEach(t => t.data_points.forEach(p => dateSet.add(p.date)));
  const labels = Array.from(dateSet).sort();

  const colors = ['#0284c7', '#9333ea', '#10b981', '#f59e0b', '#ef4444', '#6366f1'];
  const datasets = trendsList.map((t, idx) => {
    const color = colors[idx % colors.length];
    const dataMap = {};
    t.data_points.forEach(p => { dataMap[p.date] = p.value; });
    const dataArray = labels.map(d => dataMap[d] !== undefined ? dataMap[d] : null);

    return {
      label: `${t.biomarker_name} (${t.unit})`,
      data: dataArray,
      borderColor: color,
      backgroundColor: `${color}15`,
      tension: 0.3,
      spanGaps: true,
      fill: true
    };
  });

  trendChartInstance = new Chart(ctx, {
    type: 'line',
    data: { labels: labels, datasets: datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'top' } }
    }
  });
}

// Medications Loader
async function loadMedications() {
  try {
    const [medRes, remRes] = await Promise.all([
      fetch("/api/v1/medications/", { headers: { "Authorization": `Bearer ${authToken}` } }),
      fetch("/api/v1/medications/today-reminders", { headers: { "Authorization": `Bearer ${authToken}` } })
    ]);

    const container = document.getElementById("medicationsDynamicContent");
    if (!container) return;

    const meds = medRes.ok ? await medRes.json() : [];
    const reminders = remRes.ok ? await remRes.json() : [];

    if (!meds.length) {
      container.innerHTML = `
        <div class="bg-white rounded-2xl border border-dashed border-slate-200 p-12 text-center space-y-3">
          <i data-lucide="pill" class="w-12 h-12 text-slate-300 mx-auto"></i>
          <h4 class="font-bold text-slate-800 text-base">No active medicines recorded yet.</h4>
          <p class="text-xs text-slate-400 max-w-sm mx-auto">Upload a prescription document or add your doctor's prescriptions to track your daily schedule.</p>
          <div class="pt-2 flex justify-center space-x-3">
            <button onclick="document.getElementById('rxFileInput').click()" class="px-5 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-bold shadow-sm">
              Upload Prescription File
            </button>
            <button onclick="openAddMedModal()" class="px-5 py-2.5 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-bold shadow-sm">
              Add Manually
            </button>
          </div>
        </div>
      `;
      lucide.createIcons();
      return;
    }

    container.innerHTML = `
      <div class="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 class="font-bold text-slate-900 text-base">Your Active Prescriptions (${meds.length})</h3>
          <button onclick="clearAllMedications()" class="text-rose-600 hover:text-rose-700 text-xs font-semibold flex items-center space-x-1">
            <i data-lucide="trash-2" class="w-3.5 h-3.5 mr-1"></i> Clear All Prescriptions
          </button>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          ${meds.map(m => `
            <div class="p-4 rounded-xl border border-slate-200 bg-slate-50/50 space-y-2">
              <div class="flex items-center justify-between">
                <h4 class="font-bold text-slate-900 text-sm">${m.brand_name} <span class="font-normal text-xs text-slate-500">(${m.strength})</span></h4>
                <div class="flex items-center space-x-2">
                  <button onclick="triggerMissedDoseGuide('${m.brand_name}')" class="text-[11px] text-sky-600 hover:underline font-semibold">Missed Dose Guide</button>
                  <button onclick="deleteSingleMedication('${m.id}', '${m.brand_name.replace(/'/g, "\\'")}')" class="text-[11px] text-rose-600 hover:underline font-semibold flex items-center">
                    <i data-lucide="trash-2" class="w-3 h-3 mr-0.5"></i> Delete
                  </button>
                </div>
              </div>
              <p class="text-xs text-slate-600">How often: <strong>${m.frequency_type.replace('_', ' ')}</strong> • Timing: <strong>${m.food_relation.replace('_', ' ')}</strong></p>
              <p class="text-[11px] text-slate-400">Prescribed by: <em>${m.prescribing_doctor || 'Healthcare Provider'}</em></p>
            </div>
          `).join("")}
        </div>
      </div>

      <div class="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <h3 class="font-bold text-slate-900 text-base">Today's Medicine Checklist</h3>
        <div class="space-y-3">
          ${reminders.map(r => `
            <div class="flex items-center justify-between p-3.5 rounded-xl border ${r.status === 'TAKEN' ? 'bg-emerald-50/60 border-emerald-200' : 'bg-slate-50 border-slate-200'}">
              <div>
                <p class="font-bold text-slate-900 text-sm">${r.brand_name} <span class="font-normal text-xs text-slate-500">${r.strength}</span></p>
                <p class="text-xs text-slate-500">Time: <strong>${r.scheduled_time}</strong> • Status: <strong>${r.status}</strong></p>
              </div>
              <div class="flex items-center space-x-2">
                ${r.status === 'TAKEN' ? `
                  <span class="text-xs text-emerald-800 bg-emerald-100 font-bold px-3 py-1 rounded-full flex items-center"><i data-lucide="check" class="w-3 h-3 mr-1"></i> Taken</span>
                ` : `
                  <button onclick="logMedAction('${r.medication_id}', '${r.schedule_id}', 'TAKEN')" class="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold">Mark as Taken</button>
                  <button onclick="logMedAction('${r.medication_id}', '${r.schedule_id}', 'SKIPPED')" class="px-3 py-1.5 bg-amber-100 hover:bg-amber-200 text-amber-800 rounded-lg text-xs font-semibold">Skip</button>
                `}
              </div>
            </div>
          `).join("")}
        </div>
      </div>
    `;
    lucide.createIcons();
  } catch (e) {
    console.error(e);
  }
}

async function deleteSingleMedication(medId, brandName) {
  if (!confirm(`Delete ${brandName || "this medication"}? This will permanently remove it from your schedule.`)) return;
  try {
    const res = await fetch(`/api/v1/medications/${medId}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    if (res.ok) {
      alert(`✓ ${brandName || "Medication"} deleted.`);
      await loadMedications();
      await loadDashboard();
  loadNotificationFeed();
  startBackgroundReminderChecker();
    } else {
      alert("Failed to delete medication.");
    }
  } catch (e) {
    console.error(e);
  }
}

async function clearAllMedications() {
  if (!confirm("Clear all recorded prescriptions and schedules? This action cannot be undone.")) return;
  try {
    const res = await fetch(`/api/v1/medications/clear-all`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    if (res.ok) {
      alert("✓ All prescriptions cleared.");
      await loadMedications();
      await loadDashboard();
  loadNotificationFeed();
  startBackgroundReminderChecker();
    } else {
      alert("Failed to clear prescriptions.");
    }
  } catch (e) {
    console.error(e);
  }
}

async function handlePrescriptionUpload(event) {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = async (e) => {
    const text = e.target.result;
    try {
      const res = await fetch("/api/v1/medications/prescriptions/upload", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${authToken}` },
        body: JSON.stringify({ raw_text: typeof text === 'string' ? text : "Prescription document" })
      });
      if (res.ok) {
        alert("✓ Prescription document read and medicines added to your schedule!");
        loadMedications();
        loadDashboard();
  loadNotificationFeed();
  startBackgroundReminderChecker();
      }
    } catch (err) {
      console.error(err);
    }
  };
  reader.readAsText(file);
  event.target.value = "";
}

async function logMedAction(medId, schId, action) {
  try {
    const res = await fetch("/api/v1/medications/log-action", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${authToken}` },
      body: JSON.stringify({ medication_id: medId, schedule_id: schId, action: action, scheduled_for: new Date().toISOString() })
    });
    if (res.ok) {
      loadMedications();
      loadDashboard();
  loadNotificationFeed();
  startBackgroundReminderChecker();
    }
  } catch (e) {
    console.error(e);
  }
}

// Diet Loader - 100% Report-Driven with 5 Full Daily Meals & Food Lists
async function loadDiet() {
  try {
    const pParam = currentSelectedPatient ? `?patient_name=${encodeURIComponent(currentSelectedPatient)}` : '';
    const [planRes, patRes] = await Promise.all([
      fetch(`/api/v1/wellness/diet-plan${pParam}`, { headers: { "Authorization": `Bearer ${authToken}` } }),
      fetch(`/api/v1/reports/patients`, { headers: { "Authorization": `Bearer ${authToken}` } })
    ]);

    const container = document.getElementById("dietFrameworkContainer");
    if (!container) return;

    if (!planRes.ok) {
      container.innerHTML = `<p class="text-xs text-rose-500 py-4">Error loading meal guide.</p>`;
      return;
    }

    const plan = await planRes.json();
    const availablePatients = patRes.ok ? await patRes.json() : [];

    // Top Patient Filter bar
    let filterBarHtml = "";
    if (availablePatients && availablePatients.length > 1) {
      const isAll = !currentSelectedPatient || currentSelectedPatient === "All";
      filterBarHtml = `
        <div class="bg-slate-100 p-2.5 rounded-2xl border border-slate-200 flex flex-wrap items-center gap-2 mb-4 text-xs">
          <span class="font-bold text-slate-500 uppercase tracking-wider text-[10px] flex items-center mr-1">
            <i data-lucide="users" class="w-3.5 h-3.5 mr-1 text-emerald-600"></i> Patient Filter:
          </span>
          <button onclick="currentSelectedPatient=null; loadDiet();" class="px-3 py-1 rounded-xl font-bold transition ${isAll ? 'bg-emerald-600 text-white shadow-sm' : 'bg-white text-slate-700 hover:bg-slate-200'}">
            <span>All Patients</span>
          </button>
          ${availablePatients.map(p => `
            <button onclick="currentSelectedPatient='${p.patient_name.replace(/'/g, "\'")}'; loadDiet();" class="px-3 py-1 rounded-xl font-bold transition flex items-center space-x-1.5 ${currentSelectedPatient === p.patient_name ? 'bg-emerald-600 text-white shadow-sm' : 'bg-white text-slate-700 hover:bg-slate-200'}">
              <span>🩺 ${p.patient_name}</span>
              <span class="text-[10px] bg-black/15 px-1.5 py-0.2 rounded-full font-mono">${p.report_count}</span>
            </button>
          `).join("")}
        </div>
      `;
    }

    if (!plan.has_data) {
      container.innerHTML = `
        ${filterBarHtml}
        <div class="bg-white rounded-3xl border border-dashed border-slate-200 p-12 text-center space-y-4 max-w-2xl mx-auto shadow-sm">
          <div class="w-16 h-16 bg-emerald-50 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto shadow-sm">
            <i data-lucide="utensils" class="w-8 h-8"></i>
          </div>
          <div class="space-y-1">
            <h4 class="font-extrabold text-slate-900 text-lg">Your personalized 5-meal guide will appear here automatically.</h4>
            <p class="text-xs text-slate-500 max-w-md mx-auto">Upload any medical report (Blood Sugar, Lipids, Vitamins) and our clinical engine will immediately build your 5 daily meals.</p>
          </div>
          <div class="pt-2 flex flex-wrap justify-center gap-3">
            <button onclick="switchTab('upload')" class="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-sm transition flex items-center space-x-1.5">
              <i data-lucide="upload-cloud" class="w-4 h-4"></i>
              <span>Upload Medical Report</span>
            </button>
            <button onclick="loadSampleReport('glucose')" class="px-4 py-2.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 rounded-xl text-xs font-bold transition flex items-center space-x-1">
              <i data-lucide="zap" class="w-3.5 h-3.5 text-emerald-600"></i>
              <span>Try Sample Report</span>
            </button>
          </div>
        </div>
      `;
      lucide.createIcons();
      return;
    }

    const focusBadges = (plan.clinical_focus || []).map(f => `
      <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-extrabold bg-emerald-100/90 text-emerald-950 border border-emerald-300">
        ✓ ${f}
      </span>
    `).join("");

    const addressedBadges = (plan.abnormal_biomarkers_addressed || []).map(b => `
      <span class="inline-flex items-center px-2.5 py-0.5 rounded-lg text-xs font-bold bg-amber-100 text-amber-950 border border-amber-300">
        ⚠️ Addressed Test: ${b}
      </span>
    `).join("");

    const scheduleList = plan.daily_schedule || [];
    const enjoyList = plan.foods_to_enjoy || [];
    const limitList = plan.foods_to_limit || [];

    container.innerHTML = `
      ${filterBarHtml}

      <!-- REPORT-DRIVEN HEADER BANNER -->
      <div class="bg-gradient-to-r from-emerald-950 via-teal-950 to-slate-950 rounded-3xl p-7 text-white shadow-xl border border-emerald-700/50 space-y-4 relative overflow-hidden">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 relative z-10">
          <div>
            <div class="flex items-center space-x-2">
              <span class="text-[10px] bg-emerald-400/20 text-emerald-300 font-extrabold px-3 py-0.5 rounded-full border border-emerald-400/40 uppercase tracking-wider">AUTOMATICALLY TAILORED FROM REPORT</span>
              <span class="text-xs text-teal-200 font-medium">• ${plan.report_title || 'Latest Report'}</span>
            </div>
            <h3 class="text-2xl font-black text-white mt-1.5">${plan.title}</h3>
          </div>
          <div class="flex items-center space-x-4 bg-white/10 backdrop-blur-md px-5 py-3 rounded-2xl border border-white/15 text-xs">
            <div>
              <span class="text-teal-300 text-[10px] uppercase font-bold tracking-wider block">Daily Calorie Target</span>
              <p class="font-black text-white text-base mt-0.5">${plan.target_calories_kcal} kcal</p>
            </div>
            <div class="border-l border-white/20 pl-4">
              <span class="text-teal-300 text-[10px] uppercase font-bold tracking-wider block">Daily Hydration</span>
              <p class="font-black text-white text-base mt-0.5">${plan.target_water_liters} Liters</p>
            </div>
          </div>
        </div>

        <div class="pt-3 border-t border-emerald-800/80 space-y-2">
          <p class="text-xs text-teal-200 font-bold uppercase tracking-wider">Clinical Nutrition Goals for Your Body:</p>
          <div class="flex flex-wrap gap-2">${focusBadges}</div>
          ${addressedBadges ? `<div class="flex flex-wrap gap-1.5 pt-1">${addressedBadges}</div>` : ''}
        </div>
      </div>

      <!-- 5-MEAL DAILY SCHEDULE -->
      <div class="bg-white rounded-3xl border border-slate-200 p-6 sm:p-7 shadow-sm space-y-5">
        <div class="flex items-center justify-between border-b border-slate-100 pb-4">
          <div>
            <h3 class="font-extrabold text-slate-900 text-lg">Your Daily 5-Meal Schedule</h3>
            <p class="text-xs text-slate-500">Every meal is chosen to support your specific blood test numbers.</p>
          </div>
          <span class="badge-normal text-xs px-3 py-1 rounded-full font-bold">5 Daily Meals</span>
        </div>

        <div class="grid grid-cols-1 gap-4">
          ${scheduleList.map((m, idx) => `
            <div class="p-5 rounded-2xl border border-slate-200/90 bg-gradient-to-r from-slate-50/80 via-white to-emerald-50/20 hover:border-emerald-300 transition space-y-3 shadow-2xs">
              <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div class="flex items-center space-x-3">
                  <span class="w-8 h-8 rounded-xl bg-emerald-100 text-emerald-800 font-bold text-sm flex items-center justify-center shadow-2xs">${idx + 1}</span>
                  <div>
                    <h4 class="font-extrabold text-slate-900 text-base">${m.meal_name || m.name || 'Meal'}</h4>
                    <span class="text-xs text-emerald-700 font-bold bg-emerald-50 px-2.5 py-0.5 rounded-lg border border-emerald-200">${m.time}</span>
                  </div>
                </div>
                <span class="text-xs font-extrabold text-slate-600 bg-white px-3 py-1 rounded-xl border border-slate-200 shadow-2xs">${m.portion || 'Standard Portion'}</span>
              </div>

              <div class="bg-white p-4 rounded-xl border border-slate-100 text-xs text-slate-900 font-semibold leading-relaxed shadow-2xs">
                ${m.food || m.suggested_foods || ''}
              </div>

              <div class="flex flex-col md:flex-row md:items-center justify-between gap-2 pt-1 text-xs">
                <p class="text-slate-600 flex items-center"><strong class="text-emerald-800 mr-1.5 flex items-center"><i data-lucide="sparkles" class="w-3.5 h-3.5 mr-1 text-emerald-600"></i> Why this helps:</strong> ${m.reason || ''}</p>
                <span class="text-[11px] font-extrabold px-2.5 py-0.5 rounded-md bg-teal-50 text-teal-800 border border-teal-200 self-start md:self-auto">${m.target_biomarker || 'Vitality'}</span>
              </div>
            </div>
          `).join("")}
        </div>
      </div>

      <!-- FOODS TO ENJOY & FOODS TO LIMIT GRID -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- FOODS TO ENJOY -->
        <div class="bg-white rounded-3xl border border-emerald-200 p-6 shadow-sm space-y-4 bg-gradient-to-b from-emerald-50/40 to-white">
          <div class="flex items-center space-x-2.5 border-b border-emerald-100 pb-3">
            <div class="w-8 h-8 rounded-xl bg-emerald-500 text-white flex items-center justify-center shadow-sm">
              <i data-lucide="check" class="w-5 h-5"></i>
            </div>
            <h4 class="font-extrabold text-emerald-950 text-base">Foods to Enjoy Daily</h4>
          </div>
          <div class="space-y-3 text-xs">
            ${enjoyList.map(item => `
              <div class="p-3.5 bg-white rounded-2xl border border-emerald-100 space-y-1 shadow-2xs">
                <p class="font-extrabold text-emerald-950 text-xs">${item.food}</p>
                <p class="text-slate-600 text-[11px] leading-relaxed">${item.reason}</p>
              </div>
            `).join("")}
          </div>
        </div>

        <!-- FOODS TO LIMIT -->
        <div class="bg-white rounded-3xl border border-rose-200 p-6 shadow-sm space-y-4 bg-gradient-to-b from-rose-50/40 to-white">
          <div class="flex items-center space-x-2.5 border-b border-rose-100 pb-3">
            <div class="w-8 h-8 rounded-xl bg-rose-500 text-white flex items-center justify-center shadow-sm">
              <i data-lucide="x" class="w-5 h-5"></i>
            </div>
            <h4 class="font-extrabold text-rose-950 text-base">Foods to Limit or Avoid</h4>
          </div>
          <div class="space-y-3 text-xs">
            ${limitList.map(item => `
              <div class="p-3.5 bg-white rounded-2xl border border-rose-100 space-y-1 shadow-2xs">
                <p class="font-extrabold text-rose-950 text-xs">${item.food}</p>
                <p class="text-slate-600 text-[11px] leading-relaxed">${item.reason}</p>
              </div>
            `).join("")}
          </div>
        </div>
      </div>

      <!-- CLINICAL DISCLAIMER FOOTER -->
      <div class="p-4 rounded-2xl bg-slate-100 border border-slate-200 text-xs text-slate-500 italic">
        ${plan.guidance_note || 'This meal guide is personalized to address the blood tests in your medical report. Always consult your doctor or registered dietitian before making drastic dietary changes.'}
      </div>
    `;
    lucide.createIcons();
  } catch (e) {
    console.error("Diet guide error:", e);
  }
}

// Notifications View Loader
async function loadNotificationsView() {
  try {
    const [mealRes, medRes, moveRes] = await Promise.all([
      fetch("/api/v1/wellness/reminders/diet", { headers: { "Authorization": `Bearer ${authToken}` } }),
      fetch("/api/v1/medications/", { headers: { "Authorization": `Bearer ${authToken}` } }),
      fetch("/api/v1/wellness/reminders/movement", { headers: { "Authorization": `Bearer ${authToken}` } })
    ]);

    if (mealRes.ok) {
      const meals = await mealRes.json();
      const container = document.getElementById("mealRemindersList");
      container.innerHTML = meals.map((r, idx) => `
        <div class="flex items-center justify-between p-3 rounded-2xl border border-slate-200 bg-slate-50/80 text-xs">
          <div class="flex items-center space-x-2.5">
            <input type="checkbox" id="remCheck_${idx}" ${r.enabled ? 'checked' : ''} class="w-4 h-4 rounded text-emerald-600 focus:ring-emerald-500">
            <span class="font-extrabold text-slate-800">${r.name}</span>
          </div>
          <input type="text" id="remTime_${idx}" value="${r.time}" class="w-24 text-center bg-white border border-slate-300 rounded-xl px-2 py-1 text-xs font-bold shadow-2xs">
        </div>
      `).join("");
    }

    if (medRes.ok) {
      const meds = await medRes.json();
      const mContainer = document.getElementById("medRemindersList");
      if (meds.length) {
        mContainer.innerHTML = meds.map(m => `
          <div class="p-3.5 bg-slate-50 rounded-2xl border border-slate-200 space-y-1 shadow-2xs">
            <div class="flex items-center justify-between">
              <p class="font-extrabold text-slate-900 text-xs">${m.brand_name} (${m.strength})</p>
              <span class="text-[10px] bg-sky-100 text-sky-800 font-bold px-2 py-0.2 rounded-full">Active</span>
            </div>
            <p class="text-slate-500 text-[11px]">Frequency: ${m.frequency_type.replace('_', ' ')}</p>
          </div>
        `).join("");
      } else {
        mContainer.innerHTML = `<p class="text-slate-400 py-3 text-center">No active prescriptions recorded.</p>`;
      }
    }

    if (moveRes.ok) {
      const move = await moveRes.json();
      const chk = document.getElementById("exRemCheck");
      const timeInput = document.getElementById("exRemTime");
      if (chk) chk.checked = move.enabled !== false;
      if (timeInput) timeInput.value = move.time || "06:00 PM";
    }

    await loadNotificationFeed();
    lucide.createIcons();
  } catch (e) {
    console.error("Notifications loader error:", e);
  }
}

async function saveMealReminders() {
  const rows = document.querySelectorAll("#mealRemindersList > div");
  const payload = [];
  rows.forEach((r, idx) => {
    const chk = document.getElementById(`remCheck_${idx}`);
    const timeInput = document.getElementById(`remTime_${idx}`);
    if (chk && timeInput) {
      payload.push({
        meal_key: `meal_${idx}`,
        name: chk.nextElementSibling.innerText,
        time: timeInput.value,
        enabled: chk.checked
      });
    }
  });

  try {
    const res = await fetch("/api/v1/wellness/reminders/diet", {
      method: "PUT",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${authToken}` },
      body: JSON.stringify(payload)
    });
    if (res.ok) alert("✓ Meal reminder times saved!");
  } catch (e) {
    console.error(e);
  }
}

// Exercise Loader - 100% Report-Driven with Daily Movement Routines
async function loadExercise() {
  try {
    const pParam = currentSelectedPatient ? `?patient_name=${encodeURIComponent(currentSelectedPatient)}` : '';
    const [planRes, patRes] = await Promise.all([
      fetch(`/api/v1/wellness/exercise-plan${pParam}`, { headers: { "Authorization": `Bearer ${authToken}` } }),
      fetch(`/api/v1/reports/patients`, { headers: { "Authorization": `Bearer ${authToken}` } })
    ]);

    const container = document.getElementById("exercisePlanContainer");
    if (!container) return;

    if (!planRes.ok) {
      container.innerHTML = `<p class="text-xs text-rose-500 py-4">Error loading movement plan.</p>`;
      return;
    }

    const plan = await planRes.json();
    const availablePatients = patRes.ok ? await patRes.json() : [];

    // Patient filter bar
    let filterBarHtml = "";
    if (availablePatients && availablePatients.length > 1) {
      const isAll = !currentSelectedPatient || currentSelectedPatient === "All";
      filterBarHtml = `
        <div class="bg-slate-100 p-2.5 rounded-2xl border border-slate-200 flex flex-wrap items-center gap-2 mb-4 text-xs">
          <span class="font-bold text-slate-500 uppercase tracking-wider text-[10px] flex items-center mr-1">
            <i data-lucide="users" class="w-3.5 h-3.5 mr-1 text-teal-600"></i> Patient Filter:
          </span>
          <button onclick="currentSelectedPatient=null; loadExercise();" class="px-3 py-1 rounded-xl font-bold transition ${isAll ? 'bg-teal-600 text-white shadow-sm' : 'bg-white text-slate-700 hover:bg-slate-200'}">
            <span>All Patients</span>
          </button>
          ${availablePatients.map(p => `
            <button onclick="currentSelectedPatient='${p.patient_name.replace(/'/g, "\'")}'; loadExercise();" class="px-3 py-1 rounded-xl font-bold transition flex items-center space-x-1.5 ${currentSelectedPatient === p.patient_name ? 'bg-teal-600 text-white shadow-sm' : 'bg-white text-slate-700 hover:bg-slate-200'}">
              <span>🩺 ${p.patient_name}</span>
              <span class="text-[10px] bg-black/15 px-1.5 py-0.2 rounded-full font-mono">${p.report_count}</span>
            </button>
          `).join("")}
        </div>
      `;
    }

    if (!plan.has_data) {
      container.innerHTML = `
        ${filterBarHtml}
        <div class="bg-white rounded-3xl border border-dashed border-slate-200 p-12 text-center space-y-4 max-w-2xl mx-auto shadow-sm">
          <div class="w-16 h-16 bg-teal-50 text-teal-600 rounded-2xl flex items-center justify-center mx-auto shadow-sm">
            <i data-lucide="heart-pulse" class="w-8 h-8"></i>
          </div>
          <div class="space-y-1">
            <h4 class="font-extrabold text-slate-900 text-lg">Your daily movement ideas will appear here automatically.</h4>
            <p class="text-xs text-slate-500 max-w-md mx-auto">Upload any medical report, and we will create easy, enjoyable 15-30 minute movement routines tailored to your blood numbers.</p>
          </div>
          <div class="pt-2 flex flex-wrap justify-center gap-3">
            <button onclick="switchTab('upload')" class="px-5 py-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold shadow-sm transition flex items-center space-x-1.5">
              <i data-lucide="upload-cloud" class="w-4 h-4"></i>
              <span>Upload Medical Report</span>
            </button>
            <button onclick="loadSampleReport('glucose')" class="px-4 py-2.5 bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-200 rounded-xl text-xs font-bold transition flex items-center space-x-1">
              <i data-lucide="zap" class="w-3.5 h-3.5 text-teal-600"></i>
              <span>Try Sample Report</span>
            </button>
          </div>
        </div>
      `;
      lucide.createIcons();
      return;
    }

    const focusBadges = (plan.clinical_focus || []).map(f => `
      <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-extrabold bg-teal-100 text-teal-950 border border-teal-300">
        ✓ ${f}
      </span>
    `).join("");

    const routinesList = plan.routines || [];
    const guidelines = plan.safety_guidelines || [
      "Stay comfortably hydrated before, during, and after your movement sessions.",
      "Take a brisk 10-15 minute walk within 30 minutes after meals to help muscles absorb blood sugar.",
      "If you experience dizziness, joint pain, or shortness of breath, rest immediately and consult your physician."
    ];

    container.innerHTML = `
      ${filterBarHtml}

      <!-- REPORT-DRIVEN HEADER BANNER -->
      <div class="bg-gradient-to-r from-teal-950 via-sky-950 to-slate-950 rounded-3xl p-7 text-white shadow-xl border border-teal-700/50 space-y-4 relative overflow-hidden">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 relative z-10">
          <div>
            <div class="flex items-center space-x-2">
              <span class="text-[10px] bg-teal-400/20 text-teal-300 font-extrabold px-3 py-0.5 rounded-full border border-teal-400/40 uppercase tracking-wider">REPORT-DRIVEN MOVEMENT</span>
              <span class="text-xs text-sky-200 font-medium">• ${plan.report_title || 'Latest Report'}</span>
            </div>
            <h3 class="text-2xl font-black text-white mt-1.5">${plan.title}</h3>
          </div>
          <div class="bg-white/10 backdrop-blur-md px-5 py-3 rounded-2xl border border-white/15 text-xs min-w-[200px]">
            <span class="text-teal-300 text-[10px] uppercase font-bold tracking-wider block">Weekly Activity Goal</span>
            <p class="font-extrabold text-white text-sm mt-0.5">150 mins / week (30 mins x 5 days)</p>
          </div>
        </div>

        <div class="pt-3 border-t border-teal-800/80 space-y-2">
          <p class="text-xs text-teal-200 font-bold uppercase tracking-wider">Movement Targets for Your Health:</p>
          <div class="flex flex-wrap gap-2">${focusBadges}</div>
        </div>
      </div>

      <!-- DAILY ROUTINES GRID -->
      <div class="bg-white rounded-3xl border border-slate-200 p-6 sm:p-7 shadow-sm space-y-5">
        <div class="flex items-center justify-between border-b border-slate-100 pb-4">
          <div>
            <h3 class="font-extrabold text-slate-900 text-lg">Your Daily Movement Schedule</h3>
            <p class="text-xs text-slate-500">Gentle, safe, and effective routines for everyday life.</p>
          </div>
          <span class="badge-normal text-xs px-3 py-1 rounded-full font-bold">Gentle & Safe</span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
          ${routinesList.map(r => `
            <div class="p-5 rounded-2xl border border-slate-200/90 bg-gradient-to-br from-slate-50 to-teal-50/20 hover:border-teal-300 transition space-y-3 flex flex-col justify-between shadow-2xs">
              <div class="space-y-2.5">
                <div class="flex items-center justify-between">
                  <h4 class="font-extrabold text-slate-900 text-sm">${r.category}</h4>
                  <span class="text-xs text-teal-700 font-black bg-white px-2.5 py-1 rounded-xl border border-slate-200 shadow-2xs">${r.duration_minutes} mins</span>
                </div>
                <p class="text-xs text-slate-800 font-medium leading-relaxed bg-white p-3.5 rounded-xl border border-slate-100 shadow-2xs">${r.activity}</p>
              </div>
              <div class="pt-2 border-t border-slate-100 text-xs text-slate-600">
                <p class="text-[11px]"><strong class="text-teal-800">How this helps:</strong> ${r.benefit}</p>
                <span class="inline-block text-[10px] font-bold mt-1.5 px-2 py-0.5 rounded bg-teal-100/70 text-teal-900">${r.target_biomarker || 'Vitality'}</span>
              </div>
            </div>
          `).join("")}
        </div>

        <!-- SAFETY GUIDELINES -->
        <div class="p-5 rounded-2xl bg-amber-50/80 border border-amber-200 text-xs text-amber-950 space-y-2">
          <p class="font-black text-amber-950 flex items-center text-sm"><i data-lucide="shield-alert" class="w-4 h-4 mr-2 text-amber-600"></i> Safe Movement Guidelines:</p>
          <ul class="list-disc list-inside space-y-1 text-amber-900 font-medium">
            ${guidelines.map(g => `<li>${g}</li>`).join("")}
          </ul>
        </div>
      </div>
    `;
    lucide.createIcons();
  } catch (e) {
    console.error("Exercise guide error:", e);
  }
}

// Patient Profile Loader & Save
async function loadPatientProfile() {
  try {
    const res = await fetch("/api/v1/auth/profile", { headers: { "Authorization": `Bearer ${authToken}` } });
    if (!res.ok) return;
    const prof = await res.json();

    document.getElementById("profEmail").value = prof.email || "";
    document.getElementById("profName").value = prof.full_name || "Patient";
    if (prof.gender) document.getElementById("profGender").value = prof.gender;
    if (prof.date_of_birth) document.getElementById("profDob").value = prof.date_of_birth;
    if (prof.height_cm) document.getElementById("profHeight").value = prof.height_cm;
    if (prof.weight_kg) document.getElementById("profWeight").value = prof.weight_kg;
    if (prof.dietary_preference) document.getElementById("profDiet").value = prof.dietary_preference;
    if (prof.activity_level) document.getElementById("profActivity").value = prof.activity_level;
    document.getElementById("profAllergies").value = (prof.allergies || []).join(", ");
  } catch (e) {
    console.error(e);
  }
}

async function savePatientProfile() {
  const payload = {
    full_name: document.getElementById("profName").value,
    gender: document.getElementById("profGender").value,
    date_of_birth: document.getElementById("profDob").value || null,
    height_cm: parseFloat(document.getElementById("profHeight").value) || null,
    weight_kg: parseFloat(document.getElementById("profWeight").value) || null,
    dietary_preference: document.getElementById("profDiet").value,
    activity_level: document.getElementById("profActivity").value,
    allergies: document.getElementById("profAllergies").value.split(",").map(s => s.trim()).filter(Boolean)
  };

  try {
    const res = await fetch("/api/v1/auth/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${authToken}` },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      alert("✓ Profile saved successfully!");
      loadPatientProfile();
      loadDashboard();
  loadNotificationFeed();
  startBackgroundReminderChecker();
    }
  } catch (e) {
    console.error(e);
  }
}

// Document Viewer
async function viewOriginalDocument(reportId) {
  try {
    const res = await fetch(`/api/v1/reports/${reportId}`, { headers: { "Authorization": `Bearer ${authToken}` } });
    if (!res.ok) return;
    const r = await res.json();

    document.getElementById("docViewerTitle").innerText = r.title;
    document.getElementById("docViewerFilename").innerText = r.file_name || "report.txt";
    document.getElementById("docViewerDate").innerText = r.report_date;
    document.getElementById("docViewerLab").innerText = r.laboratory_name || "Diagnostic Laboratory";
    document.getElementById("docViewerContent").innerText = r.raw_extracted_text || r.results.map(b => `${b.biomarker_name}: ${b.numeric_value} ${b.unit || ''} (Healthy Range: ${b.ref_range_raw || ''})`).join("\n");

    const bGrid = document.getElementById("docViewerBiomarkers");
    bGrid.innerHTML = r.results.map(b => `
      <div class="p-2 rounded-lg border bg-slate-50 text-xs">
        <p class="font-bold truncate text-slate-800">${b.biomarker_name}</p>
        <p class="font-extrabold text-sky-700">${b.numeric_value} ${b.unit || ''}</p>
      </div>
    `).join("");

    const dlBtn = document.getElementById("docViewerDownloadBtn");
    dlBtn.onclick = () => downloadReportFile(r.id, r.file_name);

    document.getElementById("documentViewerModal").classList.remove("hidden");
    lucide.createIcons();
  } catch (e) {
    console.error(e);
  }
}

function closeDocumentViewerModal() {
  document.getElementById("documentViewerModal").classList.add("hidden");
}

async function downloadReportFile(reportId, filename) {
  try {
    const res = await fetch(`/api/v1/reports/${reportId}/file`, { headers: { "Authorization": `Bearer ${authToken}` } });
    if (!res.ok) { alert("Download failed"); return; }
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename || "medical_report";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  } catch (e) {
    console.error(e);
  }
}

// Add Medication
function openAddMedModal() {
  document.getElementById("addMedModal").classList.remove("hidden");
}

function closeAddMedModal() {
  document.getElementById("addMedModal").classList.add("hidden");
}

async function submitNewMedication() {
  const brandName = document.getElementById("newMedBrand").value.trim();
  const strength = document.getElementById("newMedStrength").value.trim();
  const freq = document.getElementById("newMedFreq").value;
  const food = document.getElementById("newMedFood").value;
  const doctor = document.getElementById("newMedDoctor").value.trim() || "Dr. Healthcare Provider";

  if (!brandName || !strength) {
    alert("Please enter the medicine name and dose strength.");
    return;
  }

  let schedules = [];
  if (freq === "once_daily") {
    schedules.push({ scheduled_time_str: "08:30 AM", dose_quantity: "1 tablet", reminder_enabled: true });
  } else if (freq === "twice_daily") {
    schedules.push({ scheduled_time_str: "08:30 AM", dose_quantity: "1 tablet", reminder_enabled: true });
    schedules.push({ scheduled_time_str: "08:30 PM", dose_quantity: "1 tablet", reminder_enabled: true });
  } else {
    schedules.push({ scheduled_time_str: "08:30 AM", dose_quantity: "1 tablet", reminder_enabled: true });
    schedules.push({ scheduled_time_str: "02:00 PM", dose_quantity: "1 tablet", reminder_enabled: true });
    schedules.push({ scheduled_time_str: "08:30 PM", dose_quantity: "1 tablet", reminder_enabled: true });
  }

  try {
    const res = await fetch("/api/v1/medications/prescriptions", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${authToken}` },
      body: JSON.stringify({
        prescribing_doctor: doctor,
        prescription_date: new Date().toISOString().split('T')[0],
        medications: [{
          brand_name: brandName,
          generic_name: brandName,
          strength: strength,
          frequency_type: freq,
          food_relation: food,
          start_date: new Date().toISOString().split('T')[0],
          schedules: schedules
        }]
      })
    });

    if (res.ok) {
      closeAddMedModal();
      await loadMedications();
      await loadDashboard();
  loadNotificationFeed();
  startBackgroundReminderChecker();
      alert("✓ Prescription saved to your daily schedule!");
    }
  } catch (e) {
    console.error(e);
  }
}

function triggerEmergencyModal() {
  document.getElementById("emergencyModal").classList.remove("hidden");
  lucide.createIcons();
}

function triggerMissedDoseGuide(medName) {
  alert(
    `What to do if you missed a dose of ${medName}:\n\n` +
    "1. Take the missed dose as soon as you remember.\n" +
    "2. If it is almost time for your next regular dose, simply skip the missed dose and resume your regular schedule.\n" +
    "3. NEVER take two pills or a double dose at the same time to make up for a missed one.\n" +
    "4. If you have any doubt, call your local pharmacist."
  );
}

function openMetricModal(type) {
  if (type === 'water') {
    fetch("/api/v1/wellness/meal-logs", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${authToken}` },
      body: JSON.stringify({ meal_type: "water", food_items_logged: "Water (Glass)", water_intake_ml: 250 })
    }).then(() => loadDashboard());
  }
}

async function loadSettings() {
  try {
    const res = await fetch("/api/v1/audit/logs", { headers: { "Authorization": `Bearer ${authToken}` } });
    if (res.ok) {
      const logs = await res.json();
      const container = document.getElementById("auditLogContainer");
      container.innerHTML = logs.map(l => `
        <div class="flex items-center justify-between p-2.5 rounded-lg border border-slate-100 text-xs bg-slate-50">
          <div>
            <span class="font-bold text-slate-800">${l.action.replace(/_/g, ' ')}</span>
            <span class="text-slate-400 ml-2">(${l.resource_type})</span>
          </div>
          <span class="text-slate-400">${l.timestamp.split('.')[0]}</span>
        </div>
      `).join("");
    }
  } catch (e) {
    console.error(e);
  }
}

async function exportAllData() {
  try {
    const res = await fetch("/api/v1/audit/export-data", { headers: { "Authorization": `Bearer ${authToken}` } });
    if (res.ok) {
      const data = await res.json();
      const str = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2));
      const a = document.createElement("a");
      a.setAttribute("href", str);
      a.setAttribute("download", "my_personal_health_records.json");
      document.body.appendChild(a);
      a.click();
      a.remove();
    }
  } catch (e) {
    console.error(e);
  }
}
