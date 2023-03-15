// https://developer.chrome.com/docs/workbox/caching-strategies-overview/
// Establish a cache name
/*const cacheName = 'Better_VPlan_cache_v1';

self.addEventListener('fetch', (event) => {
    // Check if this is a navigation request
    if (event.request.method == "GET") {
        // Open the cache
        event.respondWith(caches.open(cacheName).then((cache) => {
            // Go to the network first
            return fetch(event.request.url).then((fetchedResponse) => {
                cache.put(event.request, fetchedResponse.clone());

                return fetchedResponse;
            }).catch(() => {
                // If the network is unavailable, get
                return cache.match(event.request.url);
            });
        }));
    } else {
        return;
    }
});*/

self.addEventListener ("fetch", function(event) {});