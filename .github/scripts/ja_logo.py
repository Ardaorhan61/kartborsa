#!/usr/bin/env python3
"""KartBorsa: Japonca set logolari ve sembolleri.

Kullanim: python3 ja_logo.py <site klasoru>
Eslesme: .github/scripts/ja_logolar.json  (set kimligi -> Pokellector gorsel adi)
Her gorsel BIR KEZ indirilir ve img/ja/<set>.png (logo) / img/ja/<set>.sym.png (sembol) olarak kaydedilir.
Zaten indirilmis olanlar icin hic istek atilmaz.
"""
import json, os, sys, time, urllib.request

KOK = sys.argv[1] if len(sys.argv) > 1 else '.'
ES = json.load(open(os.path.join(KOK, '.github/scripts/ja_logolar.json'), encoding='utf-8'))
KLASOR = os.path.join(KOK, 'img', 'ja')
os.makedirs(KLASOR, exist_ok=True)

yeni = hata = 0
for sid, ad in ES.items():
    if not ad:
        continue
    slug, n = ad.rsplit('.', 1)
    for tur, son in (('logo', ''), ('symbol', '.sym')):
        yol = os.path.join(KLASOR, f'{sid}{son}.png')
        if os.path.exists(yol):
            continue
        url = f'https://den-media.pokellector.com/logos/{slug}.{tur}.{n}.png'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'KartBorsa/1.0 (kartborsa.com)'})
            with urllib.request.urlopen(req, timeout=30) as r:
                b = r.read()
            if b[:8] == b'\x89PNG\r\n\x1a\n':
                open(yol, 'wb').write(b)
                yeni += 1
            else:
                print('PNG degil:', url)
                hata += 1
        except Exception as e:
            print('alinamadi:', url, e)
            hata += 1
        time.sleep(0.4)
print('yeni gorsel:', yeni, 'alinamayan:', hata)
