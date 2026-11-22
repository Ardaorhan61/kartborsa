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

## Japonca eksikler — 19 Kasım 2026 (öğleden sonra)
- Uzun iş (ja-ayrinti.yml) gece başarıyla bitti: 241 set, 22.619 kart; SV4a 360 kartla tam.
- `ja_duzeltme.json` yeni anahtarlar (yayin.yml uygular):
  - `adid`: kart kimliği → Japonca ad (1.008 kart; PokeAPI tür adları + katalogdaki EN→JA eşleşmeleri + Bulbapedia + kart görsellerinden elle). Sadece Ｎ ve AZ Latin harfli kaldı (resmi adları bu).
  - `setad`: set kimliği → Japonca set adı (103 set).
  - `setsayi`: set kart sayısı düzeltmesi (ja-PT2 = 90; Pokellector 96 diyordu, Bulbapedia'ya göre Japonca set 90 kart → eksik yok).
  - `nadir`: kart kimliği → nadirlik (elle düzeltme için, şimdilik boş).
- `ja_ek.py`: TCGdex setlerinde nadirliği / fiyatı / Japonca adı eksik kartların Pokellector kart sayfaları da okunuyor (nadirlik, ad, Cardmarket € fiyatı). "card-placeholder" resimleri boş sayılıp aynı adlı kartın resmiyle dolduruluyor (37 kart).
- 19 Kasım 14:53'te ja-ayrinti.yml yeniden başlatıldı (~2–3 saat). Bitince kontrol: nadirliksiz kart (2.959'du), fiyatlı kart (12.163'tü), yer tutucu resim (37'ydi). Pokellector'da sayfası olmayan setler (ör. ja-MC) nadirliksiz kalabilir.

## 19 Kasım 2026 (akşamüstü) — tasarım, geri tuşu, McDonald's, arkadaşlar
- Tasarım: ana sayfa vitrini (en değerli 3 kart yelpazesi, popüler aramalar, Günün kartı, Bugün yükselenler / en değerliler), tür renkleri (TIP_TR, tipPill, tipDot), nadirlik rozetleri (rarSeviye, RAR_G), saldırı maliyeti enerji topları (maliyet), holo parlama, enerji şeridi.
- Geri tuşu: history.pushState ile site içi geçmiş (görünüm, set, arama, filtreler, açık kart, kaydırma yeri). Logo = anaSayfa(). Hash kullanılmıyor (Supabase şifre sıfırlama hash'i bozulmasın).
- McDonald's: ja_duzeltme.json yeni anahtarlar `yeniset` (ja-MCD02 ミニマム★パック 18 kart, ja-MCD10 旅立ちの仲間 9 kart; Bulbapedia) ve `etiket` (71 numaralı McDonald's promosu, kartın c[12] alanına yazılır; arama anahtarına girer). Japonca ana sayfada "🍔 McDonald's promoları" düğmesi.
- Arkadaşlar: Supabase'de `friendships` tablosu (requester, addressee, status pending/accepted; RLS: taraflar görür, istek sadece kendi adına, kabulü sadece alan yapar, iki taraf da silebilir) ve `arkadas_mi(a,b)` fonksiyonu. `collection` okuma kuralı: sahibi VEYA show_collection açık VEYA kabul edilmiş arkadaş. Profil > "Arkadaşlarım" sekmesi (isimle arama, istek gönder/kabul/reddet/geri al, arkadaşlıktan çıkar, koleksiyonu gör = openSeller). Gelen istek sayısı menüde rozet olarak görünür. Günlük yedeğe friendships tablosu henüz eklenmedi.

## 20 Kasım 2026 (gece) — kaynağı kesin olan eksikler tamamlandı
- Kural (Arda): kaynakta birebir bulunmayan hiçbir bilgi tahminle doldurulmaz.
- `.github/scripts/ja_tip.json`: 5.639 Pokellector Pokémon kartının enerji tipi (harf kodu G R W L P F D M Y N C). Bulbapedia set listelerinde kart numarası + İngilizce ad birebir eşleşenler. yayin.yml dz bloğunda c[7] boşsa uygulanır. Eşleşmeyen 438 kart boş bırakıldı.
- `.github/scripts/en_duzeltme.json`: İngilizce katalogda eksik SWSH299 Jirachi V, SWSH300 Unown V, SWSH301 Lugia V (veri TCGdex, resim Bulbapedia'daki promo taraması). yayin.yml'de cards.json'a eklenir.
- ja_duzeltme.json `sembol`: 7 Japonca set sembolü (web1, E1, E3, E4, E5, PCG1, MC; Bulbapedia'daki Japonca adlı SetSymbol dosyaları). PCG2–PCG9 için sadece İngilizce set sembolü var → eklenmedi.
- Kaynağı olmadığı için boş: Japonca 1.044 nadirlik (ja-MC Bulbapedia'da boş, ja-M6a "-"), 10.475 Japonca fiyat, 438 tip, 10 sembol, 2 McDonald's set logosu; İngilizce 295 nadirlik (çoğu McDonald's), 132 fiyat.

## 20 Kasım 2026 — hız ve renk
- Hız: index.html'de `window.SURUM='__SURUM__'` yayında (yayin.yml "Siteyi hazırla": sed ile zaman damgası). Aynı sitedeki tüm .json istekleri `?v=SURUM` ile gider (fetch sarmalayıcı), `cache:'no-cache'` kaldırılır.
- `sw.js` (köke kopyalanır): sayfa önce internetten; sürümlü .json önbellekten (yoksa indirip saklar, eski sürümleri siler); Google yazı tipleri ve Supabase kütüphanesi önbellekten. Kayıt sadece kartborsa.com'da.
- loadCatalog: önce seçili dilin kataloğu, diğeri 400 ms sonra arka planda (`window.__ikinciDil`), CAT'e eklenir.
- Ön yükleme (preload) seçili katalog + fiyat özeti; `content-visibility:auto` set ve kart ızgaralarında; resimlerde decoding=async.
- Ölçüm: ilk açılış ~1,4 MB → ~1,0 MB (diğer dil sonradan); tekrar açılışta veri için ağ 0 KB, ~100 ms.
- Renk: seri başına renk (SRK dizisi, --sc) set kutularında şerit/zemin/parlama; kartlarda tür rengi (--tc) çerçeve, parlama ve ad çizgisi; kart detayında üst şerit tür renginde (--mc); renkli butonlar, sekmeler, başlıklar, vitrin kutuları.

## 20 Kasım 2026 (gece) — giriş/kayıt, yenileme, hız 2
- Yenileme: history.state (setId ile) sayfa yenilenince geri yüklenir (görünüm, set, filtreler, açık kart, kaydırma); pagehide/visibilitychange'de konum kaydedilir.
- Giriş/Kayıt: profil sayfasında iki büyük seçenek. Kayıt: ad, soyad (auth user_metadata'da, gizli), kullanıcı adı (profiles.display_name, benzersizlik kontrolü), şehir, e-posta, şifre + tekrar, gizlilik onayı. Onay e-postası gerekirse profil ilk girişte `profilTamamla()` ile oluşur.
- Hız 2: yayında cards.json / cards_ja.json içindeki resim adresi başları kısaltılır: `~0`…`~6` = d['pfx'] listesindeki önek (scrydex, tcgdex, pokellector, bulbapedia, pokemontcg, pokellector logos, img/ja). Site yüklerken geri açar. **Denetimde "~" ile başlayan adres bozuk değildir.** Yazı tipleri sayfayı bekletmez (preload+onload), resim sunucularına preconnect, ikinci dil boşta (requestIdleCallback) yüklenir, arama anahtarları sadece yeni kartlar için hesaplanır.

## 20 Kasım 2026 (~01:50) — kalite ve kaldığımız yer
- Kart resimleri: `px(u,w,q)` / `pxImg()` / `cardImg()` — kaynak her zaman en büyük orijinal (imgLarge), wsrv.nl ile WebP'ye çevrilir: ızgarada srcset 240w/480w, detayda 600w/1000w; set logoları 320, semboller 48, listeler 96. Hata olursa orijinal adrese döner. wsrv önbelleği 1 yıl.
- DURDUK: Arda "devam" yazınca buradan sürdürülecek. Açık işler: (1) ~10.475 Japonca fiyat için ücretli kaynak kararı (Arda'da), (2) PayTR başvurusu (TC kimlik no'yu Arda yazacak) ve iki hesapla deneme ödemesi, (3) Profil Ayarları'na ad/soyad düzenleme önerisi, (4) yeni kayıt formu gerçek bir hesapla henüz denenmedi. Kalan eksiklik tablosu: "KartBorsa – Kalan eksiklikler" (Claude Sheets).

## 20 Kasım 2026 (öğle) — site denetimi
- İngilizce katalogda eksik bulunan 187 kart eklendi: MEP Black Star Promos (111 kart, yeni set), Mega Evolution Energies (16 kart, yeni set), Scarlet & Violet Black Star Promos'ta 166–225 arası 60 kart. Kaynak TCGdex, resimler Scrydex (yer tutucu resim kontrolü yapılıyor).
- Bunu `.github/scripts/en_ek.py` yapıyor; `yayin.yml` her yayında depo `cards.json`'unu değiştirmeden yayın kopyasına uyguluyor (yeni promolar da kendiliğinden eklenir). Yeni set eklemek için betikteki EK_SETLER listesine yazılır.
- Nadirlik düzeltmeleri (TCGdex'te doğrulandı): Ascended Heroes'taki 7 kart "MEGA_ATTACK_RARE" → "Mega Attack Rare"; 30th Celebration Mew R/G/B "Common" → "RGB Rare"; eski setlerdeki 36 temel enerji ve Dragon Vault'taki 3 kart (boştu).
- `fiyatlar.py`: mep/mee TCGDEX_SETS'e eklendi; SVP'de Pokémon TCG API'de olmayan yeni promoların fiyatı TCGdex'ten (TCGDEX_EK). Fiyatlar ertesi sabah 06:41 güncellemesiyle gelir.
- Alt bilgide tüm veri kaynakları yazıldı.
- Kaynakta resmi olmayan için eklenmeyenler: svp-500 Terapagos & Friends, MEP "Pikachu at the Museum". Logosu kaynakta olmayan Japonca setler: ja-MCD02, ja-MCD10. Southern Islands nadirliği boş bırakıldı (kaynak güvenilir değil).

## 20 Kasım 2026 (öğle) — günlük bakım (otomatik görev)
- Kontrol: GitHub Actions son 24 saatte hatasız (fiyat 04:35, yedek 01:26 UTC başarılı); site, Piyasa, Kart Al, İlan Ver, dil geçişi, kart detayı çalışıyor, konsolda hata yok.
- Katalog sayıları önceki günle aynı (kaynağı olmayanlar): JA 1.044 nadirliksiz, 10.475 fiyatsız, 10 sembolsüz, 2 logosuz set (MCD02, MCD10); EN 295 nadirliksiz, 132 fiyatsız. Yer tutucu resim, kartsız set, eksik kartlı set, Japonca olmayan ad: 0.
- Eksik Japonca set eklendi: **ja-PCG10 ワールドチャンピオンズパック** (World Champions Pack, 2007/07/05, 108 kart). `ja_bulbapedia.json`'a Bulbapedia set listesinden (kart karşılığı EX Power Keepers / ex16, Japonca adlar Bulbapedia kart sayfalarındaki jname); logo `ja_duzeltme.json` logo (Bulbagarden paket resmi), adlar `ad` ("ja-PCG10|no"). `yayin.yml`: bp setlerinde `seri` alanı okunur (yoksa eski kural ADV/DP).
- TCGdex'te olup sitede görünmeyen BW5a/BW5b aslında var (ja-pl22, ja-BW5). EN'de eksik set yok (B2a = TCG Pocket).

## 20 Kasım 2026 (akşam) — Japonca adların yanına İngilizce adlar
- Japonca kart ve set adları sitede "ピカチュウ (Pikachu)" biçiminde görünüyor (yalnızca yayın kopyasında; veri dosyaları değişmedi).
- `.github/scripts/ja_en.py`: Limitless TCG (Japonca setlerin İngilizce kart listeleri) ve Bulbapedia'dan (eski setlerde kart sayfasındaki Japonca ad) kaynak verisini toplar → fiyat-verisi dalında `japonca/ja_en.json`. Haftada bir yenilenir; `ZORLA=1` ile hemen yenilenir.
- `.github/scripts/ja_en_uygula.py`: yayında uygular. Sıra: kartın kendi İngilizce adı (Limitless daha ayrıntılıysa o), Limitless (aynı numara), katalogda aynı Japonca adlı kart, Bulbapedia. Tahmin yok.
- Sonuç: 22.741 Japonca adlı kartın 22.313'ünde, 244 setin 242'sinde İngilizce ad var. Kalanların çoğu eski setlerde (neo, VS, e-Card, PCG) adı kaynakta makine çevirisi olan ya da zaten İngilizce harf içeren kartlar; ayrıca SV-P/M-P'de numarası Limitless ile eşleşmeyen birkaç promo. Adı olmayan setler: ja-MCD10, ja-S10B.

## 20 Kasım 2026 (gece) — kalan eksiklerin taranması
- Japonca: kaynakta makine çevirisiyle bozulmuş eski Japonca adlar (neo, e-Card, PCG vb.) Bulbapedia'daki gerçek adlarla değiştiriliyor (ör. "奇妙な" → "ナゾノクサ"). Numaralı setlerde numara, numarasız setlerde Bulbapedia listesindeki sıra (kayma payıyla, %90 doğrulamayla) kullanılıyor.
- GitHub sunucuları Bulbapedia'ya erişemiyor (403). Eski setlerin ad listesi tarayıcıdan bir kez çekildi ve depoya kondu: `.github/scripts/ja_bulbapedia_adlar.json` (53 set, 3.619 kart). `ja_en.py` bu dosya varken Bulbapedia'yı denemiyor.
- Limitless'ın Japonca adları da alınıyor (`kj`); katalogda numarası tutmayan kartlar Japonca adla eşleniyor.
- Sonuç: 22.741 Japonca adlı kartın 22.486'sında İngilizce ad var. Kalan 255 kartın hiçbir ücretsiz kaynakta İngilizce adı yok (çoğu VS ve neo 4 setleri; ayrıca Limitless'ta çevirisi olmayan bazı promo/trainer kartları).
- `fiyatlar.py`: Pokémon TCG API'de fiyatı boş gelen kartlar artık TCGdex'ten (McDonald's 2014–2018, EX Trainer Kit'ler, promolar). İlk sonuç bir sonraki 06:41 güncellemesinde.
- Hâlâ açık: Japonca fiyatı olmayan kartlar için ücretli kaynak kararı; PayTR başvurusu; iki hesapla deneme ödemesi; svp-500 ve MEP "Pikachu at the Museum" (ikisi de jumbo/özel kart, resmi kaynakta yok).

## 21 Kasım 2026
- 06:41 fiyat güncellemesi başarılı: fiyatsız İngilizce kart 132 → 95. McDonald's 2015–2017, EX Trainer Kit 2 Plusle, MEE (16/16), SVP (225/225), MEP (110/111) artık fiyatlı.
- Bulunan sorun 1: Pokémon TCG API mcd14, tk1a, tk1b (ve zaman zaman mcd18, tk2b) için bozuk/boş yanıt veriyor → set "alınamadı" sayılıp TCGdex'e hiç geçilmiyordu. `fiyatlar.py`: API hata verirse set TCGdex'ten alınıyor; `tcgdex_set_id` artık `TCGDEX_EK` eşlemesini de kullanıyor. Bu 5 setin 56 kartı TCGdex'te numara+adla eşleşiyor (denendi).
- Bulunan sorun 2: fiyat adımı 45 dk'ya sığmıyordu, her sabah 179 setin yalnız ~103'ü yenileniyordu. `yayin.yml`: FIYAT_SURE_DK=80, iş süresi 180 dk. Site yayını bu yüzden sabah ~08:00–08:30 arası olabilir.
- Kontrol (22 Kasım sabahı): mcd14, mcd18, tk1a, tk1b, tk2b fiyatları geldi mi; tüm setlerin fiyat/set/*.json tarihi bugün mü.
- Japonca fiyatlar (Arda "eksiksiz yap" dedi): yeni kaynak TCGplayer Pokémon Japan, tcgcsv.com'un ücretsiz günlük dökümüyle (kategori 85, 463 set). `.github/scripts/ja_tcgplayer.py`: sadece fiyatı başka kaynaktan gelmeyen Japonca kartlara dokunur; set eşlemesi adla + `ELLE` listesi (26 set); kart eşlemesi aynı numara + aynı ad, numarasız eski setlerde ad (+ gerekirse HP), Japonca ön ekler (わるい→Dark, タケシの→Brock's …) çevrilir; "Mirror Holofoil" ürünleri ters holo varyantı sayılır; belirsiz eşleşme doldurulmaz. Kendi fiyat geçmişi fiyat-verisi dalında `japonca/tcgplayer.json`; set dosyalarında kayıtlar `tp: 1` işaretli.
- `yayin.yml`: "Japonca adların yanına İngilizce adlar"dan sonra "Japonca fiyatı olmayan kartlar (TCGplayer)" + ikinci "fiyat verisini kaydet" adımı (push'ta çalışmaz, zamanlı ve elle çalıştırmada çalışır).
- Sonuç (21 Kasım): fiyatsız Japonca kart 10.583 → 2.414 (8.169 kart TCGplayer fiyatlı). Kalan: 2.000'i TCGplayer'da listeli ama şu an fiyat verisi yok (her gün yeniden denenir), 414'ü TCGplayer'da hiç yok (çoğu numarasız promo/enerji: XY-P, SM-P, S-P, BW-P, PCG-10…). Bunlar için ücretsiz kaynak kalmadı; seçenek ücretli kaynak ya da Japon mağaza fiyatları (karar Arda'da).
- Akıcılık (Arda "çok takılıyor" dedi): JS ölçümleri hızlı (arama 1–5 ms, 774 kartlık set 25 ms); takılma çizimdendi. index.html sonuna `<style id="akici">`: body'deki 4 radial-gradient + background-attachment:fixed (her kaydırmada tüm ekran yeniden boyanıyordu) → sabit `body::before` katmanı; header backdrop-filter kaldırıldı (zaten %94 opaktı); kart kutusu gölgeleri hafifletildi; kart detayındaki parlama gölgesi artık animasyonsuz (kbHale kapalı, kbSallan duruyor). Not: GitHub Pages sayfayı 10 dk tarayıcıda tutar, yeni sürüm en geç 10 dk'da gelir.

## Öneriler (22 Kasım 2026) — diğer kart siteleri incelendi
Arda "devam" yazınca bu liste tekrar gösterilir. 1 satıcı puanı + yorum + "Güvenilir satıcı" rozeti · 2 alıcı koruması (para teslimata kadar PayTR'de) · 3 "Teklif ver" (+ site içi mesajlaşma) · 4 derecelendirilmiş kartlar (PSA/CGC/BGS, not, sertifika no, filtre) · 5 e-postayla fiyat alarmı (Resend) · 6 set tamamlama ilerlemesi ("87/190" + eksik kartlar filtresi) · 7 kapalı ürün ilan türü · 8 Google'da bulunabilen set/kart sayfaları + paylaş düğmesi · 9 telefona uygulama gibi kurma · 10 rehberler (kart durumu, sahte kart, SSS). Önerilen sıra: şimdi 6, 9, 5 · sonra 1, 3, 4 · şirket/PayTR sonrası 2 · büyüme 8, 10, 7. Tek kart fiyatı + ilan + koleksiyonu birleştiren Türk rakip bulunamadı.
- 22 Kasım 2026 akşamı yapıldı: 1, 3 (site içi yazışma OLMADAN — Arda istemedi), 4, 6, 7, 10. Kalan: 2 (PayTR'ye bağlı), 5, 8, 9.

## 22 Kasım 2026 — puanlar, teklifler, derecelendirme, set tamamlama, kapalı ürünler, rehber
- Veritabanı: `supabase-ozellikler.sql` (Supabase'de çalıştırıldı). Kod: index.html sonundaki `<style id="ozellikler">` ve `<script id="ozellikler-js">` (eski fonksiyonları sarmalar: listingRow, drawAl, openListing, openSeller, drawProfil, drawMine, drawColl, crumb, drawCat, runCat, tileFor, pickForListing, go, updateNav, loadMine).
- **Satıcı değerlendirmeleri** (`reviews`): herkes okur; profili olan kullanıcı her satıcıya 1 değerlendirme (1–5 yıldız + yorum) yazar, düzenler, siler; satıcı herkese açık cevap yazar (tetikleyici yazanın cevabı, satıcının puanı/yorumu değiştirmesini engeller); günde en fazla 20. "✓ Doğrulanmış alışveriş": aralarında kabul edilmiş teklif ya da teslim edilmiş/tamamlanmış sipariş varsa (`alisveris_var()`, otomatik). "✓ Güvenilir satıcı" rozeti: en az 3 değerlendirme, ortalama ≥ 4,5, üyelik ≥ 30 gün. Satıcı sayfasında özet, yıldız dağılımı, yorumlar; ilanlarda ve Kart Al'da yıldız; Kart Al'da "Sadece güvenilir satıcılar" filtresi.
- **Teklif ver** (`offers`, site içi yazışma yok): ilan satırında "💰 Teklif ver" → adet + toplam teklif + not. Kurallar (veritabanında): ilan fiyatından düşük, en az %30'u, adet ≤ ilan adedi, ilana 1 açık teklif, saatte 30. Durumlar: bekliyor → kabul / red / karsi (satıcının karşı teklifi, teklifin üstünde) → alıcı kabul (tutar = karşı teklif) / red; alıcı geri çekebilir; kabulden sonra iki taraf "iptal" edebilir. Teklifi sadece alıcı ve satıcı görür. Profil › Teklifler sekmesi (gelen / verdiğim); kabulde iletişim düğmeleri, satıcıya "ilandan adet düş / satıldı yap". Menüde 💰 sayısı (bekleyen gelen + karşı teklif + görülmemiş kabul), 90 sn'de bir yenilenir. E-posta bildirimi var (aşağıya bak).
- **Derecelendirilmiş kartlar**: listings'e `grade_co` (PSA, CGC, BGS, TAG, SGC, ACE, Diğer), `grade` (1–10, buçuklu), `grade_label`, `cert_no`. İlan Ver'de "Derecelendirilmiş kart" kutusu (durum yerine şirket/not/etiket/sertifika no; `cond` nottan otomatik). Kart Al'da rozet ("PSA 10") ve filtre; ilanda PSA/CGC/BGS için sertifika doğrulama bağlantısı.
- **Kapalı ürünler**: listings'e `kind` ('kart' | 'kapali') ve `product_type` (Booster paketi, Booster kutusu, Elite Trainer Box, Koleksiyon kutusu, Tin kutu, Blister, Build & Battle, Hazır deste, Premium koleksiyon, Booster bundle, Diğer). `card_id` = `kapali:<set kimliği>` ya da `kapali:-`; `card_name` = ürün adı. Durum: Jelatinli / Jelatinsiz / Kutusu hasarlı. Kendi fotoğraf zorunlu. Diller: Korece ve Çince eklendi. Kart Al'da filtre (ürün türü), satıcı sayfasında ve İlanlarım'da ayrı bölüm. Kartla ödeme (TEST) kapalı ürünlerde yok.
- **Set tamamlama**: set açıkken "Bu setten X / Y kartın var" + çubuk + Hepsi / Bende olanlar / Eksiklerim; koleksiyondaki kartlarda ✓ rozeti; Koleksiyonum'da "Set tamamlama" listesi ("Eksikleri gör"). Farklı kart sayısına göre, gizli nadirler dahil.
- **Rehber** (menüde "Rehber", alt bilgide bağlantı): kart durumu tablosu, derecelendirme, sahte kart, kapalı ürün, güvenli alışveriş, teklif, SSS.
- Deneme: veritabanı kuralları geçici test kullanıcılarıyla, geri alınan bir işlemde 22 adımda denendi (hepsi doğru). Arayüz sahte verilerle denendi. Gerçek iki hesapla uçtan uca deneme yapılmadı.
- Günlük yedek (`yedekle.py`): `degerlendirmeler/` eklendi. Gizli veriler (teklifler vb.) için aşağıdaki veritabanı içi yedeğe bak.
- Not: GitHub web düzenleyicisinde içerik yapıştırırken önce gerçek Ctrl+A ile tümü seçilmeli; JS ile seçim çalışmıyor, dosya iki kez ekleniyor (21 ve 22 Kasım'da oldu, hemen düzeltildi).

## 22 Kasım 2026 (akşam) — e-posta bildirimleri ve gizli verilerin yedeği
- Veritabanı: `supabase-bildirim.sql` (Supabase'de çalıştırıldı). pg_net ve pg_cron eklentileri açıldı.
- **E-posta bildirimleri** (Resend API, gönderen KartBorsa <noreply@kartborsa.com>): `kb_eposta()` fonksiyonu; tetikleyiciler `offers_bildir` (yeni teklif → satıcı; karşı teklif → alıcı; kabul → karşı taraf; red → karşı taraf; geri çekme → satıcı; iptal → karşı taraf) ve `reviews_bildir` (yeni değerlendirme → satıcı; satıcı cevabı → yazan). Kullanıcı metinleri HTML'e kaçışlı yazılır. Düğmeler `https://www.kartborsa.com/?sayfa=teklifler` / `?sayfa=degerlendirmeler` (site açılınca ilgili yere gider).
- Profil Ayarları'nda "E-posta bildirimleri" kutusu (`profiles.email_bildirim`, varsayılan açık).
- **Anahtar**: Resend API anahtarı Supabase → Project Settings → Vault'ta `resend_api_key` adıyla durmalı. Yoksa hiç e-posta gitmez, site hata vermez. Anahtarı Arda kendisi oluşturup yapıştırır (Claude anahtar giremez).
- Deneme (geri alınan işlemde, sahte anahtarla): 5 e-posta doğru kişiye, doğru konuyla kuyruğa girdi; <script> gibi metinler kaçışlı. Gönderim durumu: `select * from net._http_response order by created desc limit 20;`
- **Gizli verilerin günlük yedeği** (depo herkese açık olduğu için GitHub'a değil, veritabanının içine): tablo `gizli_yedek` (gün → teklifler, koleksiyon, takip, arkadaşlık, sipariş; kimse okuyamaz, sadece Supabase yöneticisi), fonksiyon `gizli_yedek_al()`, pg_cron işi `kartborsa-gizli-yedek` her gün 03:23 (TR), 30 gün saklanır. Yanlışlıkla silmeye karşı korur; Supabase projesinin tamamen kaybına karşı korumaz. Geri yüklemek için: `select veri->'teklifler' from gizli_yedek where gun = 'YYYY-MM-DD';`

## 22 Kasım 2026 (akşam) — Pokémon / Cyberpunk seçimi
- Üstte "⚡ Pokémon / 🌆 Cyberpunk" seçici (`#oyunSec`). Cyberpunk seçilince İngilizce/Japonca seçimi gizlenir, site sarı-camgöbeği renge geçer. Teknik olarak Cyberpunk üçüncü "dil": `DIL='cp'`, setlerde `s[7]='cp'`, katalog `cards_cp.json` (seçili oyunun kataloğu önce, diğerleri arkada yüklenir; dosya yoksa site İngilizce Pokémon'a döner).
- Veri: `.github/scripts/cyberpunk.py` (yayin.yml'de "Cyberpunk TCG kataloğu ve fiyatları", her yayında çalışır, ardından fiyat-verisi kaydedilir). Kaynak tcgcsv.com = TCGplayer günlük dökümü, kategori 92. 22 Kasım: 14 set, 528 kart (Welcome to Night City Retail + Beta 172'şer, iki başlangıç destesi ×2 baskı, box topper'lar, Set 1 promoları, Judge, Pre-Release, Night City Brawl, Edgerunner Open); 501 kartın fiyatı var. "Alpha Kit" grubunda kart yok (sadece kapalı ürün). Yeni setler TCGplayer'a eklenince kendiliğinden gelir.
- Kart kimliği `cp-<grup>-<ürün no>`; kart dizisinde c[4]=kart türü (Legend/Unit/Program/Gear), c[5]=renk (Türkçe), c[12]=arama (renk, tür, etiketler), c[17]={r renk, m maliyet, g güç, ram, e eddies, t etiketler, x kart metni, u TCGplayer adresi}. Nadirlik kısaltmaları: C Common, UC Uncommon, R Rare, E Epic, NR Nova Rare, S Secret, IL Iconic Legend, IO Iconic Other, IS Iconic Secret. Kart adlarının sonundaki "(Epic)" gibi nadirlik ekleri çıkarılır.
- Resimler TCGplayer CDN'den doğrudan (`_200w`/`_400w` ızgarada, `_in_1000x1000` detayda); wsrv.nl TCGplayer resimlerini açamıyor.
- Fiyatlar: TCGplayer market (yoksa orta) fiyatı, Normal ve Foil varyant; `fiyat/set/cp-*.json` + `ozet.json`; geçmiş fiyat-verisi dalında `cyberpunk/gecmis.json`; tam katalog `cyberpunk/cards_cp.json`.
- Kart detayında maliyet, güç, RAM, Eddies simgesi, etiketler ve kart metni; fiyat bağlantıları TCGplayer ürün sayfası + eBay. Tür filtresi Legend/Unit/Program/Gear; vitrin, Piyasa, Kart Al, İlan Ver (kapalı ürünlerde "Cyberpunk TCG setleri"), koleksiyon, set tamamlama, takip, teklif ve değerlendirme Cyberpunk'ta da aynı çalışır.
- Kart tarama: `kart_izi.py` 4. argüman olarak `veri/cyberpunk/cards_cp.json`'u okur (kart-izi.yml güncellendi); izler bir sonraki kart-izi çalışmasında eklenir.
