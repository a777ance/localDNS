/* A777ance statement gallery — service worker.
 * Makes the gallery installable (PWA) and openable offline on phone and laptop.
 * Cache-first for the known static assets; network with an offline fallback for
 * everything else. Bump CACHE when the published assets change. */
const CACHE = 'a777ance-statements-v2';

// Precache the shell. Only list files that always exist, so install never fails.
const ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './client/archetype-prime-time.html',
  './client/archetype-home-office.html',
  './client/archetype-connected-family.html',
  './operator/alliance-member-portfolio.html',
  './business-plan/index.html',
  './previews/archetype-prime-time.png',
  './previews/archetype-home-office.png',
  './previews/archetype-connected-family.png',
  './previews/alliance-member-portfolio.png',
  './icons/icon.svg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    caches.match(event.request).then((hit) => {
      if (hit) return hit;
      return fetch(event.request)
        .then((resp) => {
          const copy = resp.clone();
          caches.open(CACHE).then((cache) => cache.put(event.request, copy));
          return resp;
        })
        .catch(() => caches.match('./index.html'));
    })
  );
});
