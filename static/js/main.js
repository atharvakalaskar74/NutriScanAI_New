/**
 * NutriScan AI — Global Client-side Utilities
 */

document.addEventListener("DOMContentLoaded", () => {
    // Mobile navigation drawer toggle
    const toggleBtn = document.getElementById("mobile-nav-toggle");
    const navLinks = document.getElementById("nav-links");

    if (toggleBtn && navLinks) {
        toggleBtn.addEventListener("click", () => {
            navLinks.classList.toggle("open");
        });
    }

    // Auto-dismiss flash alerts after 6 seconds
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach((alert) => {
        setTimeout(() => {
            alert.style.transition = "opacity 0.5s ease";
            alert.style.opacity = "0";
            setTimeout(() => alert.remove(), 500);
        }, 6000);
    });
});
