document.addEventListener("DOMContentLoaded", function () {
    loadAppointments();
    initCalendar();
    // ✅ FIX: Removed saveAppointment() from here — it's called by the button onclick
});


// 📅 LIST VIEW
function loadAppointments() {
    showLoader();

    authFetch("/api/v1/appointments/")
        .then(res => {
            if (!res.ok) throw new Error("Failed to fetch");
            return res.json();
        })
        .then(data => renderAppointments(data))
        .catch(err => {
            console.error(err);
            showToast("Failed to load appointments", "error");
        })
        .finally(() => hideLoader());
}


function formatTime(dateTime) {
    if (!dateTime) return "";
    const date = new Date(dateTime);
    return date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    });
}


function renderAppointments(appointments) {
    const container = document.getElementById("appointmentsList");
    if (!container) return;

    container.innerHTML = "";

    if (!appointments.length) {
        container.innerHTML = "<p>No appointments found</p>";
        return;
    }

    const today = new Date().toISOString().split("T")[0];

    appointments.forEach(app => {
        const date = app.start ? app.start.split("T")[0] : "";
        const time = app.start ? formatTime(app.start) : "";
        const isToday = date === today;

        const div = document.createElement("div");
        div.className = "appointment-item" + (isToday ? " today" : "");

        div.innerHTML = `
            <div class="appointment-card">
                <div class="appointment-time">${time}</div>
                <div class="appointment-name">${app.title}</div>
                <div class="appointment-status ${app.extendedProps?.status || ""}">
                    ${app.extendedProps?.status || ""}
                </div>
            </div>
        `;

        container.appendChild(div);
    });
}


// 🌍 GLOBAL CALENDAR INSTANCE
let calendarInstance = null;

// 📊 CALENDAR
function initCalendar() {
    const calendarEl = document.getElementById("calendar");
    if (!calendarEl) return;

    // ✅ FIX: Use calendarInstance (not local const) so saveAppointment() can access it
    calendarInstance = new FullCalendar.Calendar(calendarEl, {

        initialView: "dayGridMonth",
        height: "auto",
        selectable: true,
        editable: true,

        eventTimeFormat: {
            hour: 'numeric',
            minute: '2-digit',
            meridiem: 'short'
        },

        headerToolbar: {
            left: "prev,next today",
            center: "title",
            right: "dayGridMonth,timeGridWeek,timeGridDay"
        },

        events: function (fetchInfo, successCallback, failureCallback) {
            showLoader();

            authFetch("/api/v1/appointments/")
                .then(res => {
                    if (!res.ok) throw new Error("Calendar fetch failed");
                    return res.json();
                })
                .then(data => {
                    const appointments = data.results || data;

                    const events = appointments.map(app => {
                        let color = "#4e73df";
                        if (app.status === "completed") color = "#1cc88a";
                        if (app.status === "cancelled") color = "#e74a3b";
                        if (app.status === "postponed") color = "#f6c23e";

                        return {
                            id: app.id,
                            title: app.title,
                            start: new Date(app.start),
                            backgroundColor: color,
                            textColor: "#fff",
                            extendedProps: {
                                status: app.status,
                                notes: app.notes
                            }
                        };
                    });

                    successCallback(events);
                })
                .catch(err => {
                    console.error("Calendar fetch error:", err);
                    failureCallback(err);
                })
                .finally(() => hideLoader());
        },

        // ➕ CREATE on date click
        dateClick: function (info) {
            openModal({ start: info.dateStr });
        },

        // 🖱 DRAG to update
        eventDrop: function (info) {
            showLoader();

            authFetch(`/api/v1/appointments/${info.event.id}/`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ date_time: info.event.startStr })
            })
            .then(res => {
                if (!res.ok) throw new Error();
                showToast("Appointment updated", "success");
                loadAppointments();
            })
            .catch(() => showToast("Update failed", "error"))
            .finally(() => hideLoader());
        },

        // ✏️ CLICK to edit
        eventClick: function (info) {
            openModal({
                id: info.event.id,
                start: info.event.startStr,
                notes: info.event.extendedProps.notes,
                status: info.event.extendedProps.status
            });
        }
    });

    calendarInstance.render();
}


// 📌 MODAL
function openModal(data = null) {
    document.getElementById("appointmentId").value = data?.id || "";
    document.getElementById("leadId").value = data?.lead || "";
    document.getElementById("notes").value = data?.notes || "";
    document.getElementById("status").value = data?.status || "scheduled";

    if (data?.start) {
        document.getElementById("dateTime").value = data.start.slice(0, 16);
    }

    const modal = new bootstrap.Modal(document.getElementById("appointmentModal"));
    modal.show();
}


// 💾 SAVE APPOINTMENT — called by button onclick only
function saveAppointment() {
    const appointmentId = document.getElementById("appointmentId").value;
    const leadId = document.getElementById("leadId").value;
    const status = document.getElementById("status").value;
    const notes = document.getElementById("notes").value;
    const rawDate = document.getElementById("dateTime").value;

    if (!leadId) {
        showToast("Lead ID is required", "error");
        return;
    }

    if (!rawDate) {
        showToast("Date & Time is required", "error");
        return;
    }

    const isoDate = new Date(rawDate).toISOString();

    // ✅ FIX: Determine if creating or updating
    const isEdit = appointmentId !== "";
    const url = isEdit
        ? `/api/v1/appointments/${appointmentId}/`
        : `/api/v1/appointments/`;
    const method = isEdit ? "PATCH" : "POST";

    authFetch(url, {                                           // this is a kind of HTTP request that we send to the backend means the djnago through urls
        method: method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            lead: parseInt(leadId),
            date_time: isoDate,       // ✅ matches Django model field name
            status: status.toLowerCase(),
            notes: notes
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
        showToast("Appointment saved!", "success");

        const modalEl = document.getElementById("appointmentModal");
        const modal = bootstrap.Modal.getInstance(modalEl);
        modal.hide();

        // ✅ FIX: Use calendarInstance, not undefined `calendar`
        if (calendarInstance) calendarInstance.refetchEvents();

        loadAppointments();
    })
    .catch(err => {
        console.error(err);
        showToast("Save failed", "error");
    });
}


// 🔄 LOADER
function showLoader() {
    document.getElementById("globalLoader")?.classList.remove("d-none");
}

function hideLoader() {
    document.getElementById("globalLoader")?.classList.add("d-none");
}


// 🔔 TOAST
function showToast(message, type = "success") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast-msg toast-${type}`;
    toast.innerText = message;
    container.appendChild(toast);

    setTimeout(() => toast.remove(), 3000);
}