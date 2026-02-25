const CACHE_NAME = 'pogo-intel-v4';
const urlsToCache = [
  '/static/manifest.json'
];

// Install event - cache resources and take over immediately
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Opened cache:', CACHE_NAME);
        return cache.addAll(urlsToCache);
      })
      .catch((err) => {
        console.log('Cache installation failed:', err);
      })
  );
  self.skipWaiting();
});

// Fetch event - network-first for CSS/JS, cache-first for images/icons
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Non-static requests: always go to network
  if (!url.pathname.startsWith('/static/')) {
    event.respondWith(fetch(event.request));
    return;
  }

  // CSS, JS, and manifest: network-first so updates are always picked up
  if (url.pathname.endsWith('.css') || url.pathname.endsWith('.js') || url.pathname.endsWith('.json')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response && response.status === 200 && response.type === 'basic') {
            const responseToCache = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseToCache);
            });
          }
          return response;
        })
        .catch(() => {
          // Offline fallback: serve from cache
          return caches.match(event.request);
        })
    );
    return;
  }

  // Images and other static assets: cache-first
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          return response;
        }

        const fetchRequest = event.request.clone();
        return fetch(fetchRequest).then((response) => {
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          const responseToCache = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });

          return response;
        });
      })
  );
});

// Activate event - clean up ALL old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  return self.clients.claim();
});