/* ===== 24 Kasım 2026: Magic: The Gathering deste kurucu (menüde "Desteler", Magic seçiliyken) =====
   index.html sonunda <script src="/magic-deste.js"> ile yüklenir; drawDeste DIL==='mg' iken window.mgDesteCiz()'i çağırır.
   Biçimler: Serbest (60+ kart, aynı isimden en fazla 4, yan deste en fazla 15), Commander (komutan + 99 = 100, tekil, renk kimliği),
   Limited (40+ kart, kopya sınırı yok). Yasaklı kart listeleri denetlenmez. Kayıt: hesapta desteler tablosu (legends=['mg',biçim,komutan]),
   yoksa cihazda (localStorage kb_mdesteler). Paylaşım: ?mdeste=ad~biçim~komutan~kimlik[xN].…~yan… */
(function(){
'use strict';
if(!document.getElementById('magic-deste-css')){const st=document.createElement('style');st.id='magic-deste-css';st.textContent='.mdmana{flex:0 0 auto;display:inline-flex;gap:1px;align-items:center;min-width:22px}.mdmana .msym{width:15px;height:15px}'
 +'.mdbaski{max-width:150px;font-size:12px;padding:2px 4px}.mdgraf{display:flex;gap:18px;flex-wrap:wrap;align-items:flex-end;margin:6px 0 12px}'
 +'.mdegri{display:flex;gap:4px;align-items:flex-end;height:110px;margin-top:4px}.mdsut{display:flex;flex-direction:column;align-items:center;justify-content:flex-end;width:22px;height:100%}'
 +'.mdsut i{display:block;width:16px;min-height:2px;border-radius:4px 4px 0 0;background:linear-gradient(180deg,#b48cff,#6a4fc9)}'
 +'.mdrenk{display:flex;height:14px;border-radius:7px;overflow:hidden;margin-top:6px;background:rgba(255,255,255,.08)}'
 +'.mdkom{display:flex;gap:12px;align-items:center;margin:6px 0 12px}.mdkomr{width:90px;cursor:pointer}.mdk{cursor:default}.mdk:hover{transform:none}';document.head.appendChild(st);}
const BICIM={serbest:{ad:'Serbest (60+ kart)',min:60,kopya:4,yan:15},commander:{ad:'Commander (100 kart, tekil)',min:100,kopya:1,yan:0},limited:{ad:'Limited / Draft (40+ kart)',min:40,kopya:99,yan:99}};
const RENKH={Beyaz:'W',Mavi:'U',Siyah:'B',Kırmızı:'R',Yeşil:'G'},RENK_AD={W:'Beyaz',U:'Mavi',B:'Siyah',R:'Kırmızı',G:'Yeşil',C:'Renksiz'};
const RENK_C={W:'#e9dfb8',U:'#3d9bf0',B:'#9a8aa8',R:'#f2683a',G:'#5fbd58',C:'#a7b0be'};
const TURLER=['Creature','Planeswalker','Instant','Sorcery','Artifact','Enchantment','Battle','Land'];
const TUR_TR={Creature:'Yaratıklar',Planeswalker:'Planeswalker\'lar',Instant:'Instant\'lar',Sorcery:'Sorcery\'ler',Artifact:'Artifact\'ler',Enchantment:'Enchantment\'lar',Battle:'Battle\'lar',Land:'Araziler',Diger:'Diğer'};
const MD={ad:'Yeni Magic destesi',bicim:'serbest',komutan:null,ana:{},yan:{},id:null,yid:null,q:'',renk:'',tur:'',sadeceBende:false};
try{const t=JSON.parse(localStorage.getItem('kb_mdeste_taslak')||'null');if(t&&t.ana)Object.assign(MD,t,{id:t.id||null});}catch(e){}
const taslak=()=>{try{localStorage.setItem('kb_mdeste_taslak',JSON.stringify({ad:MD.ad,bicim:MD.bicim,komutan:MD.komutan,ana:MD.ana,yan:MD.yan,id:MD.id,yid:MD.yid}));}catch(e){}};
const kart=id=>{const i=BYID[id];return i!=null?CAT.cards[i]:null;};
const anahtar=i=>(CAT.keys&&CAT.keys[i])||'';
const tip=c=>String(c&&c[12]||'');
const temelArazi=c=>/\bBasic\b/.test(tip(c))&&/\bLand\b/.test(tip(c));
const efsaneviYaratik=(c,d)=>(/\bLegendary\b/.test(tip(c))&&/\bCreature\b/.test(tip(c)))||/can be your commander/i.test(((d&&d.y)||[]).map(y=>y.x||'').join(' '));
const sinirsiz=d=>/A deck can have any number of cards named/i.test(((d&&d.y)||[]).map(y=>y.x||'').join(' '));
const fiyat=id=>{try{const v=mainValue(OZET&&OZET.c[id]);return v?v.tl:null;}catch(e){return null;}};
const anaTur=c=>{const t=tip(c);if(/\bLand\b/.test(t)&&!/\bCreature\b/.test(t))return 'Land';for(const x of TURLER)if(new RegExp('\\b'+x+'\\b').test(t))return x;return 'Diger';};
function manaDegeri(m){let v=0;String(m||'').replace(/\{([^}]+)\}/g,(_,s)=>{if(/^\d+$/.test(s))v+=+s;else if(/^[XYZ]$/.test(s)){}else if(/^2\//.test(s))v+=2;else if(s!=='½')v+=1;return '';});return v;}
function kimlik(c,d){const s=new Set();Object.entries(RENKH).forEach(([ad,h])=>{if(tip(c).includes(ad))s.add(h);});
  ((d&&d.y)||[]).forEach(y=>{const metin=(y.m||'')+' '+String(y.x||'').replace(/\([^)]*\)/g,'');(metin.match(/\{[^}]+\}/g)||[]).forEach(sym=>{for(const h of 'WUBRG')if(sym.includes(h))s.add(h);});});return s;}
const DET={};
async function detaylar(ids){await Promise.all([...new Set(ids)].map(async id=>{const c=kart(id);if(!c||DET[id])return;try{DET[id]=await mgDetay(c);}catch(e){DET[id]={};}}));}
const adi=c=>String(c[0]);
function durum(){const B=BICIM[MD.bicim],ana=Object.entries(MD.ana).filter(([id,n])=>n>0&&kart(id)),yan=Object.entries(MD.yan).filter(([id,n])=>n>0&&kart(id));
  const kom=MD.bicim==='commander'&&MD.komutan&&kart(MD.komutan)?MD.komutan:null;
  const anaSay=ana.reduce((t,[,n])=>t+n,0)+(kom?1:0),yanSay=yan.reduce((t,[,n])=>t+n,0);const hatalar=[];
  if(MD.bicim==='commander'){if(!kom)hatalar.push('Bir komutan seç (efsanevi yaratık).');else if(!efsaneviYaratik(kart(kom),DET[kom]))hatalar.push('Komutan efsanevi (Legendary) bir yaratık olmalı.');
    if(anaSay!==100)hatalar.push(`Komutanla birlikte tam 100 kart olmalı (şu an ${anaSay}).`);}
  else if(anaSay<B.min)hatalar.push(`Ana destede en az ${B.min} kart olmalı (şu an ${anaSay}).`);
  if(yanSay>B.yan&&MD.bicim!=='limited')hatalar.push(MD.bicim==='commander'?'Commander\'da yan deste olmaz; yan destedeki kartları çıkar.':`Yan destede en fazla ${B.yan} kart olabilir (şu an ${yanSay}).`);
  const adSay={};[...ana,...yan].forEach(([id,n])=>{const c=kart(id);if(temelArazi(c)||sinirsiz(DET[id]))return;adSay[adi(c)]=(adSay[adi(c)]||0)+n;});
  if(kom){const a=adi(kart(kom));if(!temelArazi(kart(kom)))adSay[a]=(adSay[a]||0)+1;}
  Object.entries(adSay).forEach(([a,n])=>{if(n>B.kopya)hatalar.push(B.kopya===1?`"${a}" kartından yalnız 1 tane olabilir (şu an ${n}).`:`"${a}" kartından en fazla ${B.kopya} kopya olabilir (şu an ${n}).`);});
  const renkDisi=new Set();if(kom){const k=kimlik(kart(kom),DET[kom]);ana.forEach(([id])=>{const s=kimlik(kart(id),DET[id]);for(const h of s)if(!k.has(h)){renkDisi.add(id);break;}});
    if(renkDisi.size)hatalar.push(`${renkDisi.size} kart komutanın renk kimliği (${[...k].map(h=>RENK_AD[h]).join(', ')||'Renksiz'}) dışında.`);}
  const egri=[0,0,0,0,0,0,0,0],renk={};let deger=0,fiyatsiz=0,eksikSay=0,eksikDeger=0;const bende={};(typeof COLL!=='undefined'&&COLL||[]).forEach(x=>{bende[x.card_id]=(bende[x.card_id]||0)+x.qty;});
  const hepsi=[...ana,...yan,...(kom?[[kom,1]]:[])];
  hepsi.forEach(([id,n])=>{const v=fiyat(id);if(v!=null)deger+=v*n;else fiyatsiz+=n;const e=Math.max(0,n-(bende[id]||0));if(e){eksikSay+=e;if(v!=null)eksikDeger+=v*e;}});
  [...ana,...(kom?[[kom,1]]:[])].forEach(([id,n])=>{const c=kart(id),d=DET[id];if(anaTur(c)==='Land')return;const mv=manaDegeri(d&&d.y&&d.y[0]&&d.y[0].m);egri[Math.min(7,mv)]+=n;
    const s=kimlik(c,d);if(!s.size)renk.C=(renk.C||0)+n;else s.forEach(h=>{renk[h]=(renk[h]||0)+n;});});
  return{ana,yan,kom,anaSay,yanSay,hatalar,renkDisi,egri,renk,deger,fiyatsiz,eksikSay,eksikDeger};}

function satir(id,n,yanMi,D){const c=kart(id),d=DET[id]||{},y=(d.y&&d.y[0])||{};
  return el('div',{class:'k2dsat'+(D.renkDisi.has(id)?' hata':'')},el('span',{class:'mdmana'},...(y.m?mgMana(y.m):[el('span',{class:'muted',text:'–'})])),
    el('span',{class:'k2dad',style:'cursor:pointer',onclick:()=>openCard(BYID[id]),text:adi(c)}),
    baskiSec(id,yanMi),
    el('span',{class:'k2dadet'},el('button',{title:'Azalt',onclick:()=>{const t=yanMi?MD.yan:MD.ana;t[id]=Math.max(0,(t[id]||0)-1);if(!t[id])delete t[id];ciz(true);}},'−'),el('b',{text:String(n)}),
      el('button',{title:'Artır',onclick:()=>ekle(id,yanMi)},'+'),MD.bicim!=='commander'?el('button',{title:yanMi?'Ana desteye taşı':'Yan desteye taşı',onclick:()=>{const a=yanMi?MD.yan:MD.ana,b=yanMi?MD.ana:MD.yan;b[id]=(b[id]||0)+1;a[id]--;if(!a[id])delete a[id];ciz(true);}},yanMi?'↑':'↓'):null));}
const BASKI={};
function baskilar(ad){if(BASKI[ad])return BASKI[ad];const l=[];CAT.cards.forEach((c,i)=>{if(isMg(c)&&c[0]===ad&&c[4]!=='Token')l.push(c[14]);});return BASKI[ad]=l;}
function baskiSec(id,yanMi){const c=kart(id),l=baskilar(adi(c));if(l.length<2)return el('span',{class:'muted small',text:(CAT.sets[c[1]]||[])[1]||''});
  const s=el('select',{class:'mdbaski',title:'Baskıyı değiştir'},...l.slice(0,200).map(x=>{const k=kart(x),v=fiyat(x);return el('option',{value:x},((CAT.sets[k[1]]||[])[1]||'')+' #'+k[2]+(v!=null?' · '+tl(v):''));}));s.value=id;
  s.addEventListener('change',()=>{const t=yanMi?MD.yan:MD.ana;const n=t[id]||0;delete t[id];t[s.value]=(t[s.value]||0)+n;ciz(true);});return s;}
function ekle(id,yanMi){const c=kart(id);if(!c)return;const t=yanMi?MD.yan:MD.ana;
  if(MD.bicim==='commander'&&!yanMi&&(t[id]||0)>=1&&!temelArazi(c)&&!sinirsiz(DET[id])){toast('Commander\'da her karttan yalnız 1 tane olabilir');return;}
  t[id]=(t[id]||0)+1;taslak();if(document.querySelector('#v-deste.on'))ciz(true);}
function egriCiz(D){const m=Math.max(1,...D.egri);return el('div',{class:'mdegri'},...D.egri.map((n,i)=>el('div',{class:'mdsut',title:`${i===7?'7+':i} mana: ${n} kart`},el('span',{class:'small',text:n||''}),el('i',{style:`height:${Math.round(n/m*70)}px`}),el('span',{class:'muted small',text:i===7?'7+':String(i)}))));}
function renkCiz(D){const top=Object.values(D.renk).reduce((a,b)=>a+b,0)||1;return el('div',{class:'mdrenk'},...Object.entries(D.renk).sort((a,b)=>b[1]-a[1]).map(([h,n])=>el('span',{style:`flex:${n};background:${RENK_C[h]}`,title:`${RENK_AD[h]}: ${n} kart (%${Math.round(n/top*100)})`})));}
function listeMetni(D){const st=([id,n])=>n+' '+adi(kart(id));const l=[];if(D.kom)l.push('Commander','1 '+adi(kart(D.kom)),'');l.push('Deck',...D.ana.map(st));if(D.yan.length)l.push('','Sideboard',...D.yan.map(st));return l.join('\n');}
function kodla(){const p=id=>String(id).replace(/^mg-/,'');const k=o=>Object.entries(o).filter(([,n])=>n>0).map(([id,n])=>p(id)+(n>1?'x'+n:'')).join('.');
  return [encodeURIComponent(MD.ad.slice(0,60)),MD.bicim,MD.komutan?p(MD.komutan):'',k(MD.ana),k(MD.yan)].join('~');}
function coz(s){const[a,b,ko,an,ya]=String(s).split('~');const ac=x=>{const o={};(x||'').split('.').forEach(t=>{const m=t.match(/^(.+?)(?:x(\d+))?$/);if(m&&m[1]&&BYID['mg-'+m[1]]!=null)o['mg-'+m[1]]=Math.min(250,+(m[2]||1));});return o;};
  MD.ad=decodeURIComponent(a||'Paylaşılan deste').slice(0,60);MD.bicim=BICIM[b]?b:'serbest';MD.komutan=ko&&BYID['mg-'+ko]!=null?'mg-'+ko:null;MD.ana=ac(an);MD.yan=ac(ya);MD.id=null;MD.yid=null;}
async function iceAktar(metin){let yanMi=false,komMi=false,bulunmayan=[];const ana={},yan={};let kom=null;
  for(const sat of String(metin).split(/\r?\n/)){const t=sat.trim();if(!t)continue;if(/^(sideboard|yan deste)/i.test(t)){yanMi=true;komMi=false;continue;}if(/^(commander|komutan)/i.test(t)){komMi=true;continue;}if(/^(deck|deste|main)/i.test(t)){yanMi=false;komMi=false;continue;}
    const m=t.match(/^(\d+)\s*x?\s+(.+?)(?:\s+\(([A-Za-z0-9]+)\)\s*([\w★†-]+))?\s*$/);if(!m)continue;const n=+m[1],ad=m[2].replace(/\s*\/\/.*$/,'').trim();
    let id=null;if(m[3]){const s='mg-'+m[3].toLowerCase()+'-'+m[4];if(BYID[s]!=null)id=s;}
    if(!id){const l=baskilar(ad).length?baskilar(ad):CAT.cards.filter(c=>isMg(c)&&String(c[0]).toLowerCase().startsWith(ad.toLowerCase()+' //')).map(c=>c[14]);
      if(l.length){id=l.slice().sort((x,y)=>(fiyat(x)==null)-(fiyat(y)==null)||(fiyat(x)||0)-(fiyat(y)||0))[0];}}
    if(!id){bulunmayan.push(ad);continue;}if(komMi){kom=id;komMi=false;continue;}const o=yanMi?yan:ana;o[id]=(o[id]||0)+n;}
  return{ana,yan,kom,bulunmayan};}
const yerel=()=>{try{return JSON.parse(localStorage.getItem('kb_mdesteler')||'[]');}catch(e){return [];}};
async function kaydet(){const row={ad:MD.ad||'Magic destesi',legends:['mg',MD.bicim,MD.komutan||null],kartlar:{ana:MD.ana,yan:MD.yan},herkese_acik:true};
  if(USER&&typeof PROFILE!=='undefined'&&PROFILE){const r=MD.id?await SB.from('desteler').update(row).eq('id',MD.id).select().single():await SB.from('desteler').insert(row).select().single();
    if(!r.error){MD.id=r.data.id;taslak();toast('Deste hesabına kaydedildi 💾');kayitlar();return;}if(!/does not exist|schema cache/i.test(r.error.message||'')){toast('Kaydedilemedi: '+r.error.message);return;}}
  try{const l=yerel().filter(d=>d.yid!==MD.yid);MD.yid=MD.yid||('m'+Date.now());l.unshift({yid:MD.yid,ad:MD.ad,bicim:MD.bicim,komutan:MD.komutan,ana:MD.ana,yan:MD.yan});localStorage.setItem('kb_mdesteler',JSON.stringify(l.slice(0,30)));taslak();toast('Deste bu cihaza kaydedildi 💾');kayitlar();}catch(e){toast('Kaydedilemedi');}}
async function kayitlar(){const kutu=document.querySelector('#v-deste .mdkayit');if(!kutu)return;let hesap=[];
  if(USER){try{const r=await SB.from('desteler').select('*').eq('owner',USER.id).order('updated_at',{ascending:false});if(!r.error)hesap=(r.data||[]).filter(d=>Array.isArray(d.legends)&&d.legends[0]==='mg');}catch(e){}}
  const y=yerel();kutu.innerHTML='';if(!hesap.length&&!y.length)return;
  kutu.append(el('b',{class:'small'},'Kayıtlı Magic destelerin: '),...hesap.map(d=>el('button',{class:'k2chip',onclick:()=>{MD.ad=d.ad;MD.bicim=d.legends[1]||'serbest';MD.komutan=d.legends[2]||null;MD.ana=(d.kartlar||{}).ana||{};MD.yan=(d.kartlar||{}).yan||{};MD.id=d.id;MD.yid=null;ciz();}},'☁️ '+d.ad)),
    ...y.map(d=>el('button',{class:'k2chip',onclick:()=>{Object.assign(MD,{ad:d.ad,bicim:d.bicim||'serbest',komutan:d.komutan||null,ana:d.ana||{},yan:d.yan||{},id:null,yid:d.yid});ciz();}},'📱 '+d.ad)));}

let CIZILIYOR=0;
async function ciz(sadecePanel){const v=document.getElementById('v-deste');if(!v||!CAT)return;
  if(!CAT.cards.some(isMg)){v.innerHTML='';v.append(el('div',{class:'card muted',text:'Magic kartları yükleniyor…'}));try{await mgYukle();}catch(e){}if(!CAT.cards.some(isMg))return;}
  const benim=++CIZILIYOR;await detaylar([...Object.keys(MD.ana),...Object.keys(MD.yan),...(MD.komutan?[MD.komutan]:[])]);if(benim!==CIZILIYOR)return;taslak();
  const D=durum(),B=BICIM[MD.bicim];
  const adI=el('input',{value:MD.ad,maxlength:60,style:'flex:1;min-width:160px;font-weight:700'});adI.addEventListener('input',()=>{MD.ad=adI.value||'Magic destesi';taslak();});
  const bicimS=el('select',{},...Object.entries(BICIM).map(([k,b])=>el('option',{value:k},b.ad)));bicimS.value=MD.bicim;bicimS.addEventListener('change',()=>{MD.bicim=bicimS.value;ciz();});
  const grup={};D.ana.forEach(x=>{const t=anaTur(kart(x[0]));(grup[t]=grup[t]||[]).push(x);});
  const mv=id=>{const d=DET[id];return manaDegeri(d&&d.y&&d.y[0]&&d.y[0].m);};
  const panel=el('div',{class:'card k2panel mdpanel'},
    el('div',{style:'display:flex;gap:8px;align-items:center;flex-wrap:wrap'},adI,bicimS),
    el('div',{class:'k2durum '+(D.hatalar.length?'kotu':'iyi'),text:D.hatalar.length?'⚠️ Deste kurallara uymuyor':'✅ Deste kurallara uygun'}),
    D.hatalar.length?el('ul',{class:'small k2hata'},...D.hatalar.map(h=>el('li',{text:h}))):null,
    el('div',{class:'muted small',text:'Biçimlerin yasaklı kart listeleri denetlenmez; turnuvadan önce resmi listeye bak.'}),
    el('div',{class:'mtiles',style:'margin:10px 0'},
      el('div',{class:'mtile'},el('div',{class:'muted small',text:MD.bicim==='commander'?'Kart (komutan dahil)':'Ana deste'}),el('div',{class:'big',text:D.anaSay+(MD.bicim==='commander'?' / 100':' / '+B.min+'+')})),
      MD.bicim!=='commander'?el('div',{class:'mtile'},el('div',{class:'muted small',text:'Yan deste'}),el('div',{class:'big',text:D.yanSay+(MD.bicim==='serbest'?' / 15':'')})):null,
      el('div',{class:'mtile'},el('div',{class:'muted small',text:'Destenin piyasa değeri'}),el('div',{class:'big',text:tl(D.deger)}),D.fiyatsiz?el('div',{class:'muted small',text:D.fiyatsiz+' kartın fiyatı yok'}):null),
      USER?el('div',{class:'mtile'},el('div',{class:'muted small',text:'Koleksiyonunda eksik'}),el('div',{class:'big',text:D.eksikSay+' kart'}),el('div',{class:'muted small',text:'≈ '+tl(D.eksikDeger)})):null),
    D.anaSay?el('div',{class:'mdgraf'},el('div',{},el('b',{class:'small',text:'Mana eğrisi (araziler hariç)'}),egriCiz(D)),el('div',{style:'flex:1;min-width:160px'},el('b',{class:'small',text:'Renk dağılımı'}),renkCiz(D),
      el('div',{class:'muted small',style:'margin-top:4px',text:Object.entries(D.renk).sort((a,b)=>b[1]-a[1]).map(([h,n])=>RENK_AD[h]+' '+n).join(' · ')}))):null,
    MD.bicim==='commander'?el('div',{},el('b',{},'Komutan'),D.kom?el('div',{class:'mdkom'},el('div',{class:'mdkomr',onclick:()=>openCard(BYID[D.kom])},cardImg(kart(D.kom),false)),el('div',{},el('div',{style:'font-weight:700',text:adi(kart(D.kom))}),
      el('div',{class:'small muted',text:'Renk kimliği: '+([...kimlik(kart(D.kom),DET[D.kom])].map(h=>RENK_AD[h]).join(', ')||'Renksiz')}),el('button',{class:'btn sec',style:'margin-top:6px;padding:6px 10px',onclick:()=>{MD.komutan=null;ciz(true);}},'Komutanı kaldır'))):el('div',{class:'k2legbos',text:'Soldan bir efsanevi yaratık seçip "👑 Komutan yap"a bas'})):null,
    ...[...TURLER,'Diger'].map(t=>{const l=(grup[t]||[]).sort((a,b)=>mv(a[0])-mv(b[0])||adi(kart(a[0])).localeCompare(adi(kart(b[0]))));if(!l.length)return null;
      return el('div',{},el('b',{text:`${TUR_TR[t]} (${l.reduce((s,[,n])=>s+n,0)})`}),...l.map(([id,n])=>satir(id,n,false,D)));}),
    D.yan.length?el('div',{},el('b',{text:`Yan deste (${D.yanSay})`}),...D.yan.map(([id,n])=>satir(id,n,true,D))):null,
    el('div',{style:'display:flex;gap:8px;flex-wrap:wrap;margin-top:12px'},
      el('button',{class:'btn',onclick:kaydet},'💾 Kaydet'),
      el('button',{class:'btn sec',onclick:async()=>{const u=location.origin+'/?mdeste='+kodla();try{if(navigator.share)await navigator.share({title:MD.ad,text:'KartBorsa\'da kurduğum Magic destesi',url:u});else{await navigator.clipboard.writeText(u);toast('Deste bağlantısı kopyalandı');}}catch(e){try{await navigator.clipboard.writeText(u);toast('Deste bağlantısı kopyalandı');}catch(e2){prompt('Bağlantıyı kopyala:',u);}}}},'🔗 Paylaş'),
      el('button',{class:'btn sec',onclick:()=>{const t=listeMetni(D);navigator.clipboard.writeText(t).then(()=>toast('Liste kopyalandı (Arena/MTGO biçimi)'),()=>prompt('Listeyi kopyala:',t));}},'📋 Listeyi kopyala'),
      el('button',{class:'btn sec',onclick:iceAktarPencere},'📥 Liste yapıştır'),
      el('button',{class:'btn sec',onclick:()=>{Object.assign(MD,{ad:'Yeni Magic destesi',komutan:null,ana:{},yan:{},id:null,yid:null});ciz();}},'Yeni deste')));
  if(sadecePanel&&v.querySelector('.mdpanel')){v.querySelector('.mdpanel').replaceWith(panel);if(MD._listele)MD._listele();return;}
  v.innerHTML='';
  const q=el('input',{placeholder:'Kart ara: ad ya da tür (Lightning Bolt, Dragon, Equipment…)',value:MD.q});
  const renkS=el('select',{},el('option',{value:''},'Tüm renkler'),...['Beyaz','Mavi','Siyah','Kırmızı','Yeşil','Renksiz','Çok renkli'].map(x=>el('option',{value:x},x)));renkS.value=MD.renk;
  const turS=el('select',{},el('option',{value:''},'Tüm türler'),...TURLER.map(x=>el('option',{value:x},x)),el('option',{value:'Legendary Creature'},'Efsanevi yaratık (komutan)'));turS.value=MD.tur;
  const bende=el('label',{class:'chk',style:'margin:0'},el('input',{type:'checkbox'}),' Sadece koleksiyonumdakiler');bende.querySelector('input').checked=MD.sadeceBende;
  const sonuc=el('div',{class:'k2dgrid'}),bilgi=el('div',{class:'muted small',style:'margin:6px 0'});
  const listele=()=>{MD.q=q.value;MD.renk=renkS.value;MD.tur=turS.value;MD.sadeceBende=bende.querySelector('input').checked;const qq=norm(q.value);sonuc.innerHTML='';
    if(!qq&&!MD.renk&&!MD.tur&&!MD.sadeceBende){bilgi.textContent='Aramak için kart adı yaz ya da renk/tür seç. Aynı kartın tüm baskıları tek kutuda; baskıyı destede değiştirebilirsin.';return;}
    const sahip=new Set(MD.sadeceBende&&typeof COLL!=='undefined'&&COLL?COLL.map(x=>x.card_id):[]);const gor=new Map();
    for(let i=0;i<CAT.cards.length;i++){const c=CAT.cards[i];if(!isMg(c)||c[4]==='Token'||c[4]==='Art Card'||c[4]==='Card'||c[4]==='Emblem')continue;
      if(MD.renk&&!(MD.renk==='Renksiz'?c[5]==='Renksiz':tip(c).includes(MD.renk)))continue;if(MD.tur&&!(MD.tur==='Legendary Creature'?/\bLegendary\b/.test(tip(c))&&/\bCreature\b/.test(tip(c)):new RegExp('\\b'+MD.tur+'\\b').test(tip(c))))continue;
      if(qq&&!anahtar(i).includes(qq))continue;if(MD.sadeceBende&&!sahip.has(c[14]))continue;
      const a=adi(c),o=gor.get(a);const v=fiyat(c[14]);
      if(!o){if(gor.size>=90)continue;gor.set(a,{i,v,n:1});}else{o.n++;if(o.v==null||(v!=null&&v<o.v)){o.i=i;o.v=v;}}}
    bilgi.textContent=gor.size?`${gor.size} kart${gor.size>=90?' (ilk 90; aramayı daralt)':''} · her kartta en ucuz baskı gösterilir`:'Sonuç yok.';
    gor.forEach(({i,v,n})=>{const c=CAT.cards[i],id=c[14],varA=MD.ana[id]||0;
      sonuc.append(el('div',{class:'k2dkart mdk'},el('div',{style:'cursor:pointer',onclick:()=>openCard(i)},cardImg(c,false)),el('div',{class:'small',style:'font-weight:600;margin-top:4px',text:adi(c)}),
        el('div',{class:'muted small',text:(v!=null?tl(v):'fiyat yok')+(n>1?' · '+n+' baskı':'')}),
        el('div',{style:'display:flex;gap:4px;flex-wrap:wrap;margin-top:4px'},el('button',{class:'btn',style:'padding:5px 9px;font-size:13px',onclick:()=>ekle(id,false)},'+ Deste'+(varA?' ('+varA+')':'')),
          MD.bicim!=='commander'?el('button',{class:'btn sec',style:'padding:5px 9px;font-size:13px',onclick:()=>ekle(id,true)},'+ Yan'):null,
          MD.bicim==='commander'&&/\bLegendary\b/.test(tip(c))&&/\bCreature\b/.test(tip(c))?el('button',{class:'btn sec',style:'padding:5px 9px;font-size:13px',onclick:()=>{MD.komutan=id;delete MD.ana[id];ciz(true);toast(adi(c)+' komutan yapıldı 👑');}},'👑 Komutan yap'):null)));});};
  MD._listele=listele;let zt=0;q.addEventListener('input',()=>{clearTimeout(zt);zt=setTimeout(listele,250);});[renkS,turS,bende.querySelector('input')].forEach(x=>x.addEventListener('change',listele));
  v.append(el('div',{class:'hero'},el('div',{},el('h2',{},'🧙 Magic deste kurucu'),el('div',{class:'muted small',text:'Serbest (60+), Commander (100) ve Limited (40+) desteleri kur: kurallar, mana eğrisi, renk dağılımı, destenin değeri ve koleksiyonunda eksikler anında görünür.'}))),
    el('div',{class:'mdkayit',style:'display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-bottom:10px'}),
    el('div',{class:'k2dkur'},el('div',{class:'card'},el('div',{class:'row',style:'margin-bottom:8px'},q,renkS,turS,bende),bilgi,sonuc),panel));
  listele();kayitlar();}
function iceAktarPencere(){const b=document.getElementById('modalBody');b.innerHTML='';
  const ta=el('textarea',{rows:12,style:'width:100%;font-family:monospace',placeholder:'4 Lightning Bolt\n4 Monastery Swiftspear\n20 Mountain\n\nSideboard\n2 Pyroblast'});
  const msg=el('div',{class:'small muted'});
  b.append(el('h3',{text:'📥 Deste listesi yapıştır'}),el('div',{class:'muted small',style:'margin-bottom:8px',text:'Arena, MTGO ya da Moxfield\'den kopyaladığın listeyi yapıştır. "4 Kart Adı" satırları; "Sideboard" ve "Commander" başlıkları da tanınır. Baskı yazılmamışsa en ucuz baskı seçilir.'}),ta,msg,
    el('div',{style:'display:flex;gap:8px;margin-top:10px'},el('button',{class:'btn',onclick:async()=>{msg.textContent='Kartlar aranıyor…';const r=await iceAktar(ta.value);
      const top=Object.values(r.ana).reduce((a,b)=>a+b,0)+Object.values(r.yan).reduce((a,b)=>a+b,0)+(r.kom?1:0);if(!top){msg.textContent='Listede tanınan kart bulunamadı.';return;}
      MD.ana=r.ana;MD.yan=r.yan;if(r.kom){MD.komutan=r.kom;MD.bicim='commander';}MD.id=null;MD.yid=null;closeModal();ciz();
      toast(top+' kart eklendi'+(r.bulunmayan.length?' · '+r.bulunmayan.length+' kart bulunamadı':''));if(r.bulunmayan.length)setTimeout(()=>alert('Bulunamayan kartlar:\n'+r.bulunmayan.slice(0,40).join('\n')),300);}},'Desteye aktar'),
      el('button',{class:'btn sec',onclick:closeModal},'Vazgeç')));document.getElementById('modal').classList.add('on');}
window.mgDesteCiz=()=>ciz();
/* kart detayına "Desteye ekle" düğmesi (Magic kartlarında) */
const _ocn=window.openCardNow;
if(typeof _ocn==='function')window.openCardNow=function(i){const r=_ocn.apply(this,arguments);try{const c=CAT.cards[i];if(isMg(c)&&c[4]!=='Token'){const b=document.getElementById('modalBody');const yer=b&&(b.querySelector('.buybox')||b.querySelector('dl'));
  if(yer&&!b.querySelector('.mdekle'))yer.after(el('div',{class:'mdekle',style:'display:flex;gap:6px;flex-wrap:wrap;margin:10px 0'},el('button',{class:'btn sec',onclick:()=>{ekle(c[14],false);toast(adi(c)+' desteye eklendi ('+MD.ad+')');}},'🧙 Desteye ekle'),
    /\bLegendary\b/.test(tip(c))&&/\bCreature\b/.test(tip(c))?el('button',{class:'btn sec',onclick:()=>{MD.bicim='commander';MD.komutan=c[14];delete MD.ana[c[14]];taslak();toast(adi(c)+' komutan yapıldı 👑');}},'👑 Commander destesi kur'):null,
    el('button',{class:'btn sec',onclick:()=>{closeModal();go('deste');}},'Desteye git →')));}}catch(e){}return r;};
/* ?mdeste= bağlantısı */
(async()=>{try{const p=new URLSearchParams(location.search).get('mdeste');if(!p)return;try{history.replaceState(history.state,'',location.pathname);}catch(e){}
  for(let i=0;i<80&&(typeof CAT==='undefined'||!CAT);i++)await new Promise(r=>setTimeout(r,250));
  const b=document.querySelector('#oyunSec button[data-o="mg"]');if(DIL!=='mg'&&b)b.click();await mgYukle();for(let i=0;i<60&&!CAT.cards.some(isMg);i++)await new Promise(r=>setTimeout(r,250));
  coz(p);go('deste');}catch(e){console.warn('mdeste',e);}})();
})();
