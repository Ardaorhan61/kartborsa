# KartBorsa

Pokémon kart kataloğu ve ilan pazarı. Site: https://ardaorhan61.github.io/kartborsa/

- `index.html` – site (katalog, Kart Al, İlan Ver, İlanlarım)
- `cards.json` – kart veritabanı (pokemon-tcg-data, Kasım 2026)
- `supabase.sql` – ilan veritabanının kurulumu (Supabase projesi: kartborsa)

İlanlar Supabase'de `listings` tablosunda, satıcı fotoğrafları `photos` deposunda durur.
Uygunsuz bir ilanı silmek için: Supabase → Table Editor → listings → satırı sil.

## Fiyatlar
Her gün 06:41'de `.github/workflows/yayin.yml` Pokémon TCG API'sinden (TCGplayer ve Cardmarket) güncel fiyatları ve
frankfurter.app'ten döviz kurlarını çeker, fiyat geçmişine ekler (`fiyat-verisi` dalı) ve siteyi yeniden yayınlar.
Site GitHub Actions ile yayınlanır (Settings → Pages → Source: GitHub Actions).

## Profil, koleksiyon, takip listesi
`supabase-profil.sql` ile kurulur. Kullanıcılar e-posta + şifreyle kayıt olur (Supabase → Authentication → "Confirm email" kapalı).
Koleksiyon ve takip listesi gizlidir; koleksiyon, kullanıcı profilinde "herkese açık" seçerse görünür.
