"""Her kartın güncel piyasa fiyatlarını çeker ve geçmişe ekler.

Kaynaklar:
  1) Pokémon TCG API (api.pokemontcg.io) — eski/normal setler
  2) TCGdex (api.tcgdex.net) — Pokémon TCG API'de henüz olmayan yeni setler
     (TCGdex de TCGplayer + Cardmarket fiyatlarını verir)

Kullanım: python3 fiyatlar.py <veri_klasörü> <cards.json>
Çıktı (veri_klasörü içinde):
  kur.json          → USD/EUR → TRY kurları ve geçmişi
  ozet.json         → tüm kartların bugünkü özet fiyatları (Piyasa tablosu için)
  set/<setId>.json  → setteki her kartın ayrıntılı fiyatları ve günlük geçmişi
"""
import json, os, re, sys, time, datetime, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

OUT = sys.argv[1]
os.makedirs(f"{OUT}/set", exist_ok=True)
TODAY = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).strftime("%Y-%m-%d")
KEEP_DAYS = 730
API = "https://api.pokemontcg.io/v2/cards"
TCGDEX = "https://api.tcgdex.net/v2/en"
HEADERS = {"User-Agent": "KartBorsa-fiyat/1.0"}
if os.environ.get("POKEMONTCG_API_KEY"):
    HEADERS["X-Api-Key"] = os.environ["POKEMONTCG_API_KEY"]
VARIANT_ORDER = ["holofoil", "normal", "reverseHolofoil", "1stEditionHolofoil", "1stEditionNormal", "unlimitedHolofoil", "1stEdition", "unlimited"]

# Sitedeki set kodu → TCGdex set kodu (Pokémon TCG API'de fiyatı olmayan setler).
# Buraya yazılmayan yeni setler de Pokémon TCG API'de bulunamazsa set adıyla TCGdex'te aranır.
TCGDEX_SETS = {
    "me2pt5": "me02.5",   # Ascended Heroes
    "me3": "me03",        # Perfect Order
    "me4": "me04",        # Chaos Rising
    "me5": "me05",        # Pitch Black
    "me55": "30th",       # 30th Celebration
    "me55c": "30th-c",    # 30th Celebration: Classic Collection
    "me6": "me06",        # Delta Reign
}


DEADLINE = time.time() + float(os.environ.get("FIYAT_SURE_DK", "45")) * 60


def fetch(url, tries=6):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise RuntimeError("Bulunamadı (404): " + url)
            if time.time() > DEADLINE:
                break
            wait = 5 * (i + 1)
            print(f"  hata ({e}); {wait} sn sonra tekrar", flush=True)
            time.sleep(wait)
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
            if time.time() > DEADLINE:
                break
            wait = 5 * (i + 1)
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


# ---- TCGdex yardımcıları ----
def nn(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def nnum(s):
    s = str(s).strip().upper()
    return s.lstrip("0") or "0"


def num_key(num):
    d = re.sub(r"\D", "", str(num))
    return (int(d) if d else 10**6, str(num))


def camel(k):
    p = k.split("-")
    return p[0] + "".join(x[:1].upper() + x[1:] for x in p[1:])


def match_cards(site_cards, tcards):
    """site_cards: [(siteId, ad, numara)], tcards: TCGdex kısa kart listesi → {siteId: tcgdexId}"""
    tcards = sorted(tcards, key=lambda x: num_key(x.get("localId", "")))
    by_num = {nnum(t.get("localId", "")): t for t in tcards}
    used, res = set(), {}
    rest = []
    # 1) aynı numara + aynı ad
    for sid, name, num in sorted(site_cards, key=lambda x: num_key(x[2])):
        t = by_num.get(nnum(num))
        if t and t["id"] not in used and nn(t.get("name")) == nn(name):
            res[sid] = t["id"]
            used.add(t["id"])
        else:
            rest.append((sid, name, num))
    # 2) sadece aynı ad (numaralar farklıysa), 3) adın başı tutuyorsa (ör. "Palkia LV.X" ~ "Palkia")
    for exact in (True, False):
        left = []
        for sid, name, num in rest:
            a = nn(name)
            t = next((t for t in tcards if t["id"] not in used and (
                nn(t.get("name")) == a if exact else (a.startswith(nn(t.get("name"))) or nn(t.get("name")).startswith(a))
            )), None)
            if t:
                res[sid] = t["id"]
                used.add(t["id"])
            else:
                left.append((sid, name, num))
        rest = left
    return res, rest


def tcgdex_to_ptcg(site_id, sid, card):
    """TCGdex kartını Pokémon TCG API biçimine çevirir (aşağıdaki kod aynen kullanabilsin diye)."""
    pr = card.get("pricing") or {}
    out = {"id": site_id, "set": {"id": sid}}
    tp = pr.get("tcgplayer") or {}
    prices = {}
    for k, v in tp.items():
        if isinstance(v, dict):
            prices[camel(k)] = {"low": v.get("lowPrice"), "mid": v.get("midPrice"),
                                "high": v.get("highPrice"), "market": v.get("marketPrice")}
    if prices:
        out["tcgplayer"] = {"prices": prices, "updatedAt": (tp.get("updated") or "")[:10].replace("-", "/")}
    cm = pr.get("cardmarket") or {}
    if cm:
        suf = ""
        # sadece holo basımı olan kartlarda normal fiyat boş gelir → holo fiyatını ana fiyat say
        if cm.get("avg") is None and not cm.get("trend") and cm.get("trend-holo"):
            suf = "-holo"
        cp = {"averageSellPrice": cm.get("avg" + suf), "lowPrice": cm.get("low" + suf),
              "trendPrice": cm.get("trend" + suf), "avg1": cm.get("avg1" + suf),
              "avg7": cm.get("avg7" + suf), "avg30": cm.get("avg30" + suf),
              "reverseHoloTrend": None if suf else cm.get("trend-holo")}
        if any(v is not None for v in cp.values()):
            out["cardmarket"] = {"prices": cp, "updatedAt": (cm.get("updated") or "")[:10].replace("-", "/")}
    return out


_tcgdex_sets = None


def tcgdex_set_id(sid, set_name):
    global _tcgdex_sets
    if sid in TCGDEX_SETS:
        return TCGDEX_SETS[sid]
    if _tcgdex_sets is None:
        try:
            _tcgdex_sets = {nn(s["name"]): s["id"] for s in fetch(f"{TCGDEX}/sets", tries=3)}
        except Exception as e:
            print("  TCGdex set listesi alınamadı:", e)
            _tcgdex_sets = {}
    return _tcgdex_sets.get(nn(set_name))


def fetch_tcgdex(sid, set_name, site_cards):
    tid = tcgdex_set_id(sid, set_name)
    if not tid:
        return None
    tset = fetch(f"{TCGDEX}/sets/{tid}", tries=3)
    pairs, unmatched = match_cards(site_cards, tset.get("cards") or [])
    if unmatched:
        print(f"  TCGdex'te eşleşmeyen {len(unmatched)} kart: " + ", ".join(f"{n} #{m}" for _, n, m in unmatched[:8]))

    def one(item):
        site_id, tcid = item
        try:
            return tcgdex_to_ptcg(site_id, sid, fetch(f"{TCGDEX}/cards/{tcid}", tries=3))
        except Exception as e:
            print(f"  {tcid}: alınamadı ({e})")
            return None

    with ThreadPoolExecutor(max_workers=6) as ex:
        got = [c for c in ex.map(one, pairs.items()) if c]
    if pairs and not got:
        raise RuntimeError("TCGdex'ten hiç kart alınamadı")
    return got, tid


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

# ---- fiyatlar (set set; alınamayan setin eski verisi korunur) ----
SITE_CARDS = sys.argv[2] if len(sys.argv) > 2 else None
site = json.load(open(SITE_CARDS)) if SITE_CARDS else {"sets": [], "cards": []}
set_ids = [x[0] for x in site["sets"]]
set_names = {x[0]: x[1] for x in site["sets"]}
site_by_set = {}
for x in site.get("cards", []):
    cid = x[-1]
    s = cid.rsplit("-", 1)[0]
    site_by_set.setdefault(s, []).append((cid, x[0], x[2]))
cards, failed = [], []
# önce hiç/en uzun süredir güncellenmemiş setler, aralarında en yeniler önce
order = {sid: i for i, sid in enumerate(set_ids)}
set_ids.sort(key=lambda sid: (load(f"{OUT}/set/{sid}.json", {}).get("u", ""), -order[sid]))
for n, sid in enumerate(set_ids, 1):
    if time.time() > DEADLINE:
        failed.append(sid)
        continue
    got, page = [], 1
    try:
        if sid not in TCGDEX_SETS:
            while True:
                d = fetch(f"{API}?q=set.id:{sid}&page={page}&pageSize=250&select=id,set,tcgplayer,cardmarket", tries=3)
                got += d.get("data", [])
                if not d.get("data") or len(got) >= d.get("totalCount", 0):
                    break
                page += 1
        kaynak = ""
        if not got and site_by_set.get(sid):
            r = fetch_tcgdex(sid, set_names.get(sid, ""), site_by_set[sid])
            if r:
                got, tid = r
                kaynak = f" (TCGdex: {tid})"
            elif sid in TCGDEX_SETS:
                raise RuntimeError("TCGdex eşleşmesi yok")
        cards += got
        print(f"[{n}/{len(set_ids)}] {sid}: {len(got)} kart{kaynak}", flush=True)
    except Exception as e:
        failed.append(sid)
        print(f"[{n}/{len(set_ids)}] {sid}: ALINAMADI ({e})", flush=True)
    time.sleep(1)

if not cards:
    raise SystemExit("Hiç fiyat alınamadı, veriler güncellenmedi.")
print(f"Gelen: {len(cards)} kart, {len(set_ids) - len(failed)} set. ", end="")
print(f"Alınamayan setler ({len(failed)}): {', '.join(failed)}")

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

old_ozet = load(f"{OUT}/ozet.json", {"c": {}})["c"]
for cid, v in old_ozet.items():
    if cid.rsplit("-", 1)[0] in failed and cid not in ozet:
        ozet[cid] = v
json.dump({"u": TODAY, "c": ozet}, open(f"{OUT}/ozet.json", "w"), separators=(",", ":"))
json.dump(kur, open(f"{OUT}/kur.json", "w"), separators=(",", ":"))
print(f"Bitti: {len(cards)} kart, {len(ozet)} fiyatlı, {len(by_set)} set. Kur: {kur.get('USD')} / {kur.get('EUR')}")
