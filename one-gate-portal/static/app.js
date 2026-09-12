/**
 * ONE GATE SYSTEM — FRONTEND INTERACTION LOGIC
 * Manages JWT Auth, Live Metrics, Dynamic App Cards & Session Persistence
 */

const API_BASE = "";
const TOKEN_KEY = "one_gate_jwt_token";
const USER_KEY = "one_gate_user_data";

// --- Initialization ---
document.addEventListener("DOMContentLoaded", () => {
    initAuthSession();
});

function initAuthSession() {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
        showView("login");
        return;
    }

    // Verify token validity with backend
    fetch(`${API_BASE}/api/auth/verify?token=${encodeURIComponent(token)}`)
        .then(res => {
            if (!res.ok) throw new Error("Sesi telah kedaluwarsa.");
            return res.json();
        })
        .then(data => {
            if (data.valid && data.user) {
                localStorage.setItem(USER_KEY, JSON.stringify(data.user));
                setupPortalView(data.user);
                showView("portal");
            } else {
                handleLogout();
            }
        })
        .catch(() => {
            handleLogout();
        });
}

function showView(viewName) {
    const loginView = document.getElementById("login-view");
    const portalView = document.getElementById("portal-view");

    if (viewName === "login") {
        loginView.classList.remove("hidden");
        portalView.classList.add("hidden");
    } else {
        loginView.classList.add("hidden");
        portalView.classList.remove("hidden");
    }
}

// --- Login Handler ---
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
            throw new Error(data.detail || "Gagal masuk. Periksa username & password.");
        }

        // Simpan token & profil
        localStorage.setItem(TOKEN_KEY, data.token);
        localStorage.setItem(USER_KEY, JSON.stringify(data.user));

        showToast(data.message || "Login berhasil!", "success");
        setupPortalView(data.user);
        showView("portal");
        pwdInput.value = "";
    } catch (err) {
        showToast(err.message, "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<span class="btn-text">Masuk ke Portal</span> <i class="ph-bold ph-arrow-right"></i>`;
    }
}

// --- Portal View Setup ---
function setupPortalView(user) {
    const displayName = user.nama_lengkap || user.username || "Mas Aan";
    document.getElementById("user-display-name").textContent = displayName;
    document.getElementById("welcome-user").textContent = displayName;
    document.getElementById("user-role-tag").textContent = (user.role || "admin").toUpperCase();

    loadQuickStats();
    loadAppDirectory();
}

// --- Fetch Quick Stats ---
async function loadQuickStats() {
    const token = localStorage.getItem(TOKEN_KEY);
    try {
        const res = await fetch(`${API_BASE}/api/quick-stats`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (!res.ok) return;

        const data = await res.json();
        const m = data.metrics || {};

        document.getElementById("stat-total-asset").textContent = formatRupiah(m.total_asset);
        document.getElementById("stat-tabungan").textContent = formatRupiah(m.tabungan);
        document.getElementById("stat-investasi").textContent = formatRupiah(m.investasi);
        document.getElementById("stat-hutang-vendor").textContent = formatRupiah(m.hutang_vendor);
        document.getElementById("stat-vendor-orders").textContent = `${m.vendor_orders_pending || 0} pesanan vendor konveksi belum lunas`;
    } catch (e) {
        console.warn("Gagal memuat quick stats:", e);
    }
}

// --- Fetch App Directory & Render Cards ---
async function loadAppDirectory() {
    const token = localStorage.getItem(TOKEN_KEY);
    const container = document.getElementById("apps-grid");
    container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted);"><i class="ph ph-spinner ph-spin"></i> Memuat daftar aplikasi...</div>`;

    try {
        const res = await fetch(`${API_BASE}/api/apps`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (!res.ok) throw new Error("Gagal mengambil data aplikasi.");

        const data = await res.json();
        const apps = data.apps || [];

        container.innerHTML = "";
        apps.forEach(app => {
            const card = createAppCard(app, token);
            container.appendChild(card);
        });
    } catch (e) {
        container.innerHTML = `<div style="grid-column: 1/-1; color: #EF4444;">Gagal memuat aplikasi: ${e.message}</div>`;
    }
}

function createAppCard(app, token) {
    const card = document.createElement("div");
    card.className = "app-card glass-panel";
    card.style.setProperty("--card-accent", app.accent_color || "var(--primary)");

    // Generate dynamic target URL (passing token for SSO auto-login if web app)
    let targetUrl = app.url;
    // Deteksi host saat ini jika sedang diakses via VPS atau local IP
    const currentHost = window.location.hostname;
    if (app.port && (currentHost !== "localhost" && currentHost !== "127.0.0.1")) {
        targetUrl = `http://${currentHost}:${app.port}`;
    }

    // Jika web app internal, sematkan SSO token di query param agar otomatis login
    const ssoUrl = app.port ? `${targetUrl}?token=${encodeURIComponent(token)}` : targetUrl;

    const portBadge = app.port ? `<span class="app-badge-pill port">Port ${app.port}</span>` : `<span class="app-badge-pill">${app.badge}</span>`;

    card.innerHTML = `
        <div class="app-card-top">
            <div class="app-icon-badge">
                <i class="ph-bold ph-${app.icon || 'squares-four'}"></i>
            </div>
            ${portBadge}
        </div>

        <div class="app-card-body">
            <span class="app-category-tag">${app.category}</span>
            <h4 class="app-name">${app.name}</h4>
            <p class="app-subtitle">${app.description}</p>
        </div>

        <div class="app-card-footer">
            <div class="app-status">
                <span class="status-dot" style="background: ${app.accent_color};"></span>
                <span>${app.status}</span>
            </div>
            <a href="${ssoUrl}" target="_blank" rel="noopener noreferrer" class="btn-launch" title="Buka ${app.name}">
                <span>Buka</span>
                <i class="ph-bold ph-arrow-square-out"></i>
            </a>
        </div>
    `;
    return card;
}

// --- Password Visibility Toggle ---
function togglePasswordVisibility(inputId, btn) {
    const input = document.getElementById(inputId);
    const icon = btn.querySelector("i");
    if (input.type === "password") {
        input.type = "text";
        icon.className = "ph ph-eye-slash";
    } else {
        input.type = "password";
        icon.className = "ph ph-eye";
    }
}

// --- Change Password Modal ---
function openPasswordModal() {
    document.getElementById("password-modal").classList.remove("hidden");
    document.getElementById("old-password").focus();
}

function closePasswordModal() {
    document.getElementById("password-modal").classList.add("hidden");
    document.getElementById("change-password-form").reset();
}

function closeModalOnBackdrop(e) {
    if (e.target.id === "password-modal") {
        closePasswordModal();
    }
}

async function handleChangePassword(e) {
    e.preventDefault();
    const token = localStorage.getItem(TOKEN_KEY);
    const oldPwd = document.getElementById("old-password").value;
    const newPwd = document.getElementById("new-password").value;
    const confirmPwd = document.getElementById("confirm-password").value;

    if (newPwd !== confirmPwd) {
        showToast("Password baru dan konfirmasi tidak cocok!", "error");
        return;
    }

    const btn = document.getElementById("btn-save-pwd");
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
        closePasswordModal();
    } catch (err) {
        showToast(err.message, "error");
    } finally {
        btn.disabled = false;
        btn.textContent = "Simpan Password";
    }
}

// --- Logout ---
function handleLogout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    showToast("Anda telah keluar dari sesi.", "success");
    showView("login");
}

// --- Helper Functions ---
function formatRupiah(val) {
    const num = Number(val) || 0;
    return "Rp " + num.toLocaleString("id-ID", { maximumFractionDigits: 0 });
}

function showToast(msg, type = "success") {
    const toast = document.getElementById("toast");
    toast.className = `toast ${type}`;
    const icon = type === "success" ? "ph-check-circle" : "ph-warning-circle";
    toast.innerHTML = `<i class="ph-bold ${icon}" style="font-size: 18px; color: ${type === 'success' ? '#10B981' : '#EF4444'};"></i> <span>${msg}</span>`;
    toast.classList.remove("hidden");

    setTimeout(() => {
        toast.classList.add("hidden");
    }, 4000);
}
