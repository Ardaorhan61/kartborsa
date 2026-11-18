#!/usr/bin/env python3
"""KartBorsa: kart tarama için her kartın resminden "görsel iz" (perceptual hash) çıkarır.

Kullanım: python3 kart_izi.py <site klasörü> <çıktı klasörü>
  - <site>/cards.json okunur
  - <çıktı>/izler.json varsa sadece eksik kartlar hesaplanır
Aynı hesap index.html içindeki taraIz() fonksiyonuyla birebir aynıdır:
  resim -> 256x352 (gri) -> 8x8 blok ortalaması -> 32x44 -> DCT 8x8 -> 64 bit
  A: tüm kart, B: resim bölgesi (satır 4..22, sütun 3..29)
"""
import io, json, os, sys, time, concurrent.futures as cf, urllib.request
import numpy as np
from PIL import Image

SITE, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
cat = json.load(open(os.path.join(SITE, 'cards.json'), encoding='utf-8'))
sets = cat['sets']
eski_yol = os.path.join(OUT, 'izler.json')
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
    gri = a[:, :, 0] * 0.299 + a[:, :, 1] * 0.587 + a[:, :, 2] * 0.114
    g = gri.reshape(44, 8, 32, 8).mean(axis=(1, 3))
    return phash(g) + phash(g[4:22, 3:29])


def indir(url):
    if not url.startswith('http'):
        return open(os.path.join(SITE, url), 'rb').read()
    req = urllib.request.Request(url, headers={'User-Agent': 'KartBorsa-kart-izi/1.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def isle(c):
    cid = c[-1]
    urls = []
    if c[13]:
        urls.append(c[13])
    urls.append('https://images.pokemontcg.io/%s/%s.png' % (sets[c[1]][0], c[2]))
    urls.append('https://images.scrydex.com/pokemon/%s/small' % cid)
    for u in urls:
        for deneme in range(2):
            try:
                return cid, iz(Image.open(io.BytesIO(indir(u))))
            except Exception:
                time.sleep(0.5)
    return cid, None


kartlar = cat['cards']
yeni = {}
eksik = []
for c in kartlar:
    if c[-1] in eski:
        yeni[c[-1]] = eski[c[-1]]
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

json.dump({'v': 1, 'n': len(yeni), 'd': yeni}, open(eski_yol, 'w', encoding='utf-8'), separators=(',', ':'))
print('bitti:', len(yeni), 'kart izi,', hata, 'resim alınamadı,', os.path.getsize(eski_yol) // 1024, 'KB')
