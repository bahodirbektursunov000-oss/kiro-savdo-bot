from aiogram import Router, F
from html import escape
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database import Database
from config import Config
from states import AdminStates
from payment_service import format_money

router=Router()

def user_link_actions(rid):
 return InlineKeyboardMarkup(inline_keyboard=[
  [InlineKeyboardButton(text='✅ To‘ladim',callback_data=f'kiropaid:{rid}')],
  [InlineKeyboardButton(text='⚠️ Link ishlamadi',callback_data=f'kiroissue:{rid}'),InlineKeyboardButton(text='❌ Bekor qilish',callback_data=f'kirocancel:{rid}')]
 ])

def admin_link_actions(rid, status='requested'):
 # Show only actions valid for the request's current status.
 if status == 'requested':
  rows = [[InlineKeyboardButton(text='🔗 To‘lov linkini yuborish', callback_data=f'kiroseturl:{rid}')],
          [InlineKeyboardButton(text='❌ So‘rovni rad etish', callback_data=f'kiroreject:{rid}')]]
 elif status == 'link_sent':
  rows = [[InlineKeyboardButton(text='🔗 Linkni qayta yuborish', callback_data=f'kiroseturl:{rid}')],
          [InlineKeyboardButton(text='❌ Rad etish', callback_data=f'kiroreject:{rid}')]]
 elif status == 'payment_reported':
  rows = [[InlineKeyboardButton(text='✅ To‘lovni tasdiqlash', callback_data=f'kiroconfirm:{rid}'),
           InlineKeyboardButton(text='❌ To‘lovni rad etish', callback_data=f'kiroreject:{rid}')]]
 else:
  rows = []
 return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None

@router.callback_query(F.data=='kiroprice')
async def kiro_price(c:CallbackQuery,state:FSMContext,db:Database,config:Config):
 if c.from_user.id not in config.admin_ids:return await c.answer('Ruxsat yo‘q.',show_alert=True)
 db.set_setting('admin_pending_setting','kiro_link_price')
 await state.set_state(AdminStates.set_value)
 await c.message.answer('💳 Kiro Link xizmati narxini so‘mda yuboring.')
 await c.answer()

@router.message(F.text=='🔗 Link')
async def link_menu(m:Message,db:Database):
 if db.setting('kiro_link_enabled','1') != '1':
  return await m.answer('🔗 Kiro Link xizmati vaqtincha o‘chirilgan. Keyinroq urinib ko‘ring.')
 price=int(db.setting('kiro_link_price','0') or 0)
 kb=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='📩 Link so‘rash',callback_data='kirorequest')],[InlineKeyboardButton(text='📋 Linklarim',callback_data='kirohistory')]])
 await m.answer(f'🔗 <b>KIRO LINK XIZMATI</b>\n\nNarx: <b>{format_money(price)}</b>\nTo‘lov linki admin tomonidan yuboriladi. To‘lov tekshirilgach admin tasdiqlaydi. Bu xizmat balans to‘ldirishdan alohida.',parse_mode='HTML',reply_markup=kb)

@router.callback_query(F.data=='kirorequest')
async def request_link(c:CallbackQuery,db:Database,config:Config):
 if db.setting('kiro_link_enabled','1') != '1': return await c.answer('Link xizmati vaqtincha o‘chirilgan.',show_alert=True)
 rid=db.create_kiro_link_request(c.from_user.id)
 await c.message.answer(f'✅ Link so‘rovingiz qabul qilindi. Buyurtma: #{rid}\nAdmin sizga to‘lov linkini yuboradi.')
 for aid in config.admin_ids:
  try:await c.bot.send_message(aid,f'🔗 <b>KIRO LINK SO‘ROVI #{rid}</b>\n👤 {c.from_user.full_name}\n🆔 <code>{c.from_user.id}</code>',parse_mode='HTML',reply_markup=admin_link_actions(rid, 'requested'))
  except Exception:pass
 await c.answer('So‘rov yuborildi.')

@router.callback_query(F.data=='kirohistory')
async def history(c:CallbackQuery,db:Database):
 rows=db.kiro_link_history(c.from_user.id)
 if not rows:return await c.answer('Hali link so‘rovlaringiz yo‘q.',show_alert=True)
 labels={'requested':'Admin ko‘rmoqda','link_sent':'Link yuborildi','payment_reported':'To‘lov tekshirilmoqda','paid':'To‘lov tasdiqlandi','rejected':'Rad etildi','cancelled':'Bekor qilindi','issue':'Link bo‘yicha muammo'}
 text='📋 <b>LINKLARIM</b>\n\n'
 for r in rows:text+=f'#{r["id"]} — {labels.get(r["status"],r["status"])}\n{r["payment_url"] or "Link hali yuborilmagan"}\n{r["created_at"][:10]}\n\n'
 await c.message.answer(text,parse_mode='HTML');await c.answer()

@router.callback_query(F.data.startswith('kiroseturl:'))
async def set_url_start(c:CallbackQuery,state:FSMContext,config:Config,db:Database):
 if c.from_user.id not in config.admin_ids:return await c.answer('Ruxsat yo‘q.',show_alert=True)
 rid=int(c.data.split(':')[1]);r=db.kiro_link_request(rid)
 if not r:
  return await c.answer('So‘rov bazadan topilmadi. Botni yangilab, admin paneldan qayta oching.', show_alert=True)
 if r['status'] not in ('requested', 'link_sent'):
  return await c.answer(f'Bu so‘rovning holati: {r["status"]}. Bu holatda link yuborib bo‘lmaydi.', show_alert=True)
 await state.update_data(kiro_link_request_id=rid);await state.set_state(AdminStates.link_admin_url)
 await c.message.answer(f'#{rid} uchun to‘lov URL manzilini yuboring (https:// bilan boshlansin).')
 await c.answer()

@router.message(AdminStates.link_admin_url,F.text)
async def set_url(m:Message,state:FSMContext,db:Database,config:Config):
 if m.from_user.id not in config.admin_ids:return
 url=m.text.strip()
 if not url.startswith('https://') or len(url)>1500:return await m.answer('❌ To‘g‘ri https:// URL yuboring.')
 d=await state.get_data();rid=int(d['kiro_link_request_id']);r=db.kiro_link_request(rid)
 if not r:
  await state.clear(); return await m.answer(f'❌ #{rid} so‘rovi bazadan topilmadi. Admin panelni yangilang.')
 if not db.set_kiro_payment_url(rid,url):
  await state.clear(); return await m.answer(f'❌ #{rid} holati “{r["status"]}”. Link saqlanmadi. Admin panelni yangilang va qayta urinib ko‘ring.')
 await state.clear()
 try:await m.bot.send_message(r['user_tg'],f'🔗 <b>KIRO TO‘LOV LINKI</b>\nBuyurtma: #{rid}\n\n{url}\n\nTo‘lovni amalga oshirgach “To‘ladim” tugmasini bosing. Admin to‘lovni alohida tekshiradi.',parse_mode='HTML',reply_markup=user_link_actions(rid))
 except Exception:await m.answer('⚠️ Link saqlandi, lekin foydalanuvchiga yuborilmadi.')
 await m.answer(f'✅ #{rid} link yuborildi.')

@router.callback_query(F.data.startswith('kiropaid:'))
async def paid_report(c:CallbackQuery,db:Database,config:Config):
 rid=int(c.data.split(':')[1]);r=db.kiro_link_request(rid)
 if not r or r['user_tg']!=c.from_user.id or r['status']!='link_sent':return await c.answer('Bu so‘rovni yuborib bo‘lmaydi.',show_alert=True)
 db.set_kiro_link_status(rid,'payment_reported')
 for aid in config.admin_ids:
  try:await c.bot.send_message(aid,f'💳 Foydalanuvchi “To‘ladim” dedi. To‘lovni provayderdan tekshiring.\nSo‘rov #{rid}\nUser ID: {c.from_user.id}',reply_markup=admin_link_actions(rid, 'payment_reported'))
  except Exception:pass
 await c.message.answer('⏳ Admin to‘lovni tekshiradi. Tugmani bosishning o‘zi to‘lov tasdig‘i emas.')
 await c.answer('Adminga yuborildi.')

@router.callback_query(F.data.startswith('kiroissue:'))
async def link_issue(c:CallbackQuery,db:Database,config:Config):
 rid=int(c.data.split(':')[1]);r=db.kiro_link_request(rid)
 if not r or r['user_tg']!=c.from_user.id:return await c.answer('So‘rov topilmadi.',show_alert=True)
 db.set_kiro_link_status(rid,'issue')
 for aid in config.admin_ids:
  try:await c.bot.send_message(aid,f'⚠️ Link ishlamadi. So‘rov #{rid}, foydalanuvchi {c.from_user.id}.')
  except Exception:pass
 await c.answer('Adminga xabar yuborildi.')

@router.callback_query(F.data.startswith('kirocancel:'))
async def cancel_link(c:CallbackQuery,db:Database):
 rid=int(c.data.split(':')[1]);r=db.kiro_link_request(rid)
 if not r or r['user_tg']!=c.from_user.id:return await c.answer('So‘rov topilmadi.',show_alert=True)
 if r['status'] not in ('requested','link_sent'):return await c.answer('Bu holatda bekor qilib bo‘lmaydi.',show_alert=True)
 if not db.set_kiro_link_status(rid,'cancelled'): return await c.answer('Bekor qilib bo‘lmadi. Holatni tekshiring.',show_alert=True)
 try: await c.bot.send_message(c.from_user.id,f'❌ Link so‘rovi #{rid} bekor qilindi.')
 except Exception: pass
 await c.message.edit_reply_markup(reply_markup=None)
 await c.answer('So‘rov bekor qilindi.')

@router.callback_query(F.data.startswith('kiroconfirm:'))
async def confirm_link(c:CallbackQuery,db:Database,config:Config):
 if c.from_user.id not in config.admin_ids:return await c.answer('Ruxsat yo‘q.',show_alert=True)
 rid=int(c.data.split(':')[1]);r=db.kiro_link_request(rid)
 if not r or r['status']!='payment_reported':return await c.answer('Avval foydalanuvchi to‘lov haqida xabar berishi kerak; holatni tekshiring.',show_alert=True)
 if not db.set_kiro_link_status(rid,'paid'):return await c.answer('Holat o‘zgargan.',show_alert=True)
 reward=db.credit_referral_reward(r['user_tg'],'kiro_link',rid)
 try:await c.bot.send_message(r['user_tg'],f'✅ Kiro Link #{rid} to‘lovi admin tomonidan tasdiqlandi.')
 except Exception:pass
 if reward:
  try:await c.bot.send_message(reward['inviter_tg'],f'🎉 Referal mukofoti! Taklif qilgan do‘stingiz Kiro Link to‘lovini admin tasdiqladi. 💰 +{format_money(reward["amount"])} balansingizga qo‘shildi.')
  except Exception:pass
 await c.message.answer(f'✅ #{rid} to‘lov tasdiqlandi. Referal mukofoti mavjud bo‘lsa, berildi.')
 await c.answer('Tasdiqlandi.')

@router.callback_query(F.data.startswith('kiroreject:'))
async def reject_link(c:CallbackQuery,db:Database,config:Config):
 if c.from_user.id not in config.admin_ids:return await c.answer('Ruxsat yo‘q.',show_alert=True)
 rid=int(c.data.split(':')[1]);r=db.kiro_link_request(rid)
 if not r:return await c.answer('So‘rov bazadan topilmadi.',show_alert=True)
 if r['status'] not in ('requested','link_sent','payment_reported'):
  return await c.answer(f'Bu so‘rov allaqachon yakunlangan: {r["status"]}.',show_alert=True)
 if not db.set_kiro_link_status(rid,'rejected'):
  return await c.answer('Holatni o‘zgartirib bo‘lmadi. Panelni yangilang.',show_alert=True)
 try:await c.bot.send_message(r['user_tg'],f'❌ Kiro Link #{rid} to‘lovi tasdiqlanmadi. Agar xato bo‘lsa, admin bilan bog‘laning.')
 except Exception:pass
 await c.answer('Rad etildi.')


@router.callback_query(F.data == 'adm:link')
async def admin_link_panel(c: CallbackQuery, db: Database, config: Config):
 if c.from_user.id not in config.admin_ids:
  return await c.answer('Ruxsat yo‘q.', show_alert=True)
 enabled = db.setting('kiro_link_enabled', '1') == '1'
 counts = db.kiro_link_counts()
 price = int(db.setting('kiro_link_price', '0') or 0)
 kb = InlineKeyboardMarkup(inline_keyboard=[
  [InlineKeyboardButton(text=('🔴 O‘chirish' if enabled else '🟢 Yoqish'), callback_data='adm:linktoggle')],
  [InlineKeyboardButton(text='💰 Link narxi', callback_data='adm:linkprice')],
  [InlineKeyboardButton(text='✅ Tasdiqlangan linklar', callback_data='adm:linkconfirmed')],
  [InlineKeyboardButton(text='👥 Berilgan linklar / foydalanuvchilar', callback_data='adm:linkusers')],
  [InlineKeyboardButton(text='🔄 Yangilash', callback_data='adm:link')]
 ])
 pending = counts.get('requested', 0) + counts.get('link_sent', 0) + counts.get('payment_reported', 0)
 text = (f'🔗 <b>LINK BOSHQARUVI</b>\n\n'
         f'Holati: <b>{"YOQILGAN" if enabled else "O‘CHIRILGAN"}</b>\n'
         f'💰 Joriy narx: <b>{format_money(price)}</b>\n\n'
         f'📊 Jami so‘rov: <b>{counts.get("total", 0)}</b>\n'
         f'🔗 Link yuborilgan: <b>{counts.get("link_sent", 0) + counts.get("payment_reported", 0) + counts.get("paid", 0)}</b>\n'
         f'✅ Tasdiqlangan: <b>{counts.get("paid", 0)}</b>\n'
         f'⏳ Kutilayotgan: <b>{pending}</b>\n'
         f'❌ Rad etilgan: <b>{counts.get("rejected", 0)}</b>\n'
         f'🚫 Bekor qilingan: <b>{counts.get("cancelled", 0)}</b>\n\n'
         'Kerakli bo‘limni tanlang:')
 await c.message.answer(text, parse_mode='HTML', reply_markup=kb)
 await c.answer()

@router.callback_query(F.data == 'adm:linkprice')
async def admin_link_price(c: CallbackQuery, state: FSMContext, db: Database, config: Config):
 if c.from_user.id not in config.admin_ids:
  return await c.answer('Ruxsat yo‘q.', show_alert=True)
 db.set_setting('admin_pending_setting', 'kiro_link_price')
 await state.set_state(AdminStates.set_value)
 current = int(db.setting('kiro_link_price', '0') or 0)
 await c.message.answer(f'💰 Hozirgi Kiro Link narxi: {format_money(current)} so‘m\nYangi narxni faqat son bilan yuboring. Bekor qilish: /cancel')
 await c.answer()

@router.callback_query(F.data == 'adm:linkconfirmed')
async def admin_link_confirmed(c: CallbackQuery, db: Database, config: Config):
 if c.from_user.id not in config.admin_ids:
  return await c.answer('Ruxsat yo‘q.', show_alert=True)
 with db.conn() as conn:
  rows = conn.execute("SELECT k.*, u.username, u.full_name FROM kiro_link_requests k LEFT JOIN users u ON u.telegram_user_id=k.user_tg WHERE k.status='paid' ORDER BY k.id DESC LIMIT 50").fetchall()
 await c.message.answer(f'✅ <b>TASDIQLANGAN LINKLAR</b> — jami ko‘rsatilgan: {len(rows)}', parse_mode='HTML')
 if not rows:
  await c.message.answer('Hozircha tasdiqlangan linklar yo‘q.')
 else:
  for r in rows:
   uname = '@' + r['username'] if r['username'] else (r['full_name'] or 'Foydalanuvchi')
   url = escape(r['payment_url'] or 'Link saqlanmagan')
   await c.message.answer(f'✅ So‘rov #{r["id"]}\n👤 {escape(uname)}\n🆔 <code>{r["user_tg"]}</code>\n🔗 {url}\n📅 {escape(r["updated_at"] or r["created_at"])}', parse_mode='HTML')
 await c.answer()

@router.callback_query(F.data == 'adm:linkusers')
async def admin_link_users(c: CallbackQuery, db: Database, config: Config):
 if c.from_user.id not in config.admin_ids:
  return await c.answer('Ruxsat yo‘q.', show_alert=True)
 with db.conn() as conn:
  rows = conn.execute("SELECT k.user_tg, COUNT(*) AS link_count, MAX(k.updated_at) AS last_at, u.username, u.full_name FROM kiro_link_requests k LEFT JOIN users u ON u.telegram_user_id=k.user_tg WHERE k.payment_url IS NOT NULL AND k.payment_url!='' GROUP BY k.user_tg ORDER BY last_at DESC LIMIT 50").fetchall()
 if not rows:
  await c.message.answer('📭 Hali hech bir foydalanuvchiga link berilmagan.')
 else:
  await c.message.answer(f'👥 <b>LINK OLGAN FOYDALANUVCHILAR</b> — {len(rows)} ta', parse_mode='HTML')
  for r in rows:
   uname = '@' + r['username'] if r['username'] else (r['full_name'] or 'Foydalanuvchi')
   kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🔎 Linklarini ko‘rish', callback_data=f'adm:linkuser:{r["user_tg"]}')]])
   await c.message.answer(f'👤 {escape(uname)}\n🆔 <code>{r["user_tg"]}</code>\n🔗 Berilgan linklar: <b>{r["link_count"]}</b>', parse_mode='HTML', reply_markup=kb)
 await c.answer()

@router.callback_query(F.data.startswith('adm:linkuser:'))
async def admin_link_user_detail(c: CallbackQuery, db: Database, config: Config):
 if c.from_user.id not in config.admin_ids:
  return await c.answer('Ruxsat yo‘q.', show_alert=True)
 try:
  user_tg = int(c.data.rsplit(':', 1)[1])
 except ValueError:
  return await c.answer('Foydalanuvchi ID noto‘g‘ri.', show_alert=True)
 with db.conn() as conn:
  rows = conn.execute("SELECT * FROM kiro_link_requests WHERE user_tg=? AND payment_url IS NOT NULL AND payment_url!='' ORDER BY id DESC LIMIT 50", (user_tg,)).fetchall()
  user = conn.execute('SELECT username, full_name FROM users WHERE telegram_user_id=?', (user_tg,)).fetchone()
 if not rows:
  return await c.answer('Bu foydalanuvchida yuborilgan link topilmadi.', show_alert=True)
 name = ('@' + user['username']) if user and user['username'] else (user['full_name'] if user else 'Foydalanuvchi')
 await c.message.answer(f'👤 <b>{escape(name)}</b>\n🆔 <code>{user_tg}</code>\n🔗 Jami berilgan link: <b>{len(rows)}</b>', parse_mode='HTML')
 labels = {'requested':'So‘rov keldi','link_sent':'Link yuborildi','payment_reported':'To‘lov tekshirilmoqda','paid':'Tasdiqlangan','rejected':'Rad etilgan','cancelled':'Bekor qilingan','issue':'Muammo bildirildi'}
 for r in rows:
  await c.message.answer(f'🔗 <b>So‘rov #{r["id"]}</b>\nHolati: {labels.get(r["status"], r["status"])}\nURL: {escape(r["payment_url"] or "-")}\nSana: {escape(r["created_at"])}', parse_mode='HTML', reply_markup=admin_link_actions(r['id'], r['status']))
 await c.answer()

@router.callback_query(F.data == 'adm:linktoggle')
async def admin_link_toggle(c: CallbackQuery, db: Database, config: Config):
 if c.from_user.id not in config.admin_ids:
  return await c.answer('Ruxsat yo‘q.', show_alert=True)
 enabled = db.setting('kiro_link_enabled', '1') == '1'
 db.set_setting('kiro_link_enabled', '0' if enabled else '1')
 await c.answer('Link xizmati ' + ('o‘chirildi.' if enabled else 'yoqildi.'), show_alert=True)
 await admin_link_panel(c, db, config)
