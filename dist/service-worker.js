const CACHE_NAME = 'pwa-cache-v1';
const urlsToCache = [
  '/',
  '/login',
  '/register',
  '/css/deteksi.css',
  '/scripts/deteksi.js',
  '/image/login.png',
  '/image/foto_profile/default.png',
  '/offline.html', // Tambahkan offline.html ke cache
  '/no-wifi.png'   // Pastikan kita juga mencache gambar no-wifi
];

// Install event - caching resources
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return Promise.all(
        urlsToCache.map(url => {
          console.log(`Caching: ${url}`);
          // Attempt to cache the resource
          return cache.add(url).catch(error => {
            console.error(`Failed to cache ${url}:`, error);
          });
        })
      );
    })
  );
});

// Fetch event - respond with cache or network
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      if (response) {
        console.log(`Serving from cache: ${event.request.url}`);
        return response; // Return cached response
      }
      console.log(`Fetching from network: ${event.request.url}`);
      return fetch(event.request).catch((error) => {
        console.error('Fetch failed:', error);
        // Jika fetch gagal (misalnya karena offline), tampilkan offline.html
        return caches.match('/offline.html'); // Kembalikan halaman offline
      });
    })
  );
});

// Activate event - remove old caches
self.addEventListener('activate', (event) => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (!cacheWhitelist.includes(cacheName)) {
            console.log(`Deleting old cache: ${cacheName}`);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});