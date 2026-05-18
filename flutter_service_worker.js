'use strict';
const MANIFEST = 'flutter-app-manifest';
const TEMP = 'flutter-temp-cache';
const CACHE_NAME = 'flutter-app-cache';

const RESOURCES = {"account-delete.html": "c435bb19832a568003477698c74c6857",
"assets/AssetManifest.bin": "44170cd5a3e86b66a5eefac3062cbbb4",
"assets/AssetManifest.bin.json": "6bc84c86d9964da289a7b45e6e323c80",
"assets/AssetManifest.json": "bad272e3bdf2329d07a56d80ed68401a",
"assets/assets/fonts/NotoSansKR-Bold.ttf": "671db5f821991c90d7f8499bcf9fed7e",
"assets/assets/fonts/NotoSansKR-Regular.ttf": "e910afbd441c5247227fb4a731d65799",
"assets/assets/icon.png": "725d339637c807372743bff0420acebe",
"assets/assets/lottie/result_alpha_MP-BTC-US.csv": "0b1c9abde4d7c53ba747c392dca47693",
"assets/assets/lottie/result_MP-BTC-US.csv": "62cc26d1c976a41f9432313fb9244d31",
"assets/assets/lottie/result_VOO_MP-BTC-US.csv": "ac0885adf9780d4df5f899970b9fb7b1",
"assets/assets/trends_report/theme_trends_report_latest.txt": "a7c22efabb696f2c5be57671e164ab71",
"assets/assets/trends_report/trends_report_260131.txt": "7b5e71a53af4c61cc4246b3105fc45f3",
"assets/FontManifest.json": "713c1cf0af498a72c3f5f3e60101d432",
"assets/fonts/MaterialIcons-Regular.otf": "d1408f4f277e616342f36eaea03bbdf7",
"assets/icon.png": "abed98b83fbd438df4f77101d0e26838",
"assets/NOTICES": "699d2c477c8d23a843457708aeb835b9",
"assets/packages/cupertino_icons/assets/CupertinoIcons.ttf": "33b7d9392238c04c131b6ce224e13711",
"assets/shaders/ink_sparkle.frag": "ecc85a2e95f5e9f53123dcaf8cb9b6ce",
"canvaskit/canvaskit.js": "728b2d477d9b8c14593d4f9b82b484f3",
"canvaskit/canvaskit.js.symbols": "bdcd3835edf8586b6d6edfce8749fb77",
"canvaskit/canvaskit.wasm": "7a3f4ae7d65fc1de6a6e7ddd3224bc93",
"canvaskit/chromium/canvaskit.js": "8191e843020c832c9cf8852a4b909d4c",
"canvaskit/chromium/canvaskit.js.symbols": "b61b5f4673c9698029fa0a746a9ad581",
"canvaskit/chromium/canvaskit.wasm": "f504de372e31c8031018a9ec0a9ef5f0",
"canvaskit/skwasm.js": "ea559890a088fe28b4ddf70e17e60052",
"canvaskit/skwasm.js.symbols": "e72c79950c8a8483d826a7f0560573a1",
"canvaskit/skwasm.wasm": "39dd80367a4e71582d234948adc521c0",
"ChatGPT%20Image%202026%EB%85%84%203%EC%9B%94%203%EC%9D%BC%20%EC%98%A4%ED%9B%84%2011_15_28.png": "c0fd0ed56cec20ec5fdce490096437e3",
"favicon.png": "d83a8ab57137a5225a1781bcab9f3cf6",
"flutter.js": "83d881c1dbb6d6bcd6b42e274605b69c",
"flutter_bootstrap.js": "c4579c8ac81613ec0f75fa91768c74e8",
"Gemini_Generated_Image_kluzrfkluzrfkluz.png": "b47216ba58c39bd88a20be7108620bd4",
"icons/Icon-192.png": "20ecc6ff49090f1ed1e765cb14666bd7",
"icons/Icon-512.png": "cda37943d26d7ade1cd036c654ec991f",
"icons/Icon-maskable-192.png": "20ecc6ff49090f1ed1e765cb14666bd7",
"icons/Icon-maskable-512.png": "cda37943d26d7ade1cd036c654ec991f",
"index.html": "31c580a18487454bcb4cb54b730575f6",
"/": "31c580a18487454bcb4cb54b730575f6",
"main.dart.js": "b44a05492d63de27c6cd84e08e862a4d",
"manifest.json": "795bf2d28ee5eb4b3130fd8d7c8017b1",
"og%20copy.png": "b2d6a9cd1a8d7951b8bf245e46633eb7",
"og.png": "5f8359e283146a99307fefd8ac12720b",
"og2.png": "04ef82b641d2c4cac01ef16514d111da",
"og3.png": "7bf8523bcb344379dc6bc85ff5d09fa7",
"og4.png": "081c798eb0926d9eb2545f5f7c8c8f88",
"og5.png": "3461511b29d265f7e9a42e74ca24a068",
"og6.png": "c0fd0ed56cec20ec5fdce490096437e3",
"og7.png": "4f9ac710726564b532d005481b91540a",
"og8.png": "ebeae9aaabf92f6b61c3ce65bfedf737",
"og9.png": "92b5b041311bacef566cf7d097c2f4ed",
"privacy.html": "febe1fdc7937d110d2fb64684011ed2b",
"terms.html": "7000fcf04a23eb9c192dfef84ad5436a",
"version.json": "7076d64576d0ac2d08a603d1f0dd846d"};
// The application shell files that are downloaded before a service worker can
// start.
const CORE = ["main.dart.js",
"index.html",
"flutter_bootstrap.js",
"assets/AssetManifest.bin.json",
"assets/FontManifest.json"];

// During install, the TEMP cache is populated with the application shell files.
self.addEventListener("install", (event) => {
  self.skipWaiting();
  return event.waitUntil(
    caches.open(TEMP).then((cache) => {
      return cache.addAll(
        CORE.map((value) => new Request(value, {'cache': 'reload'})));
    })
  );
});
// During activate, the cache is populated with the temp files downloaded in
// install. If this service worker is upgrading from one with a saved
// MANIFEST, then use this to retain unchanged resource files.
self.addEventListener("activate", function(event) {
  return event.waitUntil(async function() {
    try {
      var contentCache = await caches.open(CACHE_NAME);
      var tempCache = await caches.open(TEMP);
      var manifestCache = await caches.open(MANIFEST);
      var manifest = await manifestCache.match('manifest');
      // When there is no prior manifest, clear the entire cache.
      if (!manifest) {
        await caches.delete(CACHE_NAME);
        contentCache = await caches.open(CACHE_NAME);
        for (var request of await tempCache.keys()) {
          var response = await tempCache.match(request);
          await contentCache.put(request, response);
        }
        await caches.delete(TEMP);
        // Save the manifest to make future upgrades efficient.
        await manifestCache.put('manifest', new Response(JSON.stringify(RESOURCES)));
        // Claim client to enable caching on first launch
        self.clients.claim();
        return;
      }
      var oldManifest = await manifest.json();
      var origin = self.location.origin;
      for (var request of await contentCache.keys()) {
        var key = request.url.substring(origin.length + 1);
        if (key == "") {
          key = "/";
        }
        // If a resource from the old manifest is not in the new cache, or if
        // the MD5 sum has changed, delete it. Otherwise the resource is left
        // in the cache and can be reused by the new service worker.
        if (!RESOURCES[key] || RESOURCES[key] != oldManifest[key]) {
          await contentCache.delete(request);
        }
      }
      // Populate the cache with the app shell TEMP files, potentially overwriting
      // cache files preserved above.
      for (var request of await tempCache.keys()) {
        var response = await tempCache.match(request);
        await contentCache.put(request, response);
      }
      await caches.delete(TEMP);
      // Save the manifest to make future upgrades efficient.
      await manifestCache.put('manifest', new Response(JSON.stringify(RESOURCES)));
      // Claim client to enable caching on first launch
      self.clients.claim();
      return;
    } catch (err) {
      // On an unhandled exception the state of the cache cannot be guaranteed.
      console.error('Failed to upgrade service worker: ' + err);
      await caches.delete(CACHE_NAME);
      await caches.delete(TEMP);
      await caches.delete(MANIFEST);
    }
  }());
});
// The fetch handler redirects requests for RESOURCE files to the service
// worker cache.
self.addEventListener("fetch", (event) => {
  if (event.request.method !== 'GET') {
    return;
  }
  var origin = self.location.origin;
  var key = event.request.url.substring(origin.length + 1);
  // Redirect URLs to the index.html
  if (key.indexOf('?v=') != -1) {
    key = key.split('?v=')[0];
  }
  if (event.request.url == origin || event.request.url.startsWith(origin + '/#') || key == '') {
    key = '/';
  }
  // If the URL is not the RESOURCE list then return to signal that the
  // browser should take over.
  if (!RESOURCES[key]) {
    return;
  }
  // If the URL is the index.html, perform an online-first request.
  if (key == '/') {
    return onlineFirst(event);
  }
  event.respondWith(caches.open(CACHE_NAME)
    .then((cache) =>  {
      return cache.match(event.request).then((response) => {
        // Either respond with the cached resource, or perform a fetch and
        // lazily populate the cache only if the resource was successfully fetched.
        return response || fetch(event.request).then((response) => {
          if (response && Boolean(response.ok)) {
            cache.put(event.request, response.clone());
          }
          return response;
        });
      })
    })
  );
});
self.addEventListener('message', (event) => {
  // SkipWaiting can be used to immediately activate a waiting service worker.
  // This will also require a page refresh triggered by the main worker.
  if (event.data === 'skipWaiting') {
    self.skipWaiting();
    return;
  }
  if (event.data === 'downloadOffline') {
    downloadOffline();
    return;
  }
});
// Download offline will check the RESOURCES for all files not in the cache
// and populate them.
async function downloadOffline() {
  var resources = [];
  var contentCache = await caches.open(CACHE_NAME);
  var currentContent = {};
  for (var request of await contentCache.keys()) {
    var key = request.url.substring(origin.length + 1);
    if (key == "") {
      key = "/";
    }
    currentContent[key] = true;
  }
  for (var resourceKey of Object.keys(RESOURCES)) {
    if (!currentContent[resourceKey]) {
      resources.push(resourceKey);
    }
  }
  return contentCache.addAll(resources);
}
// Attempt to download the resource online before falling back to
// the offline cache.
function onlineFirst(event) {
  return event.respondWith(
    fetch(event.request).then((response) => {
      return caches.open(CACHE_NAME).then((cache) => {
        cache.put(event.request, response.clone());
        return response;
      });
    }).catch((error) => {
      return caches.open(CACHE_NAME).then((cache) => {
        return cache.match(event.request).then((response) => {
          if (response != null) {
            return response;
          }
          throw error;
        });
      });
    })
  );
}
