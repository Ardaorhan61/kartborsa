-- KartBorsa: güvenlik sıkılaştırması + 7/24 güvenlik izleme (23 Kasım 2026)
-- Mevcut verilere dokunmaz; yetkileri daraltır, kurallar ekler, 10 dakikada bir kontrol eden bir görev kurar.
-- 23 Kasım 2026 akşamı Supabase SQL Editor'da çalıştırıldı.

-- 1) Gereksiz yetkiler: ziyaretçi (anon) hiçbir tabloya yazamaz; kimse TRUNCATE/TRIGGER/REFERENCES kullanamaz
do $g$
declare t record;
begin
  for t in select c.relname from pg_class c join pg_namespace n on n.oid = c.relnamespace
           where n.nspname = 'public' and c.relkind in ('r','v','m','p') loop
    execute format('revoke insert, update, delete, truncate, references, trigger on public.%I from anon', t.relname);
    execute format('revoke truncate, references, trigger on public.%I from authenticated', t.relname);
  end loop;
end $g$;
alter default privileges in schema public revoke insert, update, delete, truncate, references, trigger on tables from anon;
alter default privileges in schema public revoke truncate, references, trigger on tables from authenticated;

-- 2) Bağlantı alanlarına zararlı adres (javascript: vb.) yazılamaz
alter table public.listings drop constraint if exists listings_photo_url_guvenli;
alter table public.listings add constraint listings_photo_url_guvenli check (photo_url is null or photo_url ~ '^https://[^\s"''<>\\]+$');
alter table public.profiles drop constraint if exists profiles_avatar_url_guvenli;
alter table public.profiles add constraint profiles_avatar_url_guvenli check (avatar_url is null or avatar_url ~ '^https://[^\s"''<>\\]+$');

-- 3) Yöneticiler ve deneme ödemesi: deneme modunda kartla ödemeyi sadece yönetici hesabı kullanabilir
create table if not exists public.kb_yonetici (user_id uuid primary key references auth.users(id) on delete cascade, eklenme timestamptz not null default now());
alter table public.kb_yonetici enable row level security;
revoke all on public.kb_yonetici from anon, authenticated;
insert into public.kb_yonetici (user_id) values ('3ce1d5d7-d228-41fd-829a-e3ac58c08d26') on conflict do nothing;

create or replace function public.siparis_deneme_kilidi() returns trigger language plpgsql security definer set search_path = public as $f$
begin
  if new.test is not false and not exists (select 1 from public.kb_yonetici where user_id = new.alici) then
    raise exception 'Kartla ödeme şu an deneme aşamasında; yakında açılacak. Şimdilik satıcıyla WhatsApp ya da Instagram''dan iletişime geçebilirsin.';
  end if;
  return new;
end $f$;
drop trigger if exists siparis_deneme_kilidi on public.siparisler;
create trigger siparis_deneme_kilidi before insert on public.siparisler for each row execute function public.siparis_deneme_kilidi();

-- 4) Güvenlik izleme
create table if not exists public.kb_guvenlik_olay (
  id bigserial primary key, zaman timestamptz not null default now(), kod text not null, ayrinti text, goruldu boolean not null default false);
create table if not exists public.kb_guvenlik_durum (
  id int primary key default 1 check (id = 1), son_kontrol timestamptz, iz jsonb not null default '{}');
alter table public.kb_guvenlik_olay enable row level security;
alter table public.kb_guvenlik_durum enable row level security;
revoke all on public.kb_guvenlik_olay, public.kb_guvenlik_durum from anon, authenticated;
insert into public.kb_guvenlik_durum (id) values (1) on conflict do nothing;

-- kb_uyari_eposta(): Resend anahtarı Vault'a (resend_api_key) eklendiğinde uyarıyı Arda'nın Gmail adresine de gönderir (adres Supabase'deki fonksiyonda yazılı)
-- kb_guvenlik_kontrol(): RLS kapalı tablo, politika/fonksiyon/yetki/cron/tablo/yönetici/Vault/depo değişikliği (parmak izi), anonim giriş,
--   olağandışı kayıt/ilan/teklif/değerlendirme/takas/fotoğraf/ilan değişikliği sayıları. Aynı uyarı 6 saatte bir kez yazılır.
-- kb_guvenlik_ozet(): ziyaretçiye açık; sadece son kontrol zamanı ve son 2 saatteki uyarı sayısı (ayrıntı yok)
-- pg_cron: kartborsa-guvenlik, */10 * * * *
-- Tam fonksiyon tanımları Supabase'de: SQL Editor'da  select pg_get_functiondef('public.kb_guvenlik_kontrol'::regproc);
