-- KartBorsa: satıcı ödeme hesapları ve siparişler (supabase-profil.sql'den sonra bir kez çalıştırılır)
-- Şimdilik TEST modu: ödeme adımı gerçek para çekmez. PayTR onaylanınca ödeme adımı gerçeğiyle değişecek.

-- ---------- satıcı ödeme hesabı (sadece sahibi görür) ----------
create table if not exists public.odeme_hesaplari (
  owner      uuid primary key default auth.uid() references auth.users(id) on delete cascade,
  ad_soyad   text not null check (char_length(ad_soyad) between 3 and 80),
  iban       text not null check (iban ~ '^TR[0-9]{24}$'),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
alter table public.odeme_hesaplari enable row level security;
drop policy if exists "odeme hesabi kendi" on public.odeme_hesaplari;
create policy "odeme hesabi kendi" on public.odeme_hesaplari for all to authenticated
  using (owner = auth.uid()) with check (owner = auth.uid());

-- herkes sadece "bu satıcı kartla satış yapıyor mu" bilgisini görebilir, IBAN'ı göremez
create or replace function public.kartla_satis_acik(satici uuid) returns boolean
language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.odeme_hesaplari where owner = satici);
$$;
grant execute on function public.kartla_satis_acik(uuid) to anon, authenticated;

-- ---------- siparişler (alıcı ve satıcı görür, sadece aşağıdaki fonksiyonlarla değişir) ----------
create table if not exists public.siparisler (
  id             uuid primary key default gen_random_uuid(),
  no             bigint generated always as identity,
  listing_id     uuid references public.listings(id) on delete set null,
  card_id        text not null,
  card_name      text not null,
  alici          uuid not null references auth.users(id) on delete cascade,
  satici         uuid not null references auth.users(id) on delete cascade,
  adet           integer not null check (adet between 1 and 99),
  birim_fiyat    integer not null check (birim_fiyat > 0),
  tutar          integer not null,
  komisyon       integer not null,
  satici_alacak  integer not null,
  teslimat       jsonb not null,
  durum          text not null default 'odeme_bekliyor'
                 check (durum in ('odeme_bekliyor','odendi','kargoda','teslim_alindi','aktarildi','iptal','itiraz')),
  kargo          text check (char_length(kargo) <= 80),
  test           boolean not null default true,
  olusturma      timestamptz not null default now(),
  odeme_zamani   timestamptz,
  kargo_zamani   timestamptz,
  teslim_zamani  timestamptz,
  aktarim_zamani timestamptz
);
create index if not exists siparisler_alici_idx on public.siparisler (alici, olusturma desc);
create index if not exists siparisler_satici_idx on public.siparisler (satici, olusturma desc);
alter table public.siparisler enable row level security;
drop policy if exists "siparis tarafları gorur" on public.siparisler;
create policy "siparis tarafları gorur" on public.siparisler for select to authenticated
  using (alici = auth.uid() or satici = auth.uid());

-- KartBorsa komisyonu (yüzde). Gerçek oran şirket kurulunca belirlenecek.
create or replace function public.komisyon_orani() returns numeric language sql immutable as $$ select 5.0 $$;

-- 1) alıcı sipariş oluşturur
create or replace function public.siparis_olustur(p_listing uuid, p_adet int, p_teslimat jsonb) returns uuid
language plpgsql security definer set search_path = public as $$
declare l public.listings; uid uuid := auth.uid(); t int; k int; sid uuid;
begin
  if uid is null then raise exception 'Satın almak için giriş yapmalısın.'; end if;
  if p_adet is null or p_adet < 1 or p_adet > 99 then raise exception 'Adet 1 ile 99 arasında olmalı.'; end if;
  if char_length(coalesce(p_teslimat->>'ad','')) < 3 or char_length(coalesce(p_teslimat->>'tel','')) < 10
     or char_length(coalesce(p_teslimat->>'adres','')) < 10 or char_length(coalesce(p_teslimat->>'il','')) < 2
     or char_length(p_teslimat::text) > 800 then
    raise exception 'Teslimat bilgilerini eksiksiz yaz (ad soyad, telefon, adres, il).';
  end if;
  select * into l from public.listings where id = p_listing for update;
  if not found or l.status <> 'active' then raise exception 'Bu ilan artık satışta değil.'; end if;
  if l.owner = uid then raise exception 'Kendi ilanını satın alamazsın.'; end if;
  if l.qty < p_adet then raise exception 'Satıcının elinde % adet var.', l.qty; end if;
  if not exists (select 1 from public.odeme_hesaplari where owner = l.owner) then
    raise exception 'Bu satıcı kartla satış açmamış; satıcıyla iletişime geçebilirsin.';
  end if;
  if (select count(*) from public.siparisler where alici = uid and durum = 'odeme_bekliyor') >= 10 then
    raise exception 'Ödenmemiş çok fazla siparişin var.';
  end if;
  t := l.price * p_adet;
  k := round(t * public.komisyon_orani() / 100.0);
  insert into public.siparisler (listing_id, card_id, card_name, alici, satici, adet, birim_fiyat, tutar, komisyon, satici_alacak, teslimat)
  values (l.id, l.card_id, l.card_name, uid, l.owner, p_adet, l.price, t, k, t - k,
          jsonb_build_object('ad', p_teslimat->>'ad', 'tel', p_teslimat->>'tel', 'adres', p_teslimat->>'adres', 'il', p_teslimat->>'il'))
  returning id into sid;
  return sid;
end $$;

-- 2) TEST ödemesi: alıcı onaylar ya da vazgeçer (gerçek para çekilmez)
create or replace function public.test_odeme(p_id uuid, p_basarili boolean) returns text
language plpgsql security definer set search_path = public as $$
declare s public.siparisler; l public.listings;
begin
  select * into s from public.siparisler where id = p_id and alici = auth.uid() for update;
  if not found then raise exception 'Sipariş bulunamadı.'; end if;
  if not s.test then raise exception 'Bu sipariş test siparişi değil.'; end if;
  if s.durum <> 'odeme_bekliyor' then raise exception 'Bu siparişin ödemesi zaten işlendi.'; end if;
  if not p_basarili then
    update public.siparisler set durum = 'iptal' where id = p_id; return 'iptal';
  end if;
  select * into l from public.listings where id = s.listing_id for update;
  if not found or l.status <> 'active' or l.qty < s.adet then
    update public.siparisler set durum = 'iptal' where id = p_id;
    raise exception 'Kart bu arada satıldı, sipariş iptal edildi.';
  end if;
  update public.listings set qty = qty - s.adet, status = case when qty - s.adet = 0 then 'sold' else status end where id = l.id;
  update public.siparisler set durum = 'odendi', odeme_zamani = now() where id = p_id;
  return 'odendi';
end $$;

-- 3) satıcı kargoya verir
create or replace function public.siparis_kargola(p_id uuid, p_kargo text) returns text
language plpgsql security definer set search_path = public as $$
begin
  if char_length(coalesce(p_kargo,'')) < 3 then raise exception 'Kargo firması ve takip numarasını yaz.'; end if;
  update public.siparisler set durum = 'kargoda', kargo = left(p_kargo, 80), kargo_zamani = now()
   where id = p_id and satici = auth.uid() and durum = 'odendi';
  if not found then raise exception 'Bu sipariş kargoya verilemez.'; end if;
  return 'kargoda';
end $$;

-- 4) alıcı teslim aldığını onaylar → para satıcıya aktarılır (testte hemen "aktarıldı" olur)
create or replace function public.siparis_teslim(p_id uuid) returns text
language plpgsql security definer set search_path = public as $$
begin
  update public.siparisler set durum = 'aktarildi', teslim_zamani = now(), aktarim_zamani = now()
   where id = p_id and alici = auth.uid() and durum = 'kargoda';
  if not found then raise exception 'Bu sipariş için teslim onayı verilemez.'; end if;
  return 'aktarildi';
end $$;

-- 5) alıcı sorun bildirir → para satıcıya geçmeden durur
create or replace function public.siparis_itiraz(p_id uuid) returns text
language plpgsql security definer set search_path = public as $$
begin
  update public.siparisler set durum = 'itiraz'
   where id = p_id and alici = auth.uid() and durum in ('odendi','kargoda');
  if not found then raise exception 'Bu sipariş için sorun bildirilemez.'; end if;
  return 'itiraz';
end $$;

-- 6) iptal: alıcı ödeme öncesi; satıcı kargodan önce (stok geri döner, testte para iadesi kendiliğinden)
create or replace function public.siparis_iptal(p_id uuid) returns text
language plpgsql security definer set search_path = public as $$
declare s public.siparisler;
begin
  select * into s from public.siparisler where id = p_id for update;
  if not found then raise exception 'Sipariş bulunamadı.'; end if;
  if s.alici = auth.uid() and s.durum = 'odeme_bekliyor' then
    update public.siparisler set durum = 'iptal' where id = p_id; return 'iptal';
  end if;
  if s.satici = auth.uid() and s.durum = 'odendi' then
    update public.listings set qty = qty + s.adet, status = 'active' where id = s.listing_id;
    update public.siparisler set durum = 'iptal' where id = p_id; return 'iptal';
  end if;
  raise exception 'Bu sipariş şu an iptal edilemez.';
end $$;

revoke execute on function public.siparis_olustur(uuid, int, jsonb), public.test_odeme(uuid, boolean),
  public.siparis_kargola(uuid, text), public.siparis_teslim(uuid), public.siparis_itiraz(uuid), public.siparis_iptal(uuid) from anon, public;
grant execute on function public.siparis_olustur(uuid, int, jsonb), public.test_odeme(uuid, boolean),
  public.siparis_kargola(uuid, text), public.siparis_teslim(uuid), public.siparis_itiraz(uuid), public.siparis_iptal(uuid) to authenticated;
