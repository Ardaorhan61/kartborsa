-- KartBorsa: Arıyorum, Takas, Fiyat alarmı, Bildirimler, Desteler (23 Kasım 2026)
-- Mevcut tablolara (ilanlar, profiller, koleksiyon...) veri olarak dokunmaz; sadece listings'e eşleşme tetikleyicisi ekler.
-- 23 Kasım 2026'da Supabase SQL Editor'da çalıştırıldı (5 tablo kuruldu, deneme geçti).
create extension if not exists pg_net with schema extensions;
create extension if not exists pg_cron;

create or replace function public.kb_guncellendi() returns trigger language plpgsql as $f$
begin new.updated_at := now(); return new; end $f$;

-- 🔍 Arıyorum
create table if not exists public.aranan (
  id         uuid primary key default gen_random_uuid(),
  owner      uuid not null default auth.uid() references auth.users(id) on delete cascade,
  card_id    text not null check (char_length(card_id) between 1 and 40),
  card_name  text not null check (char_length(card_name) between 1 and 80),
  set_name   text check (char_length(set_name) <= 80),
  max_price  integer check (max_price between 1 and 10000000),
  note       text check (char_length(note) <= 300),
  active     boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (owner, card_id)
);
create index if not exists aranan_kart on public.aranan (card_id) where active;
alter table public.aranan enable row level security;
drop policy if exists aranan_oku on public.aranan;
create policy aranan_oku on public.aranan for select using (active or owner = auth.uid());
drop policy if exists aranan_ekle on public.aranan;
create policy aranan_ekle on public.aranan for insert to authenticated with check (owner = auth.uid());
drop policy if exists aranan_guncelle on public.aranan;
create policy aranan_guncelle on public.aranan for update to authenticated using (owner = auth.uid()) with check (owner = auth.uid());
drop policy if exists aranan_sil on public.aranan;
create policy aranan_sil on public.aranan for delete to authenticated using (owner = auth.uid());
drop trigger if exists aranan_limit on public.aranan;
create trigger aranan_limit before insert on public.aranan for each row execute function public.row_limit('300');
drop trigger if exists aranan_tarih on public.aranan;
create trigger aranan_tarih before update on public.aranan for each row execute function public.kb_guncellendi();

-- 🔁 Takas
create table if not exists public.takas (
  id          uuid primary key default gen_random_uuid(),
  owner       uuid not null default auth.uid() references auth.users(id) on delete cascade,
  card_id     text not null check (char_length(card_id) between 1 and 40),
  card_name   text not null check (char_length(card_name) between 1 and 80),
  set_name    text check (char_length(set_name) <= 80),
  cond        text not null default 'Near Mint' check (cond in ('Mint','Near Mint','Excellent','Good','Played','Hasarlı')),
  lang        text not null default 'İngilizce' check (lang in ('İngilizce','Japonca','Türkçe','Korece','Çince','Diğer')),
  istenen     text[] not null default '{}' check (cardinality(istenen) <= 12),
  istenen_not text check (char_length(istenen_not) <= 300),
  city        text check (char_length(city) <= 40),
  status      text not null default 'active' check (status in ('active','closed')),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index if not exists takas_kart on public.takas (card_id) where status = 'active';
alter table public.takas enable row level security;
drop policy if exists takas_oku on public.takas;
create policy takas_oku on public.takas for select using (status = 'active' or owner = auth.uid());
drop policy if exists takas_ekle on public.takas;
create policy takas_ekle on public.takas for insert to authenticated with check (owner = auth.uid());
drop policy if exists takas_guncelle on public.takas;
create policy takas_guncelle on public.takas for update to authenticated using (owner = auth.uid()) with check (owner = auth.uid());
drop policy if exists takas_sil on public.takas;
create policy takas_sil on public.takas for delete to authenticated using (owner = auth.uid());
drop trigger if exists takas_limit on public.takas;
create trigger takas_limit before insert on public.takas for each row execute function public.row_limit('200');
drop trigger if exists takas_tarih on public.takas;
create trigger takas_tarih before update on public.takas for each row execute function public.kb_guncellendi();

-- ⏰ Fiyat alarmı
create table if not exists public.fiyat_alarm (
  id            uuid primary key default gen_random_uuid(),
  owner         uuid not null default auth.uid() references auth.users(id) on delete cascade,
  card_id       text not null check (char_length(card_id) between 1 and 40),
  card_name     text not null check (char_length(card_name) between 1 and 80),
  hedef         integer not null check (hedef between 1 and 10000000),
  yon           text not null check (yon in ('alti','ustu')),
  active        boolean not null default true,
  tetiklendi_at timestamptz,
  created_at    timestamptz not null default now(),
  unique (owner, card_id, yon)
);
alter table public.fiyat_alarm enable row level security;
drop policy if exists alarm_oku on public.fiyat_alarm;
create policy alarm_oku on public.fiyat_alarm for select to authenticated using (owner = auth.uid());
drop policy if exists alarm_ekle on public.fiyat_alarm;
create policy alarm_ekle on public.fiyat_alarm for insert to authenticated with check (owner = auth.uid());
drop policy if exists alarm_guncelle on public.fiyat_alarm;
create policy alarm_guncelle on public.fiyat_alarm for update to authenticated using (owner = auth.uid()) with check (owner = auth.uid());
drop policy if exists alarm_sil on public.fiyat_alarm;
create policy alarm_sil on public.fiyat_alarm for delete to authenticated using (owner = auth.uid());
drop trigger if exists alarm_limit on public.fiyat_alarm;
create trigger alarm_limit before insert on public.fiyat_alarm for each row execute function public.row_limit('200');

-- 🔔 Bildirimler (sadece veritabanı fonksiyonları ekler; kullanıcı kendininkini görür, okundu yapar, siler)
create table if not exists public.bildirimler (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references auth.users(id) on delete cascade,
  tur        text not null default 'sistem' check (tur in ('aranan','alarm','takas','sistem')),
  baslik     text not null check (char_length(baslik) <= 200),
  metin      text check (char_length(metin) <= 600),
  link       text check (char_length(link) <= 300),
  card_id    text,
  okundu     boolean not null default false,
  created_at timestamptz not null default now()
);
create index if not exists bildirimler_kisi on public.bildirimler (user_id, created_at desc);
alter table public.bildirimler enable row level security;
drop policy if exists bildirim_oku on public.bildirimler;
create policy bildirim_oku on public.bildirimler for select to authenticated using (user_id = auth.uid());
drop policy if exists bildirim_guncelle on public.bildirimler;
create policy bildirim_guncelle on public.bildirimler for update to authenticated using (user_id = auth.uid()) with check (user_id = auth.uid());
drop policy if exists bildirim_sil on public.bildirimler;
create policy bildirim_sil on public.bildirimler for delete to authenticated using (user_id = auth.uid());
revoke insert on public.bildirimler from anon, authenticated;

-- 🃏 Desteler
create table if not exists public.desteler (
  id           uuid primary key default gen_random_uuid(),
  owner        uuid not null default auth.uid() references auth.users(id) on delete cascade,
  ad           text not null default 'Deste' check (char_length(ad) between 1 and 60),
  legends      jsonb not null default '[]',
  kartlar      jsonb not null default '[]',
  herkese_acik boolean not null default true,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),
  check (pg_column_size(kartlar) < 20000 and pg_column_size(legends) < 2000)
);
alter table public.desteler enable row level security;
drop policy if exists deste_oku on public.desteler;
create policy deste_oku on public.desteler for select using (herkese_acik or owner = auth.uid());
drop policy if exists deste_ekle on public.desteler;
create policy deste_ekle on public.desteler for insert to authenticated with check (owner = auth.uid());
drop policy if exists deste_guncelle on public.desteler;
create policy deste_guncelle on public.desteler for update to authenticated using (owner = auth.uid()) with check (owner = auth.uid());
drop policy if exists deste_sil on public.desteler;
create policy deste_sil on public.desteler for delete to authenticated using (owner = auth.uid());
drop trigger if exists deste_limit on public.desteler;
create trigger deste_limit before insert on public.desteler for each row execute function public.row_limit('100');
drop trigger if exists deste_tarih on public.desteler;
create trigger deste_tarih before update on public.desteler for each row execute function public.kb_guncellendi();

-- Bildirim yazma yardımcısı (site bildirimi + Resend anahtarı varsa e-posta)
create or replace function public.kb_bildir(alici uuid, p_tur text, p_baslik text, p_metin text, p_link text, p_kart text, e_konu text, e_html text, e_dugme text)
returns void language plpgsql security definer set search_path = public as $f$
begin
  insert into public.bildirimler (user_id, tur, baslik, metin, link, card_id) values (alici, p_tur, left(p_baslik,200), left(p_metin,600), p_link, p_kart);
  perform public.kb_eposta(alici, e_konu, p_baslik, e_html, e_dugme, p_link);
exception when others then raise warning 'KartBorsa bildirimi yazılamadı: %', sqlerrm;
end $f$;
revoke all on function public.kb_bildir(uuid,text,text,text,text,text,text,text,text) from public, anon, authenticated;

-- Eşleşme: aranan bir kart satışa konunca arayanlara haber
create or replace function public.listings_eslesme() returns trigger language plpgsql security definer set search_path = public as $f$
declare a record; link text := 'https://www.kartborsa.com/?kart=' || new.card_id;
begin
  if new.status <> 'active' then return new; end if;
  if tg_op = 'UPDATE' and old.status = 'active' then return new; end if;
  for a in select * from public.aranan where active and card_id = new.card_id and owner <> new.owner
           and (max_price is null or new.price <= max_price) loop
    perform public.kb_bildir(a.owner, 'aranan', 'Aradığın kart satışta: ' || new.card_name,
      kb_tl(new.price) || ' · ' || coalesce(new.cond,'') || coalesce(' · ' || new.city,''), link, new.card_id,
      'Aradığın kart satışta: ' || new.card_name,
      'Aradığın <b>' || kb_esc(new.card_name) || '</b> kartı <b>' || kb_tl(new.price) || '</b> fiyatla satışa kondu (' || kb_esc(new.cond) || coalesce(', ' || kb_esc(new.city),'') || ').',
      'Karta git');
  end loop;
  return new;
end $f$;
drop trigger if exists listings_eslesme on public.listings;
create trigger listings_eslesme after insert or update of status on public.listings for each row execute function public.listings_eslesme();

-- Eşleşme: aranan kart takasa konunca arayanlara; istediğin kart takasa konunca takas sahibine haber
create or replace function public.takas_eslesme() returns trigger language plpgsql security definer set search_path = public as $f$
declare a record; link text := 'https://www.kartborsa.com/?sayfa=takas';
begin
  if new.status <> 'active' then return new; end if;
  for a in select * from public.aranan where active and card_id = new.card_id and owner <> new.owner loop
    perform public.kb_bildir(a.owner, 'takas', 'Aradığın kart takasta: ' || new.card_name,
      new.cond || coalesce(' · ' || new.city,''), link, new.card_id,
      'Aradığın kart takasta: ' || new.card_name,
      'Aradığın <b>' || kb_esc(new.card_name) || '</b> kartı takas ilanına kondu (' || kb_esc(new.cond) || coalesce(', ' || kb_esc(new.city),'') || ').',
      'Takas ilanlarına git');
  end loop;
  for a in select distinct on (owner) * from public.takas where status = 'active' and owner <> new.owner and new.card_id = any(istenen) loop
    perform public.kb_bildir(a.owner, 'takas', 'Takasta istediğin kart çıktı: ' || new.card_name,
      'Karşılığında senin ' || a.card_name || ' kartını isteyebilirsin', link, new.card_id,
      'Takasta istediğin kart çıktı: ' || new.card_name,
      'Takas ilanında istediğin <b>' || kb_esc(new.card_name) || '</b> kartını başka biri takasa koydu.',
      'Takas ilanlarına git');
  end loop;
  return new;
end $f$;
drop trigger if exists takas_eslesme on public.takas;
create trigger takas_eslesme after insert on public.takas for each row execute function public.takas_eslesme();

-- Fiyat alarmları: her sabah fiyat güncellemesinden sonra sitenin fiyat dosyaları okunur
create table if not exists public.kb_istek (ad text primary key, istek_id bigint, zaman timestamptz not null default now());
alter table public.kb_istek enable row level security;
revoke all on public.kb_istek from anon, authenticated;

create or replace function public.alarm_fiyat_iste() returns void language plpgsql security definer set search_path = public, extensions as $f$
declare v text := to_char(now(),'YYYYMMDDHH24MI');
begin
  insert into public.kb_istek (ad, istek_id) values ('ozet', net.http_get('https://www.kartborsa.com/fiyat/ozet.json?a=' || v, timeout_milliseconds := 60000))
    on conflict (ad) do update set istek_id = excluded.istek_id, zaman = now();
  insert into public.kb_istek (ad, istek_id) values ('kur', net.http_get('https://www.kartborsa.com/fiyat/kur.json?a=' || v, timeout_milliseconds := 30000))
    on conflict (ad) do update set istek_id = excluded.istek_id, zaman = now();
end $f$;
revoke all on function public.alarm_fiyat_iste() from public, anon, authenticated;

create or replace function public.alarm_kontrol() returns text language plpgsql security definer set search_path = public as $f$
declare oz jsonb; kur jsonb; a record; p jsonb; v numeric; n int := 0; kac int := 0;
begin
  select r.content::jsonb into oz from net._http_response r join public.kb_istek i on i.istek_id = r.id where i.ad = 'ozet' and r.status_code = 200;
  select r.content::jsonb into kur from net._http_response r join public.kb_istek i on i.istek_id = r.id where i.ad = 'kur' and r.status_code = 200;
  if oz is null or kur is null then return 'fiyat dosyası okunamadı'; end if;
  for a in select * from public.fiyat_alarm where active and tetiklendi_at is null loop
    kac := kac + 1;
    p := oz->'c'->a.card_id;
    if p is null then continue; end if;
    v := case when jsonb_typeof(p->0) = 'number' then (p->>0)::numeric * (kur->>'USD')::numeric
              when jsonb_typeof(p->1) = 'number' then (p->>1)::numeric * (kur->>'EUR')::numeric end;
    if v is null then continue; end if;
    if (a.yon = 'alti' and v <= a.hedef) or (a.yon = 'ustu' and v >= a.hedef) then
      update public.fiyat_alarm set active = false, tetiklendi_at = now() where id = a.id;
      perform public.kb_bildir(a.owner, 'alarm', 'Fiyat alarmı: ' || a.card_name,
        'Piyasa değeri ' || kb_tl(round(v)) || ' (hedefin ' || kb_tl(a.hedef) || case when a.yon = 'alti' then ' altı)' else ' üstü)' end,
        'https://www.kartborsa.com/?kart=' || a.card_id, a.card_id,
        'Fiyat alarmı: ' || a.card_name || ' – ' || kb_tl(round(v)),
        '<b>' || kb_esc(a.card_name) || '</b> kartının piyasa değeri <b>' || kb_tl(round(v)) || '</b> oldu. Kurduğun hedef: ' || kb_tl(a.hedef)
          || case when a.yon = 'alti' then ' altına düşünce.' else ' üstüne çıkınca.' end || '<br><br>Alarm bir kez çaldı; istersen kart sayfasından yeniden kurabilirsin.',
        'Karta git');
      n := n + 1;
    end if;
  end loop;
  return format('%s alarm kontrol edildi, %s alarm çaldı', kac, n);
end $f$;
revoke all on function public.alarm_kontrol() from public, anon, authenticated;

-- TR 09:47 / 09:52 (UTC 06:47 / 06:52)
select cron.schedule('kartborsa-alarm-iste', '47 6 * * *', 'select public.alarm_fiyat_iste()');
select cron.schedule('kartborsa-alarm-kontrol', '52 6 * * *', 'select public.alarm_kontrol()');

-- gizli yedeğe yeni tablolar da girsin
create or replace function public.gizli_yedek_al() returns text language plpgsql security definer set search_path = public as $f$
declare v jsonb;
begin
  v := jsonb_build_object(
    'teklifler', (select coalesce(jsonb_agg(x), '[]') from public.offers x),
    'koleksiyon', (select coalesce(jsonb_agg(x), '[]') from public.collection x),
    'takip', (select coalesce(jsonb_agg(x), '[]') from public.watchlist x),
    'arkadaslar', (select coalesce(jsonb_agg(x), '[]') from public.friendships x),
    'siparisler', (select coalesce(jsonb_agg(x), '[]') from public.siparisler x),
    'aranan', (select coalesce(jsonb_agg(x), '[]') from public.aranan x),
    'takas', (select coalesce(jsonb_agg(x), '[]') from public.takas x),
    'fiyat_alarm', (select coalesce(jsonb_agg(x), '[]') from public.fiyat_alarm x),
    'desteler', (select coalesce(jsonb_agg(x), '[]') from public.desteler x));
  insert into public.gizli_yedek (gun, veri) values (current_date, v)
    on conflict (gun) do update set veri = excluded.veri, olusturma = now();
  delete from public.gizli_yedek where gun < current_date - 30;
  return format('teklif %s, koleksiyon %s, takip %s, arkadaşlık %s, sipariş %s, aranan %s, takas %s, alarm %s, deste %s',
    jsonb_array_length(v->'teklifler'), jsonb_array_length(v->'koleksiyon'), jsonb_array_length(v->'takip'),
    jsonb_array_length(v->'arkadaslar'), jsonb_array_length(v->'siparisler'), jsonb_array_length(v->'aranan'),
    jsonb_array_length(v->'takas'), jsonb_array_length(v->'fiyat_alarm'), jsonb_array_length(v->'desteler'));
end $f$;
revoke all on function public.gizli_yedek_al() from public, anon, authenticated;
