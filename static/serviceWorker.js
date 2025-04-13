const CACHE_NAME = 'packtrack-v1';
const urlsToCache = [
  '/',
  '/static/css/bootstrap.min.css',
  '/static/js/bootstrap.bundle.min.js',
  '/static/css/fontawesome.min.css',
  '/static/js/jquery.min.js',
  '/static/manifest.json',
  '/static/js/pwa.js',
  '/register',
  '/track',
  '/login',
  '/Templates/offline.html'
];

// Instalación del Service Worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Cache abierto');
        return cache.addAll(urlsToCache);
      })
  );
});

// Activación del Service Worker
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Estrategia de caché: Network First, fallback to cache
self.addEventListener('fetch', event => {
  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Si la respuesta es válida, clonamos y almacenamos en caché
        if (response && response.status === 200) {
          const responseToCache = response.clone();
          caches.open(CACHE_NAME)
            .then(cache => {
              cache.put(event.request, responseToCache);
            });
        }
        return response;
      })
      .catch(() => {
        // Si falla la conexión, intentamos recuperar de caché
        return caches.match(event.request)
          .then(response => {
            // Si tenemos la respuesta en caché, la devolvemos
            if (response) {
              return response;
            }
            // Si no tenemos la página en caché, mostramos la página offline
            return caches.match('/Templates/offline.html');
          });
      })
  );
}); 