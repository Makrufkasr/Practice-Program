/**
 * ECOSYSTEM INTELLIGENCE — AUTHENTICATION & SINGLE-SIGN ON (SSO) ENGINE
 * Features:
 * 1. User Registration with Superadmin (Aan) Approval Workflow
 * 2. Real-time Pending Approval Notifications & Management Modal for Aan
 * 3. Strict Per-Username Data Isolation (Zero Data Leak)
 * 4. Seamless App Hub & SSO Link Launcher
 * 5. Account Profile & Password Management Modal
 * 6. Interactive ASPIRAN! AI & Financial Simulator
 */

const API_BASE = "";
const TOKEN_KEY = "one_gate_jwt_token";
const USER_KEY = "one_gate_user_data";

let pendingAppKey = null;
let pendingTargetUrl = null;
let pendingAppName = null;

// =========================================================================
// 1. INITIALIZATION & LIFECYCLE
// =========================================================================
document.addEventListener("DOMContentLoaded", () => {
    initAuthStatus();
    initScrollSpy();
    initTelegramSimulator();
});

function initAuthStatus() {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
        setGuestNavState();
        return;
    }

    fetch(`${API_BASE}/api/auth/verify?token=${encodeURIComponent(token)}`)
        .then(res => {
            if (!res.ok) throw new Error("Sesi berakhir.");
            return res.json();
        })
        .then(data => {
            if (data.valid && data.user) {
                localStorage.setItem(USER_KEY, JSON.stringify(data.user));
                setUserNavState(data.user);
                loadQuickStats();
                loadAppDirectory();
            } else {
                handleLogout(false);
            }
        })
        .catch(() => {
            setGuestNavState();
        });
}

function setGuestNavState() {
    const guestNav = document.getElementById("nav-guest-actions");
    const userNav = document.getElementById("nav-user-actions");
    const adminBell = document.getElementById("btn-admin-approvals");
    const adminTag = document.getElementById("superadmin-badge-nav");

    if (guestNav) guestNav.classList.remove("hidden");
    if (userNav) userNav.classList.add("hidden");
    if (adminBell) adminBell.classList.add("hidden");
    if (adminTag) adminTag.classList.add("hidden");
}

function setUserNavState(user) {
    const guestNav = document.getElementById("nav-guest-actions");
    const userNav = document.getElementById("nav-user-actions");
    const nameEl = document.getElementById("user-display-name");
    const adminBell = document.getElementById("btn-admin-approvals");
    const adminTag = document.getElementById("superadmin-badge-nav");

    if (guestNav) guestNav.classList.add("hidden");
    if (userNav) userNav.classList.remove("hidden");

    const displayName = user.nama_lengkap || user.username || "User";
    if (nameEl) nameEl.textContent = displayName;

    // Superadmin UI features for Aan
    const isSuper = user.is_superadmin || (user.username && user.username.toLowerCase() === "aan");
    if (isSuper) {
        if (adminBell) adminBell.classList.remove("hidden");
        if (adminTag) adminTag.classList.remove("hidden");
        loadPendingApprovals();
    } else {
        if (adminBell) adminBell.classList.add("hidden");
        if (adminTag) adminTag.classList.add("hidden");
    }
}

// =========================================================================
// 2. UNIVERSAL CTA & APP HUB ACTION HANDLER
// =========================================================================
let registeredAppsMap = {};

function openExternalLink(url) {
    if (!url) return;
    try {
        const a = document.createElement("a");
        a.href = url;
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        document.body.appendChild(a);
        a.click();
        setTimeout(() => {
            if (a && a.parentNode) a.parentNode.removeChild(a);
        }, 300);
    } catch (e) {
        window.open(url, "_blank");
    }
}

function getDynamicAppUrl(appKey, fallbackUrl) {
    if (registeredAppsMap && registeredAppsMap[appKey] && registeredAppsMap[appKey].url) {
        return registeredAppsMap[appKey].url;
    }
    const host = window.location.hostname || "basecampmeera.cloud";
    const isLocal = host === "localhost" || host === "127.0.0.1";

    if (appKey === "aspiran") {
        return "https://t.me/SeniorInvestorBot";
    }
    if (appKey === "nexat") {
        if (!isLocal) {
            return "https://basecampmeera.cloud:8002";
        }
        return "http://localhost:8002";
    }
    if (appKey === "finance") {
        if (!isLocal) {
            return "https://finance.basecampmeera.cloud";
        }
        return "http://localhost:8003";
    }
    if (appKey === "asset-tracker") {
        return "https://practice-program-fb3wd5vvoslgltdyf9fwzq.streamlit.app/";
    }

    if (fallbackUrl && fallbackUrl.trim() !== "" && (!fallbackUrl.includes("localhost") || isLocal)) {
        return fallbackUrl;
    }
    return window.location.origin;
}

function launchAppWithAuthCheck(appKey, targetUrl, appName) {
    const token = localStorage.getItem(TOKEN_KEY);
    const userStr = localStorage.getItem(USER_KEY);
    const finalUrl = getDynamicAppUrl(appKey, targetUrl);

    // 1. If not logged in -> Prompt auth modal
    if (!token || !userStr) {
        pendingAppKey = appKey;
        pendingTargetUrl = finalUrl;
        pendingAppName = appName;
        showToast(`Silakan masuk atau daftar terlebih dahulu untuk mengakses ${appName || 'sistem'}.`, "info");
        openLoginModal();
        return;
    }

    // 2. User is authenticated -> Open app with SSO token
    let ssoUrl = finalUrl;
    if (appKey !== 'aspiran' && finalUrl && finalUrl.startsWith("http")) {
        ssoUrl = `${finalUrl}${finalUrl.includes('?') ? '&' : '?'}token=${encodeURIComponent(token)}`;
    }
    console.log("[LaunchApp]", appKey, ssoUrl);
    openExternalLink(ssoUrl);
}

function clearPendingTarget() {
    pendingAppKey = null;
    pendingTargetUrl = null;
    pendingAppName = null;
}

// =========================================================================
// 3. AUTHENTICATION (LOGIN & REGISTRATION WITH APPROVAL)
// =========================================================================
function switchAuthTab(tab) {
    const btnLogin = document.getElementById("tab-btn-login");
    const btnRegister = document.getElementById("tab-btn-register");
    const formLogin = document.getElementById("login-form");
    const formRegister = document.getElementById("register-form");
    const titleEl = document.getElementById("auth-modal-title");

    if (tab === "register") {
        if (btnLogin) btnLogin.classList.remove("active");
        if (btnRegister) btnRegister.classList.add("active");
        if (formLogin) formLogin.classList.add("hidden");
        if (formRegister) formRegister.classList.remove("hidden");
        if (titleEl) titleEl.textContent = "Daftar Akun Baru";
        const fn = document.getElementById("reg-fullname");
        if (fn) fn.focus();
    } else {
        if (btnLogin) btnLogin.classList.add("active");
        if (btnRegister) btnRegister.classList.remove("active");
        if (formLogin) formLogin.classList.remove("hidden");
        if (formRegister) formRegister.classList.add("hidden");
        if (titleEl) titleEl.textContent = "Akses Ekosistem";
        const un = document.getElementById("username");
        if (un) un.focus();
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const btn = document.getElementById("btn-login");
    const unameInput = document.getElementById("username");
    const pwdInput = document.getElementById("password");

    const username = unameInput.value.trim();
    const password = pwdInput.value;

    if (!username || !password) {
        showToast("Mohon isi username dan password.", "error");
        return;
    }

    btn.disabled = true;
    btn.innerHTML = `<i class="ph ph-spinner ph-spin"></i> <span>Memvalidasi...</span>`;

    try {
        const res = await fetch(`${API_BASE}/api/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || "Username atau password tidak sesuai.");
        }

        // Save token and user details
        localStorage.setItem(TOKEN_KEY, data.token);
        localStorage.setItem(USER_KEY, JSON.stringify(data.user));

        showToast(data.message || `Selamat datang, ${data.user.nama_lengkap}!`, "success");
        setUserNavState(data.user);
        closeLoginModal();
        pwdInput.value = "";
        loadQuickStats();
        loadAppDirectory();

        // If there was a pending app request before login, launch it!
        if (pendingTargetUrl) {
            let dest = pendingTargetUrl;
            if (pendingAppKey !== 'aspiran' && dest && dest.startsWith("http")) {
                dest = `${dest}${dest.includes('?') ? '&' : '?'}token=${encodeURIComponent(data.token)}`;
            }
            showToast(`Membuka ${pendingAppName || 'aplikasi'}...`, "success");
            openExternalLink(dest);
            clearPendingTarget();
        }
    } catch (err) {
        showToast(err.message, "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<span>Masuk ke Sistem</span> <i class="ph-bold ph-arrow-right"></i>`;
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const btn = document.getElementById("btn-register");
    const fullname = document.getElementById("reg-fullname").value.trim();
    const username = document.getElementById("reg-username").value.trim();
    const password = document.getElementById("reg-password").value;
    const confirmPwd = document.getElementById("reg-confirm-password").value;

    if (!fullname || !username || !password) {
        showToast("Mohon lengkapi semua kolom pendaftaran.", "error");
        return;
    }

    if (password !== confirmPwd) {
        showToast("Konfirmasi password tidak cocok!", "error");
        return;
    }

    if (password.length < 6) {
        showToast("Password minimal 6 karakter.", "error");
        return;
    }

    btn.disabled = true;
    btn.innerHTML = `<i class="ph ph-spinner ph-spin"></i> <span>Mendaftarkan akun...</span>`;

    try {
        const res = await fetch(`${API_BASE}/api/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                nama_lengkap: fullname,
                username: username,
                password: password
            })
        });

        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || "Gagal melakukan registrasi.");
        }

        // Registration queued for Aan's approval
        showToast(data.message || "Pendaftaran akun berhasil! Menunggu persetujuan Aan.", "info");
        document.getElementById("register-form").reset();
        switchAuthTab('login');
        
        const loginUname = document.getElementById("username");
        if (loginUname) loginUname.value = username;
    } catch (err) {
        showToast(err.message, "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<span>Daftar & Masuk Sekarang</span> <i class="ph-bold ph-user-plus"></i>`;
    }
}

function handleLogout(notify = true) {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setGuestNavState();
    clearPendingTarget();
    loadQuickStats();
    loadAppDirectory();
    if (notify) {
        showToast("Anda telah keluar dari sesi akun.", "info");
    }
}

// =========================================================================
// 4. SUPERADMIN REGISTRATION APPROVAL FLOW (AAN EXCLUSIVE)
// =========================================================================
async function loadPendingApprovals() {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) return;

    try {
        const res = await fetch(`${API_BASE}/api/admin/pending-users`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (!res.ok) return;

        const data = await res.json();
        const count = data.count || 0;
        const users = data.pending_users || [];

        // Update badges
        const countBadge = document.getElementById("pending-approval-count");
        const modalCounter = document.getElementById("modal-pending-counter");

        if (countBadge) {
            countBadge.textContent = count;
            countBadge.style.display = count > 0 ? "flex" : "none";
        }
        if (modalCounter) {
            modalCounter.textContent = `${count} Menunggu`;
        }

        renderPendingList(users);
    } catch (err) {
        console.warn("Gagal memuat daftar approval:", err);
    }
}

function renderPendingList(users) {
    const listContainer = document.getElementById("approval-users-list");
    if (!listContainer) return;

    if (!users || users.length === 0) {
        listContainer.innerHTML = `
            <div class="approval-empty-state">
                <i class="ph-bold ph-shield-check"></i>
                <p>Tidak ada permintaan registrasi baru yang menunggu persetujuan.</p>
            </div>
        `;
        return;
    }

    listContainer.innerHTML = "";
    users.forEach(u => {
        const card = document.createElement("div");
        card.className = "approval-card-item";
        card.id = `approval-card-${u.id}`;
        card.innerHTML = `
            <div class="approval-user-info">
                <div class="approval-avatar"><i class="ph-bold ph-user"></i></div>
                <div class="approval-meta">
                    <h5>${escapeHtml(u.nama_lengkap)}</h5>
                    <span>@${escapeHtml(u.username)}</span>
                    <span class="approval-date"><i class="ph-bold ph-clock"></i> ${u.created_at}</span>
                </div>
            </div>
            <div class="approval-actions">
                <button class="btn-approve" onclick="approveUser(${u.id}, '${escapeHtml(u.username)}')" title="Setujui pendaftaran ${escapeHtml(u.username)}">
                    <i class="ph-bold ph-check"></i> <span>Setujui</span>
                </button>
                <button class="btn-reject" onclick="rejectUser(${u.id}, '${escapeHtml(u.username)}')" title="Tolak pendaftaran ${escapeHtml(u.username)}">
                    <i class="ph-bold ph-x"></i> <span>Tolak</span>
                </button>
            </div>
        `;
        listContainer.appendChild(card);
    });
}

function openApprovalModal() {
    const modal = document.getElementById("approval-modal");
    if (modal) {
        modal.classList.remove("hidden");
        loadPendingApprovals();
    }
}

function closeApprovalModal() {
    const modal = document.getElementById("approval-modal");
    if (modal) modal.classList.add("hidden");
}

async function approveUser(userId, username) {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) return;

    try {
        const res = await fetch(`${API_BASE}/api/admin/approve-user/${userId}`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Gagal menyetujui akun.");

        showToast(data.message || `Akun @${username} berhasil disetujui!`, "success");
        loadPendingApprovals();
    } catch (err) {
        showToast(err.message, "error");
    }
}

async function rejectUser(userId, username) {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) return;

    if (!confirm(`Apakah Anda yakin ingin menolak pendaftaran akun @${username}?`)) {
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/api/admin/reject-user/${userId}`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Gagal menolak akun.");

        showToast(data.message || `Pendaftaran akun @${username} ditolak.`, "info");
        loadPendingApprovals();
    } catch (err) {
        showToast(err.message, "error");
    }
}

// =========================================================================
// 5. USER PROFILE & PASSWORD SETTINGS MODAL
// =========================================================================
function openProfileSettingsModal() {
    const userStr = localStorage.getItem(USER_KEY);
    if (!userStr) {
        openLoginModal();
        return;
    }

    const user = JSON.parse(userStr);

    document.getElementById("profile-fullname").textContent = user.nama_lengkap || user.username || "-";
    document.getElementById("profile-username").textContent = `@${user.username || "-"}`;

    const modal = document.getElementById("profile-settings-modal");
    if (modal) modal.classList.remove("hidden");
}

function closeProfileSettingsModal() {
    const modal = document.getElementById("profile-settings-modal");
    if (modal) {
        modal.classList.add("hidden");
        const form = document.getElementById("profile-pwd-form");
        if (form) form.reset();
    }
}

async function handleChangePassword(e) {
    e.preventDefault();
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
        showToast("Silakan masuk terlebih dahulu.", "error");
        openLoginModal();
        return;
    }

    const oldPwd = document.getElementById("settings-old-password").value;
    const newPwd = document.getElementById("settings-new-password").value;
    const confirmPwd = document.getElementById("settings-confirm-password").value;

    if (newPwd !== confirmPwd) {
        showToast("Password baru dan konfirmasi tidak cocok!", "error");
        return;
    }

    if (newPwd.length < 6) {
        showToast("Password minimal 6 karakter.", "error");
        return;
    }

    const btn = document.getElementById("btn-save-settings-pwd");
    btn.disabled = true;
    btn.textContent = "Menyimpan...";

    try {
        const res = await fetch(`${API_BASE}/api/auth/change-password`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ old_password: oldPwd, new_password: newPwd })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Gagal mengubah password.");

        showToast(data.message || "Password berhasil diubah!", "success");
        closeProfileSettingsModal();
    } catch (err) {
        showToast(err.message, "error");
    } finally {
        btn.disabled = false;
        btn.textContent = "Simpan Password Baru";
    }
}

// =========================================================================
// 6. MODAL HELPERS
// =========================================================================
function openLoginModal() {
    const modal = document.getElementById("login-modal");
    if (modal) {
        modal.classList.remove("hidden");
        switchAuthTab('login');
    }
}

function closeLoginModal() {
    const modal = document.getElementById("login-modal");
    if (modal) modal.classList.add("hidden");
}

function closeModalOnBackdrop(e) {
    if (e.target.classList.contains("modal-backdrop")) {
        e.target.classList.add("hidden");
    }
}

function togglePasswordVisibility(inputId, btn) {
    const input = document.getElementById(inputId);
    const icon = btn.querySelector("i");
    if (!input) return;
    if (input.type === "password") {
        input.type = "text";
        if (icon) icon.className = "ph-bold ph-eye-slash";
    } else {
        input.type = "password";
        if (icon) icon.className = "ph-bold ph-eye";
    }
}

// =========================================================================
// 7. APP HUB DRAWER & USER-ISOLATED METRICS
// =========================================================================
function toggleAppHub() {
    const drawer = document.getElementById("app-hub-drawer");
    if (!drawer) return;
    drawer.classList.toggle("open");
    if (drawer.classList.contains("open")) {
        loadAppDirectory();
        loadQuickStats();
    }
}

function closeAppHub() {
    const drawer = document.getElementById("app-hub-drawer");
    if (drawer) drawer.classList.remove("open");
}

async function loadQuickStats() {
    const token = localStorage.getItem(TOKEN_KEY) || "";
    const elTotal = document.getElementById("drawer-stat-total-asset");
    const elTabungan = document.getElementById("drawer-stat-tabungan");
    const elInvestasi = document.getElementById("drawer-stat-investasi");
    const elHutang = document.getElementById("drawer-stat-hutang");

    if (!token) {
        if (elTotal) elTotal.textContent = "Silakan Masuk";
        if (elTabungan) elTabungan.textContent = "Silakan Masuk";
        if (elInvestasi) elInvestasi.textContent = "Silakan Masuk";
        if (elHutang) elHutang.textContent = "Silakan Masuk";
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/api/quick-stats`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (!res.ok) return;

        const data = await res.json();
        const m = data.metrics || {};

        if (elTotal) elTotal.textContent = formatRupiah(m.total_asset || 0);
        if (elTabungan) elTabungan.textContent = formatRupiah(m.tabungan || 0);
        if (elInvestasi) elInvestasi.textContent = formatRupiah(m.investasi || 0);
        if (elHutang) elHutang.textContent = formatRupiah(m.hutang_vendor || 0);
    } catch (e) {
        console.warn("Gagal memuat quick stats:", e);
    }
}

async function loadAppDirectory() {
    const container = document.getElementById("apps-grid");
    if (!container) return;

    const token = localStorage.getItem(TOKEN_KEY) || "";

    try {
        const res = await fetch(`${API_BASE}/api/apps`, {
            headers: token ? { "Authorization": `Bearer ${token}` } : {}
        });
        if (!res.ok) throw new Error("Gagal mengambil data sistem.");

        const data = await res.json();
        const apps = data.apps || [];

        container.innerHTML = "";
        apps.forEach(app => {
            registeredAppsMap[app.key] = app;
            const card = createAppCard(app);
            container.appendChild(card);
        });
    } catch (e) {
        console.warn("Gagal render directory:", e);
    }
}

function createAppCard(app) {
    const card = document.createElement("div");
    card.className = "app-card";
    card.style.setProperty("--card-accent", app.accent_color || "#38BDF8");

    const targetUrl = app.url || getDynamicAppUrl(app.key, "");
    const portBadge = app.port ? `<span class="app-badge-pill">Port ${app.port}</span>` : `<span class="app-badge-pill">${app.badge || 'Cloud'}</span>`;
    
    card.innerHTML = `
        <div class="app-card-top">
            <div class="app-icon-badge">
                <i class="ph-bold ph-${app.icon || 'squares-four'}"></i>
            </div>
            ${portBadge}
        </div>
        <div class="app-card-body">
            <h5>${app.name}</h5>
            <p>${app.description || ''}</p>
        </div>
        <div class="app-card-footer">
            <span class="app-status"><span class="status-dot"></span><span>Terhubung</span></span>
            <button onclick="launchAppWithAuthCheck('${app.key}', '${targetUrl}', '${app.name}')" class="btn-launch" title="Buka ${app.name}">
                <span>Buka</span> <i class="ph-bold ph-arrow-square-out"></i>
            </button>
        </div>
    `;
    return card;
}

// =========================================================================
// 8. ASPIRAN! AI TELEGRAM SIMULATOR
// =========================================================================
const ASPIRAN_PRESETS = {
    nexat: {
        query: "/status_nexat",
        response: `Update operasional <b>NEXAT Apparel</b>:<br><br>
• <b>Order Aktif:</b> 6 batch konveksi (Total 2.450 pcs apparel)<br>
• <b>Hutang Vendor:</b> Rp 18.500.000 (Jatuh tempo Termin 2: 18 Sept)<br>
• <b>Margin HPP Rata-rata:</b> 38.4%<br>
• <b>Status QC:</b> 98.2% lolos uji tanpa reject.<br><br>
<i>Data terhubung dengan database <code>Vendor_tracker</code> (Port 8002).</i>`
    },
    asset: {
        query: "/total_networth",
        response: `Ringkasan valuasi <b>Asset Tracker OS</b>:<br><br>
• <b>Total Net Worth:</b> <span style="color:#10B981;font-weight:700;">Rp 385.000.000</span> (+14.2% YoY)<br>
• <b>Alokasi Aset:</b><br>
  - Properti & Fisik: 42% (Rp 161.7M)<br>
  - Saham IHSG: 28% (Rp 107.8M)<br>
  - Emas & Reksa Dana: 18% (Rp 69.3M)<br>
  - Kas & Likuid: 12% (Rp 46.2M)<br><br>
<i>Target Milestone 2026: Rp 500.000.000 (Tercapai 77%).</i>`
    },
    screener: {
        query: "/screener BBRI TPIA",
        response: `Screener AI untuk <b>BBRI & TPIA</b>:<br><br>
🏦 <b>BBRI (Bank Rakyat Indonesia):</b><br>
• Harga: Rp 4.950 | PER: 11.2x | PBV: 2.1x<br>
• Dividend Yield: ~5.8% | Status: <b>Strong Accumulation</b><br><br>
🧪 <b>TPIA (Chandra Asri Pacific):</b><br>
• Harga: Rp 8.825 | Momentum: Support Rebound<br>
• Status: <b>Watchlist Breakout</b><br><br>
<i>Insight di-generate via Google Gemini Flash.</i>`
    },
    finance: {
        query: "/forecast_cashflow",
        response: `Proyeksi Cash Flow Finansial (Q4):<br><br>
• <b>Estimasi Inflow:</b> Rp 32.500.000/bln (NEXAT + Dividen)<br>
• <b>Beban Tetap & Pos Rutin:</b> Rp 17.200.000/bln<br>
• <b>Net Surplus:</b> +Rp 15.300.000/bln<br>
• <b>Dana Darurat:</b> 100% (Coverage 6 bulan aman).<br><br>
<i>Terhubung ke modul Financial Management (Port 8003).</i>`
    }
};

function initTelegramSimulator() {
    const input = document.getElementById("telegram-chat-input");
    if (!input) return;

    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleTelegramSubmit(e);
        }
    });
}

function askTelegramPrompt(presetKey) {
    const preset = ASPIRAN_PRESETS[presetKey];
    if (!preset) return;

    const input = document.getElementById("telegram-chat-input");
    if (input) input.value = preset.query;

    renderTelegramInteraction(preset.query, preset.response);
}

function handleTelegramSubmit(e) {
    if (e && e.preventDefault) e.preventDefault();
    const input = document.getElementById("telegram-chat-input");
    if (!input) return;

    const text = input.value.trim();
    if (!text) return;

    input.value = "";

    let responseText = "";
    const lower = text.toLowerCase();

    if (lower.includes("nexat") || lower.includes("baju") || lower.includes("vendor") || lower.includes("order")) {
        responseText = ASPIRAN_PRESETS.nexat.response;
    } else if (lower.includes("asset") || lower.includes("networth") || lower.includes("kekayaan") || lower.includes("emas")) {
        responseText = ASPIRAN_PRESETS.asset.response;
    } else if (lower.includes("saham") || lower.includes("screener") || lower.includes("bbri") || lower.includes("tpia")) {
        responseText = ASPIRAN_PRESETS.screener.response;
    } else if (lower.includes("keuangan") || lower.includes("finance") || lower.includes("forecast") || lower.includes("beban")) {
        responseText = ASPIRAN_PRESETS.finance.response;
    } else {
        responseText = `Halo! Saya ASPIRAN! siap membantu. Perintah <b>"${escapeHtml(text)}"</b> berhasil diproses untuk akun Anda. Semua modul sistem berstatus online.`;
    }

    renderTelegramInteraction(text, responseText);
}

function renderTelegramInteraction(userText, botHtml) {
    const messagesContainer = document.getElementById("telegram-messages-container");
    if (!messagesContainer) return;

    const now = new Date();
    const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

    // User Message
    const userMsg = document.createElement("div");
    userMsg.className = "tg-msg user";
    userMsg.innerHTML = `
        <div class="tg-msg-bubble">
            <p>${escapeHtml(userText)}</p>
            <span class="tg-time">${timeStr} <i class="ph-bold ph-checks"></i></span>
        </div>
    `;
    messagesContainer.appendChild(userMsg);

    // Typing Indicator
    const typingIndicator = document.createElement("div");
    typingIndicator.className = "tg-msg bot tg-typing-row";
    typingIndicator.id = "tg-typing-temp";
    typingIndicator.innerHTML = `
        <div class="tg-msg-bubble tg-typing-bubble">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
        </div>
    `;
    messagesContainer.appendChild(typingIndicator);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    setTimeout(() => {
        const temp = document.getElementById("tg-typing-temp");
        if (temp) temp.remove();

        const botMsg = document.createElement("div");
        botMsg.className = "tg-msg bot animate-pop";
        botMsg.innerHTML = `
            <div class="tg-msg-bubble">
                <div class="tg-bot-badge"><i class="ph-bold ph-sparkle"></i> ASPIRAN! AI</div>
                <div class="tg-bot-content">${botHtml}</div>
                <span class="tg-time">${timeStr}</span>
            </div>
        `;
        messagesContainer.appendChild(botMsg);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }, 550);
}

// =========================================================================
// 9. FINANCIAL FORECAST & DONUT CONTROLLERS
// =========================================================================
const FORECAST_BARS = {
    now: [65, 70, 75, 60, 80, 85, 95],
    next_month: [70, 75, 60, 80, 85, 95, 100],
    three_months: [60, 80, 85, 95, 100, 110, 125],
    six_months: [85, 95, 100, 110, 125, 120, 135]
};

const MONTH_LABELS = {
    now: ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Sep"],
    next_month: ["Feb", "Mar", "Apr", "Mei", "Jun", "Sep", "Okt"],
    three_months: ["Apr", "Mei", "Jun", "Sep", "Okt", "Nov", "Des"],
    six_months: ["Jun", "Sep", "Okt", "Nov", "Des", "Jan", "Feb"]
};

function switchForecastHorizon(horizon, btn) {
    document.querySelectorAll(".forecast-tab-btn").forEach(b => b.classList.remove("active"));
    if (btn) btn.classList.add("active");

    const bars = FORECAST_BARS[horizon] || FORECAST_BARS.now;
    const labels = MONTH_LABELS[horizon] || MONTH_LABELS.now;
    const chartContainer = document.getElementById("forecast-bars-container");

    if (chartContainer) {
        chartContainer.innerHTML = "";
        bars.forEach((val, idx) => {
            const barItem = document.createElement("div");
            barItem.className = "forecast-bar-item";
            const fillHeight = Math.min(100, Math.max(15, (val / 140) * 100));
            barItem.innerHTML = `
                <div class="forecast-bar-fill-track">
                    <div class="forecast-bar-fill" style="height: ${fillHeight}%;"></div>
                </div>
                <span class="forecast-bar-label">${labels[idx]}</span>
            `;
            chartContainer.appendChild(barItem);
        });
    }
}

const ASSET_SEGMENTS = {
    properti: { label: "Properti", value: "Rp 161.7M" },
    saham: { label: "Saham IHSG", value: "Rp 107.8M" },
    emas: { label: "Emas & RD", value: "Rp 69.3M" },
    kas: { label: "Kas Likuid", value: "Rp 46.2M" }
};

function highlightAssetSegment(key) {
    const item = ASSET_SEGMENTS[key];
    if (!item) return;

    const t = document.getElementById("donut-center-title");
    const v = document.getElementById("donut-center-val");
    if (t) t.textContent = item.label;
    if (v) v.textContent = item.value;
}

function resetAssetSegment() {
    const t = document.getElementById("donut-center-title");
    const v = document.getElementById("donut-center-val");
    if (t) t.textContent = "Total Assets";
    if (v) v.textContent = "Rp 385M";
}

// =========================================================================
// 10. SCROLL SPY & UTILITIES
// =========================================================================
function initScrollSpy() {
    const sections = document.querySelectorAll("section[id], header[id]");
    const navLinks = document.querySelectorAll(".nav-link");

    window.addEventListener("scroll", () => {
        let current = "";
        const scrollPosition = window.pageYOffset + 120;

        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;
            if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                current = section.getAttribute("id");
            }
        });

        navLinks.forEach(link => {
            link.classList.remove("active");
            if (link.getAttribute("data-target") === current) {
                link.classList.add("active");
            }
        });
    });
}

function formatRupiah(val) {
    const num = Number(val) || 0;
    return "Rp " + num.toLocaleString("id-ID", { maximumFractionDigits: 0 });
}

function escapeHtml(str) {
    if (!str) return "";
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function showToast(msg, type = "success") {
    const toast = document.getElementById("toast");
    if (!toast) return;

    toast.className = `toast ${type}`;
    let iconClass = "ph-bold ph-check-circle";
    if (type === "error") iconClass = "ph-bold ph-warning-circle";
    else if (type === "info") iconClass = "ph-bold ph-info";

    toast.innerHTML = `<i class="${iconClass}" style="font-size: 18px;"></i> <span>${msg}</span>`;
    toast.classList.remove("hidden");

    setTimeout(() => {
        toast.classList.add("hidden");
    }, 4500);
}
