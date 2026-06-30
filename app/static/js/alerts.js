const alertsCanvas = document.getElementById("alertsChart");
if (alertsCanvas && window.Chart) {
    const data = window.IocAlerts || {};
    new Chart(alertsCanvas, {
        type: "bar",
        data: {
            labels: Object.keys(data),
            datasets: [{
                data: Object.values(data),
                backgroundColor: ["#38bdf8", "#eab308", "#f97316", "#ef4444"],
                borderRadius: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false }, ticks: { color: "#cbd5e1" } },
                y: { beginAtZero: true, ticks: { precision: 0, color: "#cbd5e1" }, grid: { color: "rgba(148, 163, 184, .16)" } }
            }
        }
    });
}
