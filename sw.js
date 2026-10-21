// Service worker minimal: syarat "install app". Tidak menyimpan cache data agent.
self.addEventListener("install",e=>self.skipWaiting());
self.addEventListener("activate",e=>self.clients.claim());
self.addEventListener("fetch",()=>{});
