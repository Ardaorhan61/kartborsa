/* KartBorsa service worker: veriler ve yazı tipleri cihazda saklanır.
   - Sayfa (index.html): önce internet, internet yoksa saklanan.
   - Sürümlü veri (.json?v=...): saklanan varsa anında o; yoksa indir ve sakla. Her yayında sürüm değişir, eski sürümler silinir.
   - Yazı tipleri ve Supabase kütüphanesi: saklanan varsa o. */
const VERI='kb-veri-1',KABUK='kb-kabuk-1';
self.addEventListener('install',e=>self.skipWaiting());
self.addEventListener('activate',e=>e.waitUntil((async()=>{for(const k of await caches.keys())if(![VERI,KABUK].includes(k))await caches.delete(k);await self.clients.claim();})()));
self.addEventListener('fetch',e=>{
  const q=e.request;if(q.method!=='GET')return;const u=new URL(q.url);
  if(u.origin===location.origin){
    if(q.mode==='navigate'){
      e.respondWith(fetch(q).then(r=>{if(r.ok&&u.pathname==='/'){const c=r.clone();caches.open(KABUK).then(k=>k.put('/',c));}return r;}).catch(()=>caches.match('/').then(r=>r||Response.error())));return;}
    const v=u.searchParams.get('v');
    if(v&&/\.json$/.test(u.pathname)){
      e.respondWith(caches.open(VERI).then(async k=>{const h=await k.match(q);if(h)return h;const r=await fetch(q);
        if(r.ok){await k.put(q,r.clone());k.keys().then(ks=>ks.forEach(x=>{if(new URL(x.url).searchParams.get('v')!==v)k.delete(x);}));}return r;}));return;}
    return;}
  if(/(^|\.)fonts\.(googleapis|gstatic)\.com$/.test(u.hostname)||(u.hostname==='cdn.jsdelivr.net'&&/supabase/.test(u.pathname))){
    e.respondWith(caches.open(KABUK).then(async k=>{const h=await k.match(q);if(h)return h;const r=await fetch(q);if(r.ok)k.put(q,r.clone());return r;}));}
});
