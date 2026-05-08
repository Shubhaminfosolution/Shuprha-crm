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

    const search = document.getElementById("search")?.value || "";
    const status = document.getElementById("status")?.value || "";
    const source = document.getElementById("source")?.value || "";

    const url = `/api/v1/leads/?search=${search}&status=${status}&source=${source}`;

    console.log("Fetching:", url);

    authFetch(url)
        .then(res => res.json())
        .then(data => {

            console.log("API RESPONSE:", data);

            // 🔥 HANDLE PAGINATION
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

    // 🧼 CLEAR
    table.innerHTML = "";

    // ❌ EMPTY STATE
    if (!leads || leads.length === 0) {
        table.innerHTML = "<tr><td colspan='6'>No leads found</td></tr>";
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
                <button class="???" 
                    onclick="deleteLead(${lead.id})">Delete</button>
            </td>
        </tr>
    `;
});

// ❌ Remove the second forEach completely
    table.innerHTML = html;

    // 🎨 APPLY STATUS BADGES
    leads.forEach(lead => {
        const el = document.getElementById(`status-${lead.id}`);
        if (el && lead.status) {
            applyStatusBadge(el, lead.status);
        }
    });
}



function deleteLead(id){
    if (!confirm("Delete this Lead?")) return;

    authFetch(`/api/v1/leads/${id}/`, {
        method: "PATCH",
        body:json.stringify({is_deleted:true})
    })
    .then(() =>{
        const leadId = getLeadId();
        loadLeads();
    })
    .catch(err => console.error(err));
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
// ===============================
document.getElementById("search")?.addEventListener("input", debounce(loadLeads, 400));
document.getElementById("status")?.addEventListener("change", loadLeads);
document.getElementById("source")?.addEventListener("change", loadLeads);


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
// 🚀 INIT
// ===============================
document.addEventListener("DOMContentLoaded", function () {
    console.log("Leads JS Loaded");
    loadLeads();
});




function exportCSV(){

    const headers = ["first_name", "last_name", "email", "phone", "status", "source"]

    const rows = allLeads.map(lead => [
        lead.first_name,
        lead.last_name,
        lead.email,
        lead.phone,
        lead.status,
        lead.source
    ])

    
    const csv = [
        headers.join(","),
        ...rows
    ].join("\n");
    const blob = new Blob([csv], {type: "text/csv"})  // treat csv string, as a file
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "leads.csv";
    a.click();

    URL.revokeObjectURL(url);  

    const worksheet = XLSX.utils.json_to_sheet(allLeads);  
    const workbook = XLSX.utils.book_new();

    XLSX.utils.book_append_sheet(workbook, worksheet, "Dates");  
    XLSX.writeFile(workbook, "export.xlsx");  
}






function saveLead() {



    const first_name = document.getElementById("first_name").value;
    const last_name = document.getElementById("last_name").value;
    const leadStatus = document.getElementById("status").value;
    const leadSource = document.getElementById("source").value;
    const phone = document.getElementById("phone").value;
    const email = document.getElementById("email").value;

    if (!first_name) {
        showToast("first name is required", "error");
        return;
    }

    if (!email) {
        showToast("Email is required", "error");
        return;
    }
    
    showLoader();
    
    const url = `/api/v1/leads/`;
    const method = "POST";

    authFetch(url, {                                           // this is a kind of HTTP request that we send to the backend means the djnago through urls
        method: method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            first_name: first_name,
            last_name: last_name,
            phone: phone,
            email: email,
            status: leadStatus,
            source: leadSource
            
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
        modal.hide();
        loadLeads();
    })
    .catch(err => {
        console.error(err);
        showToast("Save failed", "error");
    })
    .finally(() => hideLoader());

}


function showLoader() {
    document.getElementById("globalLoader")?.classList.remove("d-none");
}


function hideLoader() {
    document.getElementById("globalLoader")?.classList.add("d-none");
}






function importCSV() {
    const fileInput = document.getElementById("importFile").click();
    const file = fileInput.files[0];

    if (!file) {
        showToast("Please select a file", "error");
        return;
    }

    const reader = new FileReader();

    reader.onload = function(e) {
        const text = e.target.result;
        const rows = text.split("\n");
        const dataRows = rows.slice(1);  // skip header

        const leads = dataRows.map(row => {
            const cols = row.split(",");
            const full_name = cols[0];
            const nameParts = full_name.split(" ");  // split name

            return {
                first_name: nameParts[0],
                last_name: nameParts[1],
                email: cols[1],
                phone: cols[2],
                source: "meta ads",  // ✅ hardcoded since it's Meta CSV
                status: "new"        // ✅ default status
            };
        });

        // Now POST each lead
        Promise.all(leads.map(lead =>
            authFetch("/api/v1/leads/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(lead)
            })
        ))
        .then(() => {
            showToast(`${leads.length} leads imported!`, "success");
            loadLeads();
        })
        .catch(() => showToast("Import failed", "error"));
    };

    reader.readAsText(file);
}





function bulkDelete() {
    // 1. Get all checked checkboxes
    const checked = document.querySelectorAll(".leadCheckbox:checked");
    
    // 2. What if none are checked?
    if (checked.length === 0) {
        showToast("Select the lead first", "error");
        return;
    }

    // 3. Confirm with user
    if (!confirm("I confirm to delete")) return;

    // 4. Get IDs and soft delete each
    // how do you loop through `checked` and get each value?
    Promise.all(
        Array.from(checked).map(checkbox =>
            authFetch(`/api/v1/leads/${checkbox.value}/`, {  // ← how to get ID from checkbox?
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ is_deleted: true })
            })
        )
    )
    .then(() => {
        showToast(`${checked.length} leads deleted`, "success");  // ← how many were deleted?
        loadLeads();
    })
    .catch(() => showToast("Delete failed", "error"));
}