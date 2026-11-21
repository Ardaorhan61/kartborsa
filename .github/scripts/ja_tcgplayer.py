"""Fiyatı olmayan Japonca kartlara TCGplayer (Pokémon Japan) fiyatı ekler.

Kaynak: tcgcsv.com — TCGplayer'ın günlük fiyat dökümü (ücretsiz), kategori 85 = Pokémon Japan.
Sadece başka kaynaktan (TCGdex / Pokellector) fiyatı GELMEYEN kartlara dokunur.
Eşleşme: aynı set + aynı numara + aynı ad; numara yoksa (eski setler) aynı ad (gerekirse aynı HP);
setteki o numarada tek kart varsa sadece numara. Belirsiz kalan kart doldurulmaz.

Kullanım: python3 ja_tcgplayer.py <veri_klasörü> <site_klasörü (_site)>
  okur  : <site>/cards_ja.json, <veri>/ozet.json
  yazar : <veri>/japonca/tcgplayer.json (kendi fiyat geçmişi), <veri>/set/ja-*.json, <veri>/ozet.json
          ve aynılarını <site>/fiyat/ altına kopyalar
"""
import json, os, re, sys, time, shutil, datetime, unicodedata, urllib.request
from concurrent.futures import ThreadPoolExecutor

VERI, SITE = sys.argv[1], sys.argv[2]
TODAY = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).strftime("%Y-%m-%d")
BASE = "https://tcgcsv.com/tcgplayer/85"
HEADERS = {"User-Agent": "KartBorsa-ja-fiyat/1.0 (kartborsa.com)"}
KEEP_DAYS = 730
GECMIS_YOL = f"{VERI}/japonca/tcgplayer.json"

# Ad eşleşmesiyle bulunamayan setler: site set kodu → TCGplayer grup adı
ELLE = {
    "ja-VEN1": "Vending Machine cards Series 1 (Blue)",
    "ja-VEN2": "Vending Machine cards Series 2 (Red)",
    "ja-VEN3": "Vending Machine cards Series 3 (Green)",
    "ja-DP1D": "DP1: Space-Time Creation",   # TCGplayer Elmas + İnci koleksiyonunu tek grupta tutuyor
    "ja-DP1P": "DP1: Space-Time Creation",
    "ja-DPP": "DP-P Promotional cards",
    "ja-PPP": "PPP Promotional cards",
    "ja-DPTP": "DPt-P Promotional cards",
    "ja-LP": "L-P: Legends Promos",
    "ja-L2": "L2: Revival Legends",
    "ja-MCD10": "CS1: Journey Partners Collection Sheet",
    "ja-BWP": "BW-P Promotional cards",
    "ja-KK": "Blastoise + Kyurem-EX Combo Deck",
    "ja-MG": "Mewtwo vs Genesect Deck Kit (Genesect)",
    "ja-pl144": "Mewtwo vs Genesect Deck Kit (Mewtwo)",
    "ja-XYP": "XY-P: XY Promos",
    "ja-XY8": "XY8-Bb: Blue Shock",
    "ja-XY11": "XY11-Bb: Fever-Burst Fighter",
    "ja-pl193": "XY11-Br: Cruel Traitor",
    "ja-SMP": "SM-P: Sun & Moon Promos",
    "ja-SM1p": "SM1+: Sun & Moon",
    "ja-SM2p": "SM2+: Facing a New Trial",
    "ja-SP": "S-P: Sword & Shield Promos",
    "ja-S8AP": "s8a-P: Promo Card Pack 25th Anniversary Edition",
    "ja-SI": "SI: Start Deck 100",
    "ja-SVLS": "SV: Ceruledge ex Stellar Tera Type Starter Set",
}
# Japonca ad ön eki → TCGplayer'daki İngilizce ön ek (eski setler)
ONEK = [("わるい", "Dark "), ("ダーク", "Dark "), ("暗い", "Dark "), ("ひかる", "Shining "), ("輝く", "Shining "),
        ("軽い", "Light "), ("ライト", "Light "), ("タケシの", "Brock's "), ("カスミの", "Misty's "),
        ("マチスの", "Lt. Surge's "), ("エリカの", "Erika's "), ("ナツメの", "Sabrina's "), ("キョウの", "Koga's "),
        ("カツラの", "Blaine's "), ("サカキの", "Giovanni's "), ("ロケット団の", "Rocket's "), ("R団の", "Rocket's ")]
# Aynı kartın ayrı ürün olarak listelenen parlak/özel baskıları
VARYANT = re.compile(r"\((mirror|reverse|master ?ball|pok[eé] ?ball|cosmos|cracked ice|non-holo|jumbo|oversized)[^)]*\)", re.I)
ALT_TUR = {"Normal": "normal", "Holofoil": "holofoil", "Reverse Holofoil": "reverseHolofoil",
           "1st Edition": "1stEdition", "1st Edition Holofoil": "1stEditionHolofoil",
           "Unlimited": "unlimited", "Unlimited Holofoil": "unlimitedHolofoil"}
SIRA = ["holofoil", "normal", "reverseHolofoil", "1stEditionHolofoil", "1stEdition", "unlimitedHolofoil", "unlimited"]


def fetch(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=60) as r:
                return json.loads(r.read())
        except Exception as e:
            if i == tries - 1:
                raise
            time.sleep(4 * (i + 1))


def load(p, d):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return d


def nn(s):
    s = unicodedata.normalize("NFKD", str(s or "").lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if not unicodedata.combining(c)))


def num(s):
    m = re.search(r"\d+", str(s or ""))
    return str(int(m.group())) if m else ""


def ext(p, ad):
    return next((x.get("value") for x in p.get("extendedData") or [] if x.get("name") == ad), None)


def temiz_ad(p):
    a = VARYANT.sub("", p.get("name") or "")
    a = re.sub(r"\s+-\s+\S*\d\S*(\s*\([^)]*\))?\s*$", "", a)   # "Pikachu - 001/XY-P (GYM)"
    a = re.sub(r"\s*\([^)]*\)\s*$", "", a)                      # "Erika's Oddish (Lv.15)"
    return a.strip()


def r2(x):
    return None if x is None else round(float(x), 2)


kat = load(f"{SITE}/cards_ja.json", None)
if not kat:
    raise SystemExit("cards_ja.json yok, atlandı")
ozet = load(f"{VERI}/ozet.json", {"u": TODAY, "c": {}})
gecmis = load(GECMIS_YOL, {})


def fiyatli(cid):
    v = ozet["c"].get(cid)
    return bool(v) and (v[0] is not None or v[1] is not None)


# Bu betiğin önceki günlerde yazdığı fiyatlar "başka kaynaktan" sayılmasın
for cid in list(gecmis):
    v = ozet["c"].get(cid)
    if v and v[1] is None and v[0] is not None:
        del ozet["c"][cid]

eksik = {}
for k in kat["cards"]:
    cid = k[14]
    if not fiyatli(cid):
        eksik.setdefault(cid.rsplit("-", 1)[0], []).append(k)
print(f"Fiyatı olmayan Japonca kart: {sum(map(len, eksik.values()))} ({len(eksik)} set)", flush=True)

gruplar = fetch(f"{BASE}/groups")["results"]
ada = {}
for g in gruplar:
    for a in {nn(g["name"]), nn(re.sub(r"^[^:]{1,12}:\s*", "", g["name"]))}:
        ada.setdefault(a, set()).add(g["groupId"])
kisa = {}
for g in gruplar:
    if g.get("abbreviation"):
        kisa.setdefault(g["abbreviation"].lower(), set()).add(g["groupId"])
tam_ad = {}
for g in gruplar:
    tam_ad.setdefault(g["name"], []).append(g["groupId"])

setler = {s[0]: s for s in kat["sets"]}
eslesme = {}
for sid in eksik:
    if sid in ELLE:
        ids = tam_ad.get(ELLE[sid], [])
        if len(ids) == 1:
            eslesme[sid] = ids[0]
        continue
    s = setler.get(sid)
    if not s:
        continue
    m = re.search(r"\(([^()]*(?:\([^()]*\))?[^()]*)\)\s*$", s[1])
    en = nn(m.group(1) if m else s[1])
    c = ada.get(en, set())
    if len(c) != 1:
        c = kisa.get(sid[3:].lower(), set())
    if len(c) == 1:
        eslesme[sid] = next(iter(c))
print(f"TCGplayer'da bulunan set: {len(eslesme)} / {len(eksik)}; bulunamayan: "
      + ", ".join(sorted(set(eksik) - set(eslesme))), flush=True)


def grup_al(gid):
    try:
        return gid, fetch(f"{BASE}/{gid}/products")["results"], fetch(f"{BASE}/{gid}/prices")["results"]
    except Exception as e:
        print(f"  grup {gid} alınamadı: {e}", flush=True)
        return gid, None, None


veri = {}
with ThreadPoolExecutor(max_workers=4) as ex:
    for gid, urunler, fiyatlar in ex.map(grup_al, sorted(set(eslesme.values()))):
        if urunler is not None:
            fy = {}
            for x in fiyatlar:
                fy.setdefault(x["productId"], []).append(x)
            veri[gid] = (urunler, fy)


def onek(k):
    jp = k[0].split(" (")[0]
    en = k[15] if len(k) > 15 and isinstance(k[15], str) else ""
    for a, b in ONEK:
        if jp.startswith(a):
            return "" if nn(en).startswith(nn(b)) or nn(en).startswith("the" + nn(b)) else b
    return ""


def fiyat_kaydi(urun_fiyatlari):
    t = {}
    for x in urun_fiyatlari or []:
        tur = ALT_TUR.get(x.get("subTypeName"))
        if tur:
            t[tur] = [r2(x.get("lowPrice")), r2(x.get("midPrice")), r2(x.get("highPrice")), r2(x.get("marketPrice"))]
    return t


bulunan = {}   # cid → (gid, ürün, varyant ürünü)
for sid, kartlar in eksik.items():
    gid = eslesme.get(sid)
    if gid not in veri:
        continue
    urunler, _ = veri[gid]
    ana = [p for p in urunler if not VARYANT.search(p.get("name") or "")]
    no_ile = {}
    for p in ana:
        no_ile.setdefault(num(ext(p, "Number")), []).append(p)
    secilen = {}
    for k in kartlar:
        cid, n = k[14], num(k[2])
        en = nn(onek(k) + (k[15] if len(k) > 15 and isinstance(k[15], str) else ""))
        if not en and not n:
            continue
        ad_tutar = lambda p: en and nn(temiz_ad(p)) in (en, "the" + en)
        c = [p for p in no_ile.get(n, []) if n and ad_tutar(p)]
        if not c and n and len(no_ile.get(n, [])) == 1:
            c = no_ile[n]
        if not c:
            c2 = [p for p in ana if ad_tutar(p) and not num(ext(p, "Number"))]
            if len(c2) > 1 and k[6]:
                c2 = [p for p in c2 if str(ext(p, "HP") or "") == str(k[6])]
            c = c2
        if len(c) == 1:
            secilen[cid] = c[0]
    # aynı setteki iki karta bağlanan ürün belirsizdir → ikisi de doldurulmaz
    say = {}
    for p in secilen.values():
        say[p["productId"]] = say.get(p["productId"], 0) + 1
    for cid, p in secilen.items():
        if say[p["productId"]] > 1:
            continue
        n = num(ext(p, "Number"))
        var = next((v for v in urunler if VARYANT.search(v.get("name") or "") and num(ext(v, "Number")) == n
                    and nn(temiz_ad(v)) == nn(temiz_ad(p))), None) if n else None
        bulunan[cid] = (gid, p, var)

# ---- fiyatları yaz ----
os.makedirs(f"{VERI}/set", exist_ok=True)
set_dosya = {}
yazilan = 0
for cid, (gid, p, var) in bulunan.items():
    fy = veri[gid][1]
    t = fiyat_kaydi(fy.get(p["productId"]))
    if var:
        tv = fiyat_kaydi(fy.get(var["productId"]))
        for tur, d in tv.items():
            t.setdefault("reverseHolofoil" if tur in ("holofoil", "normal") else tur, d)
    ana_v = next((v for v in SIRA if v in t and (t[v][3] or t[v][1])), None)
    usd = (t[ana_v][3] or t[ana_v][1]) if ana_v else None
    if usd is None:
        continue   # TCGplayer'da bugün fiyat yok: eski fiyatı güncelmiş gibi göstermeyelim
    h = [x for x in gecmis.get(cid, []) if x[0] != TODAY]
    h.append([TODAY, usd, None])
    h = h[-KEEP_DAYS:]
    gecmis[cid] = h
    son = h[-1]
    sid = cid.rsplit("-", 1)[0]
    if sid not in set_dosya:
        set_dosya[sid] = load(f"{VERI}/set/{sid}.json", {"u": TODAY, "c": {}})
    d = set_dosya[sid]
    rec = d["c"].get(cid)
    if rec and not rec.get("tp") and (rec.get("m") or rec.get("t")) and any(x[2] is not None for x in rec.get("h", [])):
        continue   # başka kaynağın fiyatı var, dokunma
    rec = {"h": h, "tp": 1, "url": p.get("url")}
    if t:
        rec["t"], rec["v"], rec["tu"] = t, ana_v, TODAY.replace("-", "/")
    d["c"][cid] = rec
    d["u"] = TODAY
    once = h[-2] if len(h) >= 2 else [None, None, None]
    ozet["c"][cid] = [son[1], None, None, None, once[1], once[2], once[0]]
    yazilan += 1

for sid, d in set_dosya.items():
    json.dump(d, open(f"{VERI}/set/{sid}.json", "w"), separators=(",", ":"))
json.dump(ozet, open(f"{VERI}/ozet.json", "w"), separators=(",", ":"))
os.makedirs(os.path.dirname(GECMIS_YOL), exist_ok=True)
json.dump(gecmis, open(GECMIS_YOL, "w"), separators=(",", ":"))

# siteye kopyala
os.makedirs(f"{SITE}/fiyat/set", exist_ok=True)
shutil.copy(f"{VERI}/ozet.json", f"{SITE}/fiyat/ozet.json")
for sid in set_dosya:
    shutil.copy(f"{VERI}/set/{sid}.json", f"{SITE}/fiyat/set/{sid}.json")

kalan = sum(1 for k in kat["cards"] if not fiyatli(k[14]))
print(f"TCGplayer: eşleşen kart {len(bulunan)}, fiyat yazılan {yazilan}; hâlâ fiyatı olmayan Japonca kart {kalan}", flush=True)
