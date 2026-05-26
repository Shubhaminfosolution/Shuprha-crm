// ===============================
// 🔐 AUTH FETCH (ROBUST)
// ===============================
function formatStatus(status) {
    return status?.replace(/\s+/g, "-").toLowerCase();
}

function applyStatusBadge(element, status) {

    const formatted = formatStatus(status);

    element.className = `status-badge status-${formatted}`;
    element.innerText = status;
}



function authFetch(url, options = {}) {
    const token =
        localStorage.getItem("token") ||
        sessionStorage.getItem("token");

    if (!token) {
        console.warn("No token found → redirecting");
        window.location.href = "/api/v1/login/";
        return Promise.reject("No token");
    }

    return fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
            ...(options.headers || {})
        }
    }).then(res => {

        if (res.status === 401) {
            console.warn("Token expired → logging out");
            localStorage.removeItem("token");
            sessionStorage.removeItem("token");
            window.location.href = "/api/v1/login/";
            logoutUser();
            return Promise.reject("Unauthorized");
        }
        if (!res.ok){
            return Promise.reject("API Error: "+ res.status);
        }

        return res;
    });
}




// ===============================
// 🚪 LOGOUT HANDLER
// ===============================

// ===============================
// 🕐 LOAD TIMELINE
// ===============================


// ===============================
// 🚀 INIT
// ===============================
document.addEventListener("DOMContentLoaded", () => {

    const leadId = getLeadId();

    if (!leadId) {
        console.error("Invalid Lead ID");
        return;
    }
    document.getElementById("saveBtn").addEventListener("click", saveAppointment);
    attachStatusListener(); 
    loadLead(leadId);
    loadTimeline();
    document.getElementById("addActivityBtn")
        ?.addEventListener("click", toggleActivityForm);
    document.getElementById("saveActivityBtn")
        ?.addEventListener("click", saveActivity);
    document.getElementById("cancelActivityBtn")
        ?.addEventListener("click", toggleActivityForm);
});



// ===============================
// 🔍 GET LEAD ID
// ===============================
function getLeadId() {
    const parts = window.location.pathname.split("/").filter(Boolean);
    return parts[parts.length - 1];
}


// ===============================
// 📊 LOAD LEAD
// ===============================
function loadLead(id) {

    setText("leadName", "Loading...");

    authFetch(`/api/v1/leads/${id}/`)
        .then(res => {
            if (!res.ok) throw new Error("Fetch failed");
            return res.json();
        })
        .then(lead => {

            console.log("Lead Data:", lead);

            // BASIC INFO
            setText("leadName", lead.first_name);
            setText("leadEmail", lead.email);
            setText("leadPhone", lead.phone);

            // STATUS
            const statusEl = document.getElementById("leadStatus");
            if (statusEl) statusEl.value = lead.status;

            applyStatusBadge(
                document.getElementById("leadStatusBadge"),
                lead.status
            );

            // ACTIVITIES
            renderActivities(lead.activities || []);

            renderAppointments(lead.appointments || []);

        })
        .catch(err => {
            console.error("LOAD ERROR:", err);
            setText("leadName", "Error loading data");
            document.getElementById("leadName").innerText="Error ;pading data";
        });
}


// ===============================
// 🧼 SAFE TEXT SETTER
// ===============================
function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.innerText = value || "-";
}


// ===============================
// 🎯 STATUS LISTENER
// ===============================
function attachStatusListener() {

    const statusEl = document.getElementById("leadStatus");

    if (!statusEl) return;

    statusEl.addEventListener("change", function () {

        const id = getLeadId();
        const newStatus = this.value;

        authFetch(`/api/v1/leads/${id}/`, {
            method: "PATCH",
            body: JSON.stringify({
                status: newStatus
            })
        })
        .then(res => {
            if (!res.ok) throw new Error("Update failed");

            applyStatusBadge(
                document.getElementById("leadStatusBadge"),
                newStatus
            );

            showToast("Status updated", "success");
        })
        .catch(err => {
            console.error("UPDATE ERROR:", err);
            showToast("Update failed", "error");
        });
    });
}


function renderAppointments(appointments){
    const container = 
    document.getElementById("appointmentsList");

    if(!container) return ;
    container.innerHTML = "";
    
    if (!appointments || appointments.length === 0){
        container.innerHTML = "<p> No appointment yet </p>";
        return;
    }

    appointments.forEach(app =>{

        const div = document.createElement("div");
        div.className = "appointment-item";

        div.innerHTML = `
        <strong>${app.status || "Scheduled"} </strong><br>
        <small>${app.notes || ""}</small><br>
        <span class="text-muted">
        ${app.date_time ? new Date(app.date_time).toLocaleString(): ""} </span>
        <button class="btn btn-ghost btn-sm" onclick='openAppointmentModal(${JSON.stringify(app)})'>Edit</button>
        <button class="btn btn-danger btn-sm" onclick='deleteAppointment(${app.id})'>Delete</button>`
        container.appendChild(div)
    })
}





// ===============================
// 📜 ACTIVITY TIMELINE
// ===============================
function renderActivities(activities) {

    const container = document.getElementById("activityTimeline");
    if (!container) return;

    container.innerHTML = "";

    if (!activities || activities.length === 0) {
        container.innerHTML = "<p>No activity</p>";
        return;
    }

    activities.forEach(act => {

        const div = document.createElement("div");
        div.className = "timeline-item";

        div.innerHTML = `
            <div class="timeline-dot"></div>
            <div class="timeline-content">
                <strong>${act.activity_type || "Activity"}</strong><br>
                <small>${act.notes || ""}</small><br>
                <span class="text-muted">
                    ${act.created_at ? new Date(act.created_at).toLocaleString() : ""}
                </span>
            </div>
        `;

        container.appendChild(div);
    });
}




let editingAppointmentId = null;

function openAppointmentModal(app = null){
    document.getElementById("appointmentModal").style.display = "block";

    if(app){
        editingAppointmentId = app.id;

        document.getElementById("appointmentDate").value = app.date_time.slice(0, 16);
        document.getElementById("appointmentNotes").value = app.notes || "";
        document.getElementById("appointmentStatus").value = app.status;

    }else{
        editingAppointmentId = null;
    }
}


function formatDate(dateStr){
    const d = new Date(dateStr);
    return d.toISOString();
}



function saveAppointment(){
    const rawDate = document.getElementById("appointmentDate").value;
    const date = formatDate(rawDate)
    const notes = document.getElementById("appointmentNotes").value;
    const status = document.getElementById("appointmentStatus").value;

    if (!date) {
        alert("Date is reqiuired");
        return;
    }

    const leadId = window.location.pathname.split("/").filter(Boolean).pop();

    const payload = {
        date_time :date,
        notes : notes,
        status : status,
        lead : parseInt(leadId),
    };

    const method = editingAppointmentId ? "PATCH" :"POST";
    const url = editingAppointmentId
    ? `/api/v1/appointments/${editingAppointmentId}/`
    : `/api/v1/appointments/`;


    console.log("Sending payload: ", payload);

    authFetch(url, {
        method: method, 
        body: JSON.stringify(payload)
    })
    .then(res =>{
        if(!res.ok){
            return res.json().then(err=>{
                console.error("Backend error: ", err, null, 2);
                throw err;
            });

        }
        return res.json();
    })
    .then(()=> {
        closeModal();
        loadLead();
    })
    .catch(err => console.error(err));
}




function deleteAppointment(id){
    if (!confirm("Delete this appointment?")) return;

    authFetch(`/api/v1/appointments/${id}/`, {
        method: "DELETE"
    })
    .then(() =>{
        const leadId = getLeadId();
        loadLead(leadId);
    })
    .catch(err => console.error(err));
}





function loadTimeline() {
    const leadId = getLeadId();

    authFetch(`/api/v1/leads/${leadId}/timeline/`)
        .then(r => r.json())
        .then(activities => {
            const container = document.getElementById("activityTimeline");

            if (!activities || activities.length === 0) {
                container.innerHTML = `<div style="color:var(--text-3); font-size:13px; padding:12px 0 12px 24px;">No activity yet.</div>`;
                return;
            }

            const iconMap = {
                call:     "📞",
                email:    "📧",
                whatsapp: "💬",
                meeting:  "🤝",
                note:     "📝",
                followup: "🔄",
            };

            container.innerHTML = activities.map(act => {
                const icon = iconMap[act.activity_type] || "📌";
                const date = act.scheduled_at
                    ? new Date(act.scheduled_at).toLocaleDateString("en-IN", {
                        day: "numeric", month: "short",
                        hour: "2-digit", minute: "2-digit"
                      })
                    : new Date(act.created_at).toLocaleDateString("en-IN", {
                        day: "numeric", month: "short",
                        hour: "2-digit", minute: "2-digit"
                      });

                return `
                <div style="display:flex; gap:12px; margin-bottom:16px; align-items:flex-start;">
                    <div style="width:32px; height:32px; border-radius:50%; background:var(--bg-2,#f3f4f6);
                        display:flex; align-items:center; justify-content:center; font-size:15px; flex-shrink:0;">
                        ${icon}
                    </div>
                    <div style="flex:1;">
                        <div style="font-size:13px; font-weight:500; color:var(--text-1,#111); text-transform:capitalize;">
                            ${act.activity_type.replace("_", " ")}
                            ${act.completed ? '<span style="color:#10b981; font-size:11px; margin-left:6px;">✓ Done</span>' : ""}
                        </div>
                        <div style="font-size:12px; color:var(--text-3,#9ca3af); margin-top:2px;">${date}</div>
                        ${act.notes ? `<div style="font-size:13px; color:var(--text-2,#6b7280); margin-top:4px;">${act.notes}</div>` : ""}
                        ${act.performed_by_name || act.performed_by ? `<div style="font-size:11px; color:var(--text-3,#9ca3af); margin-top:4px;">by ${act.performed_by_name || act.performed_by}</div>` : ""}
                    </div>
                </div>`;
            }).join("");
        })
        .catch(() => {
            document.getElementById("activityTimeline").innerHTML =
                `<div style="color:var(--text-3); font-size:13px; padding:12px 0 12px 24px;">Failed to load activities.</div>`;
        });
}


// ===============================
// ➕ TOGGLE ACTIVITY FORM
// ===============================
function toggleActivityForm() {
    const form = document.getElementById("activityForm");
    if (form.style.display === "none" || form.style.display === "") {
        form.style.display = "block";
    } else {
        form.style.display = "none";
    }
}



// ===============================
// 💾 SAVE ACTIVITY
// ===============================
function saveActivity() {
    const leadId = getLeadId();
    const activity_type = document.getElementById("activityType").value;
    const notes = document.getElementById("activityNotes").value.trim();
    const scheduled_at = document.getElementById("activityScheduled").value;

    if (!notes) { showToast("Notes are required", "error"); return; }

    authFetch(`/api/v1/leads/${leadId}/add_activity/`, {
        method: "POST",
        body: JSON.stringify({
            activity_type,
            notes,
            scheduled_at: scheduled_at
                ? new Date(scheduled_at).toISOString()
                : null,
            completed: false
        })
    })
    .then(r => {
        if (!r.ok) return r.json().then(e => { throw e; });
        return r.json();
    })
    .then(() => {
        showToast("Activity added!", "success");
        document.getElementById("activityNotes").value = "";
        document.getElementById("activityScheduled").value = "";
        toggleActivityForm();
        loadTimeline(); // reload timeline after save
    })
    .catch(err => {
        console.error(err);
        showToast("Failed to save activity", "error");
    });
}
// ===============================
// 🔔 TOAST (SAFE FALLBACK)
// ===============================
function showToast(message, type = "info") {
    console.log(`[${type}]`, message);
}




function closeModal(){
    document.getElementById("appointmentModal").style.display = "none";
}