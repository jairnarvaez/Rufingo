const CACHE_NAME = 'rufingo-v4';
const urlsToCache = [
  '/',
  '/static/manifest.json'
];
// Instalación del Service Worker
self.addEventListener('install', event => {
 self.skipWaiting(); 
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});
// Activación del Service Worker
self.addEventListener('activate', event => {
  clients.claim();
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
  let data = {};

  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    console.error('Error parseando push event:', e);
  }

  const title = data.title || 'Rufingo';
  const options = {
    body: data.body || '¡Tienes tarjetas pendientes!',
    icon: data.icon || '/static/android-chrome-192x192.png',
    badge: data.badge || '/static/android-chrome-192x192.png',
    data: { url: data.url || '/' },
    vibrate: [200, 100, 200],
    tag: 'rufingo-notification',
    requireInteraction: true
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Click en notificación
self.addEventListener('notificationclick', event => {
  event.notification.close();
  const url = event.notification.data?.url || '/';
  event.waitUntil(clients.openWindow(url));
});
