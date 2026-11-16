-- KartBorsa: profil, koleksiyon ve takip listesi (supabase.sql'den sonra bir kez çalıştırılır)

-- ---------- profiller (herkese açık) ----------
create table if not exists public.profiles (
  id              uuid primary key references auth.users(id) on delete cascade,
  display_name    text not null check (char_length(display_name) between 2 and 40),
  city            text check (char_length(city) <= 40),
  bio             text check (char_length(bio) <= 400),
  avatar_url      text check (char_length(avatar_url) <= 300),
  instagram       text check (char_length(instagram) <= 40),
  whatsapp        text check (char_length(whatsapp) <= 20),
  show_collection boolean not null default false,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);
alter table public.profiles enable row level security;
drop policy if exists "profiller herkese acik" on public.profiles;
create policy "profiller herkese acik" on public.profiles for select to anon, authenticated using (true);
drop policy if exists "kendi profilini olusturur" on public.profiles;
create policy "kendi profilini olusturur" on public.profiles for insert to authenticated with check (id = auth.uid());
drop policy if exists "kendi profilini duzenler" on public.profiles;
create policy "kendi profilini duzenler" on public.profiles for update to authenticated using (id = auth.uid()) with check (id = auth.uid());

-- profil değişince ilanlardaki satıcı bilgileri de güncellensin
create or replace function public.profiles_sync() returns trigger language plpgsql security definer set search_path = public as $$
begin
  new.updated_at := now();
  if tg_op = 'UPDATE' then
    new.created_at := old.created_at;
    update public.listings set seller_name = new.display_name, city = new.city,
      instagram = coalesce(nullif(new.instagram, ''), instagram), whatsapp = coalesce(nullif(new.whatsapp, ''), whatsapp)
      where owner = new.id;
  end if;
  return new;
end $$;
drop trigger if exists profiles_sync on public.profiles;
create trigger profiles_sync before insert or update on public.profiles for each row execute function public.profiles_sync();

-- ---------- koleksiyon ----------
create table if not exists public.collection (
  id         uuid primary key default gen_random_uuid(),
  owner      uuid not null default auth.uid() references auth.users(id) on delete cascade,
  card_id    text not null check (char_length(card_id) between 1 and 40),
  qty        integer not null default 1 check (qty between 1 and 9999),
  cond       text not null default 'Near Mint' check (cond in ('Mint','Near Mint','Excellent','Good','Played','Hasarlı')),
  paid       integer check (paid between 0 and 100000000),
  note       text check (char_length(note) <= 200),
  created_at timestamptz not null default now()
);
create index if not exists collection_owner_idx on public.collection (owner);
alter table public.collection enable row level security;
drop policy if exists "koleksiyon okuma" on public.collection;
create policy "koleksiyon okuma" on public.collection for select to anon, authenticated
  using (owner = auth.uid() or exists (select 1 from public.profiles p where p.id = owner and p.show_collection));
drop policy if exists "koleksiyon ekleme" on public.collection;
create policy "koleksiyon ekleme" on public.collection for insert to authenticated with check (owner = auth.uid());
drop policy if exists "koleksiyon duzenleme" on public.collection;
create policy "koleksiyon duzenleme" on public.collection for update to authenticated using (owner = auth.uid()) with check (owner = auth.uid());
drop policy if exists "koleksiyon silme" on public.collection;
create policy "koleksiyon silme" on public.collection for delete to authenticated using (owner = auth.uid());

-- ---------- takip listesi (sadece sahibi görür) ----------
create table if not exists public.watchlist (
  owner      uuid not null default auth.uid() references auth.users(id) on delete cascade,
  card_id    text not null check (char_length(card_id) between 1 and 40),
  created_at timestamptz not null default now(),
  primary key (owner, card_id)
);
alter table public.watchlist enable row level security;
drop policy if exists "takip kendi" on public.watchlist;
create policy "takip kendi" on public.watchlist for all to authenticated using (owner = auth.uid()) with check (owner = auth.uid());

-- kötüye kullanım sınırları
create or replace function public.row_limit() returns trigger language plpgsql security definer set search_path = public as $$
declare n int; lim int := tg_argv[0]::int;
begin
  execute format('select count(*) from public.%I where owner = $1', tg_table_name) into n using new.owner;
  if n >= lim then raise exception 'Sınıra ulaştın (%).', lim; end if;
  return new;
end $$;
drop trigger if exists collection_limit on public.collection;
create trigger collection_limit before insert on public.collection for each row execute function public.row_limit('3000');
drop trigger if exists watchlist_limit on public.watchlist;
create trigger watchlist_limit before insert on public.watchlist for each row execute function public.row_limit('500');
