const searchInput = document.querySelector("#search");
const categorySelect = document.querySelector("#category");
const cards = Array.from(document.querySelectorAll(".opportunity-card"));
const noResults = document.querySelector("#no-results");

function filterOpportunities() {
    const searchTerm = searchInput.value.trim().toLowerCase();
    const selectedCategory = categorySelect.value.toLowerCase();
    let visibleCount = 0;

    for (const card of cards) {
        const matchesSearch =
            card.dataset.title.includes(searchTerm) ||
            card.dataset.organization.includes(searchTerm);
        const matchesCategory =
            selectedCategory === "all" ||
            card.dataset.category === selectedCategory;
        const isVisible = matchesSearch && matchesCategory;

        card.hidden = !isVisible;
        if (isVisible) {
            visibleCount += 1;
        }
    }

    noResults.hidden = visibleCount > 0;
}

if (searchInput && categorySelect && noResults) {
    searchInput.addEventListener("input", filterOpportunities);
    categorySelect.addEventListener("change", filterOpportunities);
}

const statusFilter = document.querySelector("#status-filter");

if (statusFilter) {
    const dashboardCards = document.querySelectorAll(".dashboard-card");

    function filterDashboard() {
        const selectedStatus = statusFilter.value;

        dashboardCards.forEach((card) => {
            const cardStatus = card.dataset.status.trim();
            card.hidden =
                selectedStatus !== "all" &&
                cardStatus !== selectedStatus;
        });
    }

    statusFilter.addEventListener("change", filterDashboard);
    filterDashboard();
}

const sortOrder = document.querySelector("#sort-order");

if (sortOrder) {
    const container = document.querySelector(".dashboard-cards");

    if (container) {
        sortOrder.addEventListener("change", () => {
            const dashboardCards = Array.from(
                container.querySelectorAll(".dashboard-card")
            );

            dashboardCards.sort((a, b) => {
                if (sortOrder.value === "saved") {
                    return b.dataset.saved.localeCompare(a.dataset.saved);
                }

                return a.dataset.deadline.localeCompare(b.dataset.deadline);
            });

            dashboardCards.forEach((card) => container.appendChild(card));
        });
    }
}

const dashboardCardsForSummary =
    document.querySelectorAll(".dashboard-card");

const totalSaved = document.querySelector("#total-saved");
const totalPreparing = document.querySelector("#total-preparing");
const totalApplied = document.querySelector("#total-applied");
const totalAccepted = document.querySelector("#total-accepted");

if (totalSaved) {
    totalSaved.textContent = dashboardCardsForSummary.length;

    totalPreparing.textContent = document.querySelectorAll(
        '.dashboard-card[data-status="Preparing"]'
    ).length;

    totalApplied.textContent = document.querySelectorAll(
        '.dashboard-card[data-status="Applied"]'
    ).length;

    totalAccepted.textContent = document.querySelectorAll(
        '.dashboard-card[data-status="Accepted"]'
    ).length;
}
