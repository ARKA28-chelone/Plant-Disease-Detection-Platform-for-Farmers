// ---------- Service worker: lets PlantCare be installed and open offline ----------
// Network first, so pages are always fresh when online; the cache is only a fallback.
const CACHE = "plantcare-v1";
const SHELL = [
  "/index.html", "/style.css", "/script.js", "/auth.js", "/i18n.js", "/chat-widget.js",
  "/upload-tools.js", "/diseases.html", "/offline.html", "/icons/icon-192.png"
];

self.addEventListener("install", function (event) {
  event.waitUntil(caches.open(CACHE).then(function (cache) { return cache.addAll(SHELL); }));
  self.skipWaiting();
});

self.addEventListener("activate", function (event) {
  // Drop caches from older versions
  event.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
  }));
  self.clients.claim();
});

self.addEventListener("fetch", function (event) {
  const req = event.request;
  const url = new URL(req.url);
  // Only handle our own GET requests; API calls and uploads always go to the network
  if (req.method !== "GET" || url.origin !== self.location.origin || url.pathname.startsWith("/api/")) return;

  event.respondWith(
    fetch(req).then(function (res) {
      if (res.ok && SHELL.indexOf(url.pathname) !== -1) {
        const copy = res.clone();
        caches.open(CACHE).then(function (cache) { cache.put(req, copy); });
      }
      return res;
    }).catch(function () {
      return caches.match(req).then(function (cached) {
        if (cached) return cached;
        if (req.mode === "navigate") return caches.match("/offline.html");
        return Response.error();
      });
    })
  );
});
