"""Magic: The Gathering kataloğu ve günlük fiyatları (Scryfall).

Kaynak: Scryfall (api.scryfall.com) — ücretsiz günlük toplu veri ("default_cards": her basılı kartın bir kaydı)
ve set listesi. Fiyatlar Scryfall'ın günlük olarak TCGplayer (USD) ve Cardmarket'ten (EUR) aldığı fiyatlardır.
Dijital (MTG Arena / MTGO) kartlar alınmaz; kağıt baskısı olan tüm setler ve kartlar (token'lar, promolar dahil) alınır.

Kullanım: python3 magic.py <magic_veri_klasörü>
  yazar : <klasör>/cards_mg.json        sitenin kullandığı kısa katalog (resim adresi önekli)
          <klasör>/detay/mg-<set>.json   kart ayrıntıları (mana, tür satırı, kart metni, güç/dayanıklılık, çizer …)
          <klasör>/set/mg-<set>.json     fiyatlar + son GUN günlük geçmiş (sitede fiyat/set/ altına kopyalanır)
          <klasör>/ozet_mg.json          kart → [usd, eur, -, -, önceki usd, önceki eur, önceki tarih] (sitede fiyat/ altına)
Kart kimliği: mg-<set kodu>-<koleksiyon numarası> (numaradaki harf dışı işaretler: ★→s, †→d, diğerleri _).
"""
import datetime
import gzip
import json
import os
import re
import sys
import time
import urllib.request

MV = sys.argv[1] if len(sys.argv) > 1 else "mveri"
UA = {"User-Agent": "KartBorsa/1.0 (+https://www.kartborsa.com)", "Accept": "application/json;q=0.9,*/*;q=0.8"}
TODAY = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).strftime("%Y-%m-%d")
GUN = 30            # set dosyalarında tutulan fiyat geçmişi (gün)
ESKI_GUN = 7        # o gün fiyatı gelmeyen kartın son fiyatı en fazla bu kadar gün korunur
RESIM = "https://cards.scryfall.io/normal/front/"
TOPLU = "/tmp/scryfall_default_cards.dat"
TCG = "https://tcgcsv.com/tcgplayer/1"   # TCGplayer günlük dökümü (Magic); Scryfall'da resmi/fiyatı olmayan kartlar için

NADIR = {"common": "Common", "uncommon": "Uncommon", "rare": "Rare", "mythic": "Mythic Rare",
         "special": "Special", "bonus": "Bonus"}
RENK = {"W": "Beyaz", "U": "Mavi", "B": "Siyah", "R": "Kırmızı", "G": "Yeşil"}
SERI = {
    "expansion": "Ana setler", "core": "Temel setler (Core)", "masters": "Masters setleri",
    "commander": "Commander setleri", "draft_innovation": "Draft setleri (Conspiracy, Jumpstart, Modern Horizons …)",
    "funny": "Eğlence setleri (Un-setler, Playtest)", "promo": "Promo kartları", "token": "Token ve emblem kartları",
    "memorabilia": "Hatıra ve özel kartlar", "box": "Kutu setleri (Secret Lair, From the Vault …)",
    "duel_deck": "Duel Decks", "from_the_vault": "From the Vault", "masterpiece": "Masterpiece serisi",
    "starter": "Başlangıç ve tanıtım setleri", "planechase": "Planechase", "archenemy": "Archenemy",
    "premium_deck": "Premium Deck Series", "spellbook": "Signature Spellbook", "arsenal": "Commander Arsenal",
    "eternal": "Eternal setleri", "vanguard": "Vanguard", "minigame": "Mini oyunlar",
}
TUR_SIRA = ["Creature", "Planeswalker", "Battle", "Instant", "Sorcery", "Enchantment", "Artifact", "Land",
            "Kindred", "Tribal", "Conspiracy", "Dungeon", "Phenomenon", "Plane", "Scheme", "Vanguard", "Emblem", "Hero"]
FIYAT_ALAN = (("normal", "usd", "eur"), ("foil", "usd_foil", "eur_foil"), ("etched", "usd_etched", "eur_etched"))


def get(url, tries=5):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return json.loads(r.read())
        except Exception as e:
            print(f"  hata ({i + 1}/{tries}) {url}: {e}", flush=True)
            time.sleep(5 * (i + 1))
    raise SystemExit(f"okunamadı: {url}")


def indir(url, yol, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r, open(yol, "wb") as f:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    f.write(b)
            return
        except Exception as e:
            print(f"  indirme hatası ({i + 1}/{tries}): {e}", flush=True)
            time.sleep(10 * (i + 1))
    raise SystemExit("Scryfall toplu verisi indirilemedi")


def load(p, d):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return d


def sayi(x):
    try:
        return float(x) if x not in (None, "") else None
    except Exception:
        return None


def no_id(n):
    s = str(n).replace("★", "s").replace("☆", "w").replace("†", "d")
    return re.sub(r"[^0-9A-Za-z]", "_", s) or "0"


def no_sira(n):
    m = re.match(r"\D*(\d+)(.*)", str(n))
    return (int(m.group(1)), m.group(2)) if m else (999999, str(n))


def ana_tur(c):
    lay = c.get("layout") or ""
    tl = (c.get("type_line") or ((c.get("card_faces") or [{}])[0].get("type_line")) or "")
    on = tl.split(" // ")[0]
    if lay in ("token", "double_faced_token") or on.startswith("Token") or " Token" in on.split("—")[0]:
        return "Token", tl
    if lay == "emblem" or on.startswith("Emblem"):
        return "Emblem", tl
    if lay == "art_series":
        return "Art Card", tl
    bas = on.split("—")[0]
    for t in TUR_SIRA:
        if re.search(r"\b" + t + r"\b", bas):
            return ("Kindred" if t == "Tribal" else t), tl
    return (bas.strip().split()[-1] if bas.strip() else ""), tl


def renk(c):
    cols = c.get("colors")
    if cols is None:
        cols = ((c.get("card_faces") or [{}])[0].get("colors")) or []
    if len(cols) > 1:
        return "Çok renkli", [RENK.get(x, x) for x in cols]
    if cols:
        return RENK.get(cols[0], cols[0]), []
    return "Renksiz", []


def resim(iu):
    u = ((iu or {}).get("normal") or "").split("?")[0]
    if u.startswith(RESIM):
        return "~0" + u[len(RESIM):]
    return u


def yuz(f):
    d = {"n": f.get("name") or "", "m": f.get("mana_cost") or "", "t": f.get("type_line") or "",
         "x": f.get("oracle_text") or f.get("printed_text") or ""}
    for k, a in (("power", "p"), ("toughness", "d"), ("loyalty", "l"), ("defense", "df")):
        if f.get(k) not in (None, ""):
            d[a] = f[k]
    if f.get("flavor_text"):
        d["fl"] = f["flavor_text"]
    return d


def main():
    os.makedirs(f"{MV}/detay", exist_ok=True)
    os.makedirs(f"{MV}/set", exist_ok=True)

    setinfo = {}
    url = "https://api.scryfall.com/sets"
    while url:
        j = get(url)
        for s in j["data"]:
            setinfo[s["code"]] = s
        url = j.get("next_page") if j.get("has_more") else None
    print(f"Scryfall: {len(setinfo)} set", flush=True)

    bulk = get("https://api.scryfall.com/bulk-data/default-cards")
    print(f"Toplu veri: {bulk.get('updated_at')} ({round((bulk.get('compressed_size') or bulk.get('size') or 0) / 1e6)} MB)", flush=True)
    kaynak = bulk.get("jsonl_download_uri") or bulk.get("download_uri")
    indir(kaynak, TOPLU)

    def kayitlar():
        ac = gzip.open if kaynak.endswith(".gz") else open
        with ac(TOPLU, "rt", encoding="utf-8") as f:
            if ".jsonl" in kaynak:
                for satir in f:
                    satir = satir.strip().rstrip(",")
                    if satir and satir not in ("[", "]"):
                        yield json.loads(satir)
            else:
                yield from json.load(f)

    set_kart = {}
    say = 0
    for c in kayitlar():
        say += 1
        if c.get("digital"):
            continue
        games = c.get("games") or []
        if games and "paper" not in games:
            continue
        set_kart.setdefault(c["set"], []).append(c)
    print(f"Toplu veride {say} kayıt", flush=True)

    def set_tarih(code):
        s = setinfo.get(code, {})
        return s.get("released_at") or "9999-12-31"

    sirali = sorted(set_kart, key=lambda k: (set_tarih(k), k))
    setler, kartlar, detay = [], [], {}
    fiyatlar = {}   # cid → (t, ana, usd, eur)
    kimlikler = set()
    ham = {}        # cid → Scryfall kaydı (TCGplayer tamamlaması için)
    for code in sirali:
        s = setinfo.get(code, {})
        ks = sorted(set_kart[code], key=lambda c: (no_sira(c.get("collector_number", "")), c.get("lang") != "en"))
        sid = f"mg-{code}"
        si = len(setler)
        sym = (s.get("icon_svg_uri") or "").split("?")[0]
        setler.append([sid, s.get("name") or ks[0].get("set_name") or code.upper(),
                       SERI.get(s.get("set_type") or ks[0].get("set_type"), "Diğer setler"),
                       set_tarih(code).replace("-", "/"), len(ks), "", sym, "mg"])
        det = {}
        for c in ks:
            cid = f"{sid}-{no_id(c.get('collector_number', ''))}"
            k = cid
            n = 2
            while k in kimlikler:
                k = f"{cid}_{n}"
                n += 1
            cid = k
            kimlikler.add(cid)
            ham[cid] = c
            faces = c.get("card_faces") or []
            tur, tl = ana_tur(c)
            rk, rkler = renk(c)
            iu = c.get("image_uris") or (faces[0].get("image_uris") if faces else None)
            ara = re.sub(r"\s+", " ", " ".join([rk] + rkler + [tl.replace("—", " ").replace("//", " ")])).strip()
            ad2 = c.get("printed_name") if c.get("lang") != "en" and c.get("printed_name") else ""
            kartlar.append([c.get("name") or "", si, str(c.get("collector_number", "")),
                            NADIR.get(c.get("rarity"), (c.get("rarity") or "").title()), tur, rk, "", "", "",
                            [], [], [], ara, resim(iu), cid, ad2, "mg"])
            d = {"a": c.get("artist") or "", "s": (c.get("scryfall_uri") or "").split("?")[0],
                 "y": [yuz(f) for f in faces] if faces else [yuz(c)]}
            if c.get("lang") and c["lang"] != "en":
                d["dil"] = c["lang"]
            if faces and len(faces) > 1 and faces[1].get("image_uris"):
                d["b"] = (faces[1]["image_uris"].get("large") or "").split("?")[0]
            if c.get("tcgplayer_id"):
                d["tp"] = c["tcgplayer_id"]
            cm = ((c.get("purchase_uris") or {}).get("cardmarket") or "")
            m = re.search(r"cardmarket\.com/[^?#]+", cm)
            if m and "/Products/Singles/" in m.group(0):
                d["cm"] = "https://www." + m.group(0)
            if c.get("finishes"):
                d["fn"] = c["finishes"]
            det[cid] = d
            p = c.get("prices") or {}
            t = {}
            for var, ku, ke in FIYAT_ALAN:
                if sayi(p.get(ku)) is not None:
                    t[var] = [None, None, None, round(sayi(p.get(ku)), 2)]
            ana = next((v for v, _, _ in FIYAT_ALAN if v in t), None)
            usd = t[ana][3] if ana else None
            eur_alan = {"normal": "eur", "foil": "eur_foil", "etched": "eur_etched"}
            eur = sayi(p.get(eur_alan[ana])) if ana else None
            if eur is None:
                eur = next((sayi(p.get(k)) for k in ("eur", "eur_foil", "eur_etched") if sayi(p.get(k)) is not None), None)
            fiyatlar[cid] = (t, ana, usd, round(eur, 2) if eur is not None else None)
        detay[sid] = det

    # ---- Scryfall'da resmi ya da fiyatı olmayan kartlar: TCGplayer (tcgcsv.com) ----
    # Eşleşme yalnız kesinse: kartın TCGplayer ürün numarası; yoksa aynı koleksiyon numarası + aynı ad
    # (Art Series setlerinde ★ = "Gold-Stamped" baskı). Belirsizse yazılmaz.
    tc_url = {}
    eksik = {}
    for k in kartlar:
        f = fiyatlar[k[14]]
        if not k[13] or (f[2] is None and f[3] is None):
            eksik.setdefault(setler[k[1]][0], []).append(k)
    try:
        ad_grup = {g["name"].lower(): g["groupId"] for g in get(f"{TCG}/groups", 3)["results"]}
    except BaseException as e:
        print(f"tcgcsv grupları okunamadı: {e}", flush=True)
        ad_grup = {}
    resimli = fiyatli = 0
    for sid, ks in eksik.items():
        s = setinfo.get(sid[3:], {})
        ad = s.get("name") or ""
        sanat = ad.endswith(" Art Series")
        gid = s.get("tcgplayer_id") or ad_grup.get(ad.lower()) or (ad_grup.get(("art series: " + ad[:-11]).lower()) if sanat else None)
        if not gid:
            continue
        try:
            urunler = get(f"{TCG}/{gid}/products", 3)["results"]
            fyt = get(f"{TCG}/{gid}/prices", 3)["results"]
        except BaseException:
            continue
        pid_urun = {p["productId"]: p for p in urunler}
        fiy = {}
        for x in fyt:
            fiy.setdefault(x["productId"], {})[x.get("subTypeName")] = x
        no_ile = {}
        for p in urunler:
            n = next((e.get("value") for e in p.get("extendedData") or [] if e.get("name") == "Number"), None)
            if n:
                no_ile.setdefault(re.sub(r"[^0-9A-Za-z]", "", str(n).split("/")[0]).lstrip("0").lower(), []).append(p)
        for k in ks:
            c = ham[k[14]]
            p = pid_urun.get(c.get("tcgplayer_id"))
            if not p:
                no = str(c.get("collector_number", ""))
                damgali = sanat and bool(re.fullmatch(r"\d+s", no))   # Art Series: "12s" = Gold-Stamped baskı
                yildiz = "★" in no or damgali
                anahtar = re.sub(r"[^0-9A-Za-z]", "", no[:-1] if damgali else no).lstrip("0").lower()
                isim = (c.get("name") or "").split(" // ")[0].strip().lower()
                aday = []
                for q in no_ile.get(anahtar, []):
                    nm = q.get("name") or ""
                    taban = re.sub(r"\s*\([^)]*\)\s*$", "", nm)
                    if sanat:
                        # Imzali urun adinda hem koleksiyon no hem imza ibaresi bulunabilir.
                        taban = re.sub(r"\s*\(\d+\s*/\s*\d+\)\s*$", "", taban)
                    taban = re.sub(r"\s+Art Card$", "", taban).strip().lower()
                    if taban != isim:
                        continue
                    if sanat and (("Gold-Stamped" in nm) != yildiz):
                        continue
                    if not sanat and "(" in nm:
                        continue
                    aday.append(q)
                if len(aday) == 1:
                    p = aday[0]
            if not p:
                continue
            detay[sid][k[14]].setdefault('tp', p['productId'])
            if not k[13] and p.get("imageUrl"):
                k[13] = re.sub(r"_\d+w\.jpg$", "_in_1000x1000.jpg", p["imageUrl"])
                resimli += 1
            t, ana, usd, eur = fiyatlar[k[14]]
            if usd is None and eur is None:
                satir = fiy.get(p["productId"], {})
                t2 = {}
                for alt, var in (("Normal", "normal"), ("Foil", "foil")):
                    x = satir.get(alt)
                    if x and (x.get("marketPrice") or x.get("midPrice")):
                        t2[var] = [x.get("lowPrice"), x.get("midPrice"), x.get("highPrice"), x.get("marketPrice")]
                ana2 = next((v for v in ("normal", "foil") if v in t2), None)
                if ana2:
                    fiyatlar[k[14]] = (t2, ana2, round(t2[ana2][3] or t2[ana2][1], 2), None)
                    tc_url[k[14]] = p.get("url") or ""
                    fiyatli += 1
    print(f"TCGplayer tamamlaması: {resimli} resim, {fiyatli} fiyat", flush=True)

    # ---- katalog ----
    kat = {"sets": setler, "cards": kartlar, "built": TODAY, "v": 1, "pfx": [RESIM]}
    json.dump(kat, open(f"{MV}/cards_mg.json", "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
    for sid, det in detay.items():
        json.dump(det, open(f"{MV}/detay/{sid}.json", "w", encoding="utf-8"), separators=(",", ":"), ensure_ascii=False)
    print(f"Magic: {len(setler)} set, {len(kartlar)} kart; katalog {os.path.getsize(f'{MV}/cards_mg.json') / 1e6:.1f} MB", flush=True)

    # ---- fiyatlar ----
    sinir = (datetime.date.fromisoformat(TODAY) - datetime.timedelta(days=GUN)).isoformat()
    eski_sinir = (datetime.date.fromisoformat(TODAY) - datetime.timedelta(days=ESKI_GUN)).isoformat()
    ozet = {"u": TODAY, "c": {}}
    yazilan = korunan = 0
    for s in setler:
        sid = s[0]
        eski = load(f"{MV}/set/{sid}.json", {"c": {}}).get("c", {})
        yeni = {"u": TODAY, "c": {}}
        for cid in detay[sid]:
            t, ana, usd, eur = fiyatlar[cid]
            once = eski.get(cid) or {}
            h = [x for x in once.get("h", []) if x[0] >= sinir and x[0] != TODAY]
            if usd is None and eur is None:
                if h and h[-1][0] >= eski_sinir and (once.get("t") or once.get("m")):
                    yeni["c"][cid] = once          # bugün fiyat yok: son fiyat birkaç gün korunur
                    o = h[-2] if len(h) >= 2 else [None, None, None]
                    ozet["c"][cid] = [h[-1][1], h[-1][2], None, None, o[1], o[2], o[0]]
                    korunan += 1
                continue
            h.append([TODAY, usd, eur])
            rec = {"h": h}
            if cid in tc_url:
                rec["tc"], rec["url"] = 1, tc_url[cid]
            if t:
                rec["t"], rec["v"], rec["tu"] = t, ana, TODAY.replace("-", "/")
            if eur is not None:
                rec["m"], rec["mu"] = [None, None, eur, None, None, None, None], TODAY.replace("-", "/")
            yeni["c"][cid] = rec
            o = h[-2] if len(h) >= 2 else [None, None, None]
            ozet["c"][cid] = [usd, eur, None, None, o[1], o[2], o[0]]
            yazilan += 1
        json.dump(yeni, open(f"{MV}/set/{sid}.json", "w", encoding="utf-8"), separators=(",", ":"))
    json.dump(ozet, open(f"{MV}/ozet_mg.json", "w", encoding="utf-8"), separators=(",", ":"))
    print(f"Fiyat: {yazilan} kart bugün fiyatlı, {korunan} kartın son fiyatı korundu, "
          f"fiyatsız {len(kartlar) - yazilan - korunan}", flush=True)


if __name__ == "__main__":
    main()
