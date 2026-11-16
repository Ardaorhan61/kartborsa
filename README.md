# KartBorsa

Pokémon kart kataloğu ve ilan pazarı. Site: https://ardaorhan61.github.io/kartborsa/

- `index.html` – site (katalog, Kart Al, İlan Ver, İlanlarım)
- `cards.json` – kart veritabanı (pokemon-tcg-data, Kasım 2026)
- `supabase.sql` – ilan veritabanının kurulumu (Supabase projesi: kartborsa)

İlanlar Supabase'de `listings` tablosunda, satıcı fotoğrafları `photos` deposunda durur.
Uygunsuz bir ilanı silmek için: Supabase → Table Editor → listings → satırı sil.
