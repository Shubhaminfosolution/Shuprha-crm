// ============================================================
// KANBAN PIPELINE — kanban.js
// ============================================================

// Column definitions — order matters
const COLUMNS = [
    { id: "new",          label: "New",          statuses: ["new"],                          cls: "col-new" },
    { id: "contacted",    label: "Contacted",    statuses: ["not received", "busy", "in progress"], cls: "col-contacted" },
    { id: "qualified",    label: "Qualified",    statuses: ["qualified"],                    cls: "col-qualified" },
    { id: "proposal",     label: "Proposal Sent",statuses: ["proposal"],                    cls: "col-proposal" },
    { id: "converted",    label: "Converted",    statuses: ["converted"],                    cls: "col-converted" },
    { id: "lost",         label: "Lost",         statuses: ["lost"],                         cls: "col-lost" },
];

// Map status → column id
const STATUS_TO_COL = {};
COLUMNS.forEach(col => {
    col.statuses.forEach(s => STATUS_TO_COL[s] = col.id);
});

// Map column id → Django status value to send on drop
const COL_TO_STATUS = {
    "new":       "new",
    "contacted": "in progress",
    "qualified": "qualified",
    "proposal":  "proposal",
    "converted": "converted",
    "lost":      "lost",
};

let allLeads = [];
let draggedLeadId = null;
let draggedCard = null;

// ── INIT ──────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    loadKanban();
});

// ── LOAD ─────────────────────────────────────────────────
function loadKanban() {
    showLoader();

    authFetch("/api/v1/leads/")
        .then(res => {
            if (!res.ok) throw new Error("Failed to load");
            return res.json();
        })
        .then(data => {
            allLeads = data.results || data;
            renderKanban(allLeads);
            updateStats(allLeads);
        })
        .catch(err => {
            console.error(err);
            showToast("Failed to load pipeline", "error");
        })
        .finally(() => hideLoader());
}

// ── RENDER ───────────────────────────────────────────────
function renderKanban(leads) {
    const board = document.getElementById("kanbanBoard");
    board.innerHTML = "";

    COLUMNS.forEach(col => {
        // Filter leads for this column
        const colLeads = leads.filter(l =>
            !l.is_deleted && col.statuses.includes(l.status)
        );

        // Build column
        const colEl = document.createElement("div");
        colEl.className = `kanban-col ${col.cls}`;
        colEl.dataset.colId = col.id;

        colEl.innerHTML = `
            <div class="kanban-col-header">
                <div class="kanban-col-title">
                    <span class="col-dot"></span>
                    ${col.label}
                </div>
                <span class="col-count">${colLeads.length}</span>
            </div>
            <div class="kanban-cards" 
                 id="col-${col.id}"
                 ondragover="onDragOver(event)"
                 ondragleave="onDragLeave(event)"
                 ondrop="onDrop(event, '${col.id}')">
                ${colLeads.length === 0
                    ? `<div class="empty-col">Drop leads here</div>`
                    : colLeads.map(lead => buildCard(lead)).join("")
                }
            </div>
        `;

        board.appendChild(colEl);
    });
}

// ── BUILD CARD ───────────────────────────────────────────
function buildCard(lead) {
    const name = `${lead.first_name || ""} ${lead.last_name || ""}`.trim() || "Unknown";
    const phone = lead.phone || "—";
    const source = (lead.source || "").replace("_", " ");
    const score = lead.score || 0;
    const timeAgo = getTimeAgo(lead.created_at);

    return `
        <div class="lead-card"
             draggable="true"
             data-lead-id="${lead.id}"
             ondragstart="onDragStart(event, ${lead.id})"
             ondragend="onDragEnd(event)"
             onclick="goToLead(${lead.id})"
             title="Click to view ${name}">
            <div class="card-name">${name}</div>
            <div class="card-phone">${phone}</div>
            <div class="card-meta">
                <span class="card-source">${source || "manual"}</span>
                <span class="card-score">⭐ ${score}</span>
                <span class="card-time">${timeAgo}</span>
            </div>
        </div>
    `;
}

// ── TIME AGO ─────────────────────────────────────────────
function getTimeAgo(dateStr) {
    if (!dateStr) return "—";
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    const hours = Math.floor(mins / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (mins > 0) return `${mins}m ago`;
    return "Just now";
}

// ── STATS ────────────────────────────────────────────────
function updateStats(leads) {
    const active = leads.filter(l => !l.is_deleted);
    const converted = active.filter(l => l.status === "converted").length;
    const hot = active.filter(l => l.score >= 7).length;
    const rate = active.length ? Math.round((converted / active.length) * 100) : 0;

    document.getElementById("stat-total").textContent = active.length;
    document.getElementById("stat-hot").textContent = hot;
    document.getElementById("stat-converted").textContent = converted;
    document.getElementById("stat-rate").textContent = `${rate}%`;
}

// ── DRAG & DROP ──────────────────────────────────────────
function onDragStart(event, leadId) {
    draggedLeadId = leadId;
    draggedCard = event.target;
    draggedCard.classList.add("dragging");
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", leadId);
}

function onDragEnd(event) {
    if (draggedCard) draggedCard.classList.remove("dragging");
    draggedCard = null;

    // Remove all drag-over highlights
    document.querySelectorAll(".kanban-cards.drag-over").forEach(el => {
        el.classList.remove("drag-over");
    });
}

function onDragOver(event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
    event.currentTarget.classList.add("drag-over");
}

function onDragLeave(event) {
    event.currentTarget.classList.remove("drag-over");
}

function onDrop(event, colId) {
    event.preventDefault();
    event.currentTarget.classList.remove("drag-over");

    const leadId = draggedLeadId;
    if (!leadId) return;

    const newStatus = COL_TO_STATUS[colId];
    if (!newStatus) return;

    // Find current status
    const lead = allLeads.find(l => l.id == leadId);
    if (!lead) return;

    // Don't update if same column
    const currentColId = STATUS_TO_COL[lead.status];
    if (currentColId === colId) return;

    // Optimistic update — move card immediately
    lead.status = newStatus;
    renderKanban(allLeads);
    updateStats(allLeads);

    // Persist to backend
    updateLeadStatus(leadId, newStatus);
}

// ── API UPDATE ───────────────────────────────────────────
function updateLeadStatus(leadId, newStatus) {
    authFetch(`/api/v1/leads/${leadId}/`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
    })
    .then(res => {
        if (!res.ok) throw new Error("Update failed");
        showToast("Status updated", "success");
    })
    .catch(err => {
        console.error(err);
        showToast("Failed to update status", "error");
        // Reload to revert optimistic update
        loadKanban();
    });
}

// ── NAVIGATION ───────────────────────────────────────────
function goToLead(id) {
    window.location.href = `/api/v1/leads-ui/${id}/`;
}
