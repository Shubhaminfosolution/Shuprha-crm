// 🔐 AUTH CHECK (can stay outside)
function authFetch(url, options = {}) {
     const token = localStorage.getItem("token") || sessionStorage.getItem("token");

    return fetch(url, {
        ...options,
        headers: {
            ...(options.headers || {}),
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`  // ✅ FIXED
        }
    });
}


(function checkAuth() {

    const token = localStorage.getItem("token") || sessionStorage.getItem("token");

    if (window.location.pathname.includes("login")) return;

    if (!token) {
        window.location.href = "/login/";
    }

})();


function showToast(message, type = "success") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast-msg toast-${type}`;
    toast.innerText = message;
    container.appendChild(toast);

    setTimeout(() => toast.remove(), 3000);
}

// ✅ DOM READY
document.addEventListener("DOMContentLoaded", () => {

    // 🌙 Theme Toggle
    const themeBtn = document.getElementById("themeToggle");

    if (localStorage.getItem("theme") === "dark") {
        document.body.classList.add("dark");
        if (themeBtn) themeBtn.innerText = "☀️";
    }

    if (themeBtn) {
        themeBtn.addEventListener("click", () => {
            document.body.classList.toggle("dark");

            if (document.body.classList.contains("dark")) {
                localStorage.setItem("theme", "dark");
                themeBtn.innerText = "☀️";
            } else {
                localStorage.setItem("theme", "light");
                themeBtn.innerText = "🌙";
            }
        });
    }

    // ☰ Sidebar Toggle
    const sidebar = document.querySelector(".sidebar");
    const main = document.querySelector(".main");
    const sidebarBtn = document.getElementById("sidebarToggle");

    if (localStorage.getItem("sidebar") === "collapsed") {
        sidebar?.classList.add("collapsed");
        main?.classList.add("collapsed");
    }

    if (sidebarBtn) {
        sidebarBtn.addEventListener("click", () => {
            sidebar.classList.toggle("collapsed");
            main.classList.toggle("collapsed");

            localStorage.setItem(
                "sidebar",
                sidebar.classList.contains("collapsed") ? "collapsed" : "expanded"
            );
        });
    }

    // 🔍 GLOBAL SEARCH
    let searchTimeout = null;

    const searchInput = document.getElementById("globalSearchInput");

    if (searchInput) {
        searchInput.addEventListener("input", function () {

            const query = this.value.trim();

            clearTimeout(searchTimeout);

            if (!query) {
                hideResults();
                return;
            }

            searchTimeout = setTimeout(() => {
                searchAPI(query);
            }, 300);
        });
    }

});




function showLoader() {
    document.getElementById("globalLoader")?.classList.remove("d-none");
}

function hideLoader() {
    document.getElementById("globalLoader")?.classList.add("d-none");
}

// 🔌 SEARCH API
function searchAPI(query) {

    showLoader();

    fetch(`/api/v1/leads/?search=${query}`)
        .then(res => {
            if (!res.ok) throw new Error();
            return res.json();
        })
        .then(data => renderSearchResults(data))
        .catch(() => showToast("Search failed", "error"))
        .finally(() => hideLoader());
}


// 🎯 RENDER
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


// ❌ HIDE
function hideResults() {
    const container = document.getElementById("searchResults");
    if (container) container.classList.add("d-none");
}


// 🧠 CLICK OUTSIDE
document.addEventListener("click", function (e) {
    if (!e.target.closest(".global-search")) {
        hideResults();
    }
});


// 🚪 LOGOUT (ALREADY CORRECT ✅)
function logout() {

    localStorage.removeItem("token");
    sessionStorage.removeItem("token");

    showToast("Logged out successfully", "success");

    setTimeout(() => {
        window.location.href = "/api/v1/login/";
    }, 500);
}