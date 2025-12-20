// Service Worker para LiberChat PWA
// Versão: 14.0.0

const CACHE_NAME = 'liberchat-v14';
const ASSETS_TO_CACHE = [
    '/',
    '/static/manifest.json',
    '/static/images/icon.svg',
    '/static/images/icon-192.png',
    '/static/images/icon-512.png',
    '/static/icons/check.svg',
    '/static/icons/shield.svg',
    '/static/icons/lock.svg',
    '/static/icons/zap.svg',
    '/static/icons/gift.svg',
    '/static/icons/sun.svg',
    '/static/icons/moon.svg',
    '/static/icons/monitor.svg',
    '/static/icons/menu.svg',
    '/static/icons/send.svg',
    '/static/icons/users.svg',
    '/static/icons/message-circle.svg',
    '/static/icons/key.svg',
    '/static/icons/settings.svg'
];

// Instalação do Service Worker
self.addEventListener('install', (event) => {
    console.log('[SW] Installing...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[SW] Caching assets');
                return cache.addAll(ASSETS_TO_CACHE);
            })
            .then(() => self.skipWaiting())
    );
});

// Ativação do Service Worker
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cache) => {
                    if (cache !== CACHE_NAME) {
                        console.log('[SW] Deleting old cache:', cache);
                        return caches.delete(cache);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch (estratégia: Network First, fallback para Cache)
self.addEventListener('fetch', (event) => {
    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // Se a resposta for válida, cache e retorne
                if (response && response.status === 200) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, responseClone);
                    });
                }
                return response;
            })
            .catch(() => {
                // Se falhar, tente buscar do cache
                return caches.match(event.request);
            })
    );
});
