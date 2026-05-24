// ===============================
// 🔐 AUTH CHECK
// ===============================
(function checkAuth() {
    const token =
        localStorage.getItem("token") ||
        sessionStorage.getItem("token");

    if (!window.location.pathname.includes("login") && !token) {
        window.location.href = "/api/v1/login/";
    }
})();


// ===============================
// 🔌 AUTH FETCH
// ===============================
function authFetch(url, options = {}) {
    const token =
        localStorage.getItem("token") ||
        sessionStorage.getItem("token");

    return fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
            ...(options.headers || {})
        }
    })
    .then(res => {
        if (res.status === 401) {
            console.error("Unauthorized - logging out");
            logout();
        }
        return res;
    });
}


let allLeads = [];


// ===============================
// 📊 LOAD LEADS
// ===============================
function loadLeads() {
    // Use filter-specific IDs to avoid conflict with modal form fields
    const search = document.getElementById("filterSearch")?.value || "";
    const status = document.getElementById("filterStatus")?.value || "";
    const source = document.getElementById("filterSource")?.value || "";

    const params = new URLSearchParams();
    if (search) params.append("search", search);
    if (status) params.append("status", status);
    if (source) params.append("source", source);

    const url = `/api/v1/leads/?${params.toString()}`;
    console.log("Fetching:", url);

    authFetch(url)
        .then(res => res.json())
        .then(data => {
            const leads = data.results || data;
            allLeads = leads;
            renderLeads(leads);
        })
        .catch(err => {
            console.error("Load error:", err);
            showToast("Failed to load leads", "error");
        });
}


// ===============================
// 🎯 RENDER LEADS
// ===============================
function renderLeads(leads) {
    const table = document.getElementById("leadsTable");
    if (!table) return;

    table.innerHTML = "";

    if (!leads || leads.length === 0) {
        table.innerHTML = "<tr><td colspan='8'>No leads found</td></tr>";
        return;
    }

    let html = "";

    leads.forEach(lead => {
        html += `
        <tr>
            <td>
                <input type="checkbox" class="leadCheckbox" value="${lead.id}">
            </td>
            <td>
                <a href="/api/v1/leads-ui/${lead.id}/">
                    ${lead.first_name || ""} ${lead.last_name || ""}
                </a>
            </td>
            <td>${lead.email || "-"}</td>
            <td>${lead.phone || "-"}</td>
            <td><span id="status-${lead.id}"></span></td>
            <td>${lead.source || "-"}</td>
            <td>${lead.next_followup_date || "-"}</td>
            <td>
                <button class="btn btn-success btn-sm"
                    onclick="sendWhatsApp('${lead.id}')">WhatsApp</button>
                <button class="btn btn-danger btn-sm"
                    onclick="deleteLead(${lead.id})">Delete</button>
            </td>
        </tr>
        `;
    });

    table.innerHTML = html;

    // Apply status badges after rendering
    leads.forEach(lead => {
        const el = document.getElementById(`status-${lead.id}`);
        if (el && lead.status) {
            applyStatusBadge(el, lead.status);
        }
    });
}


// ===============================
// 🗑️ DELETE LEAD (soft delete)
// ===============================
function deleteLead(id) {
    if (!confirm("Delete this lead?")) return;

    authFetch(`/api/v1/leads/${id}/`, {
        method: "PATCH",
        body: JSON.stringify({ is_deleted: true })  // fixed: was json.stringify
    })
    .then(() => {
        showToast("Lead deleted", "success");
        loadLeads();
    })
    .catch(err => {
        console.error(err);
        showToast("Delete failed", "error");
    });
}


// ===============================
// 🗑️ BULK DELETE
// ===============================
function bulkDelete() {
    const checked = document.querySelectorAll(".leadCheckbox:checked");

    if (checked.length === 0) {
        showToast("Select at least one lead first", "error");
        return;
    }

    if (!confirm(`Delete ${checked.length} selected leads?`)) return;

    Promise.all(
        Array.from(checked).map(checkbox =>
            authFetch(`/api/v1/leads/${checkbox.value}/`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ is_deleted: true })
            })
        )
    )
    .then(() => {
        showToast(`${checked.length} leads deleted`, "success");
        loadLeads();
    })
    .catch(() => showToast("Delete failed", "error"));
}


// ===============================
// 💬 WHATSAPP ACTION
// ===============================
function sendWhatsApp(id) {
    authFetch(`/api/v1/leads/${id}/whatsapp_click/`, {
        method: "POST"
    })
    .then(res => {
        if (!res.ok) throw new Error();
        showToast("WhatsApp triggered", "success");
    })
    .catch(() => showToast("Failed", "error"));
}


// ===============================
// 🎯 STATUS BADGE SYSTEM
// ===============================
function formatStatus(status) {
    return status?.replace(/\s+/g, "-").toLowerCase();
}

function applyStatusBadge(element, status) {
    const formatted = formatStatus(status);
    element.className = `status-badge status-${formatted}`;
    element.innerText = status;
}


// ===============================
// 🔍 FILTER EVENTS
// — IDs are now filterSearch, filterStatus, filterSource
// — These must match your HTML filter input IDs
// ===============================
document.getElementById("filterSearch")?.addEventListener("input", debounce(loadLeads, 400));
document.getElementById("filterStatus")?.addEventListener("change", loadLeads);
document.getElementById("filterSource")?.addEventListener("change", loadLeads);


// ===============================
// ⏳ DEBOUNCE
// ===============================
function debounce(func, delay) {
    let timeout;
    return function () {
        clearTimeout(timeout);
        timeout = setTimeout(func, delay);
    };
}


// ===============================
// ➕ SAVE LEAD (manual entry)
// ===============================
function saveLead() {
    const first_name = document.getElementById("first_name").value.trim();
    const last_name = document.getElementById("last_name").value.trim();
    const phone = document.getElementById("phone").value.trim();
    const email = document.getElementById("email").value.trim();
    const leadStatus = document.getElementById("leadStatus").value;   // modal field IDs
    const leadSource = document.getElementById("leadSource").value;   // renamed to avoid filter conflict

    if (!first_name) {
        showToast("First name is required", "error");
        return;
    }

    if (!phone) {
        showToast("Phone is required", "error");
        return;
    }

    showLoader();

    authFetch("/api/v1/leads/", {
        method: "POST",
        body: JSON.stringify({
            first_name,
            last_name,
            phone,
            email,
            status: leadStatus,
            source: leadSource,
        })
    })
    .then(res => {
        if (!res.ok) {
            return res.json().then(err => {
                console.error("Backend error:", err);
                throw new Error("Failed to save");
            });
        }
        return res.json();
    })
    .then(() => {
        showToast("Lead saved!", "success");
        const modalEl = document.getElementById("addLeadModal");
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal?.hide();
        loadLeads();
    })
    .catch(err => {
        console.error(err);
        showToast("Save failed", "error");
    })
    .finally(() => hideLoader());
}


// ===============================
// 📤 EXPORT CSV
// — Uses backend endpoint, not frontend memory
// — Respects business isolation automatically
// ===============================
function exportCSV() {
    const token =
        localStorage.getItem("token") ||
        sessionStorage.getItem("token");

    // Use the backend export endpoint — already business-scoped
    fetch("/api/v1/leads/export_csv/", {
        headers: { "Authorization": "Bearer " + token }
    })
    .then(res => {
        if (!res.ok) throw new Error("Export failed");
        return res.blob();
    })
    .then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "leads.csv";
        a.click();
        URL.revokeObjectURL(url);
    })
    .catch(() => showToast("Export failed", "error"));
}


// ===============================
// 📥 IMPORT CSV
// ===============================
function importCSV() {
    // Trigger file picker correctly
    const fileInput = document.getElementById("importFile");
    if (!fileInput) return;

    fileInput.onchange = function () {
        const file = fileInput.files[0];
        if (!file) {
            showToast("Please select a file", "error");
            return;
        }

        const reader = new FileReader();
        reader.onload = function (e) {
            const text = e.target.result;
            const rows = text.split("\n").filter(r => r.trim());
            const dataRows = rows.slice(1); // skip header

            const leads = dataRows.map(row => {
                const cols = row.split(",");
                const full_name = (cols[0] || "").trim();
                const nameParts = full_name.split(" ");
                return {
                    first_name: nameParts[0] || "",
                    last_name: nameParts.slice(1).join(" ") || "",
                    email: (cols[1] || "").trim(),
                    phone: (cols[2] || "").trim(),
                    source: "meta ads",
                    status: "new"
                };
            }).filter(l => l.first_name); // skip empty rows

            Promise.all(
                leads.map(lead =>
                    authFetch("/api/v1/leads/", {
                        method: "POST",
                        body: JSON.stringify(lead)
                    })
                )
            )
            .then(() => {
                showToast(`${leads.length} leads imported!`, "success");
                loadLeads();
            })
            .catch(() => showToast("Import failed", "error"));
        };

        reader.readAsText(file);
    };

    fileInput.click();
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
// 🚀 INIT
// ===============================
document.addEventListener("DOMContentLoaded", function () {
    console.log("Leads JS Loaded");
    loadLeads();
});