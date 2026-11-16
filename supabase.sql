-- KartBorsa veritabanı kurulumu (Supabase SQL Editor'de bir kez çalıştırılır)

create table if not exists public.listings (
  id          uuid primary key default gen_random_uuid(),
  owner       uuid not null default auth.uid() references auth.users(id) on delete cascade,
  card_id     text not null check (char_length(card_id) between 1 and 40),
  card_name   text not null check (char_length(card_name) between 1 and 80),
  set_name    text check (char_length(set_name) <= 80),
  price       integer not null check (price between 1 and 10000000),
  qty         integer not null default 1 check (qty between 0 and 999),
  cond        text not null default 'Near Mint' check (cond in ('Mint','Near Mint','Excellent','Good','Played','Hasarlı')),
  lang        text not null default 'İngilizce' check (lang in ('İngilizce','Japonca','Türkçe','Diğer')),
  note        text check (char_length(note) <= 300),
  seller_name text not null check (char_length(seller_name) between 1 and 40),
  instagram   text check (char_length(instagram) <= 40),
  whatsapp    text check (char_length(whatsapp) <= 20),
  city        text check (char_length(city) <= 40),
  photo_url   text check (char_length(photo_url) <= 300),
  status      text not null default 'active' check (status in ('active','sold')),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),
  constraint contact_required check (coalesce(instagram,'') <> '' or coalesce(whatsapp,'') <> '')
);

create index if not exists listings_card_idx on public.listings (card_id) where status = 'active';
create index if not exists listings_created_idx on public.listings (created_at desc);

alter table public.listings enable row level security;

drop policy if exists "herkes okur" on public.listings;
create policy "herkes okur" on public.listings for select to anon, authenticated using (true);

drop policy if exists "kendi ilanini ekler" on public.listings;
create policy "kendi ilanini ekler" on public.listings for insert to authenticated with check (owner = auth.uid());

drop policy if exists "kendi ilanini duzenler" on public.listings;
create policy "kendi ilanini duzenler" on public.listings for update to authenticated using (owner = auth.uid()) with check (owner = auth.uid());

drop policy if exists "kendi ilanini siler" on public.listings;
create policy "kendi ilanini siler" on public.listings for delete to authenticated using (owner = auth.uid());

-- owner değiştirilemesin, updated_at güncellensin
create or replace function public.listings_guard() returns trigger language plpgsql as $$
begin
  new.owner := old.owner;
  new.created_at := old.created_at;
  new.updated_at := now();
  return new;
end $$;
drop trigger if exists listings_guard on public.listings;
create trigger listings_guard before update on public.listings for each row execute function public.listings_guard();

-- spam sınırı: kişi başı en fazla 200 ilan, saatte en fazla 30 yeni ilan
create or replace function public.listings_limit() returns trigger language plpgsql security definer set search_path = public as $$
begin
  if (select count(*) from public.listings where owner = new.owner) >= 200 then
    raise exception 'İlan sınırına ulaştın (200).';
  end if;
  if (select count(*) from public.listings where owner = new.owner and created_at > now() - interval '1 hour') >= 30 then
    raise exception 'Çok hızlı ilan ekliyorsun, biraz sonra tekrar dene.';
  end if;
  return new;
end $$;
drop trigger if exists listings_limit on public.listings;
create trigger listings_limit before insert on public.listings for each row execute function public.listings_limit();

-- fotoğraflar: herkese açık okunur, herkes sadece kendi klasörüne yükler/siler
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('photos', 'photos', true, 1048576, array['image/jpeg','image/png','image/webp'])
on conflict (id) do update set public = true, file_size_limit = 1048576, allowed_mime_types = array['image/jpeg','image/png','image/webp'];

drop policy if exists "foto yukle" on storage.objects;
create policy "foto yukle" on storage.objects for insert to authenticated
  with check (bucket_id = 'photos' and (storage.foldername(name))[1] = auth.uid()::text);

drop policy if exists "foto sil" on storage.objects;
create policy "foto sil" on storage.objects for delete to authenticated
  using (bucket_id = 'photos' and (storage.foldername(name))[1] = auth.uid()::text);
