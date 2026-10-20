# Kiro Savdo Bot — Exact JSON & Admin Prompt Fix

## Ushbu yangilanish
- JSON sotish bo‘limida JSON sintaksisi tekshiriladi, lekin foydalanuvchining asl matni qayta formatlanmaydi.
- `.json` hujjat uchun asl baytlar SQLite bazasida BLOB sifatida saqlanadi; fayl nomi ham saqlanadi.
- Admin paneldagi JSON yuklab olish asl baytlar va asl fayl nomidan foydalanadi. Eski bazadagi yozuvlar uchun orqaga mos fallback mavjud.
- Admin foydalanuvchidan so‘raladigan ma’lumot ko‘rsatmasini `JSON so‘rov matni` bo‘limida o‘zi belgilashi mumkin. Bu ko‘rsatma JSON tayyorlash oqimida foydalanuvchiga ko‘rsatiladi.
- Eski `jsonmarket.db` faylini o‘chirmang: yangi ustunlar avtomatik migratsiya qilinadi.

## Muhim
- Matn ko‘rinishida yuborilgan JSON Telegram xabari sifatida saqlanadi; fayl sifatida yuborilgan JSON esa asl fayl baytlari bilan saqlanadi.
- Python sintaksisi va ZIP arxivi tekshirildi. To‘liq Telegram integratsion testi bajarilmagan.
- `.env` faylingizni ommaga yuklamang. Hostingda maxfiy qiymatlarni environment variables orqali kiriting.
