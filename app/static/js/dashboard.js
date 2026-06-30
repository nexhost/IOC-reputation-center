const gridColor = "rgba(148, 163, 184, 0.18)";
const textColor = "#cbd5e1";

function buildSeverityChart() {
    const canvas = document.getElementById("severityChart");
    if (!canvas || !window.Chart) return;
    const data = window.IocDashboard?.severity || {};
    const values = Object.values(data).map((value) => Number(value) || 0);
    new Chart(canvas, {
        type: "doughnut",
        data: {
            labels: Object.keys(data),
            datasets: [{
                data: values.some((value) => value > 0) ? values : [1],
                backgroundColor: ["#ef4444", "#f97316", "#facc15", "#86efac", "#5eead4"],
                borderColor: "#102131",
                borderWidth: 2,
                cutout: "58%"
            }]
        },
        options: {
            maintainAspectRatio: false,
            plugins: { legend: { display: false } }
        }
    });
}

function buildTypeChart() {
    const canvas = document.getElementById("typeChart");
    if (!canvas || !window.Chart) return;
    const data = window.IocDashboard?.types || {};
    const labels = Object.keys(data);
    const values = Object.values(data).map((value) => Number(value) || 0);
    new Chart(canvas, {
        type: "bar",
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: ["#2563eb", "#22c55e", "#eab308", "#f97316", "#8b5cf6"],
                borderRadius: 2,
                barPercentage: 0.58,
                categoryPercentage: 0.72
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { ticks: { color: textColor, font: { size: 11 }, maxRotation: 0 }, grid: { display: false } },
                y: { ticks: { color: textColor, precision: 0 }, grid: { color: gridColor }, beginAtZero: true }
            }
        }
    });
}

buildSeverityChart();
buildTypeChart();
