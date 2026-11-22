-- KartBorsa: teklif ve değerlendirme e-posta bildirimleri (Resend) + gizli verilerin günlük veritabanı içi yedeği (22 Kasım 2026)
-- Resend API anahtarı Supabase Vault'ta "resend_api_key" adıyla durur; yoksa e-posta gönderilmez (hata vermez).
create extension if not exists pg_net with schema extensions;
create extension if not exists pg_cron;

alter table public.profiles add column if not exists email_bildirim boolean not null default true;

create or replace function public.kb_esc(t text) returns text language sql immutable as $f$
  select replace(replace(replace(replace(coalesce(t,''),'&','&amp;'),'<','&lt;'),'>','&gt;'),'"','&quot;');
$f$;
create or replace function public.kb_tl(n numeric) returns text language sql immutable as $f$
  select replace(to_char(n,'FM999,999,999,990'),',','.')||' ₺';
$f$;

create or replace function public.kb_eposta(alici uuid, konu text, baslik text, metin text, dugme text default 'Tekliflerime git', link text default 'https://www.kartborsa.com/?sayfa=teklifler')
returns void language plpgsql security definer set search_path = public, extensions as $f$
declare k text; adres text; acik boolean; html text;
begin
  select decrypted_secret into k from vault.decrypted_secrets where name = 'resend_api_key' limit 1;
  if coalesce(k,'') = '' then return; end if;
  select email into adres from auth.users where id = alici;
  select email_bildirim into acik from public.profiles where id = alici;
  if adres is null or acik is false then return; end if;
  html := '<div style="font-family:Arial,Helvetica,sans-serif;max-width:520px;margin:0 auto;padding:24px;background:#0f1220;color:#eef0fa;border-radius:14px">'
    || '<div style="font-size:22px;font-weight:700;color:#ffcb3d;margin-bottom:14px">⚡ KartBorsa</div>'
    || '<div style="font-size:18px;font-weight:700;margin-bottom:8px">' || baslik || '</div>'
    || '<div style="font-size:15px;line-height:1.55;color:#d6d9ee">' || metin || '</div>'
    || '<a href="' || link || '" style="display:inline-block;margin-top:18px;background:#ffcb3d;color:#1a1300;padding:12px 20px;border-radius:10px;text-decoration:none;font-weight:700">' || dugme || '</a>'
    || '<div style="font-size:12px;color:#9aa1c3;margin-top:22px">Bu bildirimleri KartBorsa › Profil › Profil Ayarları''ndan kapatabilirsin.</div></div>';
  perform net.http_post(url := 'https://api.resend.com/emails',
    headers := jsonb_build_object('Authorization', 'Bearer ' || k, 'Content-Type', 'application/json'),
    body := jsonb_build_object('from', 'KartBorsa <noreply@kartborsa.com>', 'to', jsonb_build_array(adres), 'subject', konu, 'html', html));
exception when others then raise warning 'KartBorsa e-postası gönderilemedi: %', sqlerrm;
end $f$;
revoke all on function public.kb_eposta(uuid,text,text,text,text,text) from public, anon, authenticated;

create or replace function public.offers_bildir() returns trigger language plpgsql security definer set search_path = public as $f$
declare ad_alici text; ad_satici text; kart text; ben uuid := auth.uid();
begin
  select display_name into ad_alici from public.profiles where id = new.buyer;
  select display_name into ad_satici from public.profiles where id = new.seller;
  kart := '<b>' || kb_esc(new.card_name) || '</b>';
  if tg_op = 'INSERT' then
    perform kb_eposta(new.seller, 'Yeni teklif: ' || new.card_name || ' – ' || kb_tl(new.amount),
      'İlanına yeni teklif geldi 💰',
      kb_esc(ad_alici) || ', ' || kart || ' ilanın için <b>' || kb_tl(new.amount) || '</b> teklif etti (' || new.qty || ' adet).'
      || case when coalesce(new.note,'') <> '' then '<br><br>Not: “' || kb_esc(new.note) || '”' else '' end
      || '<br><br>Kabul edebilir, reddedebilir ya da karşı teklif verebilirsin.');
    return new;
  end if;
  if new.status is not distinct from old.status then return new; end if;
  if new.status = 'karsi' then
    perform kb_eposta(new.buyer, 'Karşı teklif: ' || new.card_name || ' – ' || kb_tl(new.counter), 'Satıcı karşı teklif verdi',
      kb_esc(ad_satici) || ', ' || kart || ' için verdiğin ' || kb_tl(old.amount) || ' teklife <b>' || kb_tl(new.counter) || '</b> karşı teklif verdi. Kabul edebilir ya da reddedebilirsin.');
  elsif new.status = 'kabul' and old.status = 'bekliyor' then
    perform kb_eposta(new.buyer, 'Teklifin kabul edildi: ' || new.card_name, 'Teklifin kabul edildi 🎉',
      kb_esc(ad_satici) || ', ' || kart || ' için verdiğin <b>' || kb_tl(new.amount) || '</b> teklifi kabul etti (' || new.qty || ' adet). Ödeme ve kargoyu ayarlamak için satıcıya WhatsApp ya da Instagram''dan yaz.');
  elsif new.status = 'kabul' and old.status = 'karsi' then
    perform kb_eposta(new.seller, 'Karşı teklifin kabul edildi: ' || new.card_name, 'Karşı teklifin kabul edildi 🎉',
      kb_esc(ad_alici) || ', ' || kart || ' için verdiğin <b>' || kb_tl(new.amount) || '</b> karşı teklifi kabul etti (' || new.qty || ' adet). Alıcı seninle iletişime geçecek.');
  elsif new.status = 'red' and ben = new.buyer then
    perform kb_eposta(new.seller, 'Karşı teklifin reddedildi: ' || new.card_name, 'Karşı teklifin reddedildi',
      kb_esc(ad_alici) || ', ' || kart || ' için verdiğin ' || kb_tl(old.counter) || ' karşı teklifi reddetti.');
  elsif new.status = 'red' then
    perform kb_eposta(new.buyer, 'Teklifin reddedildi: ' || new.card_name, 'Teklifin reddedildi',
      kb_esc(ad_satici) || ', ' || kart || ' için verdiğin ' || kb_tl(new.amount) || ' teklifi kabul etmedi. İstersen yeni bir teklif verebilirsin.',
      'İlanlara git', 'https://www.kartborsa.com/');
  elsif new.status = 'geri' then
    perform kb_eposta(new.seller, 'Teklif geri çekildi: ' || new.card_name, 'Teklif geri çekildi',
      kb_esc(ad_alici) || ', ' || kart || ' için verdiği ' || kb_tl(new.amount) || ' teklifi geri çekti.');
  elsif new.status = 'iptal' then
    perform kb_eposta(case when ben = new.buyer then new.seller else new.buyer end, 'Anlaşma iptal edildi: ' || new.card_name, 'Anlaşma iptal edildi',
      kb_esc(case when ben = new.buyer then ad_alici else ad_satici end) || ', ' || kart || ' için ' || kb_tl(new.amount) || ' tutarındaki kabul edilmiş teklifi iptal etti.');
  end if;
  return new;
end $f$;
drop trigger if exists offers_bildir on public.offers;
create trigger offers_bildir after insert or update on public.offers for each row execute function public.offers_bildir();

create or replace function public.reviews_bildir() returns trigger language plpgsql security definer set search_path = public as $f$
declare ad text;
begin
  if tg_op = 'INSERT' then
    select display_name into ad from public.profiles where id = new.reviewer;
    perform kb_eposta(new.seller, 'Yeni değerlendirme: ' || repeat('★', new.rating), 'Hakkında yeni bir değerlendirme var',
      kb_esc(ad) || ' sana <b>' || repeat('★', new.rating) || repeat('☆', 5 - new.rating) || '</b> verdi.'
      || case when coalesce(new.comment,'') <> '' then '<br><br>“' || kb_esc(new.comment) || '”' else '' end
      || '<br><br>İstersen profilinden herkese açık bir cevap yazabilirsin.', 'Değerlendirmelerime git', 'https://www.kartborsa.com/?sayfa=degerlendirmeler');
  elsif coalesce(new.reply,'') <> '' and new.reply is distinct from old.reply then
    select display_name into ad from public.profiles where id = new.seller;
    perform kb_eposta(new.reviewer, 'Satıcı değerlendirmene cevap verdi', 'Satıcı değerlendirmene cevap verdi',
      kb_esc(ad) || ' yorumuna cevap yazdı:<br><br>“' || kb_esc(new.reply) || '”', 'KartBorsa''yı aç', 'https://www.kartborsa.com/');
  end if;
  return new;
end $f$;
drop trigger if exists reviews_bildir on public.reviews;
create trigger reviews_bildir after insert or update on public.reviews for each row execute function public.reviews_bildir();

-- gizli verilerin günlük yedeği (teklifler, koleksiyon, takip, arkadaşlık, sipariş); sadece veritabanı yöneticisi görür, 30 gün saklanır
create table if not exists public.gizli_yedek (gun date primary key, veri jsonb not null, olusturma timestamptz not null default now());
alter table public.gizli_yedek enable row level security;
revoke all on public.gizli_yedek from anon, authenticated;
create or replace function public.gizli_yedek_al() returns text language plpgsql security definer set search_path = public as $f$
declare v jsonb;
begin
  v := jsonb_build_object(
    'teklifler', (select coalesce(jsonb_agg(x), '[]') from public.offers x),
    'koleksiyon', (select coalesce(jsonb_agg(x), '[]') from public.collection x),
    'takip', (select coalesce(jsonb_agg(x), '[]') from public.watchlist x),
    'arkadaslar', (select coalesce(jsonb_agg(x), '[]') from public.friendships x),
    'siparisler', (select coalesce(jsonb_agg(x), '[]') from public.siparisler x));
  insert into public.gizli_yedek (gun, veri) values (current_date, v)
    on conflict (gun) do update set veri = excluded.veri, olusturma = now();
  delete from public.gizli_yedek where gun < current_date - 30;
  return format('teklif %s, koleksiyon %s, takip %s, arkadaşlık %s, sipariş %s',
    jsonb_array_length(v->'teklifler'), jsonb_array_length(v->'koleksiyon'), jsonb_array_length(v->'takip'),
    jsonb_array_length(v->'arkadaslar'), jsonb_array_length(v->'siparisler'));
end $f$;
revoke all on function public.gizli_yedek_al() from public, anon, authenticated;
select cron.schedule('kartborsa-gizli-yedek', '23 0 * * *', 'select public.gizli_yedek_al()');
select public.gizli_yedek_al() as ilk_yedek;
