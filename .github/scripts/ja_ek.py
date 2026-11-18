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
import datetime, html, json, os, re, sys, time, urllib.parse, urllib.request

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
    for href, r, no, ad in re.findall(
            r'<div class="card[^"]*">.*?<a href="([^"]+)"[^>]*>.*?data-src="([^"]+)".*?<div class="plaque">#(\S*) - (.*?)</div>',
            p, re.S):
        kartlar.append([no.strip(), html.unescape(ad).strip(), html.unescape(r).replace('.thumb.png', '.png'),
                        html.unescape(href)])
    return {'seri': seri, 'tarih': t, 'sayi': sayi, 'kartlar': kartlar}


# ---------- Pokellector set listesi ----------
ek = load(EKY, {})
if ek.get('v') != 2:
    ek = {'v': 2, 'sayfa': {}, 'kart': {}}
ek.setdefault('kart', {})
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
BAS = time.time()
BUTCE = float(os.environ.get('BUTCE', '1200'))  # kart sayfaları için saniye
TODAY = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).strftime('%Y-%m-%d')

# önceki eklemeleri çıkar (her çalışmada temiz eklenir)
eski_setler = kat['sets']
tut = [i for i, s in enumerate(eski_setler) if not (len(s) > 8 and s[8] == 'pl')]
yeni_idx = {i: n for n, i in enumerate(tut)}
kat['sets'] = [eski_setler[i] for i in tut]
kat['cards'] = [c for c in kat['cards'] if c[1] in yeni_idx and not (len(c) > 16 and c[16] == 'pl')]
for c in kat['cards']:
    c[1] = yeni_idx[c[1]]
mevcut_kimlik = {s[0].lower() for s in kat['sets']}
sid_idx = {s[0]: i for i, s in enumerate(kat['sets'])}

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


# ---------- Pokémon adları (kart türü için) ----------
TUR = set()
try:
    for x in json.loads(get('https://pokeapi.co/api/v2/pokemon-species?limit=2000'))['results']:
        TUR.add(x['name'].replace('-', ' '))
except Exception as e:
    print('PokeAPI alınamadı:', e)


def kategori(en, ja=''):
    if 'Energy' in en or 'エネルギー' in ja:
        return 'Energy'
    n = ' ' + re.sub(r"[^a-z0-9 ]", ' ', en.lower().replace("'s ", ' ').replace('.', '')) + ' '
    n = re.sub(r'\s+', ' ', n)
    for t in TUR:
        if f' {t} ' in n:
            return 'Pokémon'
    return 'Trainer' if TUR else ''


def kart_bilgi(href):
    """Kart sayfası: Japonca ad, nadirlik, Cardmarket € fiyatı."""
    p = get(BASE + urllib.parse.quote(href, safe="/%-._~'()!*,;:@&=+$"))
    m = re.search(r'<strong>JPN:</strong>\s*(?:<a[^>]*>)?([^<]*)', p)
    ja = html.unescape(m.group(1)).strip() if m else ''
    m = re.search(r'<strong>Rarity:</strong>\s*([^<]*)', p)
    nd = html.unescape(m.group(1)).strip() if m else ''
    m = re.search(r'<div class="price">\s*€\s*([\d.,]+)\s*</div>\s*<cite>\s*from\s*<a href="https://www\.cardmarket', p)
    eur = None
    if m:
        try:
            eur = round(float(m.group(1).replace(',', '')), 2)
        except Exception:
            eur = None
    return [ja, nd, eur, TODAY]


# ---------- 1) TCGdex setleri: resmi olmayan ve hiç olmayan kartlar ----------
doldurulan = eklenen_no = 0
tcg_ek = []   # (set index, pokellector kartı)
for ps in liste:
    sid = kapsanan.get(ps['num'])
    if not sid or sid not in sid_idx:
        continue
    d = sayfa(ps)
    if not d:
        continue
    si = sid_idx[sid]
    kartlar = [c for c in kat['cards'] if c[1] == si]
    var = {sade(c[2]) for c in kartlar}
    resim = {sade(k[0]): k[2] for k in d['kartlar']}
    for c in kartlar:
        if not c[13] and resim.get(sade(c[2])):
            c[13] = resim[sade(c[2])]
            doldurulan += 1
    for k in d['kartlar']:
        if sade(k[0]) not in var:
            var.add(sade(k[0]))
            tcg_ek.append((si, sid, k))

# ---------- 2) TCGdex'te olmayan setler ----------
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
    yeni_setler.append((s, d['kartlar']))
    mevcut_kimlik.add(sid.lower())

# ---------- 3) kart sayfaları (Japonca ad, nadirlik, fiyat) — zaman bütçesiyle ----------
gerek = [k[3] for _, _, k in tcg_ek if len(k) > 3] + [k[3] for _, ks in yeni_setler for k in ks if len(k) > 3]
hic = [h for h in gerek if h not in ek['kart']]
eski = sorted((h for h in gerek if h in ek['kart'] and ek['kart'][h][3] < TODAY),
              key=lambda h: ek['kart'][h][3])
sira = hic + [h for h in eski if (datetime.date.fromisoformat(TODAY) -
                                  datetime.date.fromisoformat(ek['kart'][h][3])).days >= 5]
kart_okunan = 0
for h in sira:
    if time.time() - BAS > BUTCE:
        break
    try:
        ek['kart'][h] = kart_bilgi(h)
        kart_okunan += 1
    except Exception as e:
        print('  kart sayfası alınamadı', h, e)
        if h not in ek['kart']:
            ek['kart'][h] = ['', '', None, TODAY]  # 5 gün sonra yeniden denenir
    time.sleep(0.6)
kalan = sum(1 for h in gerek if h not in ek['kart'])
print(f'Kart sayfası okunan: {kart_okunan}, bilgisi hiç alınmamış kalan: {kalan}', flush=True)
open(f'{VERI}/japonca/ek_kalan.txt', 'w').write(str(kalan))


def kart_yap(sid, k, on=''):
    no, ad, r = k[0], k[1], k[2]
    b = ek['kart'].get(k[3]) if len(k) > 3 else None
    ja = (b[0] if b else '') or ad
    nd = b[1] if b else ''
    nk = re.sub(r'[^0-9A-Za-z]', '', no) or 'x'
    return [ja, None, sade(no), nd, kategori(ad, ja), '', '', '', '', [], [], [], '', r, f'{sid}-{on}{nk}', ad, 'pl'], \
        (b[2] if b else None)


fiyat = {}
for si, sid, k in tcg_ek:
    c, eur = kart_yap(sid, k, 'p')
    c[1] = si
    kat['cards'].append(c)
    if eur is not None:
        fiyat.setdefault(sid, {})[c[14]] = eur
eklenen_kart = 0
gruplar = {i: (s, []) for i, s in enumerate(kat['sets'])}
for c in kat['cards']:
    gruplar[c[1]][1].append(c)
for s, ks in yeni_setler:
    liste_k, gorulen = [], set()
    for k in ks:
        c, eur = kart_yap(s[0], k)
        while c[14] in gorulen:
            c[14] += 'b'
        gorulen.add(c[14])
        liste_k.append(c)
        if eur is not None:
            fiyat.setdefault(s[0], {})[c[14]] = eur
    gruplar[len(gruplar)] = (s, liste_k)
    eklenen_kart += len(liste_k)

# ---------- birleştir, tarihe göre sırala ----------
hepsi = sorted(gruplar.values(), key=lambda g: (g[0][3] or '9999', g[0][0]))
kat['sets'], kat['cards'] = [], []
for i, (s, kartlar) in enumerate(hepsi):
    kat['sets'].append(s)
    for c in sorted(kartlar, key=lambda c: (int(c[2]) if str(c[2]).isdigit() else 99999, str(c[2]))):
        c[1] = i
        kat['cards'].append(c)
# resmi hâlâ olmayanlar: aynı adlı başka kartın resmi (temel enerjiler vb.)
ad_resim = {}
for c in kat['cards']:
    if c[13] and c[0] not in ad_resim:
        ad_resim[c[0]] = c[13]
for c in kat['cards']:
    if not c[13] and ad_resim.get(c[0]):
        c[13] = ad_resim[c[0]]
        doldurulan += 1
json.dump(kat, open(KATY, 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
json.dump(ek, open(EKY, 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)

# ---------- fiyatlar (Pokellector'daki Cardmarket €) ----------
os.makedirs(f'{VERI}/set', exist_ok=True)
ozet = load(f'{VERI}/ozet.json', {'u': TODAY, 'c': {}})
say = 0
for sid, kartlar in fiyat.items():
    yol = f'{VERI}/set/{sid}.json'
    dosya = load(yol, {'u': TODAY, 'c': {}})
    for cid, eur in kartlar.items():
        if cid in dosya['c'] and dosya['c'][cid].get('pl') is None:
            continue  # TCGdex fiyatı varsa ona dokunma
        hist = [h for h in dosya['c'].get(cid, {}).get('h', []) if h[0] != TODAY]
        if not hist or hist[-1][2] != eur:
            hist.append([TODAY, None, eur])
        hist = hist[-400:]
        dosya['c'][cid] = {'h': hist, 'm': [None, None, eur, None, None, None, None], 'mu': TODAY.replace('-', '/'),
                           'pl': 1}
        once = hist[-2] if len(hist) >= 2 else [None, None, None]
        ozet['c'][cid] = [None, eur, None, None, once[1], once[2], once[0]]
        say += 1
    dosya['u'] = TODAY
    json.dump(dosya, open(yol, 'w'), separators=(',', ':'))
json.dump(ozet, open(f'{VERI}/ozet.json', 'w'), separators=(',', ':'))
print(f'TCGdex setlerinde resmi tamamlanan: {doldurulan}, eklenen eksik numara: {len(tcg_ek)}; '
      f'yeni set: {len(yeni_setler)}, kart: {eklenen_kart}; okunan set sayfası: {okunan}; fiyatlı kart: {say}; '
      f'toplam {len(kat["sets"])} set, {len(kat["cards"])} kart; resmi olmayan '
      f'{sum(1 for c in kat["cards"] if not c[13])}', flush=True)
