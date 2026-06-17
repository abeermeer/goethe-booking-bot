const CACHE = "goethe-booking-v1";
const PRECACHE = [
  "/",
  "/manifest.json",
];
self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(PRECACHE)).then(() => self.skipWaiting())
  );
});
self.addEventListener("activate", e => {
  e.waitUntil(clients.claim());
});
self.addEventListener("fetch", e => {
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request).catch(() => new Response("Offline", {status: 503})))
  );
});
