-- KartBorsa: satıcı değerlendirmeleri (reviews), teklifler (offers), derecelendirilmiş kartlar ve kapalı ürünler için ilan alanları (22 Kasım 2026)
-- supabase-odeme.sql'den sonra Supabase SQL Editor'de bir kez çalıştırılır (22 Kasım 2026'da çalıştırıldı). Tekrar çalıştırmak zarar vermez.
alter table public.listings add column if not exists kind text not null default 'kart';
alter table public.listings add column if not exists product_type text;
alter table public.listings add column if not exists grade_co text;
alter table public.listings add column if not exists grade numeric(3,1);
alter table public.listings add column if not exists grade_label text;
alter table public.listings add column if not exists cert_no text;

alter table public.listings drop constraint if exists listings_kind_check;
alter table public.listings add constraint listings_kind_check check (kind in ('kart','kapali'));
alter table public.listings drop constraint if exists listings_product_type_check;
alter table public.listings add constraint listings_product_type_check check (
  product_type is null or product_type in ('Booster paketi','Booster kutusu','Elite Trainer Box','Koleksiyon kutusu','Tin kutu',
    'Blister','Build & Battle','Hazır deste','Premium koleksiyon','Booster bundle','Diğer'));
alter table public.listings drop constraint if exists listings_kapali_check;
alter table public.listings add constraint listings_kapali_check check (
  (kind = 'kart' and product_type is null) or (kind = 'kapali' and product_type is not null and grade_co is null));
alter table public.listings drop constraint if exists listings_grade_co_check;
alter table public.listings add constraint listings_grade_co_check check (grade_co is null or grade_co in ('PSA','CGC','BGS','TAG','SGC','ACE','Diğer'));
alter table public.listings drop constraint if exists listings_grade_check;
alter table public.listings add constraint listings_grade_check check (
  grade is null or (grade_co is not null and grade between 1 and 10 and grade * 2 = round(grade * 2)));
alter table public.listings drop constraint if exists listings_grade_label_check;
alter table public.listings add constraint listings_grade_label_check check (grade_label is null or (grade_co is not null and char_length(grade_label) <= 20));
alter table public.listings drop constraint if exists listings_cert_no_check;
alter table public.listings add constraint listings_cert_no_check check (cert_no is null or (grade_co is not null and cert_no ~ '^[A-Za-z0-9-]{4,30}$'));
alter table public.listings drop constraint if exists listings_cond_check;
alter table public.listings add constraint listings_cond_check check (cond in
  ('Mint','Near Mint','Excellent','Good','Played','Hasarlı','Jelatinli','Jelatinsiz','Kutusu hasarlı'));
alter table public.listings drop constraint if exists listings_lang_check;
alter table public.listings add constraint listings_lang_check check (lang in ('İngilizce','Japonca','Türkçe','Korece','Çince','Diğer'));

create table if not exists public.reviews (
  id         uuid primary key default gen_random_uuid(),
  seller     uuid not null references auth.users(id) on delete cascade,
  reviewer   uuid not null default auth.uid() references auth.users(id) on delete cascade,
  rating     smallint not null check (rating between 1 and 5),
  comment    text check (char_length(comment) <= 500),
  reply      text check (char_length(reply) <= 500),
  verified   boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (seller, reviewer),
  check (seller <> reviewer)
);
create index if not exists reviews_seller_idx on public.reviews (seller, created_at desc);
alter table public.reviews enable row level security;
drop policy if exists "yorumlar herkese acik" on public.reviews;
create policy "yorumlar herkese acik" on public.reviews for select to anon, authenticated using (true);
drop policy if exists "yorum yazar" on public.reviews;
create policy "yorum yazar" on public.reviews for insert to authenticated
  with check (reviewer = auth.uid() and seller <> auth.uid()
    and exists (select 1 from public.profiles p where p.id = auth.uid()));
drop policy if exists "yorum duzenler" on public.reviews;
create policy "yorum duzenler" on public.reviews for update to authenticated
  using (auth.uid() in (reviewer, seller)) with check (auth.uid() in (reviewer, seller));
drop policy if exists "yorum siler" on public.reviews;
create policy "yorum siler" on public.reviews for delete to authenticated using (reviewer = auth.uid());

create table if not exists public.offers (
  id         uuid primary key default gen_random_uuid(),
  listing_id uuid not null references public.listings(id) on delete cascade,
  buyer      uuid not null default auth.uid() references auth.users(id) on delete cascade,
  seller     uuid references auth.users(id) on delete cascade,
  amount     integer not null check (amount between 1 and 10000000),
  qty        integer not null default 1 check (qty between 1 and 999),
  note       text check (char_length(note) <= 200),
  counter    integer check (counter between 1 and 10000000),
  status     text not null default 'bekliyor' check (status in ('bekliyor','karsi','kabul','red','geri','iptal')),
  card_name  text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (buyer <> seller)
);
create index if not exists offers_buyer_idx on public.offers (buyer, created_at desc);
create index if not exists offers_seller_idx on public.offers (seller, created_at desc);
create unique index if not exists offers_tek_acik on public.offers (listing_id, buyer) where status in ('bekliyor','karsi');
alter table public.offers enable row level security;
drop policy if exists "teklif taraflari gorur" on public.offers;
create policy "teklif taraflari gorur" on public.offers for select to authenticated using (auth.uid() in (buyer, seller));
drop policy if exists "teklif verir" on public.offers;
create policy "teklif verir" on public.offers for insert to authenticated with check (buyer = auth.uid());
drop policy if exists "teklif gunceller" on public.offers;
create policy "teklif gunceller" on public.offers for update to authenticated using (auth.uid() in (buyer, seller)) with check (auth.uid() in (buyer, seller));

create or replace function public.alisveris_var(alan uuid, satan uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.offers o where o.buyer = alan and o.seller = satan and o.status = 'kabul')
      or exists (select 1 from public.siparisler s where s.alici = alan and s.satici = satan and s.durum in ('teslim_alindi','aktarildi'));
$$;

create or replace function public.offers_ekle() returns trigger language plpgsql security definer set search_path = public as $$
declare l public.listings;
begin
  select * into l from public.listings where id = new.listing_id;
  if l.id is null then raise exception 'İlan bulunamadı.'; end if;
  if l.status <> 'active' or l.qty < 1 then raise exception 'Bu ilan artık satışta değil.'; end if;
  if l.owner = auth.uid() then raise exception 'Kendi ilanına teklif veremezsin.'; end if;
  if new.qty > l.qty then raise exception 'İlanda % adet var.', l.qty; end if;
  if new.amount >= l.price * new.qty then raise exception 'Teklif, ilan fiyatından düşük olmalı (ilan fiyatına satın almak için satıcıyla iletişime geç).'; end if;
  if new.amount < ceil(l.price * new.qty * 0.3) then raise exception 'Teklif, ilan fiyatının en az %%30''u olmalı.'; end if;
  if (select count(*) from public.offers where buyer = auth.uid() and created_at > now() - interval '1 hour') >= 30 then
    raise exception 'Çok hızlı teklif veriyorsun, biraz sonra tekrar dene.'; end if;
  new.buyer := auth.uid(); new.seller := l.owner; new.status := 'bekliyor'; new.counter := null;
  new.card_name := l.card_name; new.created_at := now(); new.updated_at := now();
  return new;
end $$;
drop trigger if exists offers_ekle on public.offers;
create trigger offers_ekle before insert on public.offers for each row execute function public.offers_ekle();

create or replace function public.offers_guncelle() returns trigger language plpgsql security definer set search_path = public as $$
declare me uuid := auth.uid(); ok boolean := false;
begin
  new.id := old.id; new.listing_id := old.listing_id; new.buyer := old.buyer; new.seller := old.seller;
  new.qty := old.qty; new.note := old.note; new.card_name := old.card_name; new.created_at := old.created_at; new.updated_at := now();
  if new.status = old.status and new.amount = old.amount and new.counter is not distinct from old.counter then return new; end if;
  if me = old.seller then
    if old.status = 'bekliyor' and new.status in ('kabul','red') then new.amount := old.amount; new.counter := old.counter; ok := true;
    elsif old.status = 'bekliyor' and new.status = 'karsi' then
      if new.counter is null or new.counter <= old.amount then raise exception 'Karşı teklif, alıcının teklifinden yüksek olmalı.'; end if;
      new.amount := old.amount; ok := true;
    elsif old.status = 'karsi' and new.status = 'red' then new.amount := old.amount; ok := true;
    end if;
  elsif me = old.buyer then
    if old.status in ('bekliyor','karsi') and new.status = 'geri' then new.amount := old.amount; new.counter := old.counter; ok := true;
    elsif old.status = 'karsi' and new.status = 'kabul' then new.amount := old.counter; new.counter := old.counter; ok := true;
    elsif old.status = 'karsi' and new.status = 'red' then new.amount := old.amount; new.counter := old.counter; ok := true;
    end if;
  end if;
  if me in (old.buyer, old.seller) and old.status = 'kabul' and new.status = 'iptal' then new.amount := old.amount; new.counter := old.counter; ok := true; end if;
  if not ok then raise exception 'Bu teklif şu an bu şekilde değiştirilemez.'; end if;
  return new;
end $$;
drop trigger if exists offers_guncelle on public.offers;
create trigger offers_guncelle before update on public.offers for each row execute function public.offers_guncelle();

create or replace function public.reviews_guard() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if tg_op = 'INSERT' then
    if (select count(*) from public.reviews where reviewer = auth.uid() and created_at > now() - interval '1 day') >= 20 then
      raise exception 'Bugün çok fazla değerlendirme yazdın, yarın tekrar dene.'; end if;
    new.reviewer := auth.uid(); new.reply := null; new.created_at := now();
  else
    new.id := old.id; new.seller := old.seller; new.reviewer := old.reviewer; new.created_at := old.created_at;
    if auth.uid() = old.seller then new.rating := old.rating; new.comment := old.comment;
    else new.reply := old.reply; end if;
  end if;
  new.verified := public.alisveris_var(new.reviewer, new.seller);
  new.updated_at := now();
  return new;
end $$;
drop trigger if exists reviews_guard on public.reviews;
create trigger reviews_guard before insert or update on public.reviews for each row execute function public.reviews_guard();

create or replace function public.offers_yorum_dogrula() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if new.status is distinct from old.status then
    update public.reviews set verified = public.alisveris_var(new.buyer, new.seller) where reviewer = new.buyer and seller = new.seller;
  end if;
  return null;
end $$;
drop trigger if exists offers_yorum_dogrula on public.offers;
create trigger offers_yorum_dogrula after update on public.offers for each row execute function public.offers_yorum_dogrula();
