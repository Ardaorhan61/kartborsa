"""KartBorsa: Google ve paylaşım için statik sayfalar (yayın sırasında çalışır).

Üretilenler (_site içine):
  kart/<id>/index.html   her kart için sayfa (başlık, resim, set, numara, nadirlik, güncel TL fiyatı)
  set/<id>/index.html    her set için sayfa (tüm kartlar ve fiyatları)
  setler/index.html      tüm setler
  sitemap.xml (+ sitemap-*.xml), robots.txt, 404.html
  og.png, icon-192.png, icon-512.png, apple-touch-icon.png, favicon.png, manifest.webmanifest

Kullanım: python3 seo.py _site
Enerji kartları (sitede gizli) için sayfa üretilmez. Fiyat: fiyat/ozet.json + fiyat/kur.json (sitedeki ile aynı hesap).
"""
import datetime, html, json, os, re, sys, urllib.parse

SITE = sys.argv[1] if len(sys.argv) > 1 else "_site"
ALAN = "https://www.kartborsa.com"
BUGUN = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).date().isoformat()
GUVENLI_ID = re.compile(r"^[A-Za-z0-9._\-]+$")


def oku(yol):
    try:
        with open(os.path.join(SITE, yol), encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print("okunamadı:", yol, e)
        return None


def e(x):
    return html.escape(str(x if x is not None else ""), quote=True)


def tl(n):
    if n is None:
        return None
    if n < 10:
        s = f"{n:,.2f}"
    else:
        s = f"{round(n):,}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".") + " ₺"


def genislet(s, pfx):
    if not s:
        return s
    m = re.match(r"^~(\d)(.*)$", s)
    if m and int(m.group(1)) < len(pfx):
        return pfx[int(m.group(1))] + m.group(2)
    return s


def resim(c, setid, pfx, buyuk=True):
    s = genislet(c[13] if len(c) > 13 else "", pfx)
    cid = str(c[14])
    if not s:
        if cid.startswith("ja-"):
            return None
        s = f"https://images.pokemontcg.io/{setid}/{c[2]}.png"
    if "tcgplayer-cdn.tcgplayer.com" in s:
        b = re.sub(r"_(in_\d+x\d+|\d+w)\.jpg$", "", s)
        return b + ("_in_1000x1000.jpg" if buyuk else "_400w.jpg")
    if "assets.tcgdex.net" in s:
        return re.sub(r"/low\.webp$", "/high.webp", s) if buyuk else s
    if "pokellector.com" in s:
        return s
    if "scrydex.com" in s:
        return re.sub(r"/small$", "/large" if buyuk else "/medium", s)
    if s.startswith("img/"):
        return ALAN + "/" + s
    return s.replace(".png", "_hires.png") if buyuk else s


def wsrv(u, w):
    if not u:
        return None
    return "https://wsrv.nl/?url=" + urllib.parse.quote(u, safe="") + f"&w={w}&output=jpg&q=82"


CSS = """*{box-sizing:border-box}body{margin:0;background:#0f1220;color:#eef0fa;font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif}
a{color:#ffcb3d}header,main,footer{max-width:980px;margin:0 auto;padding:14px 18px}
header{display:flex;align-items:center;gap:10px}header a{text-decoration:none;color:#eef0fa;font-weight:800;font-size:20px;display:flex;gap:10px;align-items:center}
.dot{width:32px;height:32px;border-radius:9px;background:#ffcb3d;color:#1a1300;display:grid;place-items:center;font-weight:900}
.yol{font-size:14px;color:#9aa1c3}.yol a{color:#9aa1c3}
h1{font-size:26px;line-height:1.25;margin:6px 0 14px}.kart{display:flex;gap:24px;flex-wrap:wrap}
.kart img{width:300px;max-width:100%;border-radius:14px;background:#1a1f35}.bilgi{flex:1;min-width:260px}
table{border-collapse:collapse;width:100%}td{padding:7px 4px;border-bottom:1px solid #262c48;vertical-align:top}td:first-child{color:#9aa1c3;width:40%}
.fiyat{background:#1a1f35;border-radius:14px;padding:14px 16px;margin:16px 0}.fiyat b{font-size:28px;color:#ffcb3d}
.btn{display:inline-block;background:#ffcb3d;color:#1a1300;font-weight:800;padding:12px 18px;border-radius:12px;text-decoration:none;margin:4px 6px 4px 0}
.btn.ikinci{background:#262c48;color:#eef0fa}.liste{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px;padding:0;list-style:none}
.liste li{background:#1a1f35;border-radius:12px;padding:8px}.liste img{width:100%;border-radius:8px;aspect-ratio:63/88;object-fit:cover;background:#262c48}
.liste a{text-decoration:none;color:#eef0fa;font-size:14px}.k{color:#9aa1c3;font-size:13px}.s{columns:2 280px}.s a{display:block;padding:3px 0}
footer{color:#9aa1c3;font-size:14px;border-top:1px solid #262c48;margin-top:30px}"""


def sayfa(baslik, aciklama, yol, govde, gorsel=None, ld=None):
    url = ALAN + yol
    g = gorsel or ALAN + "/og.png"
    return f"""<!DOCTYPE html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(baslik)}</title><meta name="description" content="{e(aciklama)}"><link rel="canonical" href="{e(url)}">
<meta property="og:type" content="website"><meta property="og:site_name" content="KartBorsa"><meta property="og:locale" content="tr_TR">
<meta property="og:title" content="{e(baslik)}"><meta property="og:description" content="{e(aciklama)}"><meta property="og:url" content="{e(url)}"><meta property="og:image" content="{e(g)}">
<meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#0f1220">
<link rel="icon" href="/favicon.png"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="stylesheet" href="/s.css">
{('<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + '</script>') if ld else ''}
</head><body><header><a href="/"><span class="dot">K</span>KartBorsa</a></header><main>{govde}</main>
<footer>KartBorsa — Pokémon ve Cyberpunk TCG kart fiyatları, ilanlar ve koleksiyon takibi. <a href="/setler/">Tüm setler</a> · <a href="/gizlilik.html">Gizlilik</a><br>
Fiyatlar TCGplayer ve Cardmarket piyasa verilerinden günlük kurla TL'ye çevrilir; bilgi amaçlıdır.<br>
Pokémon ve kart görselleri The Pokémon Company, Nintendo, Creatures ve GAME FREAK'e; Cyberpunk ve kart görselleri CD PROJEKT RED ve WeirdCo'ya aittir. Bu site resmi değildir.</footer></body></html>"""


def yaz(yol, icerik):
    tam = os.path.join(SITE, yol.strip("/"), "index.html") if yol.endswith("/") else os.path.join(SITE, yol.lstrip("/"))
    os.makedirs(os.path.dirname(tam), exist_ok=True)
    with open(tam, "w", encoding="utf-8") as f:
        f.write(icerik)


def breadcrumb(ogeler):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": ad, "item": ALAN + yol} for i, (ad, yol) in enumerate(ogeler)]}


oz = (oku("fiyat/ozet.json") or {}).get("c", {})
kur = oku("fiyat/kur.json") or {}
USD, EUR = kur.get("USD"), kur.get("EUR")


def fiyat(cid):
    o = oz.get(cid)
    if not o or not USD:
        return None, None
    if isinstance(o[0], (int, float)) and o[0] > 0:
        return o[0] * USD, "TCGplayer"
    if len(o) > 1 and isinstance(o[1], (int, float)) and o[1] > 0 and EUR:
        return o[1] * EUR, "Cardmarket"
    return None, None


OYUN = {"en": ("Pokémon TCG", "İngilizce"), "ja": ("Pokémon TCG", "Japonca"), "cp": ("Cyberpunk TCG", "İngilizce")}
url_listesi = {"set": [], "en": [], "ja": [], "cp": []}
setler_ozet = []
toplam = 0

for dosya, dil in (("cards.json", "en"), ("cards_ja.json", "ja"), ("cards_cp.json", "cp")):
    kat = oku(dosya)
    if not kat:
        continue
    pfx = kat.get("pfx", [])
    sets = kat["sets"]
    kartlar_set = {}
    for c in kat["cards"]:
        if dil != "cp" and len(c) > 4 and c[4] == "Energy":
            continue
        cid = str(c[14])
        if not GUVENLI_ID.match(cid):
            continue
        kartlar_set.setdefault(c[1], []).append(c)
    oyun, lisan = OYUN[dil]
    for si, kartlar in kartlar_set.items():
        s = sets[si]
        sid, sad, seri, tarih, sayi = s[0], s[1], s[2], s[3], s[4]
        if not GUVENLI_ID.match(str(sid)):
            continue
        set_yol = f"/set/{sid}/"
        logo = genislet(s[5] if len(s) > 5 else "", pfx)
        if logo and logo.startswith("img/"):
            logo = ALAN + "/" + logo
        kartlar.sort(key=lambda c: (int(re.sub(r"\D", "", str(c[2])) or 0), str(c[2])))
        lis, deger = [], 0
        for i, c in enumerate(kartlar):
            cid = str(c[14])
            ad = c[0]
            k_yol = f"/kart/{cid}/"
            v, kaynak = fiyat(cid)
            if v:
                deger += v
            gorsel = resim(c, sid, pfx, True)
            kucuk = wsrv(resim(c, sid, pfx, False), 220)
            lis.append(f'<li><a href="{k_yol}">{f"<img src={chr(34)}{e(kucuk)}{chr(34)} alt={chr(34)}{e(ad)}{chr(34)} loading=lazy>" if kucuk else ""}'
                       f'<div>{e(ad)}</div><div class="k">#{e(c[2])}{" · " + e(tl(v)) if v else ""}</div></a></li>')
            onceki = kartlar[i - 1] if i > 0 else None
            sonraki = kartlar[i + 1] if i + 1 < len(kartlar) else None
            nadir = c[3] if len(c) > 3 else ""
            baslik = f"{ad} – {sad} #{c[2]} Fiyatı | KartBorsa"
            fiyat_metni = f"Güncel piyasa fiyatı: {tl(v)} ({kaynak})." if v else "Piyasa fiyatı henüz yok."
            aciklama = f"{ad} ({oyun}, {lisan}, {sad} seti, #{c[2]}{', ' + nadir if nadir else ''}). {fiyat_metni} Fiyat geçmişi, satış ilanları ve koleksiyon takibi KartBorsa'da."
            satirlar = [("Oyun", f"{oyun} ({lisan})"), ("Set", f'<a href="{set_yol}">{e(sad)}</a>'), ("Seri", e(seri)),
                        ("Kart no", f"{e(c[2])}{' / ' + e(sayi) if sayi else ''}"), ("Nadirlik", e(nadir)),
                        ("Tür", e(" · ".join(x for x in [c[4] if len(c) > 4 else "", c[5] if len(c) > 5 else "", c[7] if len(c) > 7 and isinstance(c[7], str) else ""] if x))),
                        ("Çizer", e(c[8] if len(c) > 8 and isinstance(c[8], str) else "")), ("Çıkış", e(tarih))]
            tablo = "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in satirlar if b)
            gezinme = " ".join(x for x in [
                f'<a href="/kart/{onceki[14]}/">‹ {e(onceki[0])}</a>' if onceki else "",
                f'<a href="/kart/{sonraki[14]}/">{e(sonraki[0])} ›</a>' if sonraki else ""] if x)
            govde = (f'<div class="yol"><a href="/">Ana sayfa</a> › <a href="/setler/">Setler</a> › <a href="{set_yol}">{e(sad)}</a> › {e(ad)}</div>'
                     f'<h1>{e(ad)} <span class="k">{e(sad)} #{e(c[2])}</span></h1><div class="kart">'
                     + (f'<img src="{e(wsrv(gorsel, 600))}" alt="{e(ad)} – {e(sad)}" width="300">' if gorsel else "")
                     + f'<div class="bilgi"><div class="fiyat">{"<div class=k>Güncel piyasa değeri</div><b>" + e(tl(v)) + "</b><div class=k>Kaynak: " + kaynak + " · " + BUGUN + "</div>" if v else "<div class=k>Bu kartın piyasa fiyatı henüz yok.</div>"}</div>'
                     f'<a class="btn" href="/?kart={urllib.parse.quote(cid)}">Fiyat geçmişi ve ilanlar</a>'
                     f'<a class="btn ikinci" href="/?kart={urllib.parse.quote(cid)}">Koleksiyona ekle / sat</a>'
                     f'<table>{tablo}</table><p>{gezinme}</p></div></div>')
            ld = breadcrumb([("Ana sayfa", "/"), ("Setler", "/setler/"), (sad, set_yol), (ad, k_yol)])
            yaz(k_yol, sayfa(baslik, aciklama, k_yol, govde, wsrv(gorsel, 600) if gorsel else None, ld))
            url_listesi[dil].append(k_yol)
            toplam += 1
        s_baslik = f"{sad} Kart Listesi ve Fiyatları ({oyun}, {lisan}) | KartBorsa"
        s_aciklama = f"{sad} setindeki {len(kartlar)} kartın listesi ve güncel TL fiyatları ({oyun}, {lisan}, {seri}, {tarih}). Set değeri, eksik kart takibi ve satış ilanları KartBorsa'da."
        s_govde = (f'<div class="yol"><a href="/">Ana sayfa</a> › <a href="/setler/">Setler</a> › {e(sad)}</div>'
                   + (f'<img src="{e(wsrv(logo, 400))}" alt="{e(sad)} logosu" style="max-width:260px;max-height:110px;margin:6px 0">' if logo else "")
                   + f'<h1>{e(sad)} kart listesi ve fiyatları</h1><p class="k">{e(oyun)} · {e(lisan)} · {e(seri)} · {e(tarih)} · {len(kartlar)} kart'
                   + (f" · fiyatı bilinen kartların toplam değeri {e(tl(deger))}" if deger else "") + '</p>'
                   f'<ul class="liste">{"".join(lis)}</ul>')
        yaz(set_yol, sayfa(s_baslik, s_aciklama, set_yol, s_govde, wsrv(logo, 1200) if logo else None,
                           breadcrumb([("Ana sayfa", "/"), ("Setler", "/setler/"), (sad, set_yol)])))
        url_listesi["set"].append(set_yol)
        setler_ozet.append((dil, seri, tarih, sid, sad, len(kartlar)))

# tüm setler
bolumler = []
for dil, baslik in (("en", "Pokémon (İngilizce)"), ("ja", "Pokémon (Japonca)"), ("cp", "Cyberpunk TCG")):
    ss = sorted([x for x in setler_ozet if x[0] == dil], key=lambda x: x[2], reverse=True)
    if ss:
        bolumler.append(f"<h2>{baslik}</h2><div class='s'>" + "".join(
            f'<a href="/set/{x[3]}/">{e(x[4])} <span class="k">({x[5]} kart, {e(x[2][:4])})</span></a>' for x in ss) + "</div>")
yaz("/setler/", sayfa("Tüm Pokémon ve Cyberpunk TCG Setleri ve Kart Fiyatları | KartBorsa",
                      f"{len(setler_ozet)} Pokémon (İngilizce ve Japonca) ve Cyberpunk TCG setinin kart listeleri ve güncel TL fiyatları.",
                      "/setler/", '<h1>Tüm setler</h1>' + "".join(bolumler)))
url_listesi["set"].insert(0, "/setler/")

with open(os.path.join(SITE, "s.css"), "w", encoding="utf-8") as f:
    f.write(CSS)

# site haritası
parcalar = []
for ad, yollar in url_listesi.items():
    for i in range(0, len(yollar), 45000):
        dosya = f"sitemap-{ad}-{i // 45000 + 1}.xml"
        with open(os.path.join(SITE, dosya), "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            if ad == "set" and i == 0:
                f.write(f"<url><loc>{ALAN}/</loc><lastmod>{BUGUN}</lastmod></url>\n")
            for y in yollar[i:i + 45000]:
                f.write(f"<url><loc>{ALAN}{urllib.parse.quote(y)}</loc><lastmod>{BUGUN}</lastmod></url>\n")
            f.write("</urlset>\n")
        parcalar.append(dosya)
with open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    for p in parcalar:
        f.write(f"<sitemap><loc>{ALAN}/{p}</loc><lastmod>{BUGUN}</lastmod></sitemap>\n")
    f.write("</sitemapindex>\n")
with open(os.path.join(SITE, "robots.txt"), "w", encoding="utf-8") as f:
    f.write(f"User-agent: *\nAllow: /\nDisallow: /tara/\nDisallow: /fiyat/\n\nSitemap: {ALAN}/sitemap.xml\n")
yaz("/404.html", sayfa("Sayfa bulunamadı | KartBorsa", "Aradığın sayfa bulunamadı.", "/404.html",
                       '<h1>Sayfa bulunamadı</h1><p>Aradığın sayfa taşınmış ya da silinmiş olabilir.</p><a class="btn" href="/">Ana sayfaya dön</a> <a class="btn ikinci" href="/setler/">Tüm setler</a>'))

# uygulama gibi kurulum (ana ekrana ekle)
with open(os.path.join(SITE, "manifest.webmanifest"), "w", encoding="utf-8") as f:
    json.dump({"name": "KartBorsa", "short_name": "KartBorsa", "lang": "tr", "start_url": "/", "scope": "/", "display": "standalone",
               "background_color": "#0f1220", "theme_color": "#0f1220",
               "description": "Pokémon ve Cyberpunk TCG kart fiyatları, ilanlar ve koleksiyon takibi",
               "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
                         {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
                         {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}, f, ensure_ascii=False)

# görseller
try:
    from PIL import Image, ImageDraw, ImageFont

    def yazi_tipi(boy, kalin=True):
        for y in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if kalin else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                  "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]:
            if os.path.exists(y):
                return ImageFont.truetype(y, boy)
        return ImageFont.load_default()

    def ikon(boy, ad):
        im = Image.new("RGB", (boy, boy), "#0f1220")
        d = ImageDraw.Draw(im)
        p = boy // 8
        d.rounded_rectangle([p, p, boy - p, boy - p], radius=boy // 5, fill="#ffcb3d")
        f = yazi_tipi(int(boy * 0.5))
        d.text((boy / 2, boy / 2), "K", fill="#1a1300", font=f, anchor="mm")
        im.save(os.path.join(SITE, ad))

    ikon(192, "icon-192.png"); ikon(512, "icon-512.png"); ikon(180, "apple-touch-icon.png"); ikon(64, "favicon.png")
    og = Image.new("RGB", (1200, 630), "#0f1220")
    d = ImageDraw.Draw(og)
    for i in range(0, 630, 3):
        d.line([(0, i), (1200, i)], fill=(15 + i // 30, 18 + i // 40, 32 + i // 14))
    d.rounded_rectangle([90, 170, 250, 330], radius=34, fill="#ffcb3d")
    d.text((170, 250), "K", fill="#1a1300", font=yazi_tipi(110), anchor="mm")
    d.text((285, 250), "KartBorsa", fill="#eef0fa", font=yazi_tipi(104), anchor="lm")
    d.text((92, 400), "Pokémon ve Cyberpunk TCG kart fiyatları", fill="#ffcb3d", font=yazi_tipi(44))
    d.text((92, 462), "Fiyat geçmişi · İlanlar · Koleksiyon · Kart tarama", fill="#c9cde6", font=yazi_tipi(34, False))
    d.text((92, 540), "www.kartborsa.com", fill="#9aa1c3", font=yazi_tipi(30, False))
    og.save(os.path.join(SITE, "og.png"), optimize=True)
    print("görseller hazır")
except Exception as ex:
    print("görseller üretilemedi:", ex)

print(f"SEO: {toplam} kart sayfası, {len(setler_ozet)} set sayfası, {len(parcalar)} site haritası parçası")
