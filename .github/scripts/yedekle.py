"""Supabase'deki ilanları ve satıcı fotoğraflarını 'yedek' dalına kaydeder."""
import json, os, sys, urllib.request, datetime, hashlib

URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_KEY"]
OUT = sys.argv[1]
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}

def get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

rows, start = [], 0
while True:
    page = json.loads(get(f"{URL}/rest/v1/listings?select=*&order=created_at.asc&offset={start}&limit=1000", H))
    rows += page
    if len(page) < 1000:
        break
    start += 1000

profiles = json.loads(get(f"{URL}/rest/v1/profiles?select=*&order=created_at.asc&limit=10000", H))

now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))
os.makedirs(f"{OUT}/ilanlar", exist_ok=True)
os.makedirs(f"{OUT}/fotograflar", exist_ok=True)
data = json.dumps(rows, ensure_ascii=False, indent=1)
open(f"{OUT}/ilanlar/son.json", "w").write(data)
open(f"{OUT}/ilanlar/{now:%Y-%m-%d}.json", "w").write(data)
os.makedirs(f"{OUT}/profiller", exist_ok=True)
pdata = json.dumps(profiles, ensure_ascii=False, indent=1)
open(f"{OUT}/profiller/son.json", "w").write(pdata)
open(f"{OUT}/profiller/{now:%Y-%m-%d}.json", "w").write(pdata)
for pr in profiles:
    u = pr.get("avatar_url") or ""
    if "/photos/" in u:
        rows.append({"photo_url": u})

saved = 0
for r in rows:
    u = r.get("photo_url") or ""
    if "/storage/v1/object/public/photos/" not in u:
        continue
    name = u.split("/photos/", 1)[1].replace("/", "_")
    path = f"{OUT}/fotograflar/{name}"
    if os.path.exists(path):
        continue
    try:
        open(path, "wb").write(get(u))
        saved += 1
    except Exception as e:
        print("Fotoğraf indirilemedi:", u, e)

active = [r for r in rows if r.get("status") == "active"]
rows_l = [r for r in rows if 'id' in r]
summary = (f"Yedek: {now:%d.%m.%Y %H:%M}\n"
           f"Profil: {len(profiles)}\n"
           f"Toplam ilan: {len([r for r in rows if 'id' in r])} (yayında {len(active)}, satıldı {len(rows_l)-len(active)})\n"
           f"Satıştaki kart adedi: {sum(r.get('qty', 0) for r in active)}\n"
           f"Bu yedekte yeni indirilen fotoğraf: {saved}\n")
open(f"{OUT}/SON-YEDEK.txt", "w").write(summary)
print(summary)
