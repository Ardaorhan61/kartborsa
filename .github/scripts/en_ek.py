#!/usr/bin/env python3
"""KartBorsa: İngilizce katalogdaki eksik kartları ve setleri tamamlar (kaynak: TCGdex + Scrydex resimleri).

Kullanım: python3 en_ek.py cards.json
  1) EK_SETLER'deki setlerde TCGdex'te olup katalogda olmayan kartları ekler (aynı numara varsa dokunmaz).
     Katalogda olmayan set (ör. MEP promoları) tarihine göre doğru yere yeni set olarak eklenir.
  2) Resim: önce Scrydex (yer tutucu resim değilse), yoksa TCGdex. Hiç resmi olmayan kart EKLENMEZ.
  3) Kaynakta doğrulanmış nadirlik düzeltmeleri (NADIR) uygulanır.
Sadece kaynakta birebir bulunan bilgi yazılır; tahmin yapılmaz.
"""
import json, re, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

YOL = sys.argv[1] if len(sys.argv) > 1 else 'cards.json'
TCGDEX = 'https://api.tcgdex.net/v2/en'
SCRY = 'https://images.scrydex.com/pokemon/'
UA = {'User-Agent': 'KartBorsa-katalog/1.0 (kartborsa.com)'}

# site set kodu -> (TCGdex set kodu, set adı, seri, çıkış tarihi)  — set katalogda varsa sadece eksik kartlar eklenir
EK_SETLER = {
    'svp': ('svp', 'Scarlet & Violet Black Star Promos', 'Scarlet & Violet', '2023/01/01'),
    'mee': ('mee', 'Mega Evolution Energies', 'Mega Evolution', '2025/09/25'),
    'mep': ('mep', 'MEP Black Star Promos', 'Mega Evolution', '2025/09/26'),
}

# TCGdex'te doğrulanmış nadirlikler (katalogda boş ya da hatalıydı)
NADIR = {k: 'Common' for k in (
    'gym1-127,gym1-128,gym1-129,gym1-130,gym1-131,gym1-132,gym2-127,gym2-128,gym2-129,gym2-130,gym2-131,gym2-132,'
    'ecard1-160,ecard1-161,ecard1-162,ecard1-163,ecard1-164,ecard1-165,base4-125,base4-126,base4-127,base4-128,'
    'base4-129,base4-130,neo1-106,neo1-107,neo1-108,neo1-109,neo1-110,neo1-111,base1-97,base1-98,base1-99,'
    'base1-100,base1-101,base1-102,dv1-21').split(',')}
NADIR.update({'dv1-18': 'Rare', 'dv1-19': 'Rare', 'me55-R': 'RGB Rare', 'me55-G': 'RGB Rare', 'me55-B': 'RGB Rare'})
NADIR_AD = {'MEGA_ATTACK_RARE': 'Mega Attack Rare'}

ENJ = {'Grass': 'G', 'Fire': 'R', 'Water': 'W', 'Lightning': 'L', 'Psychic': 'P', 'Fighting': 'F',
       'Darkness': 'D', 'Metal': 'M', 'Fairy': 'Y', 'Dragon': 'N', 'Colorless': 'C'}


def get(url, tries=4):
    for t in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(3 * (t + 1))
        except Exception:
            time.sleep(3 * (t + 1))
    raise RuntimeError('alınamadı: ' + url)


def png_bas(url):
    """PNG başlığı: (genişlik, yükseklik, renk tipi) ya da None."""
    try:
        h = dict(UA, Range='bytes=0-63')
        with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=40) as r:
            b = r.read(64)
        if b[:8] != b'\x89PNG\r\n\x1a\n':
            return 'x'  # PNG değil ama resim var (ör. webp)
        return (int.from_bytes(b[16:20], 'big'), int.from_bytes(b[20:24], 'big'), b[25])
    except Exception:
        return None


def var_mi(url):
    try:
        req = urllib.request.Request(url, headers=UA, method='HEAD')
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status == 200
    except Exception:
        return False


YER_TUTUCU = png_bas(SCRY + 'zzz-999/large')  # Scrydex'in "resim yok" görseli
print('Scrydex yer tutucu:', YER_TUTUCU, flush=True)


def scry_gercek(url):
    b = png_bas(url)
    return b is not None and b != YER_TUTUCU


def sade(no):
    no = str(no).strip()
    return (no.lstrip('0') or '0') if no.isdigit() else no


def nk(no):
    d = re.sub(r'\D', '', str(no))
    return (int(d) if d else 10 ** 6, str(no))


def kart_yap(sid, tid):
    d = get(f'{TCGDEX}/cards/{tid}')
    if not d:
        return None
    no = sade(d.get('localId', ''))
    kat = {'Pokemon': 'Pokémon'}.get(d.get('category'), d.get('category') or '')
    alt = ''
    if kat == 'Pokémon':
        p = [re.sub(r'^Stage(\d)', r'Stage \1', d.get('stage') or '')]
        if d.get('name', '').startswith('Mega '):
            p.append('MEGA')
        if d.get('suffix'):
            p.append('ex' if d['name'].endswith(' ex') else d['suffix'])
        alt = '/'.join(x for x in p if x)
    elif kat == 'Trainer':
        alt = d.get('trainerType') or ''
    elif kat == 'Energy':
        alt = {'Normal': 'Basic'}.get(d.get('energyType'), d.get('energyType') or '')
    atk = [[a.get('name', ''), ''.join(ENJ.get(x, '') for x in a.get('cost') or []),
            '' if a.get('damage') is None else str(a['damage']), a.get('effect') or ''] for a in d.get('attacks') or []]
    yet = [[a.get('name', ''), a.get('effect') or ''] for a in d.get('abilities') or []]
    nadir = d.get('rarity') if d.get('rarity') not in (None, '', 'None') else ('Promo' if sid.endswith('p') else '')
    resim = ''
    s = f'{SCRY}{sid}-{no}/'
    if scry_gercek(s + 'large'):
        resim = s + 'small'
    elif d.get('image') and var_mi(d['image'] + '/low.webp'):
        resim = d['image'] + '/low.webp'
    if not resim:
        print(f'  resmi yok, eklenmedi: {sid}-{no} {d.get("name")}')
        return None
    return [d.get('name', ''), 0, no, nadir, kat, alt, str(d['hp']) if d.get('hp') else '',
            '/'.join(d.get('types') or []), d.get('illustrator') or '', atk, yet,
            (d.get('effect') or '') if kat != 'Pokémon' else '', d.get('evolveFrom') or '', resim, f'{sid}-{no}']


kat = json.load(open(YOL, encoding='utf-8'))
gr = [[s, []] for s in kat['sets']]
for c in kat['cards']:
    gr[c[1]][1].append(c)
sidx = {s[0]: i for i, s in enumerate(kat['sets'])}

# nadirlik düzeltmeleri
nd = 0
for c in kat['cards']:
    yeni = NADIR.get(c[14]) or NADIR_AD.get(c[3])
    if yeni and c[3] != yeni and (not c[3] or c[3] in NADIR_AD or c[14] in NADIR):
        c[3] = yeni
        nd += 1
print('Nadirlik düzeltilen:', nd, flush=True)

eklenen = 0
for sid, (tid, ad, seri, tarih) in EK_SETLER.items():
    ts = get(f'{TCGDEX}/sets/{tid}')
    if not ts:
        print(sid, ': TCGdex seti yok')
        continue
    if sid in sidx:
        g = gr[sidx[sid]]
    else:
        logo, sem = SCRY + f'{sid}-logo/logo', SCRY + f'{sid}-symbol/symbol'
        g = [[sid, ad, seri, tarih, 0, logo if png_bas(logo) else '', sem if png_bas(sem) else ''], []]
        gr.append(g)
    var = {sade(c[2]) for c in g[1]}
    eksik = [c['id'] for c in ts.get('cards') or [] if sade(c.get('localId', '')) not in var]
    with ThreadPoolExecutor(max_workers=6) as ex:
        yeni = [k for k in ex.map(lambda t: kart_yap(sid, t), eksik) if k]
    g[1].extend(yeni)
    g[1].sort(key=lambda c: nk(c[2]))
    if sid not in sidx:
        g[0][4] = len(g[1])
    eklenen += len(yeni)
    print(f'{sid}: TCGdex {len(ts.get("cards") or [])} kart, eksik {len(eksik)}, eklenen {len(yeni)}', flush=True)

gr = [g for g in gr if g[1] or g[0][0] in sidx]  # boş kalan yeni set eklenmez
sira = sorted(range(len(gr)), key=lambda i: (gr[i][0][3] or '9999', i))
kat['sets'], kat['cards'] = [], []
for n, i in enumerate(sira):
    kat['sets'].append(gr[i][0])
    for c in gr[i][1]:
        c[1] = n
        kat['cards'].append(c)
kat['built'] = time.strftime('%Y-%m-%d')
json.dump(kat, open(YOL, 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
print(f'Toplam eklenen kart: {eklenen}; {len(kat["sets"])} set, {len(kat["cards"])} kart', flush=True)
