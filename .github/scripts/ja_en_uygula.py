#!/usr/bin/env python3
"""KartBorsa: Japonca kart ve set adlarının yanına İngilizce adlarını parantez içinde yazar.

Kullanım: python3 ja_en_uygula.py <veri klasörü> <site klasörü> <_site/cards_ja.json>
Sıra: 1) kartın kendi İngilizce adı (TCGdex/Pokellector), Limitless daha ayrıntılıysa o (ör. "Sceptile" -> "Sceptile-GX")
      2) Limitless (aynı set, aynı numara)  3) katalogda aynı Japonca adlı kartın İngilizce adı
      4) Bulbapedia (aynı set, aynı Japonca ad). Hiçbirinde yoksa ad olduğu gibi kalır (tahmin yok).
"""
import json, re, sys, unicodedata

VERI, SITE, KAT = sys.argv[1], sys.argv[2], sys.argv[3]
JP = re.compile(r'[぀-ヿ一-鿿]')


def load(p, d):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return d


kat = json.load(open(KAT, encoding='utf-8'))
src = load(f'{VERI}/japonca/ja_en.json', {})
lim, bp = src.get('lim', {}), src.get('bp', {'setler': [], 'kart': {}})
ek = load(f'{VERI}/japonca/ek.json', {})
logolar = load(f'{SITE}/.github/scripts/ja_logolar.json', {})
pl_ad = {p['num']: p['ad'] for p in ek.get('liste', [])}


def nn(s):
    s = unicodedata.normalize('NFD', str(s).lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn'))


def jn(s):
    return unicodedata.normalize('NFKC', re.sub(r'[\s　・･「」『』]', '', str(s)))


def moji(s):
    return s.replace('Ã©', 'é').replace('â€™', '’') if s else s


def sade(no):
    no = str(no).strip()
    return (no.lstrip('0') or '0') if no.isdigit() else no


def pl_en(s):
    u = f'{s[5] or ""}{s[6] or ""}'
    m = re.search(r'\.(?:logo|symbol)\.(\d+)\.png', u)
    if m and pl_ad.get(m.group(1)):
        return pl_ad[m.group(1)]
    v = logolar.get(s[0])
    if v and pl_ad.get(v.rsplit('.', 1)[-1]):
        return pl_ad[v.rsplit('.', 1)[-1]]
    return None


# ---- Limitless: Japonca ad -> İngilizce ad (tüm setler; %80 ve üzeri aynıysa) ----
_say = {}
for v in lim.values():
    for n, a in (v.get('kj') or {}).items():
        e = v.get('k', {}).get(n)
        if e and a:
            _say.setdefault(jn(a), {}).setdefault(e, 0)
            _say[jn(a)][e] += 1
genel_lj = {}
for a, m in _say.items():
    e = sorted(m.items(), key=lambda x: -x[1])
    if e[0][1] / sum(m.values()) >= 0.8:
        genel_lj[a] = e[0][0]

# ---- set eşleştirme: site seti -> Limitless kodu ----
lkod = {nn(k): k for k in lim}
lad = {nn(v['ad']): k for k, v in lim.items()}
lja = {jn(v['ja']): k for k, v in lim.items() if v.get('ja')}
ELLE = {'ja-BW8': 'BW8n', 'ja-pl144': 'MGm', 'ja-XY8': 'XY8b', 'ja-pl175': 'XY8r', 'ja-XY11': 'XY11b', 'ja-pl193': 'XY11r'}
HARIC = {'ja-MG'}  # aynı kod, farklı set
ESET = {'ja-PP': 'P Promotional cards', 'ja-TP': 'T Promotional cards', 'ja-ADVP': 'ADV-P Promotional cards',
        'ja-ADV1': 'ADV Expansion Pack', 'ja-PCGP': 'PCG-P Promotional cards', 'ja-DP1D': 'Diamond Collection',
        'ja-DP1P': 'Pearl Collection', 'ja-DP4D': 'Dawn Dash', 'ja-DP4M': 'Moonlit Pursuit', 'ja-DP5T': 'Temple of Anger',
        'ja-DP5C': 'Cry from the Mysterious', 'ja-LP': 'L-P Promotional cards'}
bpset = [(jn(j), b) for j, b, _ in bp.get('setler', [])]


def bp_baslik(s):
    n = jn(s[1])
    for j, b in bpset:
        if j.startswith(n) and (len(j) == len(n) or not JP.match(j[len(n)])):
            return b
    return None


set_lim, set_en, set_lj = {}, {}, {}
for s in kat['sets']:
    sid = s[0]
    plen = pl_en(s)
    k = None
    if sid not in HARIC:
        k = ELLE.get(sid) or lkod.get(nn(sid[3:])) or lja.get(jn(s[1])) or (lad.get(nn(plen)) if plen else None)
    if k and lim.get(k, {}).get('k'):
        set_lim[sid] = lim[k]['k']
        kj = lim[k].get('kj') or {}
        set_lj[sid] = {jn(a): lim[k]['k'][n] for n, a in kj.items() if lim[k]['k'].get(n)}
    if k and lim.get(k, {}).get('k'):
        set_en[sid] = lim[k]['ad']
    elif ESET.get(sid):
        set_en[sid] = ESET[sid]
    elif plen:
        set_en[sid] = plen
    elif bp_baslik(s):
        set_en[sid] = bp_baslik(s)

# ---- Bulbapedia: kaynakta makine çevirisiyle bozulmuş Japonca adları gerçek adla değiştir ----
ad_duz = 0
grup = {}
for c in kat['cards']:
    grup.setdefault(c[1], []).append(c)
for i, s in enumerate(kat['sets']):
    b = bp_baslik(s)
    satirlar = bp.get('satir', {}).get(b) if b else None
    if not satirlar:
        continue
    jset = {jn(j) for _, _, j in satirlar}
    enmap = {}
    for _, e, j in satirlar:
        enmap.setdefault(nn(e), set()).add(j)
    nomap = {}
    for no, e, j in satirlar:
        if re.fullmatch(r'\d+', no or '') and sade(no) not in nomap:
            nomap[sade(no)] = (e, j)
    kartlar = grup.get(i, [])
    ayni = top = 0
    for c in kartlar:
        c15 = moji(c[15]) if len(c) > 15 and c[15] and not JP.search(c[15]) else ''
        r = nomap.get(sade(c[2]))
        if c15 and r:
            top += 1
            ayni += nn(r[0]) == nn(c15)
    numara_ok = top >= 10 and ayni / top >= 0.85
    jmap = {}
    for _, e, j in satirlar:
        jmap.setdefault(jn(j), set()).add(e)
    for c in kartlar:
        if jn(c[0]) in jset:
            if len(c) > 15 and not (c[15] and not JP.search(c[15])):
                r = nomap.get(sade(c[2]))
                if numara_ok and r and jn(r[1]) == jn(c[0]):
                    c[15] = r[0]
                elif len(jmap.get(jn(c[0]), ())) == 1:
                    c[15] = next(iter(jmap[jn(c[0])]))
            continue
        c15 = moji(c[15]) if len(c) > 15 and c[15] and not JP.search(c[15]) else ''
        aday = None
        if numara_ok and nomap.get(sade(c[2])):
            aday = nomap[sade(c[2])]
        elif c15 and len(enmap.get(nn(c15), ())) == 1:
            aday = (c15, next(iter(enmap[nn(c15)])))
        if aday:
            c[0] = aday[1]
            if len(c) > 15 and not c15:
                c[15] = aday[0]
            ad_duz += 1
print('Bulbapedia ile düzeltilen Japonca ad:', ad_duz)

# ---- kartlar ----
en, nasil = {}, {}
for c in kat['cards']:
    if not JP.search(c[0] or ''):
        continue
    sid = kat['sets'][c[1]][0]
    c15 = moji(c[15]) if len(c) > 15 and c[15] and not JP.search(c[15]) else ''
    l = set_lim.get(sid, {}).get(sade(c[2]))
    if c15 and l and nn(l) != nn(c15) and nn(c15) in nn(l):
        en[c[14]], nasil[c[14]] = l, 'limitless+'
    elif c15:
        en[c[14]], nasil[c[14]] = c15, 'kendi'
    elif l:
        en[c[14]], nasil[c[14]] = l, 'limitless'
say = {}
for c in kat['cards']:
    e = en.get(c[14])
    if e:
        say.setdefault(c[0], {}).setdefault(e, 0)
        say[c[0]][e] += 1
sozluk = {}
for ja, m in say.items():
    e = sorted(m.items(), key=lambda x: -x[1])
    if e[0][1] / sum(m.values()) >= 0.8:
        sozluk[ja] = e[0][0]
for c in kat['cards']:
    if JP.search(c[0] or '') and c[14] not in en:
        sid = kat['sets'][c[1]][0]
        if sozluk.get(c[0]):
            en[c[14]], nasil[c[14]] = sozluk[c[0]], 'katalog'
            continue
        lj = set_lj.get(sid, {}).get(jn(c[0]))
        if lj:
            en[c[14]], nasil[c[14]] = lj, 'limitless-ad'
            continue
        if genel_lj.get(jn(c[0])):
            en[c[14]], nasil[c[14]] = genel_lj[jn(c[0])], 'limitless-ad'
            continue
        b = bp_baslik(kat['sets'][c[1]])
        m = {jn(k): v for k, v in bp.get('kart', {}).get(b, {}).items()} if b else {}
        v = m.get(jn(c[0]))
        if v and len(v) == 1:
            en[c[14]], nasil[c[14]] = v[0], 'bulbapedia'

# ---- uygula ----
n_k = n_s = 0
for c in kat['cards']:
    e = en.get(c[14])
    if e and nn(e) not in nn(c[0]):
        if len(c) > 15:
            c[15] = e
        c[0] = f'{c[0]} ({e})'
        n_k += 1
for s in kat['sets']:
    e = set_en.get(s[0])
    if e and JP.search(s[1] or '') and e not in s[1]:
        s[1] = f'{s[1]} ({e})'
        n_s += 1
json.dump(kat, open(KAT, 'w', encoding='utf-8'), separators=(',', ':'), ensure_ascii=False)
toplam = sum(1 for c in kat['cards'] if JP.search(c[0] or ''))
kaynak = {}
for v in nasil.values():
    kaynak[v] = kaynak.get(v, 0) + 1
print(f'İngilizce ad eklenen kart: {n_k} / {toplam} ({kaynak}); set: {n_s} / {len(kat["sets"])}')
print('İngilizce adı bulunamayan setler:', [s[0] for s in kat['sets'] if s[0] not in set_en])
