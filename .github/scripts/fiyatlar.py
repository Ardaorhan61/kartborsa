"""Her kartın güncel piyasa fiyatlarını Pokémon TCG API'sinden çeker ve geçmişe ekler.

Kullanım: python3 fiyatlar.py <veri_klasörü>
Çıktı (veri_klasörü içinde):
  kur.json          → USD/EUR → TRY kurları ve geçmişi
  ozet.json         → tüm kartların bugünkü özet fiyatları (Piyasa tablosu için)
  set/<setId>.json  → setteki her kartın ayrıntılı fiyatları ve günlük geçmişi
"""
import json, os, sys, time, datetime, urllib.request, urllib.error

OUT = sys.argv[1]
os.makedirs(f"{OUT}/set", exist_ok=True)
TODAY = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).strftime("%Y-%m-%d")
KEEP_DAYS = 730
API = "https://api.pokemontcg.io/v2/cards"
HEADERS = {"User-Agent": "KartBorsa-fiyat/1.0"}
if os.environ.get("POKEMONTCG_API_KEY"):
    HEADERS["X-Api-Key"] = os.environ["POKEMONTCG_API_KEY"]
VARIANT_ORDER = ["holofoil", "normal", "reverseHolofoil", "1stEditionHolofoil", "1stEditionNormal", "unlimitedHolofoil", "1stEdition", "unlimited"]


def fetch(url, tries=6):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            wait = 10 * (i + 1)
            print(f"  hata ({e}); {wait} sn sonra tekrar", flush=True)
            time.sleep(wait)
    raise RuntimeError("API'ye ulaşılamadı: " + url)


def load(path, default):
    try:
        return json.load(open(path))
    except Exception:
        return default


def r2(x):
    return None if x is None else round(float(x), 2)


# ---- kurlar ----
kur = load(f"{OUT}/kur.json", {"gecmis": {}})
try:
    usd = fetch("https://api.frankfurter.app/latest?from=USD&to=TRY,EUR")
    eur = fetch("https://api.frankfurter.app/latest?from=EUR&to=TRY")
    kur.update({"tarih": TODAY, "USD": usd["rates"]["TRY"], "EUR": eur["rates"]["TRY"]})
    kur["gecmis"][TODAY] = [kur["USD"], kur["EUR"]]
except Exception as e:
    print("Kur alınamadı, eski kur kullanılıyor:", e)
kur["gecmis"] = dict(sorted(kur["gecmis"].items())[-KEEP_DAYS:])

# ---- fiyatlar ----
cards, page = [], 1
while True:
    url = f"{API}?page={page}&pageSize=250&orderBy=id&select=id,set,tcgplayer,cardmarket"
    d = fetch(url)
    cards += d.get("data", [])
    total = d.get("totalCount", 0)
    print(f"sayfa {page}: {len(cards)}/{total}", flush=True)
    if not d.get("data") or len(cards) >= total:
        break
    page += 1
    time.sleep(1.5)

if len(cards) < 1000:
    raise SystemExit(f"Çok az kart geldi ({len(cards)}), veriler güncellenmedi.")

by_set = {}
for c in cards:
    sid = (c.get("set") or {}).get("id") or c["id"].rsplit("-", 1)[0]
    by_set.setdefault(sid, []).append(c)

ozet = {}
for sid, lst in by_set.items():
    path = f"{OUT}/set/{sid}.json"
    old = load(path, {"c": {}})
    out = {"u": TODAY, "c": {}}
    for c in lst:
        cid = c["id"]
        prev = old["c"].get(cid, {})
        tp = (c.get("tcgplayer") or {}).get("prices") or {}
        cm = (c.get("cardmarket") or {}).get("prices") or {}
        t = {}
        for v, p in tp.items():
            t[v] = [r2(p.get("low")), r2(p.get("mid")), r2(p.get("high")), r2(p.get("market"))]
        main_v = next((v for v in VARIANT_ORDER if v in t and (t[v][3] or t[v][1])), next(iter(t), None))
        usd_main = (t[main_v][3] or t[main_v][1]) if main_v else None
        m = [r2(cm.get(k)) for k in ("averageSellPrice", "lowPrice", "trendPrice", "avg1", "avg7", "avg30", "reverseHoloTrend")] if cm else None
        eur_trend = m[2] if m else None
        hist = [h for h in prev.get("h", []) if h[0] != TODAY]
        if usd_main is not None or eur_trend is not None:
            hist.append([TODAY, usd_main, eur_trend])
        hist = hist[-KEEP_DAYS:]
        rec = {"h": hist}
        if t:
            rec["t"] = t
            rec["v"] = main_v
            rec["tu"] = (c.get("tcgplayer") or {}).get("updatedAt")
        if m:
            rec["m"] = m
            rec["mu"] = (c.get("cardmarket") or {}).get("updatedAt")
        out["c"][cid] = rec
        if usd_main is not None or eur_trend is not None:
            before = hist[-2] if len(hist) >= 2 else [None, None, None]
            ozet[cid] = [usd_main, eur_trend, m[4] if m else None, m[5] if m else None, before[1], before[2], before[0]]
    json.dump(out, open(path, "w"), separators=(",", ":"))

json.dump({"u": TODAY, "c": ozet}, open(f"{OUT}/ozet.json", "w"), separators=(",", ":"))
json.dump(kur, open(f"{OUT}/kur.json", "w"), separators=(",", ":"))
print(f"Bitti: {len(cards)} kart, {len(ozet)} fiyatlı, {len(by_set)} set. Kur: {kur.get('USD')} / {kur.get('EUR')}")
