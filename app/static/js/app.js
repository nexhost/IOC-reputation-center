const savedTheme = localStorage.getItem("ioc-theme");
if (savedTheme) {
    document.documentElement.setAttribute("data-theme", savedTheme);
}

const themeToggle = document.getElementById("themeToggle");
function paintIcons() {
    if (window.lucide) {
        window.lucide.createIcons({ attrs: { "stroke-width": 1.8 } });
    }
}

function setThemeIcon(theme) {
    if (!themeToggle) return;
    themeToggle.innerHTML = `<i data-lucide="${theme === "light" ? "sun" : "moon"}"></i>`;
    paintIcons();
}

setThemeIcon(savedTheme || "dark");

if (themeToggle) {
    themeToggle.addEventListener("click", () => {
        const current = document.documentElement.getAttribute("data-theme") || "dark";
        const next = current === "light" ? "dark" : "light";
        document.documentElement.setAttribute("data-theme", next);
        localStorage.setItem("ioc-theme", next);
        setThemeIcon(next);
    });
}

paintIcons();

function updateSantoDomingoClock() {
    const clock = document.querySelector("[data-sd-clock]");
    if (!clock) return;
    const now = new Date();
    clock.textContent = new Intl.DateTimeFormat("es-DO", {
        timeZone: "America/Santo_Domingo",
        hour: "numeric",
        minute: "2-digit",
        second: "2-digit",
        hour12: true,
        day: "2-digit",
        month: "2-digit",
        year: "numeric"
    }).format(now);
}

updateSantoDomingoClock();
setInterval(updateSantoDomingoClock, 1000);
