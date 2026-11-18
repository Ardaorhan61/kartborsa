#!/usr/bin/env python3
"""KartBorsa: Japonca kart kataloğu + Japonca kart fiyatları.

Kullanım: python3 japonca.py <veri klasörü>
  <veri>/japonca/cards_ja.json   → sitedeki cards.json ile aynı biçimde Japonca katalog
  <veri>/japonca/resim.json      → Scrydex resim kontrolü önbelleği
  <veri>/set/ja-<set>.json       → Japonca kartların fiyatları ve geçmişi
  <veri>/ozet.json               → Japonca fiyatlar da eklenir (fiyatlar.py'den SONRA çalışır)
Kaynaklar: TCGdex (kart bilgisi, resim, Cardmarket fiyatı), Scrydex resim adresleri (sadece daha önce kaydedilmiş olanlar, Scrydex'e otomatik istek atılmaz),
PokeAPI (Pokémon'ların İngilizce adları, aramada kullanılır).
"""
import hashlib, json, os, re, sys, time, datetime, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

OUT = sys.argv[1]
TCG = 'https://api.tcgdex.net/v2/ja'
TODAY = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).strftime('%Y-%m-%d')
KEEP_DAYS = 400
os.makedirs(f'{OUT}/japonca', exist_ok=True)
os.makedirs(f'{OUT}/set', exist_ok=True)


def get(url, raw=False, tries=4):
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'KartBorsa/1.0 (kartborsa.com)'})
            with urllib.request.urlopen(req, timeout=40) as r:
                b = r.read()
                return b if raw else json.loads(b)
        except Exception as e:
            if t == tries - 1:
                raise
            time.sleep(1.5 * (t + 1))


def load(p, d):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return d


def r2(x):
    return None if x is None else round(float(x), 2)


# ---------- Pokémon İngilizce adları (arama için) ----------
EN = {}
try:
    for s in get('https://pokeapi.co/api/v2/pokemon-species?limit=2000')['results']:
        n = int(s['url'].rstrip('/').split('/')[-1])
        EN[n] = s['name'].replace('-', ' ').title()
except Exception as e:
    print('PokeAPI alınamadı:', e)

# ---------- setler ----------
liste = get(f'{TCG}/sets')
def set_al(s):
    try:
        return get(f"{TCG}/sets/{urllib.parse.quote(s['id'])}")
    except Exception as e:
        print('  set alınamadı', s['id'], e)
        return None


with ThreadPoolExecutor(12) as ex:
    detay = list(ex.map(set_al, liste))
detay = [s for s in detay if s and s.get('cards')]
detay.sort(key=lambda s: (s.get('releaseDate') or '9999', s['id']))
print('Japonca set:', len(detay), 'kart:', sum(len(s['cards']) for s in detay), flush=True)

# ---------- kart ayrıntıları ----------
def kart(cid):
    try:
        return get(f'{TCG}/cards/{urllib.parse.quote(cid)}')
    except Exception as e:
        return None

ids = [c['id'] for s in detay for c in s['cards']]
bas = time.time()
KART = {}
with ThreadPoolExecutor(16) as ex:
    for n, (cid, d) in enumerate(zip(ids, ex.map(kart, ids)), 1):
        if d:
            KART[cid] = d
        if n % 1000 == 0:
            print(n, '/', len(ids), int(time.time() - bas), 'sn', flush=True)
print('Kart ayrıntısı alınan:', len(KART), '/', len(ids), flush=True)

# ---------- Scrydex resim kontrolü (TCGdex'te resmi olmayanlar) ----------
def scrydex_kod(tid):
    t = tid.lower()
    m = re.fullmatch(r'pmcg(\d)', t)
    if m:
        return 'base' + m.group(1)
    m = re.fullmatch(r'e(\d)', t)
    if m:
        return 'ecard' + m.group(1)
    if re.fullmatch(r's\d.*', t) and not t.startswith('sv') and not t.startswith('sm'):
        return 'swsh' + t[1:]
    return {'sv-p': 'svp', 'm-p': 'mp', 'smp2': 'smp'}.get(t, t)


def no_sade(local):
    local = str(local)
    return (local.lstrip('0') or '0') if local.isdigit() else local


RESIM = load(f'{OUT}/japonca/resim.json', {})


def scrydex_var(key):
    # Scrydex'e otomatik istek atılmaz (kuralları gereği); sadece daha önce kaydedilmiş sonuç kullanılır.
    return RESIM.get(key, False)


gerek = []
for s in detay:
    for c in s['cards']:
        d = KART.get(c['id']) or c
        if not d.get('image'):
            gerek.append(f"{scrydex_kod(s['id'])}_ja-{no_sade(c['localId'])}")

# ---------- katalog ----------
HARF = {'Grass': 'G', 'Fire': 'R', 'Water': 'W', 'Lightning': 'L', 'Psychic': 'P', 'Fighting': 'F', 'Darkness': 'D',
        'Metal': 'M', 'Fairy': 'Y', 'Dragon': 'N', 'Colorless': 'C'}
KAT = {'Pokemon': 'Pokémon', 'Trainer': 'Trainer', 'Energy': 'Energy'}
EVRE = {'Basic': 'Basic', 'Stage1': 'Stage 1', 'Stage2': 'Stage 2', 'BREAK': 'BREAK', 'VMAX': 'VMAX', 'VSTAR': 'VSTAR',
        'MEGA': 'MEGA', 'LEVEL-UP': 'LEVEL-UP', 'RESTORED': 'Restored'}


def nadir(r):
    return ' '.join(w[:1].upper() + w[1:] for w in str(r or '').split()) if r and r != 'None' else ''


sets_out, cards_out, fiyat = [], [], {}
resimsiz = 0
for si, s in enumerate(detay):
    logo = (s.get('logo') + '.png') if s.get('logo') else ''
    sembol = (s.get('symbol') + '.png') if s.get('symbol') else ''
    tarih = (s.get('releaseDate') or '').replace('-', '/')
    seri = (s.get('serie') or {}).get('name') or ''
    resmi = (s.get('cardCount') or {}).get('official') or 0
    sets_out.append(['ja-' + s['id'], s['name'], seri, tarih, resmi, logo, sembol, 'ja'])
    for c in s['cards']:
        d = KART.get(c['id']) or c
        local = str(d.get('localId') or c.get('localId'))
        cid = f"ja-{s['id']}-{local}"
        if d.get('image'):
            img = d['image'] + '/low.webp'
        else:
            key = f"{scrydex_kod(s['id'])}_ja-{no_sade(local)}"
            img = f'https://images.scrydex.com/pokemon/{key}/small' if RESIM.get(key) else ''
            if not img:
                resimsiz += 1
        kat = KAT.get(d.get('category'), d.get('category') or '')
        alt = []
        if d.get('stage'):
            alt.append(EVRE.get(d['stage'], d['stage']))
        if d.get('trainerType'):
            alt.append(d['trainerType'])
        if d.get('energyType'):
            alt.append(d['energyType'])
        suf = d.get('suffix')
        if suf:
            alt.append('ex' if suf == 'EX' and (s.get('serie') or {}).get('id') in ('SV', 'M') else suf)
        atk = [[a.get('name') or '', ''.join(HARF.get(x, 'C') for x in (a.get('cost') or [])),
                str(a.get('damage') or ''), a.get('effect') or ''] for a in (d.get('attacks') or [])]
        abl = [[a.get('name') or '', a.get('effect') or ''] for a in (d.get('abilities') or [])]
        kural = d.get('effect') or ''
        ingilizce = ' '.join(EN.get(n, '') for n in (d.get('dexId') or [])).strip()
        cards_out.append([d.get('name') or c.get('name') or '', si, no_sade(local), nadir(d.get('rarity')), kat,
                          '/'.join(alt), str(d.get('hp') or ''), '/'.join(d.get('types') or []),
                          d.get('illustrator') or '', atk, abl, [kural] if kural else [], d.get('evolveFrom') or '',
                          img, cid, ingilizce])
        # fiyat (Cardmarket, EUR)
        pr = d.get('pricing') or {}
        if not pr.get('cardmarket'):
            for v in d.get('variants_detailed') or []:
                if (v.get('pricing') or {}).get('cardmarket'):
                    pr = v['pricing']
                    break
        cm = pr.get('cardmarket') or {}
        if cm:
            suf2 = '-holo' if cm.get('avg') is None and not cm.get('trend') and cm.get('trend-holo') else ''
            m = [r2(cm.get(k + suf2)) for k in ('avg', 'low', 'trend', 'avg1', 'avg7', 'avg30')] + [None if suf2 else r2(cm.get('trend-holo'))]
            if any(x is not None for x in m):
                fiyat.setdefault('ja-' + s['id'], {})[cid] = (m, (cm.get('updated') or '')[:10].replace('-', '/'))

json.dump({'v': 1, 'built': TODAY, 'sets': sets_out, 'cards': cards_out},
          open(f'{OUT}/japonca/cards_ja.json', 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
print(f'cards_ja.json: {len(sets_out)} set, {len(cards_out)} kart, resmi olmayan {resimsiz}', flush=True)

# ---------- fiyat dosyaları + özet ----------
ozet = load(f'{OUT}/ozet.json', {'u': TODAY, 'c': {}})
ozet['c'] = {k: v for k, v in ozet['c'].items() if not k.startswith('ja-')}
say = 0
for sid, kartlar in fiyat.items():
    yol = f'{OUT}/set/{sid}.json'
    eski = load(yol, {'c': {}})
    yeni = {'u': TODAY, 'c': {}}
    for cid, (m, mu) in kartlar.items():
        hist = [h for h in eski['c'].get(cid, {}).get('h', []) if h[0] != TODAY]
        if m[2] is not None:
            hist.append([TODAY, None, m[2]])
        hist = hist[-KEEP_DAYS:]
        yeni['c'][cid] = {'h': hist, 'm': m, 'mu': mu}
        if m[2] is not None:
            once = hist[-2] if len(hist) >= 2 else [None, None, None]
            ozet['c'][cid] = [None, m[2], m[4], m[5], once[1], once[2], once[0]]
            say += 1
    json.dump(yeni, open(yol, 'w'), separators=(',', ':'))
json.dump(ozet, open(f'{OUT}/ozet.json', 'w'), separators=(',', ':'))
print('Japonca fiyatlı kart:', say)
