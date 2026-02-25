function toggleSection(element) {
    const content = element.nextElementSibling;
    const expanded = content.classList.toggle("expanded");
    element.classList.toggle("expanded", expanded);
}

function setupNavbarMorph() {
    const nav = document.getElementById("floatingNav");
    const sentinel = document.getElementById("navSentinel");
    if (!nav || !sentinel) return;

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                nav.classList.toggle("scrolled", !entry.isIntersecting);
            });
        },
        { threshold: 0.05 }
    );

    observer.observe(sentinel);
}

function setupRevealAnimations() {
    const revealItems = document.querySelectorAll(".reveal");
    if (!revealItems.length) return;

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                entry.target.classList.add("in-view");
                observer.unobserve(entry.target);
            });
        },
        {
            threshold: 0.15,
            rootMargin: "0px 0px -40px 0px"
        }
    );

    revealItems.forEach((item) => observer.observe(item));
}

function setupMobileNav() {
    const nav = document.getElementById("floatingNav");
    const navToggle = document.getElementById("navToggle");
    const navPanel = document.getElementById("navPanel");
    if (!nav || !navToggle || !navPanel) return;

    const setOpen = (isOpen) => {
        nav.classList.toggle("menu-open", isOpen);
        navToggle.setAttribute("aria-expanded", String(isOpen));
    };

    navToggle.addEventListener("click", (e) => {
        e.stopPropagation();
        const isOpen = !nav.classList.contains("menu-open");
        setOpen(isOpen);
    });

    navPanel.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", () => setOpen(false));
    });

    document.addEventListener("click", (event) => {
        if (!nav.classList.contains("menu-open")) return;
        if (nav.contains(event.target)) return;
        setOpen(false);
    });

    window.addEventListener("resize", () => {
        if (window.innerWidth > 980) {
            setOpen(false);
        }
    });
}

function setupThemeToggle() {
    const html = document.documentElement;
    const body = document.body;
    const themeToggle = document.getElementById("themeToggle");
    const icon = themeToggle ? themeToggle.querySelector(".theme-toggle-icon") : null;
    const label = themeToggle ? themeToggle.querySelector(".theme-toggle-label") : null;
    const metaTheme = document.querySelector('meta[name="theme-color"]');

    const applyTheme = (theme) => {
        html.setAttribute("data-theme", theme);
        body.setAttribute("data-theme", theme);
        if (icon) icon.textContent = theme === "light" ? "☀️" : "🌙";
        if (label) label.textContent = theme === "light" ? "Light" : "Dark";
        if (metaTheme) metaTheme.setAttribute("content", theme === "light" ? "#f6f6fb" : "#0A0A14");
    };

    // Sync body with html (the early <script> in <head> set html's data-theme)
    const savedTheme = html.getAttribute("data-theme") || "dark";
    applyTheme(savedTheme);

    if (!themeToggle) return;

    themeToggle.addEventListener("click", () => {
        const current = html.getAttribute("data-theme") || "dark";
        const nextTheme = current === "light" ? "dark" : "light";
        applyTheme(nextTheme);
        try {
            localStorage.setItem("pogo-theme", nextTheme);
        } catch (error) {
            // localStorage not available
        }
    });
}

function setupSmoothNavigation() {
    const body = document.body;
    const allLinks = document.querySelectorAll("a[href]");

    allLinks.forEach((link) => {
        const href = link.getAttribute("href");
        if (!href) return;

        // Smooth scroll for anchors
        if (href.startsWith("#")) {
            link.addEventListener("click", (event) => {
                const target = document.querySelector(href);
                if (!target) return;
                event.preventDefault();
                target.scrollIntoView({ behavior: "smooth", block: "start" });
            });
            return;
        }

        // Only handle internal same-origin paths
        if (!href.startsWith("/") || href.startsWith("//")) return;

        link.addEventListener("click", (event) => {
            if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
            if (link.target && link.target !== "_self") return;

            const targetUrl = new URL(link.href, window.location.origin);
            if (targetUrl.pathname === window.location.pathname) return;

            event.preventDefault();
            body.classList.add("is-leaving");
            setTimeout(() => {
                window.location.href = targetUrl.href;
            }, 180);
        });
    });

    // Remove leaving class on back/forward
    window.addEventListener("pageshow", (event) => {
        if (event.persisted) {
            body.classList.remove("is-leaving");
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    setupThemeToggle();
    setupNavbarMorph();
    setupRevealAnimations();
    setupMobileNav();
    setupSmoothNavigation();
});

// Register Service Worker for PWA
if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
        navigator.serviceWorker
            .register("/service-worker.js")
            .then((registration) => {
                console.log("Service Worker registered successfully:", registration.scope);
            })
            .catch((error) => {
                console.log("Service Worker registration failed:", error);
            });
    });
}