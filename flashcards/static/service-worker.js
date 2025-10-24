const CACHE_NAME = 'rufingo-v2';
const urlsToCache = [
  '/',
  '/static/manifest.json'
];

// Instalación del Service Worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

// Activación del Service Worker
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Interceptar peticiones
self.addEventListener('fetch', event => {
  event.respondWith(
    fetch(event.request)
      .then(response => {
        const cloned = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, cloned));
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});

// Listener para notificaciones push (para Fase 4)
self.addEventListener('push', event => {
  const options = {
    body: event.data ? event.data.text() : '¡Tienes tarjetas pendientes!',
    icon: '/static/android-chrome-192x192.png',
    badge: '/static/android-chrome-192x192.png',
    vibrate: [200, 100, 200],
    tag: 'rufingo-notification',
    requireInteraction: true
  };
  
  event.waitUntil(
    self.registration.showNotification('Rufingo', options)
  );
});

// Click en notificación
self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow('/')
  );
});

