// ============================================================
// Sahayata frontend — talks to the FastAPI backend at API_BASE.
// Change this if your backend runs on a different host/port.
// ============================================================
const API_BASE = "http://127.0.0.1:8000";

const state = {
  token: localStorage.getItem("token") || null,
  userName: localStorage.getItem("userName") || null,
  preferredLanguage: localStorage.getItem("preferredLanguage") || "te",
};

// ---------- API helper ----------
async function api(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth && state.token) headers["Authorization"] = `Bearer ${state.token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  let data = null;
  try { data = await res.json(); } catch (_) { /* no body */ }

  if (!res.ok) {
    const msg = (data && data.detail) || `Request failed (${res.status})`;
    throw new Error(msg);
  }
  return data;
}

// ============================================================
// ROUTING — simple hash-based view switcher
// ============================================================
const views = ["home", "login", "dashboard", "notifications"];

function navigate(view) {
  if (view === "dashboard" && !state.token) view = "login";
  views.forEach((v) => {
    document.getElementById(`view-${v}`).classList.toggle("hidden", v !== view);
  });
  document.querySelectorAll("[data-nav]").forEach((el) => {
    el.classList.toggle("active", el.dataset.nav === view);
  });
  window.scrollTo({ top: 0, behavior: "instant" });

  if (view === "dashboard") loadDashboard();
  if (view === "notifications") loadNotifications();
}

window.addEventListener("hashchange", () => navigate(location.hash.slice(1) || "home"));

document.querySelectorAll("[data-nav]").forEach((el) => {
  el.addEventListener("click", (e) => {
    e.preventDefault();
    location.hash = el.dataset.nav;
  });
});

document.querySelector('[data-action="start"]').addEventListener("click", () => {
  location.hash = state.token ? "dashboard" : "login";
});

// ============================================================
// AUTH — mock Aadhaar OTP flow
// ============================================================
function refreshAuthUI() {
  const chip = document.getElementById("userChip");
  const loginBtn = document.getElementById("loginBtn");
  const logoutBtn = document.getElementById("logoutBtn");
  if (state.token) {
    chip.textContent = state.userName || "Logged in";
    chip.classList.remove("hidden");
    loginBtn.classList.add("hidden");
    logoutBtn.classList.remove("hidden");
  } else {
    chip.classList.add("hidden");
    loginBtn.classList.remove("hidden");
    logoutBtn.classList.add("hidden");
  }
}

document.getElementById("logoutBtn").addEventListener("click", () => {
  localStorage.removeItem("token");
  localStorage.removeItem("userName");
  localStorage.removeItem("preferredLanguage");
  state.token = null;
  state.userName = null;
  resetProfileForm();
  document.getElementById("eligibleList").innerHTML = "";
  document.getElementById("nearlyList").innerHTML = "";
  document.getElementById("chatLog").innerHTML = "";
  refreshAuthUI();
  location.hash = "home";
});

let pendingAadhaar = null;

document.getElementById("otpSendForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("authError");
  errorEl.classList.add("hidden");
  const aadhaar = document.getElementById("aadhaarNumber").value.trim();
  const phone = document.getElementById("phoneNumber").value.trim();

  try {
    const res = await api("/auth/aadhaar/send-otp", {
      auth: false,
      method: "POST",
      body: { aadhaar_number: aadhaar, phone_number: phone },
    });
    pendingAadhaar = aadhaar;
    document.getElementById("otpHint").textContent = res.demo_note || "OTP sent.";
    document.getElementById("otpSendForm").classList.add("hidden");
    document.getElementById("otpVerifyForm").classList.remove("hidden");
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.classList.remove("hidden");
  }
});

document.getElementById("otpVerifyForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("authError");
  errorEl.classList.add("hidden");

  try {
    const res = await api("/auth/aadhaar/verify-otp", {
      auth: false,
      method: "POST",
      body: {
        aadhaar_number: pendingAadhaar,
        otp: document.getElementById("otpInput").value.trim(),
        full_name: document.getElementById("fullName").value.trim(),
        preferred_language: document.getElementById("preferredLanguage").value,
      },
    });
    state.token = res.access_token;
    state.userName = document.getElementById("fullName").value.trim();
    state.preferredLanguage = document.getElementById("preferredLanguage").value;
    localStorage.setItem("token", state.token);
    localStorage.setItem("userName", state.userName);
    localStorage.setItem("preferredLanguage", state.preferredLanguage);
    refreshAuthUI();
    document.getElementById("otpSendForm").reset();
    document.getElementById("otpVerifyForm").reset();
    document.getElementById("otpSendForm").classList.remove("hidden");
    document.getElementById("otpVerifyForm").classList.add("hidden");
    location.hash = "dashboard";
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.classList.remove("hidden");
  }
});

// ============================================================
// HERO SLIDER — recent scheme highlights (static demo content;
// swap for a real GET /schemes call once that endpoint exists)
// ============================================================
const RECENT_SCHEMES = [
  { title: "PM-KISAN", benefit: "₹6,000 / year", desc: "Income support for small and marginal farmers, paid in three installments." },
  { title: "NSAP Widow Pension", benefit: "₹500 / month", desc: "Monthly pension for widows aged 40+ from BPL households." },
  { title: "PMAY-G", benefit: "Housing assistance", desc: "Financial support to build a pucca house for eligible rural households." },
  { title: "State Scholarship", benefit: "Fees covered", desc: "Full tuition support for meritorious students from low-income families." },
];

let sliderIndex = 0;
let sliderTimer = null;

function renderSlider() {
  const slider = document.getElementById("schemeSlider");
  const dots = document.getElementById("sliderDots");
  slider.innerHTML = RECENT_SCHEMES.map((s, i) => `
    <div class="slide ${i === 0 ? "active" : ""}" data-i="${i}">
      <div class="slide-title">${s.title}</div>
      <div class="slide-benefit">${s.benefit}</div>
      <p class="slide-desc">${s.desc}</p>
    </div>
  `).join("");
  dots.innerHTML = RECENT_SCHEMES.map((_, i) =>
    `<span data-i="${i}" class="${i === 0 ? "active" : ""}"></span>`
  ).join("");
  dots.querySelectorAll("span").forEach((dot) => {
    dot.addEventListener("click", () => showSlide(Number(dot.dataset.i)));
  });
}

function showSlide(i) {
  sliderIndex = i;
  document.querySelectorAll(".slide").forEach((el, idx) => el.classList.toggle("active", idx === i));
  document.querySelectorAll(".slider-dots span").forEach((el, idx) => el.classList.toggle("active", idx === i));
}

function startSliderAutoplay() {
  clearInterval(sliderTimer);
  sliderTimer = setInterval(() => {
    showSlide((sliderIndex + 1) % RECENT_SCHEMES.length);
  }, 4000);
}

// ============================================================
// DASHBOARD — profile, intake, eligibility, checklist, chat, applications
// ============================================================
async function loadDashboard() {
  resetProfileForm(); // always clear first — prevents the previous user's data from lingering
  document.getElementById("overviewGreeting").textContent = `Welcome, ${state.userName || "back"}`;

  let profile = null;
  try {
    profile = await api("/profile");
    fillProfileForm(profile);
  } catch (_) { /* fresh user, no profile fields yet — fine */ }

  const hasProfileData = profile && profile.age !== null && profile.age !== undefined;
  if (hasProfileData) {
    showProfileSummary(profile);
  } else {
    showProfileForm();
  }

  loadApplications();
  loadEligibilityStats();
}
function resetProfileForm() {
  const ids = ["p_age", "p_gender", "p_district", "p_income", "p_category", "p_occupation",
               "p_land", "p_ration", "p_disability", "p_marital"];
  ids.forEach((id) => { document.getElementById(id).value = ""; });
  document.getElementById("p_student").checked = false;
  document.getElementById("intakeText").value = "";
  document.getElementById("intakeStatus").textContent = "";
}
function fillProfileForm(p) {
  const map = {
    p_age: p.age, p_gender: p.gender, p_district: p.district, p_income: p.annual_income,
    p_category: p.category, p_occupation: p.occupation, p_land: p.land_holding_acres,
    p_ration: p.ration_card, p_disability: p.disability_pct, p_marital: p.marital_status,
  };
  Object.entries(map).forEach(([id, val]) => {
    if (val === null || val === undefined) return;
    document.getElementById(id).value = val;
  });
  document.getElementById("p_student").checked = !!p.is_student;
}
function showProfileForm() {
  document.getElementById("profileForm").classList.remove("hidden");
  document.getElementById("profileSummary").classList.add("hidden");
  document.getElementById("editProfileBtn").classList.add("hidden");
}

function showProfileSummary(profile) {
  const summary = document.getElementById("profileSummary");
  const fields = [
    ["Age", profile.age], ["Gender", profile.gender], ["District", profile.district],
    ["Annual income", profile.annual_income ? `₹${profile.annual_income}` : null],
    ["Category", profile.category], ["Occupation", profile.occupation],
    ["Land holding", profile.land_holding_acres ? `${profile.land_holding_acres} acres` : null],
    ["Ration card", profile.ration_card], ["Marital status", profile.marital_status],
    ["Student", profile.is_student ? "Yes" : "No"],
  ];
  summary.innerHTML = fields
    .filter(([, value]) => value !== null && value !== undefined && value !== "")
    .map(([label, value]) => `
      <div class="field">
        <span class="field-label">${label}</span>
        <span class="field-value">${value}</span>
      </div>
    `).join("");

  summary.classList.remove("hidden");
  document.getElementById("profileForm").classList.add("hidden");
  document.getElementById("editProfileBtn").classList.remove("hidden");
}

async function loadEligibilityStats() {
  try {
    const res = await api("/eligibility/latest");
    document.getElementById("statEligible").textContent = (res.eligible || []).length;
    document.getElementById("statNearly").textContent = (res.nearly_eligible || []).length;
    if (res.eligible?.length || res.nearly_eligible?.length) {
      renderEligibility(res); // also populate the results cards below, so a returning user sees their last result immediately
    }
  } catch (_) {
    document.getElementById("statEligible").textContent = "0";
    document.getElementById("statNearly").textContent = "0";
    document.getElementById("overviewHint").textContent = "Run your first eligibility check below to see your matches here.";
  }
}
// ---- Voice/text intake (F7) ----
document.getElementById("intakeSubmit").addEventListener("click", async () => {
  const text = document.getElementById("intakeText").value.trim();
  const statusEl = document.getElementById("intakeStatus");
  if (!text) { statusEl.textContent = "Type or speak something first."; return; }
  statusEl.textContent = "Reading your details...";
  try {
    const profile = await api("/profile/intake", { method: "POST", body: { text, language: state.preferredLanguage } });
    fillProfileForm(profile);
    statusEl.textContent = "Got it — check the profile fields below and fill in anything we missed.";
  } catch (err) {
    statusEl.textContent = `Couldn't extract details: ${err.message}`;
  }
});
document.getElementById("editProfileBtn").addEventListener("click", showProfileForm);

// Web Speech API voice input — browser-native, no backend call needed
const voiceBtn = document.getElementById("voiceBtn");
if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;

    voiceBtn.addEventListener("click", () => {
    recognition.lang = state.preferredLanguage === "hi" ? "hi-IN"
      : state.preferredLanguage === "en" ? "en-IN" : "te-IN";
    voiceBtn.textContent = "🎙 Listening...";
    recognition.start();
  });
  recognition.addEventListener("result", (e) => {
    const transcript = e.results[0][0].transcript;
    document.getElementById("intakeText").value = transcript;
    voiceBtn.textContent = "🎙 Speak";
  });
  recognition.addEventListener("end", () => { voiceBtn.textContent = "🎙 Speak"; });
  recognition.addEventListener("error", () => { voiceBtn.textContent = "🎙 Speak"; });
} else {
  voiceBtn.addEventListener("click", () => {
    alert("Voice input isn't supported in this browser. Try Chrome, or just type instead.");
  });
}

// ---- Profile form (F1 / manual edit) ----
document.getElementById("profileForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = {
    age: numOrNull("p_age"), gender: valOrNull("p_gender"), district: valOrNull("p_district"),
    annual_income: numOrNull("p_income"), category: valOrNull("p_category"), occupation: valOrNull("p_occupation"),
    land_holding_acres: numOrNull("p_land"), ration_card: valOrNull("p_ration"),
    disability_pct: numOrNull("p_disability") ?? 0, marital_status: valOrNull("p_marital"),
    is_student: document.getElementById("p_student").checked,
  };
    try {
    const updated = await api("/profile", { method: "PUT", body });
    showProfileSummary(updated);
  } catch (err) {
    alert(`Couldn't save profile: ${err.message}`);
  }
});

function valOrNull(id) { const v = document.getElementById(id).value; return v === "" ? null : v; }
function numOrNull(id) { const v = document.getElementById(id).value; return v === "" ? null : Number(v); }
// Event delegation: the per-scheme "Documents & how to apply" buttons are
// created dynamically by schemeCard(), so we listen on their shared parent
// instead of attaching a listener to each card individually.
document.getElementById("eligibleList").addEventListener("click", (e) => {
  const btn = e.target.closest(".toggle-docs-btn");
  if (!btn) return;
  const target = document.getElementById(btn.dataset.target);
  if (target) target.classList.toggle("hidden");
});
// ---- Eligibility check (F2/F3/F4) ----
document.getElementById("checkEligibilityBtn").addEventListener("click", async () => {
  const statusEl = document.getElementById("eligStatus");
  statusEl.textContent = "Checking against scheme rules...";
  try {
    const res = await api("/eligibility/check", { method: "POST" });
    renderEligibility(res);
    statusEl.textContent = "";
  } catch (err) {
    statusEl.textContent = `Couldn't check eligibility: ${err.message}`;
  }
});

function renderEligibility(res) {
  const eligibleEl = document.getElementById("eligibleList");
  const nearlyEl = document.getElementById("nearlyList");

  eligibleEl.innerHTML = (res.eligible && res.eligible.length)
    ? res.eligible.map(schemeCard).join("")
    : `<p class="empty-note">No matches yet — save your profile and check again.</p>`;

  nearlyEl.innerHTML = (res.nearly_eligible && res.nearly_eligible.length)
    ? res.nearly_eligible.map(nearlyCard).join("")
    : `<p class="empty-note">Nothing close right now.</p>`;
}

function schemeCard(s) {
  const reasons = (s.reasons || []).map((r) => `<li>${r}</li>`).join("");
  const checklistItems = (s.documents || []).map((d, i) => `
    <div class="checklist-item">
      <input type="checkbox" id="doc-${s.scheme_id}-${i}">
      <label for="doc-${s.scheme_id}-${i}">${d}</label>
    </div>
  `).join("");

  return `
    <div class="result-card eligible">
      <h4>${s.name || s.scheme_id}</h4>
      ${s.benefit ? `<div class="result-benefit">${s.benefit}</div>` : ""}
      <ul>${reasons}</ul>

      <button class="btn btn-outline btn-sm toggle-docs-btn" data-target="docs-${s.scheme_id}" type="button">
        Documents &amp; how to apply
      </button>

      <div id="docs-${s.scheme_id}" class="scheme-details hidden">
        <div class="checklist-box">${checklistItems}</div>
        ${s.where_to_apply ? `<p class="where-to-apply">${s.where_to_apply}</p>` : ""}
        ${s.apply_url ? `<a href="${s.apply_url}" target="_blank" rel="noopener" class="btn btn-primary btn-sm">Open official portal</a>` : ""}
      </div>
    </div>`;
}

function nearlyCard(s) {
  return `
    <div class="result-card nearly">
      <h4>${s.name || s.scheme_id}</h4>
      <div class="result-benefit">${s.missing || "Close to qualifying"}</div>
    </div>`;
}



// ---- Chat (F9) ----
document.getElementById("chatSendBtn").addEventListener("click", sendChat);
document.getElementById("chatInput").addEventListener("keydown", (e) => { if (e.key === "Enter") sendChat(); });

async function sendChat() {
  const input = document.getElementById("chatInput");
  const message = input.value.trim();
  if (!message) return;
  const log = document.getElementById("chatLog");

  log.insertAdjacentHTML("beforeend", `<div class="chat-msg user">${message}</div>`);
  input.value = "";
  log.scrollTop = log.scrollHeight;

  try {
    const res = await api("/chat", { method: "POST", body: { message } });
    log.insertAdjacentHTML("beforeend", `<div class="chat-msg assistant">${res.reply}</div>`);
  } catch (err) {
    log.insertAdjacentHTML("beforeend", `<div class="chat-msg assistant">Sorry, I couldn't reach the assistant: ${err.message}</div>`);
  }
  log.scrollTop = log.scrollHeight;
}

// ---- Applications / status tracking ----
async function loadApplications() {
  const list = document.getElementById("applicationsList");
  try {
    const apps = await api("/applications");
    list.innerHTML = apps.length ? apps.map(appItem).join("") : `<p class="empty-note">No applications tracked yet.</p>`;
    document.getElementById("statApplied").textContent = apps.length;
  } catch (err) {
    list.innerHTML = `<p class="empty-note">${err.message}</p>`;
    document.getElementById("statApplied").textContent = "0";
  }
}

function appItem(a) {
  return `
    <div class="app-item">
      <h4>${a.scheme_name}</h4>
      <span class="status-pill status-${a.status}">${a.status.replace("_", " ")}</span>
      ${a.submitted_office ? `<p class="muted small" style="margin-top:8px;">${a.submitted_office}</p>` : ""}
    </div>`;
}

// ============================================================
// NOTIFICATIONS
// ============================================================
async function loadNotifications() {
  const list = document.getElementById("notifList");
  try {
    const notifs = await api("/notifications");
    list.innerHTML = notifs.length ? notifs.map(notifItem).join("") : `<p class="empty-note">No notifications yet.</p>`;
  } catch (err) {
    list.innerHTML = `<p class="empty-note">${err.message}</p>`;
  }
}

function notifItem(n) {
  return `
    <div class="notif-item">
      <span class="notif-tag">${n.scheme_id.replace(/_/g, " ")}</span>
      <h4>${n.title}</h4>
      <p>${n.message}</p>
    </div>`;
}

// ============================================================
// INIT
// ============================================================
renderSlider();
startSliderAutoplay();
refreshAuthUI();
navigate(location.hash.slice(1) || "home");
