"""KartBorsa 7/24 güvenlik izleme (GitHub Actions, 15 dakikada bir).

Kontroller:
  1. Site açılıyor mu, HTTPS zorunlu mu, sertifika geçerli mi
  2. Yayındaki index.html ve sw.js, repodaki ile aynı mı (biri siteyi değiştirdiyse yakalar)
  3. Alan adı (DNS) hâlâ GitHub Pages'i mi gösteriyor (alan adı ele geçirilirse yakalar)
  4. Sitede gizli (sb_secret / service_role) anahtar var mı
  5. Supabase: ziyaretçi veri silebiliyor / gizli tabloları okuyabiliyor mu
  6. Supabase'in kendi 10 dakikalık güvenlik kontrolü çalışıyor mu, uyarı buldu mu

Sorun bulunursa GitHub'da "⚠️ KartBorsa güvenlik uyarısı" başlıklı bir kayıt (issue) açılır ve iş
başarısız olur; GitHub ikisini de repo sahibinin GitHub e-posta adresine gönderir.
Sorun düzelince kayıt kendiliğinden kapanır.
"""
import base64, datetime, json, os, re, socket, ssl, subprocess, sys, time, urllib.error, urllib.request

SITE = "https://www.kartborsa.com"
GITHUB_IP = {"185.199.108.153", "185.199.109.153", "185.199.110.153", "185.199.111.153"}
REPO = os.environ.get("REPO", "Ardaorhan61/kartborsa")
GH_TOKEN = os.environ.get("GH_TOKEN", "")
ETIKET = "guvenlik"
sorunlar = []


def istek(url, method="GET", data=None, headers=None, timeout=30, takip=True):
    h = {"User-Agent": "KartBorsa-guvenlik/1.0", "Cache-Control": "no-cache"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    if not takip:
        class Durdur(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k):
                return None
        opener = urllib.request.build_opener(Durdur)
    else:
        opener = urllib.request.build_opener()
    try:
        with opener.open(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), e.read()


def tekrar(fn, kez=3, bekle=20):
    son = None
    for i in range(kez):
        try:
            sonuc = fn()
            if sonuc is True:
                return True
            son = sonuc
        except Exception as e:  # ağ hatası
            son = f"{type(e).__name__}: {e}"
        if i < kez - 1:
            time.sleep(bekle)
    return son


def gh(yol, method="GET", veri=None):
    data = json.dumps(veri).encode() if veri is not None else None
    s, _, b = istek(f"https://api.github.com/repos/{REPO}{yol}", method, data,
                    {"Authorization": f"Bearer {GH_TOKEN}", "Accept": "application/vnd.github+json",
                     "Content-Type": "application/json"})
    try:
        return s, json.loads(b or b"null")
    except Exception:
        return s, None


# 1) site açık mı
canli = {}
def site_acik():
    s, _, b = istek(f"{SITE}/?guvenlik={int(time.time())}")
    if s != 200 or b"KartBorsa" not in b:
        return f"Site açılmıyor (HTTP {s})"
    canli["index"] = b.decode("utf-8", "replace")
    return True
r = tekrar(site_acik)
if r is not True:
    sorunlar.append(str(r))

# HTTP -> HTTPS yönlendirmesi
def https_zorunlu():
    s, h, _ = istek("http://www.kartborsa.com/", takip=False)
    yer = h.get("Location") or h.get("location") or ""
    if s in (301, 302, 307, 308) and yer.startswith("https://"):
        return True
    return f"HTTP isteği HTTPS'e yönlendirilmiyor (HTTP {s})"
r = tekrar(https_zorunlu)
if r is not True:
    sorunlar.append(str(r))

# sertifika
def sertifika():
    ctx = ssl.create_default_context()
    with socket.create_connection(("www.kartborsa.com", 443), timeout=20) as sock:
        with ctx.wrap_socket(sock, server_hostname="www.kartborsa.com") as ss:
            c = ss.getpeercert()
    bitis = datetime.datetime.strptime(c["notAfter"], "%b %d %H:%M:%S %Y %Z")
    gun = (bitis - datetime.datetime.utcnow()).days
    if gun < 10:
        return f"HTTPS sertifikasının bitmesine {gun} gün kaldı"
    return True
r = tekrar(sertifika)
if r is not True:
    sorunlar.append(f"Sertifika sorunu: {r}")

# 3) DNS
def dns():
    hatalar = []
    for ad in ("kartborsa.com", "www.kartborsa.com"):
        ipler = {a[4][0] for a in socket.getaddrinfo(ad, 443, socket.AF_INET)}
        yabanci = ipler - GITHUB_IP
        if yabanci:
            hatalar.append(f"{ad} → {', '.join(sorted(yabanci))}")
    return True if not hatalar else "Alan adı GitHub Pages dışında bir sunucuyu gösteriyor: " + "; ".join(hatalar)
r = tekrar(dns)
if r is not True:
    sorunlar.append(str(r))

# 2) yayındaki dosyalar repodakiyle aynı mı
def git_surumleri(dosya, n=15):
    out = subprocess.run(["git", "log", f"-n{n}", "--format=%H", "--", dosya], capture_output=True, text=True).stdout.split()
    for h in out:
        icerik = subprocess.run(["git", "show", f"{h}:{dosya}"], capture_output=True).stdout
        yield icerik.decode("utf-8", "replace")

def yayin_suruyor():
    s, j = gh("/actions/runs?per_page=10")
    if s != 200 or not j:
        return True  # emin değilsek sorun saymayalım
    for run in j.get("workflow_runs", []):
        if run.get("status") in ("queued", "in_progress", "waiting", "pending", "requested"):
            return True
        if run.get("conclusion") == "success" and run.get("path", "").endswith("yayin.yml"):
            bitti = datetime.datetime.strptime(run["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
            if datetime.datetime.utcnow() - bitti < datetime.timedelta(minutes=12):
                return True
    return False

def eslesir(canli_metin, repo_metin):
    if "__SURUM__" not in repo_metin:
        return canli_metin == repo_metin
    parcalar = [re.escape(p) for p in repo_metin.split("__SURUM__")]
    return re.fullmatch(r"\d+".join(parcalar), canli_metin, flags=re.S) is not None

if "index" in canli:
    def butunluk():
        hatali = []
        if not any(eslesir(canli["index"], v) for v in git_surumleri("index.html")):
            hatali.append("index.html")
        s, _, b = istek(f"{SITE}/sw.js?guvenlik={int(time.time())}")
        if s == 200 and not any(b.decode("utf-8", "replace") == v for v in git_surumleri("sw.js")):
            hatali.append("sw.js")
        if hatali and not yayin_suruyor():
            return "Yayındaki site dosyası repodakinden farklı (biri siteyi değiştirmiş olabilir): " + ", ".join(hatali)
        return True
    r = tekrar(butunluk, kez=3, bekle=60)
    if r is not True:
        sorunlar.append(str(r))

# 4) gizli anahtar sızıntısı ve 5) Supabase erişim kontrolleri
if "index" in canli:
    html = canli["index"]
    if re.search(r"sb_secret_[A-Za-z0-9_\-]{10,}", html):
        sorunlar.append("Sitede gizli Supabase anahtarı (sb_secret) görünüyor!")
    for jwt in re.findall(r"eyJ[A-Za-z0-9_\-]+\.eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+", html):
        try:
            p = jwt.split(".")[1]
            rol = json.loads(base64.urlsafe_b64decode(p + "=" * (-len(p) % 4))).get("role")
            if rol == "service_role":
                sorunlar.append("Sitede service_role (tam yetkili) Supabase anahtarı görünüyor!")
        except Exception:
            pass
    url = re.search(r"SUPABASE_URL\s*=\s*['\"]([^'\"]+)", html)
    key = re.search(r"SUPABASE_KEY\s*=\s*['\"]([^'\"]+)", html)
    if not (url and key):
        sorunlar.append("Sitede Supabase bağlantı bilgisi bulunamadı (site değişmiş olabilir)")
    else:
        U, K = url.group(1).rstrip("/"), key.group(1)
        H = {"apikey": K, "Authorization": f"Bearer {K}", "Content-Type": "application/json"}

        def supabase():
            hatalar = []
            # ziyaretçi ilan silememeli
            s, _, b = istek(f"{U}/rest/v1/listings?id=eq.00000000-0000-0000-0000-000000000000", "DELETE", headers=H)
            if s < 400:
                hatalar.append("Ziyaretçi (giriş yapmadan) ilan tablosuna yazabiliyor")
            # gizli tablolar okunamamalı
            for t in ("odeme_hesaplari", "siparisler", "offers", "gizli_yedek", "kb_guvenlik_olay", "kb_yonetici", "bildirimler", "fiyat_alarm", "watchlist"):
                s, _, b = istek(f"{U}/rest/v1/{t}?select=*&limit=1", headers=H)
                if s == 200 and b.strip() not in (b"[]", b""):
                    hatalar.append(f"Ziyaretçi gizli tabloyu okuyabiliyor: {t}")
            # veritabanının kendi güvenlik kontrolü
            s, _, b = istek(f"{U}/rest/v1/rpc/kb_guvenlik_ozet", "POST", b"{}", H)
            if s != 200:
                hatalar.append(f"Supabase güvenlik özeti alınamadı (HTTP {s})")
            else:
                o = json.loads(b)
                son = o.get("son_kontrol")
                if not son:
                    hatalar.append("Supabase güvenlik kontrolü hiç çalışmamış")
                else:
                    t = datetime.datetime.fromisoformat(son.replace("Z", "+00:00"))
                    if datetime.datetime.now(datetime.timezone.utc) - t > datetime.timedelta(minutes=35):
                        hatalar.append("Supabase'in 10 dakikalık güvenlik kontrolü durmuş (son çalışma: " + son[:16] + ")")
                if (o.get("yeni_uyari") or 0) > 0:
                    hatalar.append(f"Supabase güvenlik kontrolü son 2 saatte {o['yeni_uyari']} uyarı verdi "
                                   "(ayrıntı: Supabase › Table Editor › kb_guvenlik_olay)")
            return True if not hatalar else hatalar
        r = tekrar(supabase, kez=2, bekle=30)
        if r is not True:
            sorunlar.extend(r if isinstance(r, list) else [str(r)])

# sonuç: GitHub kaydı (issue) + e-posta
simdi = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).strftime("%d.%m.%Y %H:%M")
print("Sorunlar:", sorunlar or "yok")
acik = []
if GH_TOKEN:
    s, j = gh(f"/issues?state=open&labels={ETIKET}&per_page=10")
    acik = j if s == 200 and isinstance(j, list) else []

if not sorunlar:
    for i in acik:
        gh(f"/issues/{i['number']}/comments", "POST", {"body": f"✅ {simdi}: Kontroller yeniden temiz, kayıt kapatıldı."})
        gh(f"/issues/{i['number']}", "PATCH", {"state": "closed"})
    print("Her şey yolunda.")
    sys.exit(0)

govde = (f"**{simdi}** tarihli otomatik güvenlik kontrolü şu sorunları buldu:\n\n"
         + "\n".join(f"- {x}" for x in sorunlar)
         + "\n\nBunu sen ya da Claude yapmadıysan hemen Claude'a yaz: *\"güvenlik uyarısı geldi, bak\"*.\n"
           "Sorun düzelince bu kayıt kendiliğinden kapanır.")
if not GH_TOKEN:
    print(govde)
    sys.exit(1)
if acik:
    i = acik[0]
    s, yorumlar = gh(f"/issues/{i['number']}/comments?per_page=100")
    onceki = (yorumlar[-1]["body"] if s == 200 and yorumlar else i.get("body") or "")
    if all(x in onceki for x in sorunlar):
        print("Aynı sorunlar zaten bildirildi; tekrar e-posta gönderilmiyor.")
        sys.exit(0)
    gh(f"/issues/{i['number']}/comments", "POST", {"body": govde})
    sys.exit(1)
gh("/labels", "POST", {"name": ETIKET, "color": "d73a4a", "description": "Otomatik güvenlik uyarıları"})
gh("/issues", "POST", {"title": "⚠️ KartBorsa güvenlik uyarısı", "body": govde, "labels": [ETIKET],
                       "assignees": [REPO.split("/")[0]]})
sys.exit(1)
