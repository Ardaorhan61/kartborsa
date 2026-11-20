#!/usr/bin/env python3
"""KartBorsa: Japonca kartların ve setlerin İngilizce adları için kaynak verisini toplar.

Kullanım: python3 ja_en.py <veri klasörü>
Kaynaklar: Limitless TCG (Japonca setlerin İngilizce kart listeleri) ve Bulbapedia (eski Japonca setler:
her kart sayfasındaki Japonca ad -> İngilizce ad). Sonuç <veri>/japonca/ja_en.json içine yazılır.
Haftada bir yenilenir (dosya 7 günden yeniyse hiçbir şey yapmaz). Siteye uygulanması: ja_en_uygula.py
"""
import datetime, html, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

VERI = sys.argv[1]
YOL = f'{VERI}/japonca/ja_en.json'
UA = {'User-Agent': 'KartBorsa/1.0 (+https://www.kartborsa.com; weekly name list)'}
SURUM = 2
BUGUN = datetime.date.today()

eski = {}
lim_taze = bp_taze = False
try:
    eski = json.load(open(YOL, encoding='utf-8'))
    yeni_mi = (BUGUN - datetime.date.fromisoformat(eski.get('t', '2000-01-01'))).days < 7 and os.environ.get('ZORLA') != '1'
    lim_taze = yeni_mi and eski.get('v') == SURUM and any(v.get('k') for v in eski.get('lim', {}).values())
    bp_taze = yeni_mi and eski.get('v') == SURUM and any(eski.get('bp', {}).get('satir', {}).values())
except Exception:
    pass
# Bulbapedia GitHub sunucularını engelliyor: eski setlerin ad listesi depoda (ja_bulbapedia_adlar.json) duruyor
if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ja_bulbapedia_adlar.json')):
    bp_taze = True
if lim_taze and bp_taze:
    print('İngilizce ad verisi güncel:', eski.get('t'))
    sys.exit(0)


def get(url, js=False):
    for t in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                b = r.read().decode('utf-8', 'replace')
                return json.loads(b) if js else b
        except urllib.error.HTTPError as e:
            if t == 4 or e.code == 404:
                raise
            time.sleep(60 if e.code in (403, 429) else 3 * (t + 1))
        except Exception:
            if t == 4:
                raise
            time.sleep(3 * (t + 1))


def temiz(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s)).strip()


# ---------- Limitless ----------
LIM = 'https://limitlesstcg.com'
lim = {}
try:
    if lim_taze:
        raise RuntimeError('güncel, yeniden okunmadı')
    sp = get(LIM + '/cards/jp')
    setler = re.findall(r'<a href="/cards/jp/([^"/?]+)"><img[^>]*>\s*([^<]*?)\s*<span class="code annotation">', sp)
    print('Limitless Japonca set:', len(setler), flush=True)
    for kod, ad in setler:
        if kod in lim:
            continue
        try:
            p = get(f'{LIM}/cards/jp/{urllib.parse.quote(kod)}?display=list&translate=en')
        except Exception as e:
            print('  alınamadı', kod, e)
            continue
        m = re.search(r'class="card-set" data-tooltip="([^"]*)"', p)
        kartlar = {}
        for no, _, ad_en in re.findall(
                r'<td><a href="/cards/jp/[^/"]+/([^?"]+)\?translate=en">([^<]*)</a></td>\s*<td><a href="[^"]+">([^<]*)</a>', p):
            kartlar[urllib.parse.unquote(no)] = temiz(ad_en)
        kj = {}
        if kartlar:
            time.sleep(0.7)
            try:
                pj = get(f'{LIM}/cards/jp/{urllib.parse.quote(kod)}?display=list')
                for no, _, ad_ja in re.findall(
                        r'<td><a href="/cards/jp/[^/"]+/([^?"]+)">([^<]*)</a></td>\s*<td><a href="[^"]+">([^<]*)</a>', pj):
                    kj[urllib.parse.unquote(no)] = temiz(ad_ja)
            except Exception as e:
                print('  Japonca liste alınamadı', kod, e)
        lim[kod] = {'ad': temiz(ad), 'ja': html.unescape(m.group(1)) if m else '', 'k': kartlar, 'kj': kj}
        time.sleep(0.7)
except Exception as e:
    print('Limitless alınamadı:', e)
    lim = eski.get('lim', {})
print('Limitless: kart listesi olan set', sum(1 for v in lim.values() if v['k']), flush=True)

# ---------- Bulbapedia ----------
API = 'https://bulbapedia.bulbagarden.net/w/api.php'


def bp_html(sayfa):
    r = get(f'{API}?action=parse&page={urllib.parse.quote(sayfa)}&prop=text&format=json&redirects=1', js=True)
    return r['parse']['text']['*'] if 'parse' in r else ''


bp = {'setler': [], 'kart': {}}
try:
    if bp_taze:
        raise RuntimeError('güncel, yeniden okunmadı')
    liste = bp_html('List of Japanese Pokémon Trading Card Game expansions')
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', liste, re.S):
        a = re.search(r'href="/wiki/([^"#]+_\(TCG\))"', tr)
        if not a:
            continue
        hucre = [temiz(x) for x in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.S)]
        ja = next((h for h in hucre if re.search(r'[぀-ヿ一-鿿]', h)), '')
        if not ja:
            continue
        baslik = urllib.parse.unquote(a.group(1)).replace('_', ' ')
        yil = re.findall(r'\b(19\d\d|20\d\d)\b', ' '.join(hucre))
        bp['setler'].append([ja, baslik[:-6], int(yil[-1]) if yil else 0])
    print('Bulbapedia Japonca set:', len(bp['setler']), flush=True)
    for ja, baslik, yil in bp['setler']:
        if not yil or yil > 2010 or baslik in bp['kart']:
            continue
        try:
            p = bp_html(baslik + ' (TCG)')
        except Exception as e:
            print('  alınamadı', baslik, e)
            continue
        basliklar, satir = [], []
        for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', p, re.S):
            hucre = re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)
            for h in re.findall(r'href="/wiki/([^"#]+)"', tr):
                t = urllib.parse.unquote(h).replace('_', ' ')
                if f'({baslik} ' in t or t.endswith(f'({baslik})'):
                    no = temiz(hucre[0]) if hucre else ''
                    satir.append([no.split('/')[0].strip(), t])
                    if t not in basliklar:
                        basliklar.append(t)
                    break
        m, bilgi = {}, {}
        for i in range(0, len(basliklar), 50):
            parca = basliklar[i:i + 50]
            r = get(f'{API}?action=query&prop=revisions&rvprop=content&rvslots=main&format=json&redirects=1&titles='
                    + urllib.parse.quote('|'.join(parca)), js=True)
            q = r.get('query', {})
            yon = {x['from']: x['to'] for x in q.get('normalized', []) + q.get('redirects', [])}
            for pg in (q.get('pages') or {}).values():
                t = pg['revisions'][0]['slots']['main']['*'] if pg.get('revisions') else ''
                jm = re.search(r'\|\s*jname\s*=\s*([^\n|]+)', t)
                cm = re.search(r'\|\s*cardname\s*=\s*([^\n|]+)', t)
                if jm and cm:
                    j_ = re.sub(r'\{\{[^}]*\}\}|<[^>]+>', '', jm.group(1)).strip()
                    e_ = re.sub(r'\{\{[^}]*\}\}|<[^>]+>', '', cm.group(1)).strip()
                    if j_ and e_:
                        bilgi[pg['title']] = [e_, j_]
                        m.setdefault(j_, [])
                        if e_ not in m[j_]:
                            m[j_].append(e_)
            for t in parca:
                son = t
                for _ in range(3):
                    son = yon.get(son, son)
                if son in bilgi:
                    bilgi[t] = bilgi[son]
            time.sleep(1)
        bp.setdefault('satir', {})[baslik] = [[no, *bilgi[t]] for no, t in satir if t in bilgi]
        bp['kart'][baslik] = m
        time.sleep(1)
except Exception as e:
    print('Bulbapedia alınamadı:', e)
    if not any(bp.get('satir', {}).values()):
        bp = eski.get('bp', bp)
print('Bulbapedia: kart adı alınan set', sum(1 for v in bp['kart'].values() if v), flush=True)

if not any(v.get('k') for v in lim.values()) and not any(bp.get('kart', {}).values()):
    sys.exit('Hiçbir kaynaktan ad alınamadı; eski veri korunuyor.')
os.makedirs(f'{VERI}/japonca', exist_ok=True)
json.dump({'v': SURUM, 't': BUGUN.isoformat(), 'lim': lim, 'bp': bp}, open(YOL, 'w', encoding='utf-8'),
          separators=(',', ':'), ensure_ascii=False)
print('Yazıldı:', YOL, os.path.getsize(YOL) // 1024, 'KB')
