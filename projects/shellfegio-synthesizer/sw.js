// Shellfegio Synthesizer — Service Worker
// Stale-while-revalidate: serve from cache instantly, refresh in background.
// First visit (online) caches everything fetched; subsequent visits work offline.

const CACHE = 'shellfeggio-v2';

// ── Install: pre-cache the shell HTML so it loads offline immediately ─────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE).then(c =>
      c.addAll([
        './makey-makey-soundboard-11-keys.html',
      ])
    )
  );
  self.skipWaiting();
});

// ── Activate: delete old caches ───────────────────────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// ── Fetch: cache-first with background revalidation ──────────────────────────
self.addEventListener('fetch', event => {
  // Only intercept same-origin GET requests
  if (event.request.method !== 'GET') return;
  if (!event.request.url.startsWith(self.location.origin)) return;

  event.respondWith(
    caches.open(CACHE).then(cache =>
      cache.match(event.request).then(cached => {
        // Always try to refresh cache in the background
        const networkFetch = fetch(event.request)
          .then(response => {
            if (response && response.status === 200) {
              cache.put(event.request, response.clone());
            }
            return response;
          })
          .catch(() => {
            // Network failed — fall back to whatever is cached
            return cached;
          });

        // Return cached version immediately if available, otherwise wait for network
        return cached || networkFetch;
      })
    )
  );
});
