function toggleSection(element) {
    const content = element.nextElementSibling;
    const expanded = content.classList.toggle('expanded');
    element.classList.toggle('expanded', expanded);
}

// Register Service Worker for PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/service-worker.js')
            .then(registration => {
                console.log('Service Worker registered successfully:', registration.scope);
            })
            .catch(error => {
                console.log('Service Worker registration failed:', error);
            });
    });
}
