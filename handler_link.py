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

def admin_link_actions(rid):
 return InlineKeyboardMarkup(inline_keyboard=[
  [InlineKeyboardButton(text='🔗 To‘lov linkini yuborish',callback_data=f'kiroseturl:{rid}')],
  [InlineKeyboardButton(text='✅ To‘lovni tasdiqlash',callback_data=f'kiroconfirm:{rid}'),InlineKeyboardButton(text='❌ Rad etish',callback_data=f'kiroreject:{rid}')]
 ])

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
  try:await c.bot.send_message(aid,f'🔗 <b>KIRO LINK SO‘ROVI #{rid}</b>\n👤 {c.from_user.full_name}\n🆔 <code>{c.from_user.id}</code>',parse_mode='HTML',reply_markup=admin_link_actions(rid))
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
 if not r or r['status']!='requested':return await c.answer('So‘rov topilmadi yoki link yuborilgan.',show_alert=True)
 await state.update_data(kiro_link_request_id=rid);await state.set_state(AdminStates.link_admin_url)
 await c.message.answer(f'#{rid} uchun to‘lov URL manzilini yuboring (https:// bilan boshlansin).')
 await c.answer()

@router.message(AdminStates.link_admin_url,F.text)
async def set_url(m:Message,state:FSMContext,db:Database,config:Config):
 if m.from_user.id not in config.admin_ids:return
 url=m.text.strip()
 if not url.startswith('https://') or len(url)>1500:return await m.answer('❌ To‘g‘ri https:// URL yuboring.')
 d=await state.get_data();rid=int(d['kiro_link_request_id']);r=db.kiro_link_request(rid)
 if not r or not db.set_kiro_payment_url(rid,url):
  await state.clear();return await m.answer('❌ So‘rov topilmadi yoki holati o‘zgargan.')
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
  try:await c.bot.send_message(aid,f'💳 Foydalanuvchi “To‘ladim” dedi. To‘lovni provayderdan tekshiring.\nSo‘rov #{rid}\nUser ID: {c.from_user.id}',reply_markup=admin_link_actions(rid))
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
 if not r or r['status'] not in ('payment_reported','link_sent'):return await c.answer('So‘rov topilmadi yoki holati o‘zgargan.',show_alert=True)
 db.set_kiro_link_status(rid,'rejected')
 try:await c.bot.send_message(r['user_tg'],f'❌ Kiro Link #{rid} to‘lovi tasdiqlanmadi. Agar xato bo‘lsa, admin bilan bog‘laning.')
 except Exception:pass
 await c.answer('Rad etildi.')


@router.callback_query(F.data == 'adm:link')
async def admin_link_panel(c: CallbackQuery, db: Database, config: Config):
 if c.from_user.id not in config.admin_ids: return await c.answer('Ruxsat yo‘q.', show_alert=True)
 enabled=db.setting('kiro_link_enabled','1') == '1'
 rows=db.all_kiro_link_requests(50)
 counts=db.kiro_link_counts()
 kb=InlineKeyboardMarkup(inline_keyboard=[
  [InlineKeyboardButton(text=('🔴 Link xizmatini o‘chirish' if enabled else '🟢 Link xizmatini yoqish'),callback_data='adm:linktoggle')],
  [InlineKeyboardButton(text='🔄 Yangilash',callback_data='adm:link')]
 ])
 await c.message.answer(f'🔗 <b>LINK BOSHQARUVI</b>\nHolati: <b>{"YOQILGAN" if enabled else "O‘CHIRILGAN"}</b>\n💰 Narx: <b>{format_money(int(db.setting("kiro_link_price","0") or 0))}</b>\n\n📊 Jami: {counts.get("total",0)} | Kutilmoqda: {counts.get("requested",0)+counts.get("link_sent",0)+counts.get("payment_reported",0)}\n🔗 Link yuborilgan: {counts.get("link_sent",0)+counts.get("payment_reported",0)+counts.get("paid",0)}\n✅ Bajarilgan: {counts.get("paid",0)}\n⏳ To‘lov tekshirilmoqda: {counts.get("payment_reported",0)}\n❌ Rad etilgan: {counts.get("rejected",0)}\n🚫 Bekor qilingan: {counts.get("cancelled",0)}\n\nOxirgi {len(rows)} ta so‘rov:',parse_mode='HTML',reply_markup=kb)
 labels={'requested':'So‘rov keldi','link_sent':'Link yuborildi','payment_reported':'To‘lov tekshirilsin','paid':'To‘landi','rejected':'Rad etildi','cancelled':'Bekor qilindi','issue':'Link muammosi'}
 for r in rows:
  user=f'@{r["username"]}' if r['username'] else (r['full_name'] or 'Foydalanuvchi')
  url=r['payment_url'] or 'Link berilmagan'
  msg=f'🔗 <b>So‘rov #{r["id"]}</b>\n👤 {escape(user)}\n🆔 <code>{r["user_tg"]}</code>\n📌 {labels.get(r["status"],r["status"])}\n🌐 {escape(url)}'
  await c.message.answer(msg,parse_mode='HTML',reply_markup=admin_link_actions(r['id']))
 if not rows: await c.message.answer('Hozircha link so‘rovlari yo‘q.')
 await c.answer()

@router.callback_query(F.data == 'adm:linktoggle')
async def admin_link_toggle(c: CallbackQuery, db: Database, config: Config):
 if c.from_user.id not in config.admin_ids: return await c.answer('Ruxsat yo‘q.',show_alert=True)
 enabled=db.setting('kiro_link_enabled','1') == '1'
 db.set_setting('kiro_link_enabled','0' if enabled else '1')
 await c.answer('Link xizmati ' + ('o‘chirildi.' if enabled else 'yoqildi.'),show_alert=True)
 await admin_link_panel(c,db,config)
