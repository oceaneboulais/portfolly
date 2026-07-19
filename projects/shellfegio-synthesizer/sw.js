// Shellfegio Synthesizer — Service Worker
// Stale-while-revalidate: serve from cache instantly, refresh in background.
// First visit (online) caches everything fetched; subsequent visits work offline.

const CACHE = 'shellfeggio-v5';

// WAV assets — pre-cached on install so they are available offline on iPhone.
// Each entry is fetched independently so one missing file never blocks install.
const WAV_ASSETS = [
  './sounds/Duck_call/soundsampAnalogData-10MAR2025-1038_VS-209sensor-rot.wav_20250310T103936_1.0x.wav',
  './sounds/Good_Purrs/soundsampDA23A1T20230819T000000.gsi_20230819T181145_1.0x.wav',
  './sounds/Louderboat_fish/soundsampDA23A1T20230819T000000.gsi_20230819T163355_1.0x.wav',
  './sounds/low_tone/soundsampAnalogData-20MAR2025-0927_VS-209sensor-rot.wav_20250320T092759_1.0x.wav',
  './sounds/Pulse_Pulse_boat/soundsampDA23A0T20230717T000000.gsi_20230717T080005_1.0x.wav',
  './sounds/Pulse_train3/soundsampDA23A0T20230717T000000.gsi_20230717T000117_1.0x.wav',
  './sounds/Purrr/soundsampDA23A0T20230717T000000.gsi_20230717T050302_1.0x.wav',
  './sounds/Shrimp_fish/soundsampAnalogData-06JUN2024-1456_VS-209sensor.wav_20240606T145828_1.0x.wav',
  './sounds/big_WHOOP/soundsampAnalogData-20MAR2025-0927_VS-209sensor-rot.wav_20250320T093148_1.0x.wav',
  './sounds/falling_tone/soundsampAnalogData-20MAR2025-0927_VS-209sensor-rot.wav_20250320T092710_1.0x.wav',
  './sounds/flutey/soundsampAnalogData-20MAR2025-0927_VS-209sensor-rot.wav_20250320T093041_1.0x.wav',
  './sounds/poppinh_pulse/soundsampDA23A1T20230817T000000.gsi_20230817T052109_1.0x.wav',
];

// ── Install: pre-cache the shell HTML + all WAV files ────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE).then(async c => {
      // Shell HTML is critical — fail install if this fails
      await c.addAll(['./makey-makey-soundboard-12-keys.html']);
      // WAV files are best-effort — a missing file must not block install
      await Promise.all(WAV_ASSETS.map(url => c.add(url).catch(() => {})));
    })
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
