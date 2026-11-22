"""Cyberpunk TCG kataloğu ve günlük fiyatları.

Kaynak: tcgcsv.com — TCGplayer'ın günlük ürün ve fiyat dökümü (ücretsiz), kategori 92 = Cyberpunk TCG.
Tüm setler (ana set, Beta baskı, başlangıç desteleri, box topper'lar, promolar, etkinlik kartları) her çalışmada
yeniden okunur; TCGplayer'a yeni set ya da kart eklenince kendiliğinden siteye gelir. Kapalı ürünler (booster, kutu)
katalogda yer almaz (kart numarası olmayan ürünler).

Kullanım: python3 cyberpunk.py <veri_klasörü> <site_klasörü (_site)>
  yazar : <site>/cards_cp.json (sitenin kullandığı kısa biçim)
          <veri>/cyberpunk/cards_cp.json (tam biçim; kart tarama izleri için), <veri>/cyberpunk/gecmis.json (fiyat geçmişi)
          <veri>/set/cp-*.json, <veri>/ozet.json ve aynılarını <site>/fiyat/ altına kopyalar
Kart kimliği: cp-<TCGplayer grup no>-<TCGplayer ürün no> (değişmez; ilan ve koleksiyonlar buna bağlı).
"""
import json, os, re, sys, time, shutil, datetime, html, urllib.request
from concurrent.futures import ThreadPoolExecutor

VERI, SITE = sys.argv[1], sys.argv[2]
TODAY = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).strftime("%Y-%m-%d")
BASE = "https://tcgcsv.com/tcgplayer/92"
HEADERS = {"User-Agent": "KartBorsa-cyberpunk/1.0 (kartborsa.com)"}
KEEP_DAYS = 730
KLASOR = f"{VERI}/cyberpunk"
GECMIS_YOL = f"{KLASOR}/gecmis.json"
TAM_YOL = f"{KLASOR}/cards_cp.json"
RESIM = "https://tcgplayer-cdn.tcgplayer.com/product/"

# TCGplayer'daki kısaltma → nadirlik adı (Cyberpunk TCG set listesindeki adlar)
NADIR = {"C": "Common", "UC": "Uncommon", "U": "Uncommon", "R": "Rare", "E": "Epic", "NR": "Nova Rare", "S": "Secret",
         "IL": "Iconic Legend", "IO": "Iconic Other", "IS": "Iconic Secret"}
RENK = {"Blue": "Mavi", "Green": "Yeşil", "Red": "Kırmızı", "Yellow": "Sarı"}
ALT_TUR = {"Normal": "normal", "Foil": "foil"}
SIRA = ["normal", "foil"]


def fetch(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=60) as r:
                return json.loads(r.read())
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(4 * (i + 1))


def load(p, d):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return d


def ext(p):
    return {x.get("name"): x.get("value") for x in p.get("extendedData") or []}


def r2(x):
    return None if x is None else round(float(x), 2)


def metin(s):
    s = re.sub(r"<br\s*/?>", "\n", s or "", flags=re.I)
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def seri(ad):
    if "Beta" in ad:
        return "Set 1 · Welcome to Night City (Beta baskı)"
    if "Retail" in ad or ad.startswith("Set 1") or ad.startswith("Welcome to Night City"):
        return "Set 1 · Welcome to Night City"
    return "Promolar, etkinlik ve turnuva kartları"


NADIR_EK = re.compile(r"\s*\((Common|Uncommon|Rare|Epic|Secret|Nova Rare|NR|ILegend|IO|ISecret|Iconic[^)]*)\)\s*$", re.I)


def kart_adi(p):
    """TCGplayer adın sonuna nadirliği ekliyor ("... (Epic)"); nadirlik ayrı gösterildiği için çıkarılır."""
    return NADIR_EK.sub("", p.get("name") or "").strip()


def numara(n):
    m = re.match(r"\D*(\d+)(.*)", str(n or ""))
    return (int(m.group(1)), m.group(2)) if m else (99999, str(n or ""))


os.makedirs(KLASOR, exist_ok=True)
os.makedirs(f"{VERI}/set", exist_ok=True)

# ---- katalog ----
fiyat = {}
kapali = []   # kapalı ürünler (booster, kutu, deste): ad, set, resim, TCGplayer fiyatı
try:
    gruplar = fetch(f"{BASE}/groups")["results"]

    def grup_al(g):
        gid = g["groupId"]
        return g, fetch(f"{BASE}/{gid}/products")["results"], fetch(f"{BASE}/{gid}/prices")["results"]

    with ThreadPoolExecutor(max_workers=4) as ex:
        veri = list(ex.map(grup_al, gruplar))
    setler, kartlar = [], []
    sirali = sorted(veri, key=lambda v: ((v[0].get("publishedOn") or "9999")[:10], v[0]["name"]))
    for g, urunler, fiyatlar in sirali:
        gid = g["groupId"]
        for x in fiyatlar:
            fiyat.setdefault(x["productId"], []).append(x)
        for p in urunler:
            if ext(p).get("Number"):
                continue
            fy = {x.get("subTypeName"): x for x in fiyat.get(p["productId"], [])}
            x = fy.get("Normal") or next(iter(fy.values()), None)
            usd = r2((x.get("marketPrice") or x.get("midPrice"))) if x else None
            kapali.append({"a": p["name"], "s": g["name"], "g": gid, "i": p["productId"], "p": usd,
                           "d": r2(x.get("lowPrice")) if x else None, "u": p.get("url"),
                           "r": f"{RESIM}{p['productId']}_in_1000x1000.jpg" if p.get("imageCount", 1) else "",
                           "t": (g.get("publishedOn") or "")[:10]})
        kart_urun = [p for p in urunler if ext(p).get("Number")]
        if not kart_urun:
            continue
        si = len(setler)
        setler.append([f"cp-{gid}", g["name"], seri(g["name"]), (g.get("publishedOn") or "")[:10].replace("-", "/"),
                       len(kart_urun), "", "", "cp"])
        for p in sorted(kart_urun, key=lambda p: (numara(ext(p).get("Number")), p["name"])):
            e = ext(p)
            etiket = [t.strip() for t in (e.get("Tags") or "").split(";") if t.strip()]
            renk = RENK.get(e.get("Color"), e.get("Color") or "")
            sayi = lambda v: str(int(v)) if str(v or "").isdigit() else v
            ayr = {"r": renk, "m": sayi(e.get("Cost")), "ram": e.get("RAM"), "g": sayi(e.get("Power")),
                   "e": str(e.get("Eddies") or "").upper() == "TRUE", "t": etiket, "x": metin(e.get("Description")),
                   "u": p.get("url")}
            ara = " ".join([renk, e.get("Color") or "", e.get("CardType") or ""] + etiket)
            kartlar.append([kart_adi(p), si, str(e.get("Number")), NADIR.get(e.get("Rarity"), e.get("Rarity") or ""),
                            e.get("CardType") or "", renk, "", "", "", [], [], [], ara,
                            f"{RESIM}{p['productId']}_in_1000x1000.jpg" if p.get("imageCount", 1) else "",
                            f"cp-{gid}-{p['productId']}", "", "cp", ayr])
    kat = {"sets": setler, "cards": kartlar, "built": TODAY, "v": 1}
    json.dump(kat, open(TAM_YOL, "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
    kapali.sort(key=lambda k: (k["t"], k["s"], k["a"]), reverse=True)
    json.dump({"u": TODAY, "k": kapali}, open(f"{KLASOR}/kapali.json", "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
    print(f"Cyberpunk TCG: {len(setler)} set, {len(kartlar)} kart (TCGplayer)", flush=True)
except Exception as hata:
    kat = load(TAM_YOL, None)
    if not kat:
        raise SystemExit(f"tcgcsv.com okunamadı ve kayıtlı katalog yok: {hata}")
    print(f"tcgcsv.com okunamadı ({hata}); kayıtlı katalog kullanılıyor, fiyatlar güncellenmedi", flush=True)

# ---- kapalı ürünler (sitede Cyberpunk ana sayfasında ve İlan Ver'de) ----
kp = load(f"{KLASOR}/kapali.json", {"u": TODAY, "k": []})
json.dump(kp, open(f"{SITE}/cp_kapali.json", "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
print(f"Cyberpunk kapalı ürün: {len(kp['k'])} ({sum(1 for k in kp['k'] if k['p'])} fiyatlı)", flush=True)

# ---- sitenin kullandığı kısa biçim ----
site = json.loads(json.dumps(kat))
for c in site["cards"]:
    if isinstance(c[13], str) and c[13].startswith(RESIM):
        c[13] = "~0" + c[13][len(RESIM):]
site["pfx"] = [RESIM]
json.dump(site, open(f"{SITE}/cards_cp.json", "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)

# ---- fiyatlar ----
ozet = load(f"{VERI}/ozet.json", {"u": TODAY, "c": {}})
gecmis = load(GECMIS_YOL, {})
set_dosya = {}
yazilan = 0
if fiyat:
    for c in kat["cards"]:
        cid = c[14]
        pid = int(cid.rsplit("-", 1)[1])
        t = {}
        for x in fiyat.get(pid, []):
            tur = ALT_TUR.get(x.get("subTypeName"))
            if tur:
                t[tur] = [r2(x.get("lowPrice")), r2(x.get("midPrice")), r2(x.get("highPrice")), r2(x.get("marketPrice"))]
        ana = next((v for v in SIRA if v in t and (t[v][3] or t[v][1])), None)
        usd = (t[ana][3] or t[ana][1]) if ana else None
        sid = cid.rsplit("-", 1)[0]
        if sid not in set_dosya:
            set_dosya[sid] = {"u": TODAY, "c": {}}
        if usd is None:
            continue   # TCGplayer'da bugün fiyat yok: eski fiyatı güncelmiş gibi göstermeyelim
        h = [x for x in gecmis.get(cid, []) if x[0] != TODAY]
        h.append([TODAY, usd, None])
        h = h[-KEEP_DAYS:]
        gecmis[cid] = h
        set_dosya[sid]["c"][cid] = {"h": h, "tp": 1, "url": c[17].get("u"), "t": t, "v": ana, "tu": TODAY.replace("-", "/")}
        once = h[-2] if len(h) >= 2 else [None, None, None]
        ozet["c"][cid] = [usd, None, None, None, once[1], once[2], once[0]]
        yazilan += 1
    for sid, d in set_dosya.items():
        json.dump(d, open(f"{VERI}/set/{sid}.json", "w"), separators=(",", ":"))
    json.dump(ozet, open(f"{VERI}/ozet.json", "w"), separators=(",", ":"))
    json.dump(gecmis, open(GECMIS_YOL, "w"), separators=(",", ":"))

os.makedirs(f"{SITE}/fiyat/set", exist_ok=True)
if os.path.exists(f"{VERI}/ozet.json"):
    shutil.copy(f"{VERI}/ozet.json", f"{SITE}/fiyat/ozet.json")
for s in kat["sets"]:
    p = f"{VERI}/set/{s[0]}.json"
    if os.path.exists(p):
        shutil.copy(p, f"{SITE}/fiyat/set/{s[0]}.json")
fiyatsiz = sum(1 for c in kat["cards"] if not (ozet["c"].get(c[14]) or [None])[0])
print(f"Cyberpunk fiyat yazılan kart: {yazilan}; fiyatı olmayan: {fiyatsiz}", flush=True)
