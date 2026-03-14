import telebot
from telebot import types
import subprocess
import os
import re
import threading
import time
import platform
import requests
from flask import Flask
from threading import Thread

TOKEN = "8713821046:AAGKsopbjOhr9ousMEiLw0T28Y60dxSCN44"
bot = telebot.TeleBot(TOKEN)

# إنشاء سيرفر Flask
app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# تخزين معلومات الملفات لكل مستخدم
user_files = {}

# تخزين معلومات جميع الملفات للمسؤول
all_files = {}
admin_id = "8112511629"  # ايديك

# إحصائيات البوت
bot_stats = {
    'total_files': 0,
    'active_files': 0,
    'stopped_files': 0,
    'total_users': 0
}

# تخزين معلومات المطور
developer_info = {
    'username': 'M02MM',
    'user_id': '1338247690'
}

@bot.message_handler(commands=['start'])
def start(message):
    try:
        user_id = message.from_user.id
        if str(user_id) == admin_id:
            send_admin_panel(message)
        else:
            markup = types.InlineKeyboardMarkup()
            upload_btn = types.InlineKeyboardButton("رفع ملف 📤", callback_data='upload')
            my_files_btn = types.InlineKeyboardButton("ملفاتي 📁", callback_data='my_files')
            dev_btn = types.InlineKeyboardButton("المطور 👨‍💻", callback_data='developer')
            markup.row(upload_btn)
            markup.row(my_files_btn)
            markup.row(dev_btn)
            bot.send_message(message.chat.id, "مرحباً! يمكنك رفع ملفات البايثون وتشغيلها على الاستضافة.", reply_markup=markup)
    except Exception as e:
        print(f"Error in start: {e}")

def send_admin_panel(message):
    try:
        markup = types.InlineKeyboardMarkup()
        stats_btn = types.InlineKeyboardButton("إحصائيات البوت 📊", callback_data='stats')
        all_files_btn = types.InlineKeyboardButton("جميع الملفات 📂", callback_data='all_files')
        broadcast_btn = types.InlineKeyboardButton("إذاعة 📢", callback_data='broadcast')
        bot_status_btn = types.InlineKeyboardButton("حالة البوت 📈", callback_data='bot_status')
        developer_settings_btn = types.InlineKeyboardButton("إعدادات المطور ⚙️", callback_data='dev_settings')
        markup.row(stats_btn, all_files_btn)
        markup.row(broadcast_btn, bot_status_btn)
        markup.row(developer_settings_btn)
        bot.send_message(message.chat.id, "لوحة التحكم للمسؤول:", reply_markup=markup)
    except Exception as e:
        print(f"Error in send_admin_panel: {e}")

@bot.message_handler(commands=['developer'])
def developer(message):
    try:
        markup = types.InlineKeyboardMarkup()
        wevy = types.InlineKeyboardButton("مطور البوت 👨‍🔧", url=f'https://t.me/{developer_info["username"]}')
        markup.add(wevy)
        bot.send_message(message.chat.id, "للتواصل مع مطور البوت، اضغط على الزر أدناه:", reply_markup=markup)
    except Exception as e:
        print(f"Error in developer: {e}")

@bot.message_handler(commands=['admin'])
def admin_command(message):
    try:
        user_id = message.from_user.id
        if str(user_id) == admin_id:
            send_admin_panel(message)
        else:
            bot.reply_to(message, "هذا الأمر متاح فقط للمسؤولين.")
    except Exception as e:
        print(f"Error in admin_command: {e}")

@bot.message_handler(content_types=['document'])
def handle_file(message):
    try:
        user_id = message.from_user.id
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        file_name = message.document.file_name
        
        if not file_name.endswith('.py'):
            bot.reply_to(message, "يرجى رفع ملف بايثون فقط (امتداد .py)")
            return
        
        # حفظ الملف
        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        # تخزين معلومات المستخدم
        if str(user_id) not in user_files:
            user_files[str(user_id)] = []
            bot_stats['total_users'] += 1
        
        user_data = {
            'first_name': message.from_user.first_name,
            'username': message.from_user.username,
            'user_id': user_id
        }
        
        file_data = {
            'file_name': file_name,
            'original_name': file_name,
            'status': 'stopped',
            'process': None,
            'user_id': user_id,
            'user_info': user_data
        }
        
        user_files[str(user_id)].append(file_data)
        
        # تخزين الملف في قائمة جميع الملفات
        file_key = f"{user_id}_{file_name}"
        all_files[file_key] = file_data
        
        bot_stats['total_files'] += 1
        bot_stats['stopped_files'] += 1
        
        # إرسال المعلومات للمسؤول
        send_to_admin(file_name, file_name, user_id, user_data)
        
        bot.reply_to(message, f"تم رفع الملف {file_name} بنجاح! يمكنك الآن تشغيله من خلال قائمة 'ملفاتي'.")
        
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ أثناء رفع الملف: {str(e)}")

def send_to_admin(file_path, original_name, user_id, user_data):
    try:
        with open(file_path, 'rb') as file:
            user_info = f"تم رفع ملف: {original_name}\nبواسطة: {user_data['first_name']} (@{user_data['username']}) - ID: {user_id}"
            
            markup = types.InlineKeyboardMarkup()
            control_btn = types.InlineKeyboardButton("التحكم بالملف", callback_data=f"admin_control_{user_id}_{original_name}")
            markup.add(control_btn)
            
            bot.send_document(admin_id, file, caption=user_info, reply_markup=markup)
    except Exception as e:
        print(f"Error sending file to admin: {e}")

def install_and_run_uploaded_file(file_name):
    try:
        # تثبيت المتطلبات إذا وجدت
        if os.path.exists('requirements.txt'):
            subprocess.Popen(['pip', 'install', '-r', 'requirements.txt']).wait()
        
        # تشغيل الملف
        process = subprocess.Popen(['python', file_name])
        return process
    except Exception as e:
        print(f"Error installing/running file: {e}")
        return None

def get_bot_token(file_name):
    try:
        with open(file_name, 'r', encoding='utf-8') as file:
            content = file.read()
            match = re.search(r'TOKEN\s*=\s*[\'"]([^\'"]+)[\'"]', content)
            if match:
                return match.group(1)
            else:
                return "تعذر العثور على التوكن"
    except Exception as e:
        print(f"Error getting bot token: {e}")
        return "تعذر العثور على التوكن"

def get_system_info():
    try:
        # معلومات النظام الأساسية
        system = platform.system()
        version = platform.version()
        machine = platform.machine()
        
        # استخدام الذاكرة (بدون psutil)
        if system == "Linux":
            with open('/proc/meminfo', 'r') as mem:
                total_memory = 0
                free_memory = 0
                for line in mem:
                    if 'MemTotal' in line:
                        total_memory = int(line.split()[1]) / 1024  # تحويل إلى MB
                    elif 'MemFree' in line:
                        free_memory = int(line.split()[1]) / 1024  # تحويل إلى MB
                
                memory_usage = ((total_memory - free_memory) / total_memory) * 100 if total_memory > 0 else 0
        else:
            total_memory = "غير متوفر"
            memory_usage = "غير متوفر"
        
        # مساحة التخزين (بدون psutil)
        if system == "Linux":
            stat = os.statvfs('/')
            total_disk = (stat.f_blocks * stat.f_frsize) / (1024 * 1024 * 1024)  # تحويل إلى GB
            free_disk = (stat.f_bfree * stat.f_frsize) / (1024 * 1024 * 1024)  # تحويل إلى GB
            disk_usage = ((total_disk - free_disk) / total_disk) * 100 if total_disk > 0 else 0
        else:
            total_disk = "غير متوفر"
            disk_usage = "غير متوفر"
        
        return {
            'system': system,
            'version': version,
            'machine': machine,
            'memory_usage': memory_usage,
            'disk_usage': disk_usage
        }
    except Exception as e:
        print(f"Error getting system info: {e}")
        return {
            'system': "غير متوفر",
            'version': "غير متوفر",
            'machine': "غير متوفر",
            'memory_usage': "غير متوفر",
            'disk_usage': "غير متوفر"
        }

def test_internet_speed():
    """اختبار سرعة الإنترنت باستخدام طرق بديلة"""
    try:
        # قياس سرعة التنزيل عن طريق تحميل ملف صغير
        start_time = time.time()
        response = requests.get("https://httpbin.org/stream-bytes/100000", stream=True, timeout=10)
        total_length = 0
        
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                total_length += len(chunk)
        
        end_time = time.time()
        download_time = end_time - start_time
        download_speed = (total_length * 8) / (download_time * 1000000)  # Mbps
        
        # قياس سرعة الرفع عن طريق رفع بيانات صغيرة
        start_time = time.time()
        data = b'0' * 50000  # 50KB من البيانات
        response = requests.post("https://httpbin.org/post", data=data, timeout=10)
        end_time = time.time()
        upload_time = end_time - start_time
        upload_speed = (50000 * 8) / (upload_time * 1000000)  # Mbps
        
        return download_speed, upload_speed
    except:
        return "غير متوفر", "غير متوفر"

def get_bot_status():
    try:
        # معلومات النظام
        system_info = get_system_info()
        
        # اختبار سرعة الإنترنت
        download_speed, upload_speed = test_internet_speed()
        
        status_message = (
            f"📊 حالة البوت:\n\n"
            f"🖥️ النظام: {system_info['system']} {system_info['version']}\n"
            f"📟 المعمارية: {system_info['machine']}\n"
        )
        
        if system_info['memory_usage'] != "غير متوفر":
            status_message += f"💾 استخدام الذاكرة: {system_info['memory_usage']:.1f}%\n"
        else:
            status_message += f"💾 استخدام الذاكرة: غير متوفر\n"
            
        if system_info['disk_usage'] != "غير متوفر":
            status_message += f"💿 استخدام التخزين: {system_info['disk_usage']:.1f}%\n"
        else:
            status_message += f"💿 استخدام التخزين: غير متوفر\n\n"
        
        status_message += (
            f"🌐 سرعة الإنترنت:\n"
        )
        
        if download_speed != "غير متوفر":
            status_message += f"⬇️ سرعة التنزيل: {download_speed:.2f} Mbps\n"
        else:
            status_message += f"⬇️ سرعة التنزيل: غير متوفر\n"
            
        if upload_speed != "غير متوفر":
            status_message += f"⬆️ سرعة الرفع: {upload_speed:.2f} Mbps\n\n"
        else:
            status_message += f"⬆️ سرعة الرفع: غير متوفر\n\n"
        
        status_message += (
            f"📁 الملفات: {bot_stats['total_files']}\n"
            f"▶️ النشطة: {bot_stats['active_files']}\n"
            f"⏹️ المتوقفة: {bot_stats['stopped_files']}\n"
            f"👥 المستخد��ين: {bot_stats['total_users']}"
        )
        
        return status_message
    except Exception as e:
        return f"حدث خطأ أثناء جلب حالة البوت: {str(e)}"

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        if call.data == 'upload':
            bot.send_message(call.message.chat.id, "ارسل الملف الذي تريد رفعه على الاستضافة.")
        
        elif call.data == 'my_files':
            send_my_files_menu(call.message, call.from_user.id)
        
        elif call.data == 'developer':
            markup = types.InlineKeyboardMarkup()
            wevy = types.InlineKeyboardButton("مطور البوت 👨‍🔧", url=f'https://t.me/{developer_info["username"]}')
            markup.add(wevy)
            bot.edit_message_text("للتواصل مع مطور البوت، اضغط على الزر أدناه:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        
        elif call.data == 'stats':
            if str(call.from_user.id) == admin_id:
                stats_text = f"إحصائيات البوت:\n\nالملفات الكلية: {bot_stats['total_files']}\nالملفات النشطة: {bot_stats['active_files']}\nالملفات المتوقفة: {bot_stats['stopped_files']}\nعدد المستخدمين: {bot_stats['total_users']}"
                markup = types.InlineKeyboardMarkup()
                back_btn = types.InlineKeyboardButton("رجوع ◀️", callback_data='admin_back')
                markup.row(back_btn)
                bot.edit_message_text(stats_text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        
        elif call.data == 'all_files':
            if str(call.from_user.id) == admin_id:
                send_admin_all_files(call.message)
        
        elif call.data == 'broadcast':
            if str(call.from_user.id) == admin_id:
                msg = bot.send_message(call.message.chat.id, "أرسل الرسالة التي تريد إذاعتها:")
                bot.register_next_step_handler(msg, process_broadcast_message)
        
        elif call.data == 'bot_status':
            if str(call.from_user.id) == admin_id:
                status_message = get_bot_status()
                markup = types.InlineKeyboardMarkup()
                refresh_btn = types.InlineKeyboardButton("تحديث 🔄", callback_data='refresh_status')
                back_btn = types.InlineKeyboardButton("رجوع ◀️", callback_data='admin_back')
                markup.row(refresh_btn, back_btn)
                bot.edit_message_text(status_message, call.message.chat.id, call.message.message_id, reply_markup=markup)
        
        elif call.data == 'refresh_status':
            if str(call.from_user.id) == admin_id:
                status_message = get_bot_status()
                markup = types.InlineKeyboardMarkup()
                refresh_btn = types.InlineKeyboardButton("تحديث 🔄", callback_data='refresh_status')
                back_btn = types.InlineKeyboardButton("رجوع ◀️", callback_data='admin_back')
                markup.row(refresh_btn, back_btn)
                bot.edit_message_text(status_message, call.message.chat.id, call.message.message_id, reply_markup=markup)
        
        elif call.data == 'dev_settings':
            if str(call.from_user.id) == admin_id:
                markup = types.InlineKeyboardMarkup()
                change_username_btn = types.InlineKeyboardButton("تغيير يوزر المطور", callback_data='change_dev_username')
                change_id_btn = types.InlineKeyboardButton("تغيير ايدي المطور", callback_data='change_dev_id')
                back_btn = types.InlineKeyboardButton("رجوع ◀️", callback_data='admin_back')
                markup.row(change_username_btn)
                markup.row(change_id_btn)
                markup.row(back_btn)
                
                current_info = f"المعلومات الحالية:\n\nيوزر المطور: @{developer_info['username']}\nايدي المطور: {developer_info['user_id']}"
                bot.edit_message_text(current_info, call.message.chat.id, call.message.message_id, reply_markup=markup)
        
        elif call.data == 'change_dev_username':
            if str(call.from_user.id) == admin_id:
                msg = bot.send_message(call.message.chat.id, "أرسل يوزر المطور الجديد (بدون @):")
                bot.register_next_step_handler(msg, process_dev_username_change)
        
        elif call.data == 'change_dev_id':
            if str(call.from_user.id) == admin_id:
                msg = bot.send_message(call.message.chat.id, "أرسل ايدي المطور الجديد:")
                bot.register_next_step_handler(msg, process_dev_id_change)
        
        elif call.data == 'admin_back':
            if str(call.from_user.id) == admin_id:
                send_admin_panel(call.message)
        
        elif call.data.startswith('admin_control_'):
            if str(call.from_user.id) == admin_id:
                parts = call.data.split('_')
                user_id = parts[2]
                file_name = '_'.join(parts[3:])
                file_key = f"{user_id}_{file_name}"
                
                if file_key in all_files:
                    send_admin_file_control(call.message, file_key, all_files[file_key])
        
        elif call.data.startswith('admin_start_'):
            if str(call.from_user.id) == admin_id:
                parts = call.data.split('_')
                user_id = parts[2]
                file_name = '_'.join(parts[3:])
                file_key = f"{user_id}_{file_name}"
                
                if file_key in all_files and all_files[file_key]['status'] == 'stopped':
                    process = install_and_run_uploaded_file(file_name)
                    if process:
                        all_files[file_key]['status'] = 'running'
                        all_files[file_key]['process'] = process
                        bot_stats['active_files'] += 1
                        bot_stats['stopped_files'] -= 1
                        
                        if str(user_id) in user_files:
                            for file_data in user_files[str(user_id)]:
                                if file_data['file_name'] == file_name:
                                    file_data['status'] = 'running'
                                    file_data['process'] = process
                        
                        bot.answer_callback_query(call.id, f"تم تشغيل الملف {file_name}")
                        send_admin_file_control(call.message, file_key, all_files[file_key])
                    else:
                        bot.answer_callback_query(call.id, "فشل في تشغيل الملف")
        
        elif call.data.startswith('admin_stop_'):
            if str(call.from_user.id) == admin_id:
                parts = call.data.split('_')
                user_id = parts[2]
                file_name = '_'.join(parts[3:])
                file_key = f"{user_id}_{file_name}"
                
                if file_key in all_files and all_files[file_key]['status'] == 'running':
                    stop_file(file_name)
                    all_files[file_key]['status'] = 'stopped'
                    all_files[file_key]['process'] = None
                    bot_stats['active_files'] -= 1
                    bot_stats['stopped_files'] += 1
                    
                    if str(user_id) in user_files:
                        for file_data in user_files[str(user_id)]:
                            if file_data['file_name'] == file_name:
                                file_data['status'] = 'stopped'
                                file_data['process'] = None
                    
                    bot.answer_callback_query(call.id, f"تم إيقاف الملف {file_name}")
                    send_admin_file_control(call.message, file_key, all_files[file_key])
        
        elif call.data.startswith('admin_delete_'):
            if str(call.from_user.id) == admin_id:
                parts = call.data.split('_')
                user_id = parts[2]
                file_name = '_'.join(parts[3:])
                file_key = f"{user_id}_{file_name}"
                
                if file_key in all_files:
                    file_status = all_files[file_key]['status']
                    
                    if all_files[file_key]['status'] == 'running':
                        stop_file(file_name)
                    
                    # حذف الملف من النظام
                    if os.path.exists(file_name):
                        os.remove(file_name)
                    
                    # حذف الملف من القوائم
                    if str(user_id) in user_files:
                        user_files[str(user_id)] = [f for f in user_files[str(user_id)] if f['file_name'] != file_name]
                        if not user_files[str(user_id)]:
                            del user_files[str(user_id)]
                            bot_stats['total_users'] -= 1
                    
                    del all_files[file_key]
                    bot_stats['total_files'] -= 1
                    
                    if file_status == 'running':
                        bot_stats['active_files'] -= 1
                    else:
                        bot_stats['stopped_files'] -= 1
                    
                    bot.answer_callback_query(call.id, f"تم حذف الملف {file_name}")
                    send_admin_all_files(call.message)
        
        elif call.data.startswith('admin_token_'):
            if str(call.from_user.id) == admin_id:
                parts = call.data.split('_')
                user_id = parts[2]
                file_name = '_'.join(parts[3:])
                
                token = get_bot_token(file_name)
                bot.answer_callback_query(call.id, f"توكن البوت: {token}", show_alert=True)
        
        elif call.data.startswith('file_'):
            user_id = call.from_user.id
            file_index = int(call.data.split('_')[1])
            
            if str(user_id) in user_files and 0 <= file_index < len(user_files[str(user_id)]):
                file_data = user_files[str(user_id)][file_index]
                send_control_panel(call.message, user_id, file_index, file_data)
        
        elif call.data.startswith('start_'):
            user_id = call.from_user.id
            file_index = int(call.data.split('_')[1])
            
            if str(user_id) in user_files and 0 <= file_index < len(user_files[str(user_id)]):
                file_data = user_files[str(user_id)][file_index]
                
                if file_data['status'] == 'stopped':
                    process = install_and_run_uploaded_file(file_data['file_name'])
                    if process:
                        file_data['status'] = 'running'
                        file_data['process'] = process
                        
                        file_key = f"{user_id}_{file_data['file_name']}"
                        if file_key in all_files:
                            all_files[file_key]['status'] = 'running'
                            all_files[file_key]['process'] = process
                        
                        bot_stats['active_files'] += 1
                        bot_stats['stopped_files'] -= 1
                        
                        bot.answer_callback_query(call.id, "تم تشغيل الملف بنجاح!")
                        send_control_panel(call.message, user_id, file_index, file_data)
                    else:
                        bot.answer_callback_query(call.id, "فشل في تشغيل الملف")
                else:
                    bot.answer_callback_query(call.id, "الملف يعمل بالفعل!")
        
        elif call.data.startswith('stop_'):
            user_id = call.from_user.id
            file_index = int(call.data.split('_')[1])
            
            if str(user_id) in user_files and 0 <= file_index < len(user_files[str(user_id)]):
                file_data = user_files[str(user_id)][file_index]
                
                if file_data['status'] == 'running':
                    stop_file(file_data['file_name'])
                    file_data['status'] = 'stopped'
                    file_data['process'] = None
                    
                    file_key = f"{user_id}_{file_data['file_name']}"
                    if file_key in all_files:
                        all_files[file_key]['status'] = 'stopped'
                        all_files[file_key]['process'] = None
                    
                    bot_stats['active_files'] -= 1
                    bot_stats['stopped_files'] += 1
                    
                    bot.answer_callback_query(call.id, "تم إيقاف الملف بنجاح!")
                    send_control_panel(call.message, user_id, file_index, file_data)
                else:
                    bot.answer_callback_query(call.id, "الملف متوقف بالفعل!")
        
        elif call.data.startswith('delete_'):
            user_id = call.from_user.id
            file_index = int(call.data.split('_')[1])
            
            if str(user_id) in user_files and 0 <= file_index < len(user_files[str(user_id)]):
                file_data = user_files[str(user_id)][file_index]
                file_status = file_data['status']
                
                if file_data['status'] == 'running':
                    stop_file(file_data['file_name'])
                
                # حذف الملف من النظام
                if os.path.exists(file_data['file_name']):
                    os.remove(file_data['file_name'])
                
                # حذف الملف من القوائم
                file_key = f"{user_id}_{file_data['file_name']}"
                if file_key in all_files:
                    del all_files[file_key]
                
                del user_files[str(user_id)][file_index]
                
                if not user_files[str(user_id)]:
                    del user_files[str(user_id)]
                    bot_stats['total_users'] -= 1
                
                bot_stats['total_files'] -= 1
                
                if file_status == 'running':
                    bot_stats['active_files'] -= 1
                else:
                    bot_stats['stopped_files'] -= 1
                
                bot.answer_callback_query(call.id, "تم حذف الملف بنجاح!")
                send_my_files_menu(call.message, user_id)
        
        elif call.data.startswith('token_'):
            user_id = call.from_user.id
            file_index = int(call.data.split('_')[1])
            
            if str(user_id) in user_files and 0 <= file_index < len(user_files[str(user_id)]):
                file_data = user_files[str(user_id)][file_index]
                token = get_bot_token(file_data['file_name'])
                bot.answer_callback_query(call.id, f"توكن البوت: {token}", show_alert=True)
        
        elif call.data == 'back_to_files':
            user_id = call.from_user.id
            send_my_files_menu(call.message, user_id)
        
        elif call.data == 'back_to_admin_files':
            if str(call.from_user.id) == admin_id:
                send_admin_all_files(call.message)
    
    except Exception as e:
        print(f"Error in callback_handler: {e}")
        bot.answer_callback_query(call.id, "حدث خطأ أثناء معالجة الطلب")

def send_my_files_menu(message, user_id):
    try:
        markup = types.InlineKeyboardMarkup()
        
        if str(user_id) in user_files and user_files[str(user_id)]:
            for i, file_data in enumerate(user_files[str(user_id)]):
                status_icon = "▶️" if file_data['status'] == 'running' else "⏹️"
                btn = types.InlineKeyboardButton(f"{status_icon} {file_data['file_name']}", callback_data=f'file_{i}')
                markup.row(btn)
        else:
            if isinstance(message, types.CallbackQuery):
                bot.edit_message_text("ليس لديك أي ملفات مرفوعة بعد.", message.message.chat.id, message.message.message_id)
            else:
                bot.send_message(message.chat.id, "ليس لديك أي ملفات مرفوعة بعد.")
            return
        
        back_btn = types.InlineKeyboardButton("رجوع ◀️", callback_data='back_to_start')
        markup.row(back_btn)
        
        if isinstance(message, types.CallbackQuery):
            bot.edit_message_text("ملفاتك المرفوعة:", message.message.chat.id, message.message.message_id, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "ملفاتك المرفوعة:", reply_markup=markup)
    except Exception as e:
        print(f"Error in send_my_files_menu: {e}")

def send_control_panel(message, user_id, file_index, file_data):
    try:
        markup = types.InlineKeyboardMarkup()
        
        status_text = "نشط" if file_data['status'] == 'running' else "متوقف"
        status_icon = "⏹️" if file_data['status'] == 'running' else "▶️"
        action_text = "إيقاف" if file_data['status'] == 'running' else "تشغيل"
        action_callback = f"stop_{file_index}" if file_data['status'] == 'running' else f"start_{file_index}"
        
        action_btn = types.InlineKeyboardButton(f"{action_text} {status_icon}", callback_data=action_callback)
        token_btn = types.InlineKeyboardButton("الحصول على التوكن 🔑", callback_data=f"token_{file_index}")
        delete_btn = types.InlineKeyboardButton("حذف الملف 🗑️", callback_data=f"delete_{file_index}")
        back_btn = types.InlineKeyboardButton("رجوع ◀️", callback_data='back_to_files')
        
        markup.row(action_btn)
        markup.row(token_btn)
        markup.row(delete_btn)
        markup.row(back_btn)
        
        text = f"الملف: {file_data['file_name']}\nالحالة: {status_text}"
        
        if isinstance(message, types.CallbackQuery):
            bot.edit_message_text(text, message.message.chat.id, message.message.message_id, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, text, reply_markup=markup)
    except Exception as e:
        print(f"Error in send_control_panel: {e}")

def send_admin_all_files(message):
    try:
        markup = types.InlineKeyboardMarkup()
        
        if all_files:
            for file_key, file_data in all_files.items():
                status_icon = "▶️" if file_data['status'] == 'running' else "⏹️"
                user_info = f"{file_data['user_info']['first_name']}" if 'user_info' in file_data else f"User_{file_data['user_id']}"
                btn_text = f"{status_icon} {file_data['file_name']} - {user_info}"
                btn = types.InlineKeyboardButton(btn_text, callback_data=f"admin_control_{file_key}")
                markup.row(btn)
        else:
            if isinstance(message, types.CallbackQuery):
                bot.edit_message_text("لا توجد ملفات مرفوعة بعد.", message.message.chat.id, message.message.message_id)
            else:
                bot.send_message(message.chat.id, "لا توجد ملفات مرفوعة بعد.")
            return
        
        back_btn = types.InlineKeyboardButton("رجوع ◀️", callback_data='admin_back')
        markup.row(back_btn)
        
        if isinstance(message, types.CallbackQuery):
            bot.edit_message_text("جميع الملفات المرفوعة:", message.message.chat.id, message.message.message_id, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "جميع الملفات المرفوعة:", reply_markup=markup)
    except Exception as e:
        print(f"Error in send_admin_all_files: {e}")

def send_admin_file_control(message, file_key, file_data):
    try:
        markup = types.InlineKeyboardMarkup()
        
        status_text = "نشط" if file_data['status'] == 'running' else "متوقف"
        status_icon = "⏹️" if file_data['status'] == 'running' else "▶️"
        action_text = "إيقاف" if file_data['status'] == 'running' else "تشغيل"
        action_callback = f"admin_stop_{file_key}" if file_data['status'] == 'running' else f"admin_start_{file_key}"
        
        user_info = f"{file_data['user_info']['first_name']} (@{file_data['user_info']['username']})" if 'user_info' in file_data else f"User_{file_data['user_id']}"
        
        action_btn = types.InlineKeyboardButton(f"{action_text} {status_icon}", callback_data=action_callback)
        token_btn = types.InlineKeyboardButton("الحصول على التوكن 🔑", callback_data=f"admin_token_{file_key}")
        delete_btn = types.InlineKeyboardButton("حذف الملف 🗑️", callback_data=f"admin_delete_{file_key}")
        back_btn = types.InlineKeyboardButton("رجوع ◀️", callback_data='back_to_admin_files')
        
        markup.row(action_btn)
        markup.row(token_btn)
        markup.row(delete_btn)
        markup.row(back_btn)
        
        text = f"الملف: {file_data['file_name']}\nالحالة: {status_text}\nالمستخدم: {user_info}"
        
        if isinstance(message, types.CallbackQuery):
            bot.edit_message_text(text, message.message.chat.id, message.message.message_id, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, text, reply_markup=markup)
    except Exception as e:
        print(f"Error in send_admin_file_control: {e}")

def process_broadcast_message(message):
    try:
        # إذاعة الرسالة لجميع المستخدمين
        sent = 0
        failed = 0
        
        for user_id in user_files.keys():
            try:
                if message.content_type == 'text':
                    bot.send_message(user_id, message.text)
                elif message.content_type == 'photo':
                    bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
                elif message.content_type == 'document':
                    bot.send_document(user_id, message.document.file_id, caption=message.caption)
                sent += 1
            except:
                failed += 1
        
        bot.send_message(message.chat.id, f"تمت الإذا��ة بنجاح!\n\nتم الإرسال: {sent}\nفشل الإرسال: {failed}")
    except Exception as e:
        print(f"Error in process_broadcast_message: {e}")

def process_dev_username_change(message):
    try:
        new_username = message.text.strip()
        if new_username.startswith('@'):
            new_username = new_username[1:]
        
        developer_info['username'] = new_username
        bot.send_message(message.chat.id, f"تم تحديث يوزر المطور إلى: @{new_username}")
    except Exception as e:
        print(f"Error in process_dev_username_change: {e}")

def process_dev_id_change(message):
    try:
        new_id = message.text.strip()
        developer_info['user_id'] = new_id
        bot.send_message(message.chat.id, f"تم تحديث ايدي المطور إلى: {new_id}")
    except Exception as e:
        print(f"Error in process_dev_id_change: {e}")

def stop_file(file_name):
    try:
        # البحث عن عملية الملف وإيقافها
        process_name = os.path.basename(file_name)
        subprocess.run(['pkill', '-f', process_name])
    except Exception as e:
        print(f"Error stopping file: {e}")

# تشغيل البوت
if __name__ == '__main__':
    keep_alive()
    print("البوت بدأ العمل...")
    bot.polling()