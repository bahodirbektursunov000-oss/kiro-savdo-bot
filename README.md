# Kiro Savdo Bot — asosiy menyu va Referral/Link

## Asosiy menyu
Barcha 12 ta bo‘lim bitta asosiy menyuda joylashgan:
- 🛒 JSON sotish
- 📝 JSON tayyorlash
- 🔗 Link
- 💰 Balansim
- ➕ Balans to‘ldirish
- 💸 Pul chiqarish
- 📦 Sotuvlarim
- 📜 Tarix
- 👤 Kabinet
- 💳 Kartalarim
- 🎁 Referal
- ❓ Yordam

`➡️ Qo‘shimcha` sahifasi olib tashlandi. Referal va Link bevosita asosiy menyudan ochiladi.

## Ishga tushirish
1. `.env.example` faylidan nusxa olib `.env` deb nomlang.
2. `.env` ichida `BOT_TOKEN` va `ADMIN_IDS` qiymatlarini to‘ldiring.
3. `pip install -r requirements.txt`
4. `python bot.py`

Hostingda `BOT_TOKEN` va `ADMIN_IDS` ni hosting Variables/Environment Variables bo‘limida kiriting. `.env` faylini GitHub’ga yuklamang.

## Referal qoidasi
Taklif qilingan foydalanuvchi botga kirgani uchun mukofot berilmaydi. JSON sotish, JSON tayyorlash yoki Kiro Link operatsiyasi admin tomonidan bajarilgani tasdiqlangandan keyingina tegishli mukofot beriladi. Bekor qilingan/tasdiqlanmagan operatsiyaga mukofot berilmasligi kerak.

## Muhim
- Deploydan oldin amaldagi SQLite bazangizning zaxira nusxasini oling va uni o‘chirib yubormang.
- SQLite fayli hostingda doimiy disk/volume’da saqlanishi kerak, aks holda qayta deployda ma’lumot yo‘qolishi mumkin.
- Kiro Link to‘lovi admin tomonidan alohida tekshiriladi; foydalanuvchining “To‘ladim” tugmasi to‘lov isboti emas.
- Click/Humo avtomatik tasdiqlash merchant/API integratsiyasini talab qiladi va bu arxivda avtomatik ulangan deb hisoblanmaydi.

## Tekshiruv
Python fayllari `py_compile` orqali sintaksis tekshiruvidan o‘tkazilgan. To‘liq bot integratsion sinovi bajarilmadi, chunki tekshiruv muhitida `aiogram` o‘rnatilmagan.


## JSON tayyorlash — asl nusxani saqlash
Admin matn yuborsa, bot matnni qayta formatlamasdan foydalanuvchiga matn va `.json` fayl sifatida yuboradi. Admin `.json`/`.txt` fayl yuborsa, bot fayl baytlarini o‘zgartirmasdan, asl fayl nomi bilan yetkazishga harakat qiladi. Matn ko‘rinishi Telegram xabar chegarasi bilan cheklangan; katta JSON fayl sifatida beriladi.
