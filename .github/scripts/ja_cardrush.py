#!/usr/bin/env python3
"""Japonca promo kartları için Card Rush (cardrush-pokemon.jp) mağaza satış fiyatları.

Arda'nın isteğiyle (24 Kasım 2026): TCGplayer / Cardmarket / TCGdex'te fiyatı olmayan Japonca
kartlar için Japon mağazası Card Rush'ın sitede gösterdiği satış fiyatı (¥, vergi dahil) okunur.

Kurallar (tahmin yok):
- Sadece ürün adındaki numara {NNN/<SET>-P} kartın numarasıyla ve setiyle birebir aynıysa.
- Durum etiketli (〔状態B〕, 〔PSA10鑑定済〕 …) ve 未開封 (açılmamış paket) ürünler alınmaz.
- Aynı numarada farklı adlı birden çok ürün varsa (ör. ちからのハチマキ(ファミ通) / (リザードンメガバトル)) belirsizdir, yazılmaz.
- Ürün adı (parantez içi hariç) katalogdaki Japonca adla aynı değilse yazılmaz.
- Stokta olan ürünün fiyatı tercih edilir; stok yoksa mağazanın gösterdiği fiyat "stokta yok" notuyla yazılır.

Çıktı: <veri>/japonca/cardrush.json  {u, kur(1 USD = ? JPY), c: {kart_id: {y, s, url, ad, tarih, usd, h:[[tarih, usd, yen]]}}}
Yayında (yayin.yml "Card Rush fiyatları" adımı) sadece başka kaynaktan fiyatı olmayan kartlara uygulanır.

Kullanım: python3 ja_cardrush.py <veri klasörü>
"""
import datetime
import html
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

VERI = sys.argv[1] if len(sys.argv) > 1 else "veri"
YOL = f"{VERI}/japonca/cardrush.json"
SITE = "https://www.cardrush-pokemon.jp"
KATALOG = "https://www.kartborsa.com/cards_ja.json"
UA = "Mozilla/5.0 (compatible; KartBorsaFiyat/1.0; +https://www.kartborsa.com)"
BEKLE = 1.5          # istekler arası saniye
GECMIS_GUN = 90

# katalog set kimliği → Card Rush'taki promo kodu ({NNN/<kod>})
SETLER = {
    "ja-XYP": "XY-P", "ja-SMP": "SM-P", "ja-SP": "S-P", "ja-BWP": "BW-P",
    "ja-SV-P": "SV-P", "ja-M-P": "M-P", "ja-DPP": "DP-P", "ja-DPTP": "DPt-P",
    "ja-LP": "L-P", "ja-PCGP": "PCG-P",
}

BUGUN = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)).date().isoformat()


def al(url, json_mu=False, deneme=3):
    for i in range(deneme):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ja,en;q=0.8"})
            with urllib.request.urlopen(req, timeout=40) as r:
                veri = r.read().decode("utf-8", "replace")
            return json.loads(veri) if json_mu else veri
        except Exception as e:
            print(f"  hata ({i + 1}/{deneme}) {url}: {e}", flush=True)
            time.sleep(5 * (i + 1))
    return None


def nn(s):
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r"\(.*?\)", "", s)
    return re.sub(r"[\s・･'’\-‐]", "", s).lower()


def sayfa_oku(kod, sayfa):
    """Bir arama sayfasını okur → (ürünler, sayfadaki ham ürün sayısı) ya da hata olursa (None, 0)."""
    q = urllib.parse.urlencode({"keyword": kod, "num": 100, "page": sayfa})
    h = al(f"{SITE}/product-list?{q}")
    if h is None:
        return None, 0
    parcalar = h.split('<li class="list_item_cell')[1:]
    sonuc = []
    for p in parcalar:          # her ürün ayrı okunur (stokta olmayanlarda <p class="stock soldout">×</p>)
        pid = re.search(r'data-product-id="(\d+)"', p)
        ad = re.search(r'<span class="goods_name">(.*?)</span>\s*<wbr', p, re.S)
        fiyat = re.search(r'<span class="figure">([\d,]+)円', p)
        stok = re.search(r'<p class="stock[^"]*">(.*?)</p>', p, re.S)
        if not (pid and ad and fiyat):
            continue
        ad = html.unescape(re.sub(r"<[^>]+>", "", ad.group(1))).strip()
        m = re.search(r"(\d+)\s*枚", stok.group(1)) if stok else None
        sonuc.append({"id": pid.group(1), "ad": ad, "y": int(fiyat.group(1).replace(",", "")),
                      "s": int(m.group(1)) if m else 0})
    return sonuc, len(parcalar)


def main():
    os.makedirs(os.path.dirname(YOL), exist_ok=True)
    try:
        eski = json.load(open(YOL, encoding="utf-8"))
    except Exception:
        eski = {"c": {}}

    kur_j = al("https://api.frankfurter.app/latest?from=USD&to=JPY", json_mu=True)
    kur = (kur_j or {}).get("rates", {}).get("JPY") or eski.get("kur")
    if not kur:
        print("JPY kuru alınamadı; çıkılıyor.")
        return
    print(f"Kur: 1 USD = {kur} JPY", flush=True)

    kat = al(KATALOG, json_mu=True)
    if not kat:
        print("Katalog alınamadı; çıkılıyor.")
        return
    setler = kat["sets"]
    kartlar = {}
    for c in kat["cards"]:
        sid = setler[c[1]][0]
        if sid in SETLER and c[4] != "Energy" and str(c[2]).isdigit():
            kartlar.setdefault(sid, []).append(c)

    yeni = {}
    for sid, kod in SETLER.items():
        if sid not in kartlar:
            continue
        urunler = []
        for s in range(1, 80):
            liste, ham = sayfa_oku(kod, s)
            time.sleep(BEKLE)
            if liste is None:
                print(f"  {kod} sayfa {s} okunamadı", flush=True)
                break
            urunler += liste
            if ham < 100:
                break
        desen = re.compile(r"^(.*?)【[^】]*】\{0*(\d+)/" + re.escape(kod) + r"\}$")
        no_ile = {}
        for u in urunler:
            if u["ad"].startswith("〔") or "未開封" in u["ad"]:
                continue
            m = desen.match(u["ad"])
            if m:
                no_ile.setdefault(int(m.group(2)), []).append(dict(u, temel=m.group(1)))
        bulunan = 0
        for c in kartlar[sid]:
            jp = c[0].split(" (")[0]
            if not re.search(r"[぀-ヿ一-鿿]", jp) or "{{" in jp:
                continue
            aday = no_ile.get(int(c[2]), [])
            if not aday:
                continue
            if len({a["temel"] for a in aday}) != 1:
                continue            # aynı numarada farklı ürünler → belirsiz
            if nn(aday[0]["temel"]) != nn(jp):
                continue            # ad tutmuyor
            stokta = [a for a in aday if a["s"] > 0]
            sec = min(stokta or aday, key=lambda a: a["y"])
            yeni[c[14]] = {
                "y": sec["y"], "s": sec["s"], "ad": sec["ad"],
                "url": f"{SITE}/product/{sec['id']}", "tarih": BUGUN,
                "usd": round(sec["y"] / kur, 2),
            }
            bulunan += 1
        print(f"{sid} ({kod}): {len(urunler)} ürün, {len(kartlar[sid])} kart, fiyat bulunan {bulunan}", flush=True)

    sinir = (datetime.date.fromisoformat(BUGUN) - datetime.timedelta(days=GECMIS_GUN)).isoformat()
    cikti = {"u": BUGUN, "kur": kur, "kaynak": "Card Rush (cardrush-pokemon.jp) mağaza satış fiyatı, ¥ vergi dahil", "c": {}}
    for cid in set(eski.get("c", {})) | set(yeni):
        e = eski.get("c", {}).get(cid, {})
        h = [x for x in e.get("h", []) if x[0] >= sinir and x[0] != BUGUN]
        if cid in yeni:
            r = yeni[cid]
            h.append([BUGUN, r["usd"], r["y"]])
        else:
            r = {k: v for k, v in e.items() if k != "h"}   # bugün bulunamadı: eski kayıt (tarihiyle) kalır
        if not r:
            continue
        r["h"] = sorted(h)
        cikti["c"][cid] = r
    json.dump(cikti, open(YOL, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"Card Rush: bugün fiyatı bulunan {len(yeni)} kart; dosyada {len(cikti['c'])} kart.", flush=True)


if __name__ == "__main__":
    main()
