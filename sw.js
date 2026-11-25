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
      const result=caches.open(VERI).catch(()=>null).then(async k=>{
        const hit=k&&await k.match(q).catch(()=>null);
        if(hit)return {response:hit};
        const response=await fetch(q);
        if(!k||!response.ok)return {response};
        const cacheWrite=k.put(q,response.clone()).then(async()=>{
          const keys=await k.keys();
          await Promise.all(keys.filter(key=>{
            const old=new URL(key.url);
            return old.pathname===u.pathname&&Number(old.searchParams.get('v'))<Number(v);
          }).map(key=>k.delete(key)));
        }).catch(()=>{});
        return {response,cacheWrite};
      });
      e.respondWith(result.then(x=>x.response));
      e.waitUntil(result.then(x=>x.cacheWrite).catch(()=>{}));return;}
    return;}
  if(/(^|\.)fonts\.(googleapis|gstatic)\.com$/.test(u.hostname)||(u.hostname==='cdn.jsdelivr.net'&&/supabase/.test(u.pathname))){
    e.respondWith(caches.open(KABUK).then(async k=>{const h=await k.match(q);if(h)return h;const r=await fetch(q);if(r.ok)k.put(q,r.clone());return r;}));}
});
