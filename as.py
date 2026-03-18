import json
import asyncio
import os
import time
from telethon import TelegramClient, events, functions
from telethon.tl.types import UserStatusOnline

# إعدادات الحساب
API_ID = 32076506
API_HASH = "adef09a48d06d5e2eb3d8a036458eecf"
PHONE = "+213799554296"
SESSION_NAME = "besoo_session"
DATA_FILE = "users_history.json"

# إعدادات الوقت (10 دقائق)
COOLDOWN_MINUTES = 10
COOLDOWN_SECONDS = COOLDOWN_MINUTES * 60

# نص الرد التلقائي
AUTO_REPLY_TEXT = (
    "⛔ نعتذر، نحن غير متاحين حاليًا وسيتم الرد عليك في أقرب وقت.\n\n"
    "━━━━━━━━━━━━━━\n"
    "📢 قناتنا الرسمية:\n"
    "https://t.me/fareshw/484\n\n"
    "🌐 متوفر استضافة شهر كاملاً بمقابل، للتواصل مع المطور:\n"
    "@far_es_ban\n\n"
    "🤖 موقعنا الخاص ببوتاتنا:\n"
    "https://f0623244022-commits.github.io/Vps/\n"
    "(⚠️ ملاحظة: البوتات متوقفة حالياً وسيتم تحديثها مع الوقت)\n"
    "━━━━━━━━━━━━━━"
)

users_data = {}
processing_users = set()
file_lock = asyncio.Lock()

def load_data():
    """تحميل السجل"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

async def save_data_async(data):
    """حفظ البيانات برمجياً بطريقة آمنة"""
    async with file_lock:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

# تمويه الاستضافة لمنع الحظر
client = TelegramClient(
    SESSION_NAME, 
    API_ID, 
    API_HASH,
    device_model="VPS Server",           
    system_version="Linux Ubuntu 22.04", 
    app_version="4.16.6 API",            
    lang_code="en",                      
    system_lang_code="en"                
)

async def main():
    global users_data
    users_data = load_data() 

    # الاتصال بحساب تليجرام
    await client.start(phone=PHONE)
    
    # إجبار السكربت على إبقاء حالة حسابك "أوفلاين" كوضع افتراضي
    await client(functions.account.UpdateStatusRequest(offline=True))
    
    print("✅ البوت يعمل بذكاء ومضاد للأخطاء! سيرد فورا وبسرعة البرق كل 10 دقائق (فقط إذا كنت أوفلاين).")

    @client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
    async def handler(event):
        sender_id = str(event.sender_id)
        current_time = time.time()

        try:
            # --- 1. التحقق من حالتك: هل أنت متصل (أونلاين)؟ ---
            me_req = await client(functions.users.GetUsersRequest(id=['me']))
            me = me_req[0]
            if isinstance(me.status, UserStatusOnline):
                print(f"👤 أنت متصل الآن.. تم تجاهل رسالة من {sender_id}.")
                return # إذا كنت أونلاين، يتوقف البوت ولن يرد
        except Exception as e:
            pass # في حال حدوث خطأ في جلب الحالة، نتجاهل ونكمل

        # --- 2. التحقق من الوقت مع إصلاح مشكلة الملف القديم ---
        last_reply_time = users_data.get(sender_id, 0)
        
        # تحويل القيمة إلى رقم (وإذا كانت نص قديم من الملف، نجعلها 0 ليرد فوراً)
        try:
            last_reply_time = float(last_reply_time)
        except (ValueError, TypeError):
            last_reply_time = 0.0

        if current_time - last_reply_time < COOLDOWN_SECONDS:
            return # لم تمر 10 دقائق بعد، تجاهل الرسالة

        # --- 3. حماية من الرسائل المتتالية (Spam) ---
        if sender_id in processing_users:
            return 
        processing_users.add(sender_id)

        try:
            # رد فوري "بسرعة البرق"
            await event.respond(AUTO_REPLY_TEXT, link_preview=False)
            print(f"⚡ تم الرد فوراً على {sender_id} لأنك أوفلاين")

            # تسجيل وقت الرد الجديد لحساب الـ 10 دقائق القادمة
            users_data[sender_id] = current_time
            await save_data_async(users_data)

        except Exception as e:
            print(f"❌ خطأ في الإرسال: {e}")
        
        finally:
            if sender_id in processing_users:
                processing_users.remove(sender_id)

    # تشغيل دائم (24/7)
    await client.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف السكربت.")
