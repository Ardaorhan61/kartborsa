# KartBorsa – Proje notları (17 Kasım 2026)

Kaldığın yerden devam etmek için bu dosya yeterli. Yeni bir sohbette Claude'a
"KartBorsa projesine devam edelim, notlar github.com/Ardaorhan61/kartborsa/blob/main/PROJE-NOTLARI.md içinde" demen yeterli.

## Nerede ne var
| Parça | Yer | Hesap |
|---|---|---|
| Site | https://ardaorhan61.github.io/kartborsa/ | GitHub: Ardaorhan61 |
| Kod | github.com/Ardaorhan61/kartborsa (`main` dalı) | GitHub |
| İlanlar, hesaplar, profiller, koleksiyon, takip, fotoğraflar | Supabase projesi `kartborsa` (nhftbsguwnpknksqmqni) | supabase.com, GitHub ile giriş |
| Kart fiyatları ve geçmişi | `fiyat-verisi` dalı (her gün yenilenir) | GitHub |
| Günlük ilan + profil yedeği | `yedek` dalı | GitHub |
| İlk claude.ai uygulaması (kamerayla tanıma) | claude.ai → Artifacts → "KartBorsa – Pokémon Kart Pazarı" | claude.ai |

Hiçbir parça senin bilgisayarında çalışmıyor; bilgisayar kapalıyken de site, fiyat güncellemesi ve yedekler çalışır.

## Otomatik işler (GitHub Actions)
- **Fiyatları güncelle ve siteyi yayınla** (`.github/workflows/yayin.yml`): her gün 06:41 (TR). Pokémon TCG API'sinden (orada olmayan yeni setler TCGdex'ten)
  TCGplayer + Cardmarket fiyatları, frankfurter.app'ten USD/EUR→TRY kuru. En fazla 45 dk çalışır; alınamayan setler
  ertesi gün önce denenir. `main`'e her yüklemede site de yeniden yayınlanır.
- **Günlük ilan yedeği** (`.github/workflows/yedek.yml`): her gün 03:17 (TR). İlanlar, profiller, fotoğraflar → `yedek` dalı.
- GitHub, 60 gün hiç değişiklik olmayan projede zamanlanmış işleri durdurabilir; e-postayla haber verir, tekrar açmak yeterli.

## Sitenin bölümleri
- **Kartlar**: 20.776 kart / 177 set (`cards.json`, pokemon-tcg-data, Kasım 2026). Setler seriye göre, orijinal resim ve logolar.
- **Piyasa**: fiyatı olan tüm kartlar; değer, dünden / 7 gün / 30 gün değişim; set filtresi.
- **Kart detayı**: bilgiler, sitedeki stok ve ilanlar, takibe al, koleksiyona ekle, piyasa değeri (TCGplayer ana kaynak,
  Cardmarket ikinci), Cardmarket 1/7/30 gün ortalamaları, varyant fiyatları, günlük grafik ve tablo.
- **Kart Al**: tüm aktif ilanlar; satıcıya WhatsApp / Instagram'dan ulaşma.
- **İlan Ver**: giriş gerekli; ilan profil bilgileriyle yayınlanır.
- **Profil**: e-posta + şifre ile giriş (e-posta doğrulaması kapalı); İlanlarım, Koleksiyonum (değer, kâr/zarar),
  Takip Listem, Profil Ayarları; herkese açık satıcı sayfası.

## Supabase ayarları
- Tablolar: `listings`, `profiles`, `collection`, `watchlist`; fotoğraflar `photos` deposunda. Kurulum: `supabase.sql`, `supabase-profil.sql`.
- Authentication → Sign In / Providers: yeni kayıt açık, "Confirm email" kapalı, anonim giriş kapalı.
- Sınırlar: kişi başı 200 ilan (saatte 30), 3000 koleksiyon kaydı, 500 takip.
- Uygunsuz ilan / kullanıcı silmek: Supabase → Table Editor (listings) veya Authentication → Users.

## Bilinen eksikler / sonraki fikirler
- 2026 setleri (Ascended Heroes, Perfect Order, Chaos Rising, Pitch Black, 30th Celebration + Classic Collection,
  Delta Reign) Pokémon TCG API'de yok; fiyatları TCGdex'ten (api.tcgdex.net) alınıyor (17 Kasım 2026'da eklendi).
  Eşleme `fiyatlar.py` içindeki `TCGDEX_SETS` listesinde; listede olmayan yeni setler set adıyla TCGdex'te kendiliğinden aranır.
- Şifremi unuttum yok (ücretsiz Supabase e-postası sadece proje sahibine gider). Çözüm: özel SMTP (ör. Brevo) bağlamak.
- Koleksiyon ve takip listesi günlük yedekte yok (gizli veri); Supabase gizli anahtarı GitHub Secrets'a eklenirse yedeklenebilir.
- `cards.json` yeni setler çıktıkça yeniden üretilmeli (pokemon-tcg-data deposundan).

## Alan adı (17 Kasım 2026)
- Site adresi: **https://www.kartborsa.com** (kartborsa.com ve eski ardaorhan61.github.io/kartborsa adresleri buraya yönlenir).
- Alan adı Porkbun'dan alındı (hesap: Argonotum), 17 Kasım 2027'ye kadar; otomatik yenileme Porkbun hesabındaki karttan.
- Porkbun DNS: kök (ALIAS) ve www (CNAME) → ardaorhan61.github.io. MX/SPF kayıtları Porkbun e-posta yönlendirmesi için duruyor.
- GitHub Pages ayarında özel alan adı www.kartborsa.com, "Enforce HTTPS" açık.
- Supabase Site URL: https://www.kartborsa.com/ ; izinli yönlendirmeler: www.kartborsa.com/** ve ardaorhan61.github.io/kartborsa/**.
- Şifremi unuttum: hatalı şifreden sonra görünür, e-postayla sıfırlama bağlantısı gider (Türkçe şablon).

## Giriş yolları ve e-posta (17 Kasım 2026)
- Giriş: e-posta + şifre, veya "Google ile devam et" (Google Identity Services düğmesi + Supabase signInWithIdToken; gizli anahtar gerekmez).
- Google Cloud projesi "KartBorsa" (orhanarda2007@gmail.com), OAuth istemcisi "KartBorsa web", yayında (In production). Gizlilik sayfası: /gizlilik.html.
- Apple ile giriş yok (Apple Developer üyeliği yılda 99$ gerektiriyor).
- E-postalar Brevo SMTP ile gidiyor: gönderen KartBorsa <bilgi@kartborsa.com>, kartborsa.com Brevo'da doğrulandı (brevo-code, DKIM x2, DMARC kayıtları Porkbun'da). SMTP anahtarı "supabase-kartborsa", süresiz (90 gün hiç kullanılmazsa Brevo kapatır). Brevo'da SMTP için IP engeli kapalı.

## Kartla ödeme — TEST modu (18 Kasım 2026)
- Veritabanı: `supabase-odeme.sql` (Supabase'de çalıştırıldı). Tablolar: `odeme_hesaplari` (satıcı IBAN'ı, sadece sahibi görür), `siparisler` (alıcı + satıcı görür).
- Fonksiyonlar: siparis_olustur, test_odeme, siparis_kargola, siparis_teslim (→ aktarildi), siparis_itiraz, siparis_iptal, kartla_satis_acik, komisyon_orani (%5, deneme oranı).
- Sipariş durumları: odeme_bekliyor → odendi → kargoda → aktarildi; ayrıca iptal / itiraz.
- Site (index.html): profilde "Siparişlerim" ve "Ödeme Hesabım" sekmeleri; ilan penceresinde "💳 Kartla satın al (TEST)" (satıcı IBAN eklediyse); sahte ödeme ekranı (gerçek para yok).
- Henüz yapılmadı: iki gerçek hesapla sitede uçtan uca deneme.
- PayTR'ye geçiş: sadece testOdeme() ekranı PayTR iFrame ile, test_odeme yerine PayTR bildirim (callback) ile değişecek; para aktarımı PayTR Pazaryeri ile.

## PayTR başvurusu — DURUM (18 Kasım 2026, yarım kaldı)
- Ön başvuru formu (paytr.com/uye-isyeri-olun) dolduruldu ama GÖNDERİLMEDİ.
- Girilenler: Yetkili Mustafa Arda Orhan · İşletme tipi: Bireysel Başvuru (vergi levhası yok) · Ürün: Sanal POS + Pazaryeri Çözümü · Site: www.kartborsa.com
- Eksik: e-posta, telefon, KVKK onayı → sonra "Ön Başvuruyu Yap".
- Karar: önce bireysel başvuru; PayTR şirket/şahıs işletmesi isterse açılacak (genç girişimci istisnası: 18–29 yaş, ilk 3 yıl yılda 400.000 TL'ye kadar gelir vergisi yok; Bağ-Kur primi var).
- Fikir: ödeme açılmadan gelir için reklam alanı veya "öne çıkan ilan".

## Kart tarama (18 Kasım 2026)
- "📷 Kart tara" (arama kutusunun yanında): kamera sürekli bakar, aynı kartı 3 karede görünce sonucu gösterir; ayrıca fotoğraf yükleme.
- Kartı resminden tanır: her kartın "görsel izi" (gri + resim bölgesi + renk, 256 bit) → `.github/scripts/kart_izi.py`, iş akışı `kart-izi.yml` (her pazartesi + elle). Çıktı `kart-izi` dalında `izler2.json`, sitede `tara/izler2.json`.
- Fotoğrafta kartın kenarlarını bulur (taraKartBul), ardından alttaki numarayı okur (Tesseract) ve aynı resimli baskıları ayırır.

## İngilizce / Japonca (18 Kasım 2026)
- Üstte "🇬🇧 İngilizce / 🇯🇵 Japonca" seçimi (tarayıcıda hatırlanır). Kartlar, setler, arama, Piyasa, Kart Al, ilan/koleksiyon aramaları seçili dile göre.
- Japonca katalog: `.github/scripts/japonca.py` (TCGdex ja + resmi olmayanlar için Scrydex, aramada PokeAPI İngilizce adları). Her gün fiyatlarla birlikte çalışır; `fiyat-verisi` dalında `japonca/cards_ja.json`, sitede `cards_ja.json`. Kart kimlikleri `ja-<set>-<no>`.
- İlk kurulum: 121 set, 13.156 kart, 12.872'si resimli; ~10.700 kartın Cardmarket fiyatı (€ → ₺).
- Eksik: TCGdex'te kartları olmayan Japonca setler (ADV, LEGEND, BW, XY ve ilk Kılıç&Kalkan setlerinin bir kısmı) henüz katalogda yok.

## Japonca set logoları ve eksik setler (19 Kasım 2026)
- TCGdex Japonca setlerde logo vermiyor. Logolar ve set sembolleri Pokellector'dan (jp.pokellector.com) BİR KEZ indirilip `img/ja/<set>.png` ve `img/ja/<set>.sym.png` olarak depoya kaydedildi.
- Eşleme: `.github/scripts/ja_logolar.json` (set kimliği → Pokellector görsel adı). İndirme: `.github/scripts/ja_logo.py`, iş akışı `ja-logo.yml` (eşleme değişince veya elle; sadece eksikleri indirir, sonra siteyi yeniden yayınlar).
- Yayında (`yayin.yml`) logosu olmayan Japonca setlere `img/ja` içindeki görsel yazılır. 121 setin 101'inde logo var.
- Logosu olmayan 20 set (Pokellector'da yok, ilk kartın resmi görünür): web1, E1, E3, E4, E5, PCG1–PCG9, WCS23, SVK, SVLN, SVLS, MC, MF.
- Eksik setler tamamlandı (19 Kasım 2026, gece): `.github/scripts/ja_ek.py` (yayin.yml'de "Japonca eksikleri tamamla" adımı, japonca.py'den sonra).
  Pokellector'da olup TCGdex'te kartı olmayan 102 set eklendi (BW, XY, LEGEND, DPt, ilk Kılıç&Kalkan, promolar, desteler, Vending): toplam 223 set, 20.635 kart.
  Bu setlerde kart adları İngilizce (Pokellector'da Japonca ad yok), resim ve logo Pokellector'dan, fiyat yok. Set kimlikleri Pokellector kodu (ör. ja-S2, ja-XY1), `pl` işaretli.
  Set sayfaları bir kez okunur, `fiyat-verisi` dalında `japonca/ek.json` önbelleğinde tutulur; sadece Pokellector'a yeni eklenen setler okunur.
  TCGdex setlerinde resmi olmayan kartlar da Pokellector resmi ya da aynı adlı kartın resmiyle dolduruldu (284 → 1).
- Tamamlama, 2. tur (19 Kasım 2026, gece):
  - `ja_ek.py` artık kart sayfalarından Japonca ad, nadirlik ve Cardmarket € fiyatını da alıyor (ek.json "kart" önbelleği; 5 günde bir yenilenir,
    günlük çalışmada 20 dk bütçe). TCGdex setlerinde eksik numaralı kartlar Pokellector'dan eklenir (kimlik `ja-<set>-p<no>`).
  - İlk büyük okuma için ayrı iş akışı `ja-ayrinti.yml` (elle başlatılır, ~2–3 saat, bitince siteyi yayınlar; bitmezse kendini yeniden başlatır).
  - ADV1–5 ve DP1–DP5 setleri: `.github/scripts/ja_bulbapedia.json` (Bulbapedia'daki Japonca set listeleri). Kart bilgisi ve resmi İngilizce karşılık
    kartından (aynı çizim, İngilizce baskı). Yayında (`yayin.yml`) kataloğa eklenir, `bp` işaretli.
  - Japonca promolar: `.github/scripts/ja_promo.json` (Bulbapedia: ADV-P, PCG-P, DP-P, DPt-P, L-P, BW-P, XY-P, SM-P, S-P, SV-P, M-P, PPP, P, T).
    Olmayan promo setleri eklenir, olan setlerde eksik numaralar tamamlanır. Resimler Bulbagarden arşivinden.
  - Bulbagarden resimleri yalnızca "referrer" gönderilmezse açılıyor: index.html'de el() tüm resimlere referrerPolicy=no-referrer koyuyor.
  - Son kontrol (19 Kasım 2026): `.github/scripts/ja_duzeltme.json` (yayında uygulanır): 38 setin logosu/paket resmi (Bulbagarden arşivi),
    50 promo kartının resmi, WCS23 destesinin 30 kartı, web1 #39 ve VS1 #77 eklendi; hiç çıkmamış kartlar silindi (S-P 134/194–197/233, M-P 128–130, neo2 #57).
    Sonuç: 241 set, 22.566 kart; resmi olmayan kart 0, logosu olmayan set 0. SV4a'daki 40 kart `ja-ayrinti.yml` bitince gelir.
    Japonca adlar: `ja_duzeltme.json` içindeki "ad" listesi (Bulbapedia kart sayfalarındaki Japonca ad, 3.601 kart); Bulbapedia'dan gelen 1.932 kartın hepsi Japonca adla. İngilizce ad aramada çalışmaya devam eder.
