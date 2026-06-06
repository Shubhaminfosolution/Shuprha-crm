// ===============================
// 🔐 AUTH FETCH
// ===============================
function authFetch(url, options = {}) {
    const token = localStorage.getItem("token") || sessionStorage.getItem("token");

    return fetch(url, {
        ...options,
        headers: {
            ...(options.headers || {}),
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
        }
    });
}

// ===============================
// 🔐 AUTH CHECK
// ===============================
(function checkAuth() {
    const token = localStorage.getItem("token") || sessionStorage.getItem("token");
    if (window.location.pathname.includes("login")) return;
    if (!token) {
        window.location.href = "/api/v1/login/";
    }
})();

// ===============================
// 🔔 TOAST
// ===============================
function showToast(message, type = "success") {
    const container = document.getElementById("toastContainer");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = `toast-msg toast-${type}`;
    toast.innerText = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// ===============================
// ⏳ LOADER
// ===============================
function showLoader() {
    document.getElementById("globalLoader")?.classList.remove("d-none");
}

function hideLoader() {
    document.getElementById("globalLoader")?.classList.add("d-none");
}

// ===============================
// 🚪 LOGOUT
// ===============================
function logout() {
    localStorage.removeItem("token");
    sessionStorage.removeItem("token");
    showToast("Logged out successfully", "success");
    setTimeout(() => {
        window.location.href = "/api/v1/login/";
    }, 500);
}

// ===============================
// 🎯 ACTIVE NAV
// ===============================
function setActiveNav() {
    const path = window.location.pathname;
    document.querySelectorAll(".nav-link").forEach(link => {
        const href = link.getAttribute("href") || "";
        if (href !== "#" && path.includes(href.split("/").filter(Boolean)[2])) {
            link.classList.add("active");
        }
    });
}

// ===============================
// 🔍 SEARCH
// ===============================
function searchAPI(query) {
    showLoader();
    fetch(`/api/v1/leads/?search=${query}`)
        .then(res => {
            if (!res.ok) throw new Error();
            return res.json();
        })
        .then(data => renderSearchResults(data.results || data))
        .catch(() => showToast("Search failed", "error"))
        .finally(() => hideLoader());
}

function renderSearchResults(data) {
    const container = document.getElementById("searchResults");
    if (!container) return;
    container.innerHTML = "";
    if (!data.length) {
        container.innerHTML = "<div class='search-item'>No results</div>";
        container.classList.remove("d-none");
        return;
    }
    data.forEach(item => {
        const div = document.createElement("div");
        div.className = "search-item";
        div.innerHTML = `
            <strong>${item.first_name}</strong><br>
            <small>${item.email || ""} | ${item.phone || ""}</small>
        `;
        div.onclick = () => {
            showToast(`Selected: ${item.first_name}`, "success");
            hideResults();
        };
        container.appendChild(div);
    });
    container.classList.remove("d-none");
}

function hideResults() {
    const container = document.getElementById("searchResults");
    if (container) container.classList.add("d-none");
}

document.addEventListener("click", function (e) {
    if (!e.target.closest(".global-search")) hideResults();
});

// ===============================
// ✅ DOM READY — single block
// ===============================
document.addEventListener("DOMContentLoaded", function () {

    // 🌙 Theme
    const themeBtn = document.getElementById("themeToggle");
    const savedTheme = localStorage.getItem("theme") || "light";
    document.documentElement.setAttribute("data-theme", savedTheme);
    if (themeBtn) {
        themeBtn.innerText = savedTheme === "dark" ? "☀️" : "🌙";
        themeBtn.addEventListener("click", () => {
            const isDark = document.documentElement.getAttribute("data-theme") === "dark";
            const newTheme = isDark ? "light" : "dark";
            document.documentElement.setAttribute("data-theme", newTheme);
            localStorage.setItem("theme", newTheme);
            themeBtn.innerText = newTheme === "dark" ? "☀️" : "🌙";
        });
    }

    // ☰ Sidebar toggle — works on every page
    const sidebar = document.querySelector(".sidebar");
    const mainEl = document.querySelector(".main");
    const sidebarBtn = document.getElementById("sidebarToggle");

    // Restore saved state
    if (localStorage.getItem("sidebar") === "collapsed") {
        sidebar?.classList.add("collapsed");
        mainEl?.classList.add("collapsed");
    }

    if (sidebarBtn && sidebar) {
        sidebarBtn.addEventListener("click", () => {
            sidebar.classList.toggle("collapsed");
            mainEl?.classList.toggle("collapsed");
            localStorage.setItem(
                "sidebar",
                sidebar.classList.contains("collapsed") ? "collapsed" : "expanded"
            );
        });
    }

    // 🔍 Global search
    let searchTimeout = null;
    const searchInput = document.getElementById("globalSearchInput");
    if (searchInput) {
        searchInput.addEventListener("input", function () {
            const query = this.value.trim();
            clearTimeout(searchTimeout);
            if (!query) { hideResults(); return; }
            searchTimeout = setTimeout(() => searchAPI(query), 300);
        });
    }

    // 🎯 Active nav
    setActiveNav();
});