#!/usr/bin/env python3
"""KartBorsa: Japonca katalogdaki eksikleri tamamlar (kaynak: Pokellector, jp.pokellector.com).

Kullanım: python3 ja_ek.py <veri klasörü> <site klasörü>
  1) TCGdex'te kartları olmayan Japonca setleri kataloğa ekler (kart adı, numara, resim, set logosu/sembolü).
  2) TCGdex'teki setlerde resmi olmayan kartlara Pokellector resmini koyar (numara eşleşmesiyle),
     o da yoksa katalogda aynı adlı başka bir kartın resmini kullanır (ör. temel enerjiler).
Set sayfaları BİR KEZ okunur ve <veri>/japonca/ek.json içinde saklanır; sonraki günlerde sadece
Pokellector'a yeni eklenen setler okunur. Sonuç <veri>/japonca/cards_ja.json içine yazılır
(japonca.py'den SONRA çalışır; her çalışmada önce eski eklemeler çıkarılıp yeniden eklenir).
"""
import datetime, html, json, os, re, sys, time, urllib.request

VERI, SITE = sys.argv[1], sys.argv[2]
BASE = 'https://jp.pokellector.com'
EKY = f'{VERI}/japonca/ek.json'
KATY = f'{VERI}/japonca/cards_ja.json'

SERI = {
    'Original Series': 'ポケットモンスターカードゲーム', 'Vending Series': 'ポケットモンスターカードゲーム',
    'Neo Series': 'ポケモンカード★neo', 'Pokemon VS Series': 'VS', 'e-Card Era Series': 'ポケモンカードe',
    'DP Era Series': 'DP', 'PPP Promos Series': 'DP', 'DPt Series': 'DPt', 'Legend Series': 'LEGEND',
    'Black & White Series': 'BW', 'Black & White Promos Series': 'BW', 'Pokemon XY Series': 'XY',
    'Sun & Moon Series': 'サン＆ムーン', 'Sword & Shield Series': '剣と盾',
    'Scarlet & Violet Series': 'ポケモンカードゲーム スカーレット&バイオレット',
    'Mega Series': 'ポケモンカードゲーム MEGA',
}


def get(url):
    for t in range(4):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'KartBorsa/1.0 (kartborsa.com)'})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception:
            if t == 3:
                raise
            time.sleep(3 * (t + 1))


def load(p, d):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return d


def sade(no):
    no = str(no).strip()
    return (no.lstrip('0') or '0') if no.isdigit() else no


def tarih(ay_gun, yil):
    try:
        ay_gun = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', ay_gun.strip())
        return datetime.datetime.strptime(f'{ay_gun} {yil}', '%b %d %Y').strftime('%Y/%m/%d')
    except Exception:
        return f'{yil}/12/31' if str(yil).isdigit() else '9999/12/31'


def set_sayfasi(yol):
    """Pokellector set sayfasından: seri, tarih, kart sayısı, kartlar [(no, ad, resim)]."""
    p = get(BASE + yol)
    seri = ''
    m = re.search(r'class="breadcrumbs">(.*?)</div>', p, re.S)
    if m:
        parcalar = re.findall(r'<a[^>]*>([^<]*)</a>', m.group(1))
        if len(parcalar) >= 2:
            seri = html.unescape(parcalar[1]).strip()
    m = re.search(r'Released</span>\s*<span>([^<]*)</span>\s*<cite>([^<]*)</cite>', p)
    t = tarih(m.group(1), m.group(2).strip()) if m else '9999/12/31'
    m = re.search(r'<span>Cards</span>\s*<span>(\d+)</span>', p)
    sayi = int(m.group(1)) if m else 0
    kartlar = []
    for r, no, ad in re.findall(
            r'<div class="card[^"]*">.*?data-src="([^"]+)".*?<div class="plaque">#(\S*) - (.*?)</div>', p, re.S):
        kartlar.append([no.strip(), html.unescape(ad).strip(), html.unescape(r).replace('.thumb.png', '.png')])
    return {'seri': seri, 'tarih': t, 'sayi': sayi, 'kartlar': kartlar}


# ---------- Pokellector set listesi ----------
ek = load(EKY, {'v': 1, 'sayfa': {}})
liste = []
try:
    sp = get(BASE + '/sets')
    for kod, yol, ad_, logo, sembol, ad in re.findall(
            r'<a class="button" name="([^"]*)" href="([^"]+)" title="([^"]*)">'
            r'<img src="([^"]+)"><img class="symbol" src="([^"]+)"[^>]*><span>([^<]*)</span>', sp):
        num = re.search(r'\.logo\.(\d+)\.png', logo)
        liste.append({'kod': kod.strip(), 'yol': yol, 'ad': html.unescape(ad).strip(), 'logo': logo,
                      'sembol': sembol, 'num': num.group(1) if num else ''})
    ek['liste'] = liste
except Exception as e:
    print('Pokellector set listesi alınamadı, önbellek kullanılıyor:', e)
    liste = ek.get('liste', [])
print('Pokellector Japonca set:', len(liste), flush=True)

logolar = load(f'{SITE}/.github/scripts/ja_logolar.json', {})
kapsanan = {}  # pokellector set numarası -> TCGdex set kimliği
for sid, ad in logolar.items():
    if ad:
        kapsanan[ad.rsplit('.', 1)[1]] = sid

kat = load(KATY, None)
if not kat:
    sys.exit('cards_ja.json yok')

# önceki eklemeleri çıkar (her çalışmada temiz eklenir)
eski_setler = kat['sets']
tut = [i for i, s in enumerate(eski_setler) if not (len(s) > 8 and s[8] == 'pl')]
yeni_idx = {i: n for n, i in enumerate(tut)}
kat['sets'] = [eski_setler[i] for i in tut]
kat['cards'] = [c for c in kat['cards'] if c[1] in yeni_idx]
for c in kat['cards']:
    c[1] = yeni_idx[c[1]]
mevcut_kimlik = {s[0].lower() for s in kat['sets']}

# resmi olmayan kartları olan TCGdex setleri
resimsiz = {}
for c in kat['cards']:
    if not c[13]:
        resimsiz.setdefault(kat['sets'][c[1]][0], []).append(c)

okunan = 0


def sayfa(ps):
    global okunan
    if ps['yol'] in ek['sayfa']:
        return ek['sayfa'][ps['yol']]
    try:
        d = set_sayfasi(ps['yol'])
    except Exception as e:
        print('  set sayfası alınamadı', ps['yol'], e)
        return None
    ek['sayfa'][ps['yol']] = d
    okunan += 1
    time.sleep(1.0)
    return d


# ---------- 1) TCGdex setlerinde resmi olmayan kartlar ----------
doldurulan = 0
for ps in liste:
    sid = kapsanan.get(ps['num'])
    if not sid or sid not in resimsiz:
        continue
    d = sayfa(ps)
    if not d:
        continue
    resim = {sade(no): r for no, ad, r in d['kartlar']}
    for c in resimsiz[sid]:
        r = resim.get(sade(c[2]))
        if r:
            c[13] = r
            doldurulan += 1

# aynı adlı kartın resmi (temel enerjiler vb.)
ad_resim = {}
for c in kat['cards']:
    if c[13] and c[0] not in ad_resim:
        ad_resim[c[0]] = c[13]
for c in kat['cards']:
    if not c[13] and ad_resim.get(c[0]):
        c[13] = ad_resim[c[0]]
        doldurulan += 1
print('Resmi tamamlanan kart:', doldurulan, flush=True)

# ---------- 2) TCGdex'te olmayan setler ----------
eklenen_set = eklenen_kart = 0
yeni_setler = []
for ps in liste:
    if ps['num'] in kapsanan:
        continue
    kod = re.sub(r'[^0-9A-Za-z]', '', ps['kod'])
    sid = 'ja-' + (kod or 'pl' + ps['num'])
    if sid.lower() in mevcut_kimlik:
        sid = 'ja-pl' + ps['num']
    if sid.lower() in mevcut_kimlik:
        continue
    d = sayfa(ps)
    if not d or not d['kartlar']:
        continue
    seri = SERI.get(d['seri'], d['seri'] or 'Diğer')
    s = [sid, ps['ad'], seri, d['tarih'], d['sayi'] or len(d['kartlar']), ps['logo'], ps['sembol'], 'ja', 'pl']
    kartlar = []
    gorulen = set()
    for no, ad, r in d['kartlar']:
        nk = re.sub(r'[^0-9A-Za-z]', '', no) or str(len(kartlar) + 1)
        cid = f'{sid}-{nk}'
        while cid in gorulen:
            cid += 'b'
        gorulen.add(cid)
        kartlar.append([ad, None, sade(no), '', '', '', '', '', '', [], [], [], '', r, cid, ad])
    yeni_setler.append((s, kartlar))
    mevcut_kimlik.add(sid.lower())
    eklenen_set += 1
    eklenen_kart += len(kartlar)

# ---------- birleştir, tarihe göre sırala ----------
gruplar = {i: (s, []) for i, s in enumerate(kat['sets'])}
for c in kat['cards']:
    gruplar[c[1]][1].append(c)
hepsi = list(gruplar.values()) + yeni_setler
hepsi.sort(key=lambda g: (g[0][3] or '9999', g[0][0]))
kat['sets'], kat['cards'] = [], []
for i, (s, kartlar) in enumerate(hepsi):
    kat['sets'].append(s)
    for c in kartlar:
        c[1] = i
        kat['cards'].append(c)

json.dump(kat, open(KATY, 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
json.dump(ek, open(EKY, 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
print(f'Eklenen set: {eklenen_set}, kart: {eklenen_kart}; okunan sayfa: {okunan}; '
      f'toplam {len(kat["sets"])} set, {len(kat["cards"])} kart; resmi olmayan '
      f'{sum(1 for c in kat["cards"] if not c[13])}', flush=True)
