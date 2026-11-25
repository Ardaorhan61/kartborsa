#!/usr/bin/env python3
"""KartBorsa: kart tarama için her kartın resminden "görsel iz" (perceptual hash) çıkarır.

Kullanım: python3 kart_izi.py <site klasörü> <çıktı klasörü> [cards_ja.json] [cards_cp.json] [cards_mg.json]
  - <site>/cards.json okunur
  - <çıktı>/izler.json varsa sadece eksik kartlar hesaplanır
Aynı hesap index.html içindeki taraIz() fonksiyonuyla birebir aynıdır:
  resim -> 256x352 (gri) -> 8x8 blok ortalaması -> 32x44 -> DCT 8x8 -> 64 bit
  A: tüm kart, B: resim bölgesi (satır 4..22, sütun 3..29), C/D: renk (Cb, Cr) tüm kart
"""
import io, json, os, sys, time, concurrent.futures as cf, urllib.request
import numpy as np
from PIL import Image

SITE, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
cat = json.load(open(os.path.join(SITE, 'cards.json'), encoding='utf-8'))
sets = cat['sets']
JA_YOL = sys.argv[3] if len(sys.argv) > 3 else ''
ja = json.load(open(JA_YOL, encoding='utf-8')) if JA_YOL and os.path.exists(JA_YOL) else {'sets': [], 'cards': []}
CP_YOL = sys.argv[4] if len(sys.argv) > 4 else ''   # Cyberpunk TCG kataloğu (cyberpunk.py yazar)
cp = json.load(open(CP_YOL, encoding='utf-8')) if CP_YOL and os.path.exists(CP_YOL) else {'sets': [], 'cards': []}
eski_yol = os.path.join(OUT, 'izler2.json')
eski = {}
if os.path.exists(eski_yol):
    try:
        eski = json.load(open(eski_yol, encoding='utf-8')).get('d', {})
    except Exception:
        eski = {}


def dct_mat(n, k=8):
    x = np.arange(n)
    return np.array([np.cos(np.pi * (2 * x + 1) * u / (2 * n)) for u in range(k)])


DCT = {}


def phash(g):
    h, w = g.shape
    if (h, w) not in DCT:
        DCT[(h, w)] = (dct_mat(h), dct_mat(w))
    dy, dx = DCT[(h, w)]
    f = (dy @ g @ dx.T).flatten()
    med = np.sort(f[1:])[31]
    bits = f > med
    bits[0] = False
    v = 0
    for b in bits:
        v = (v << 1) | int(b)
    return '%016x' % v


def iz(img):
    img = img.convert('RGBA')
    zemin = Image.new('RGBA', img.size, (128, 128, 128, 255))
    img = Image.alpha_composite(zemin, img).convert('RGB').resize((256, 352), Image.LANCZOS)
    a = np.asarray(img, dtype=np.float64)
    R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    kucult = lambda m: m.reshape(44, 8, 32, 8).mean(axis=(1, 3))
    g = kucult(R * 0.299 + G * 0.587 + B * 0.114)
    cb = kucult(-0.168736 * R - 0.331264 * G + 0.5 * B)
    cr = kucult(0.5 * R - 0.418688 * G - 0.081312 * B)
    return phash(g) + phash(g[4:22, 3:29]) + phash(cb) + phash(cr)


def indir(url):
    if not url.startswith('http'):
        return open(os.path.join(SITE, url), 'rb').read()
    req = urllib.request.Request(url, headers={'User-Agent': 'KartBorsa-kart-izi/1.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def isle(c):
    cid = c[14]
    urls = []
    if c[13]:
        urls.append(c[13])
    if not cid.startswith(('ja-', 'cp-')):
        urls.append('https://images.pokemontcg.io/%s/%s.png' % (sets[c[1]][0], c[2]))
    # Scrydex'e otomatik istek atılmaz (kuralları gereği)
    urls = [u for u in urls if 'scrydex.com' not in u]
    for u in urls:
        for deneme in range(2):
            try:
                return cid, iz(Image.open(io.BytesIO(indir(u))))
            except Exception:
                time.sleep(0.5)
    return cid, None


kartlar = cat['cards'] + [c for c in ja['cards'] if c[13]] + [c for c in cp['cards'] if c[13]]
yeni = {}
eksik = []
for c in kartlar:
    if c[14] in eski:
        yeni[c[14]] = eski[c[14]]
    else:
        eksik.append(c)
print('toplam', len(kartlar), 'hazır', len(yeni), 'hesaplanacak', len(eksik), flush=True)

bas = time.time()
hata = 0
with cf.ThreadPoolExecutor(24) as ex:
    for n, (cid, h) in enumerate(ex.map(isle, eksik), 1):
        if h:
            yeni[cid] = h
        else:
            hata += 1
        if n % 500 == 0:
            print(n, '/', len(eksik), 'kart', int(time.time() - bas), 'sn', 'hata', hata, flush=True)

json.dump({'v': 2, 'n': len(yeni), 'd': yeni}, open(eski_yol, 'w', encoding='utf-8'), separators=(',', ':'))
print('bitti:', len(yeni), 'kart izi,', hata, 'resim alınamadı,', os.path.getsize(eski_yol) // 1024, 'KB')

# ---- Magic: The Gathering (ayrı dosya: izler_mg.json; Scryfall küçük resimleri) ----
# 5. argüman: magic-verisi dalındaki cards_mg.json. İlk çalışmada ~110 bin kart var; MG_SURE saniye (varsayılan 5400)
# dolunca o ana kadarkiler kaydedilir, kalanlar sonraki çalışmada eklenir.
MG_YOL = sys.argv[5] if len(sys.argv) > 5 else ''
if MG_YOL and os.path.exists(MG_YOL):
    mg = json.load(open(MG_YOL, encoding='utf-8'))
    mg_yol = os.path.join(OUT, 'izler_mg.json')
    meski = {}
    if os.path.exists(mg_yol):
        try:
            meski = json.load(open(mg_yol, encoding='utf-8')).get('d', {})
        except Exception:
            meski = {}
    onekler = mg.get('pfx') or []
    mk = [c for c in mg['cards'] if len(c) > 14 and c[13]]
    myeni = {c[14]: meski[c[14]] for c in mk if c[14] in meski}
    meksik = [c for c in mk if c[14] not in meski]
    SURE = float(os.environ.get('MG_SURE', '5400'))
    print('Magic: toplam', len(mk), 'hazır', len(myeni), 'hesaplanacak', len(meksik), flush=True)

    def misle(c):
        u = c[13]
        if u.startswith('~'):
            if len(u) < 3 or not u[1].isascii() or not u[1].isdigit() or int(u[1]) >= len(onekler):
                return c[14], None
            u = onekler[int(u[1])] + u[2:]
        if u.startswith('https://cards.scryfall.io/normal/'):
            u = u.replace('/normal/', '/small/', 1)
        for deneme in range(2):
            try:
                return c[14], iz(Image.open(io.BytesIO(indir(u))))
            except Exception:
                time.sleep(1)
        return c[14], None

    def mkaydet():
        json.dump({'v': 2, 'n': len(myeni), 'd': myeni}, open(mg_yol, 'w', encoding='utf-8'), separators=(',', ':'))

    mbas = time.time()
    mhata = 0
    for i in range(0, len(meksik), 2000):
        if time.time() - mbas > SURE:
            print('Magic: süre doldu, kalanlar sonraki çalışmada', flush=True)
            break
        with cf.ThreadPoolExecutor(8) as ex:
            for cid, h in ex.map(misle, meksik[i:i + 2000]):
                if h:
                    myeni[cid] = h
                else:
                    mhata += 1
        mkaydet()
        print('Magic:', min(i + 2000, len(meksik)), '/', len(meksik), int(time.time() - mbas), 'sn, hata', mhata, flush=True)
    mkaydet()
    print('Magic bitti:', len(myeni), 'kart izi,', mhata, 'resim alınamadı,', os.path.getsize(mg_yol) // 1024, 'KB', flush=True)
