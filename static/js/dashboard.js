// 🔌 AUTH FETCH (FIXED)
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
    });
}


// 📊 CHART INSTANCES
let leadsChartInstance = null;
let sourceChartInstance = null;


// 🚀 LOAD DASHBOARD
function loadDashboard(days = 7) {

    authFetch(`/api/v1/dashboard/?days=${days}`)
        .then(res => {

            if (res.status === 401) {
                localStorage.removeItem("token");
                sessionStorage.removeItem("token");

                window.location.href = "api/v1/login/";
                return;
            }

            if (!res.ok) throw new Error("Failed to load dashboard");

            return res.json();
        })
        .then(data => {

            if (!data) return;

            console.log("DASHBOARD DATA:", data);

            // ✅ KPI
            document.getElementById("total_leads").innerText = data.total_leads || 0;
            document.getElementById("today_leads").innerText = data.today_leads || 0;
            document.getElementById("total_appointments").innerText = data.total_appointments || 0;
            document.getElementById("completed").innerText = data.completed || 0;

            // ✅ Destroy old charts
            if (leadsChartInstance) leadsChartInstance.destroy();
            if (sourceChartInstance) sourceChartInstance.destroy();

            // =========================
            // 📈 LEADS TREND
            // =========================
            const leadsTrend = data.leads_trend || data.monthly_data || [];

            const labels = leadsTrend.map(x =>
                x.created_at__date || x.month || "N/A"
            );

            const values = leadsTrend.map(x => x.count || 0);

            const leadsCanvas = document.getElementById("leadsChart");

            if (leadsCanvas && labels.length > 0) {

                const ctx = leadsCanvas.getContext("2d");

                const gradient = ctx.createLinearGradient(0, 0, 0, 400);
                gradient.addColorStop(0, "rgba(78,115,223,0.4)");
                gradient.addColorStop(1, "rgba(78,115,223,0)");

                leadsChartInstance = new Chart(ctx, {
                    type: "line",
                    data: {
                        labels: labels,
                        datasets: [{
                            label: "Leads",
                            data: values,
                            borderColor: "#4e73df",
                            backgroundColor: gradient,
                            fill: true,
                            tension: 0.4,
                            pointRadius: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        aspectRatio: 3,
                        animation: {
                            duration: 1200
                        },
                        plugins: {
                            legend: { display: false }
                        },
                        scales: {
                            y: { beginAtZero: true }
                        }
                    }
                });
            }

            // =========================
            // 🥧 SOURCE CHART
            // =========================
            const sourceData = data.source_data || data.source || [];

            const sourceLabels = sourceData.map(x => x.source || "Unknown");
            const sourceValues = sourceData.map(x => x.count || 0);

            const sourceCanvas = document.getElementById("sourceChart");

            if (sourceCanvas && sourceLabels.length > 0) {

                sourceChartInstance = new Chart(sourceCanvas, {
                    type: "doughnut",
                    data: {
                        labels: sourceLabels,
                        datasets: [{
                            data: sourceValues,
                            backgroundColor: [
                                "#4e73df",
                                "#1cc88a",
                                "#36b9cc",
                                "#f6c23e",
                                "#e74a3b"
                            ]
                        }]
                    },
                    options: {
                        cutout: "65%",
                        plugins: {
                            legend: {
                                position: "bottom"
                            }
                        }
                    }
                });
            }

            // =========================
            // 📊 FUNNEL
            // =========================
            if (data.funnel) {

                document.getElementById("f_leads").innerText = data.funnel.leads || 0;
                document.getElementById("f_appointments").innerText = data.funnel.appointments || 0;
                document.getElementById("f_completed").innerText = data.funnel.completed || 0;

                document.getElementById("conversion_rate").innerText = data.conversion_rate?.toFixed(1) + "%" || "0%";
                document.getElementById("appointment_rate").innerText = data.appointment_rate?.toFixed(1) + "%" || "0%";

                
            }

            document.getElementById("best_source").innerText = data.best_source || "-";
            document.getElementById("stale_leads").innerText = data.stale_leads || 0;
            console.log("Todays appointment details:", data.today_appointments)
            renderTodayAppointments(data.today_appointments || []);
            
            renderTodayFollowups(data.today_followups || []);

        })
        .catch(err => {
            console.error("Dashboard Error:", err);
        });
}




function saveTask() {
    const title = document.getElementById("taskTitle").value.trim();
    const priority = document.getElementById("taskPriority").value;
    const assigned_to = document.getElementById("taskAssignee").value;
    const due_date = document.getElementById("taskDueDate").value;

    if (!title) { showToast("Title is required", "error"); return; }
    if (!due_date) { showToast("Due date is required", "error"); return; }

    // assigned_to must resolve — use select value, fallback to currentUserId
    const assigneeId = assigned_to || currentUserId;
    if (!assigneeId) {
        showToast("Please select an assignee", "error");
        return;
    }

    authFetch("/api/v1/tasks/", {
        method: "POST",
        body: JSON.stringify({
            title,
            priority,
            assigned_to: parseInt(assigneeId),
            due_date: new Date(due_date).toISOString()
        })
    })











function renderTodayAppointments(appointments) {
    const container = document.getElementById("todayAppointments");
    const countEl = document.getElementById("apt-count");
    
    if (!container) return;
    
    countEl.innerText = appointments.length;

    if (appointments.length === 0) {
        container.innerHTML = `
            <div style="color:var(--text-3); font-size:13px;">
                No appointments today
            </div>`;
        return;
    }

    container.innerHTML = appointments.map(apt => {
        const name = `${apt.lead__first_name || ""} ${apt.lead__last_name || ""}`.trim();
        const time = apt.date_time ? new Date(apt.date_time).toLocaleTimeString([], {
            hour: '2-digit', minute: '2-digit', hour12: true
        }) : "—";

        return `
            <div class="appointment-item" 
                 onclick="window.location.href='/api/v1/leads-ui/${apt.lead__id}/'"
                 style="cursor:pointer;">
                <div class="apt-dot"></div>
                <div style="flex:1;">
                    <div class="apt-name">${name}</div>
                    <div class="apt-time">${time}</div>
                </div>
                <span class="badge badge-scheduled">Scheduled</span>
            </div>
        `;
    }).join("");
}


function renderTodayFollowups(followups) {
    const container = document.getElementById("todayFollowups");
    const countEl = document.getElementById("followup-count");

    if (!container) return;

    countEl.innerText = followups.length;

    if (followups.length === 0) {
        container.innerHTML = `
            <div style="color:var(--text-3); font-size:13px;">
                No follow-ups today
            </div>`;
        return;
    }

    container.innerHTML = followups.map(f => {
        const name = `${f.lead__first_name || ""} ${f.lead__last_name || ""}`.trim();
        const time = f.scheduled_at ? new Date(f.scheduled_at).toLocaleTimeString([], {
            hour: '2-digit', minute: '2-digit', hour12: true
        }) : "—";
        const type = f.activity_type || "followup";

        return `
            <div class="appointment-item"
                 onclick="window.location.href='/api/v1/leads-ui/${f.lead__id}/'"
                 style="cursor:pointer;">
                <div class="apt-dot" style="background:var(--purple)"></div>
                <div style="flex:1;">
                    <div class="apt-name">${name}</div>
                    <div class="apt-time">${type} · ${time}</div>
                </div>
            </div>
        `;
    }).join("");
}





// 🔄 FILTER
document.getElementById("filter")?.addEventListener("change", function () {
    loadDashboard(this.value);
});


// 🚀 INITIAL LOAD
loadDashboard();