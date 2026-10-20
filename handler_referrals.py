from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database import Database
from config import Config
from states import AdminStates
from payment_service import format_money

router = Router()
REWARD_KEYS = {
    'json_sale': ('ref_reward_json_sale', 'JSON sotish'),
    'json_service': ('ref_reward_json_service', 'JSON tayyorlatish'),
    'kiro_link': ('ref_reward_kiro_link', 'Kiro Link to‘lovi'),
}

def reward_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🛒 JSON sotish mukofoti', callback_data='refset:json_sale')],
        [InlineKeyboardButton(text='📝 JSON tayyorlatish mukofoti', callback_data='refset:json_service')],
        [InlineKeyboardButton(text='🔗 Kiro Link to‘lovi mukofoti', callback_data='refset:kiro_link')],
        [InlineKeyboardButton(text='🔙 Admin panel', callback_data='adm:home')],
    ])

@router.message(F.text == '🎁 Referal')
async def referral_home(m: Message, db: Database):
    me = await m.bot.get_me()
    st = db.referral_stats(m.from_user.id)
    link = f'https://t.me/{me.username}?start=ref_{m.from_user.id}'
    await m.answer(
        '🎁 <b>KIRO REFERAL DASTURI</b>\n\n'
        'Do‘stlaringizni shaxsiy havolangiz orqali taklif qiling. 🎁\n\n'
        '⚠️ <b>Mukofot qoidasi:</b> do‘stingiz botga qo‘shilgani uchungina mukofot berilmaydi. Mukofot faqat haqiqiy JSON savdosi, JSON tayyorlash xizmati yoki Kiro Link to‘lovi admin tomonidan tekshirilib, bajarilgani tasdiqlangandan keyin balansingizga qo‘shiladi. Bekor qilingan yoki tasdiqlanmagan operatsiyaga mukofot yo‘q.\n\n'
        f'👥 Taklif qilganlar: <b>{st["invited"]}</b>\n'
        f'🎁 Mukofot berilgan operatsiyalar: <b>{st["rewards"]}</b>\n'
        f'💰 Jami topilgan: <b>{format_money(st["earned"])}</b>\n\n'
        f'🔗 <a href="{link}">Shaxsiy referal havolangiz</a>\n<code>{link}</code>', parse_mode='HTML')

@router.callback_query(F.data == 'adm:referrals')
async def admin_referrals(c: CallbackQuery, db: Database, config: Config):
    if c.from_user.id not in config.admin_ids:
        return await c.answer('Ruxsat yo‘q.', show_alert=True)
    labels=[]
    for key,label in REWARD_KEYS.values():
        try: amount=max(0,int(db.setting(key,'0')))
        except ValueError: amount=0
        labels.append(f'• {label}: {format_money(amount)}')
    await c.message.answer('🎁 <b>REFERAL MUKOFOTLARI</b>\n\n'+'\n'.join(labels)+'\n\nHar bir qiymatni alohida sozlang:',parse_mode='HTML',reply_markup=reward_keyboard())
    await c.answer()

@router.callback_query(F.data.startswith('refset:'))
async def admin_referral_set(c: CallbackQuery, state: FSMContext, db: Database, config: Config):
    if c.from_user.id not in config.admin_ids:
        return await c.answer('Ruxsat yo‘q.', show_alert=True)
    kind=c.data.split(':',1)[1]
    if kind not in REWARD_KEYS:return await c.answer('Noto‘g‘ri tanlov.',show_alert=True)
    key,label=REWARD_KEYS[kind]
    await state.update_data(referral_reward_key=key,referral_reward_label=label)
    await state.set_state(AdminStates.referral_reward_value)
    await c.message.answer(f'🎁 {label} uchun mukofot summasini yuboring (so‘m). 0 — o‘chirish.')
    await c.answer()

@router.message(AdminStates.referral_reward_value, F.text)
async def save_referral_reward(m: Message, state: FSMContext, db: Database, config: Config):
    if m.from_user.id not in config.admin_ids:return
    try:amount=int(m.text.replace(' ','').replace(',','').replace('_',''))
    except ValueError:return await m.answer('❌ Faqat butun son kiriting.')
    if amount<0 or amount>1000000000:return await m.answer('❌ 0 dan 1 000 000 000 gacha kiriting.')
    d=await state.get_data();db.set_setting(d['referral_reward_key'],amount);await state.clear()
    await m.answer(f'✅ {d["referral_reward_label"]} mukofoti: {format_money(amount)}',reply_markup=reward_keyboard())
