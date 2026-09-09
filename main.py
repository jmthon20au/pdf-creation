import telebot
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
import arabic_reshaper
from bidi.algorithm import get_display

# التوكن الخاص بك
TOKEN = "6418845303:AAFsJChPM-D-Ka4sqYNRzCpNxVMDzjdIK1g"
bot = telebot.TeleBot(TOKEN)
import json
import os

DB_PATH = "database/users.json"  # ملف التخزين الدائم

# تحميل قاعدة بيانات المستخدمين
def load_users_db():
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# حفظ قاعدة بيانات المستخدمين
def save_users_db(data):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# تحديث بيانات مستخدم واحد
def update_user_db(chat_id):
    db = load_users_db()
    db[str(chat_id)] = user_data[chat_id]
    save_users_db(db)

# إعدادات الخطوط العربية والإنجليزية
FONTS = {
    "Arial": {"path": "fonts/arial.ttf", "name": "arial"},
    "amiri": {"path": "fonts/Amiri-Regular.ttf", "name": "Amiri"}
}


for key, font in FONTS.items():
    if os.path.exists(font["path"]):
        pdfmetrics.registerFont(TTFont(key, font["path"]))
    else:
       
        print(f"تنبيه: ملف الخط {font['path']} غير موجود.")


THEMES = {
    "classic": {"primary": "#2C3E50", "secondary": "#BDC3C7", "bg": "#FFFFFF", "name": "🏛️ الملكي الكلاسيكي"},
    "warm": {"primary": "#5D4037", "secondary": "#D7CCC8", "bg": "#FFFDE7", "name": "☕ الدافئ المريح"},
    "modern": {"primary": "#006064", "secondary": "#B2EBF2", "bg": "#FAFAFA", "name": "📱 الحديث المعاصر"}
}

user_data = {}

def process_arabic_text(text):
    """معالجة النصوص العربية لتبدو متصلة ومن اليمين إلى اليسار"""
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text

def is_line_arabic(text):
    """معرفة إذا كان السطر يحتاج إلى محاذاة لليمين"""
    clean_text = re.sub(r'<[^>]*>', '', text)
    arabic_chars = sum(1 for char in clean_text if '\u0600' <= char <= '\u06FF')
    english_chars = sum(1 for char in clean_text if ('a' <= char.lower() <= 'z'))
    if arabic_chars > 0 or arabic_chars >= english_chars:
        return True
    return False

def convert_markdown_to_html(text):
    """تحويل Markdown الأساسي إلى HTML تدعمه ReportLab"""
    text = re.sub(r'\*\*(.*?)\*\*|__(.__?)__', r'<b>\1\2</b>', text)
    text = re.sub(r'\*(.*?)\*|_(._?)_', r'<i>\1\2</i>', text)
    text = re.sub(r'`(.*?)`', r'<font name="Courier" color="red">\1</font>', text)
    return text

def init_user_settings(chat_id, first_name=""):
    db = load_users_db()
    if str(chat_id) not in db:
        db[str(chat_id)] = {
            "first_name": first_name,
            "text_list": [],
            "intro_list": [],  # 👈 إضافة القائمة الخاصة بنصوص المقدمة
            "font_size": 14,
            "theme": "classic",
            "password": "",
            "watermark": "",
            "user_display_name": first_name if first_name else "مستخدم البوت",
            "mode": "normal",
            "report_info": {},
            "saved_report_info": None,
            "font_name": "Arial"   # الخط الافتراضي
        }
        save_users_db(db)
    # تحميل بيانات المستخدم للذاكرة المؤقتة
    user_data[chat_id] = db[str(chat_id)]


def get_main_settings_keyboard(chat_id):
    """توليد لوحة التحكم الرئيسية بالأزرار مع خيار التقرير الجامعي"""
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    
    markup.add(telebot.types.InlineKeyboardButton("📝 بدء الان لإنشاء تقرير جامعي مخصص", callback_data="menu_start_report"))
    
    markup.add(
        telebot.types.InlineKeyboardButton("📂 معلوماتي المحفوظة", callback_data="menu_show_profile"),
        telebot.types.InlineKeyboardButton("🎨 اختيار ثيم الألوان", callback_data="menu_theme"),
        telebot.types.InlineKeyboardButton("✒️ اختيار نوع الخط", callback_data="menu_font"),
        telebot.types.InlineKeyboardButton("📏 حجم خط المتن", callback_data="menu_size"),
        telebot.types.InlineKeyboardButton("🔒 قفل بكلمة سر", callback_data="menu_password")
    )
    return markup

@bot.message_handler(commands=['start', 'help', 'settings'])
def send_welcome(message):
    chat_id = message.chat.id
    init_user_settings(chat_id, message.from_user.first_name)
    
    welcome_text = (
        "👑 مرحباً بك في منصة توليد الـ PDF الاحترافية الشاملة!**\n\n"
        "⚙️ **لوحة التحكم والأزرار:**\n"
        "يمكنك تخصيص كل ميزات المستند الخاص بك مباشرة من الأزرار أدناه.\n\n"
        "📥 **بدء العمل:**\n"
        "اضغط على زر البدء لتجهيز تقريرك الجامعي:\n"
        "ملاحظة مهمة: من تدز اسم الجامعة او اسم الكلية او اسم القسم العلمي دز فقط الاسم بدون كلمة 'كلية العلوم' خطا | بس خلي العلوم  "
    )
    bot.send_message(chat_id, welcome_text, parse_mode="Markdown", reply_markup=get_main_settings_keyboard(chat_id))
@bot.callback_query_handler(func=lambda call: call.data == "menu_show_profile")
def show_profile_info(call):
    chat_id = call.message.chat.id
    db = load_users_db()
    user_info = db.get(str(chat_id), {})

    if not user_info or not user_info.get("saved_report_info"):
        bot.answer_callback_query(call.id, "⚠️ لا توجد معلومات محفوظة لك بعد.")
        return

    info = user_info["saved_report_info"]

    # النص الوصفي
    caption = (
        f"<b>📂 معلوماتك المحفوظة حالياً:</b>\n\n"
        f"🏢 الجامعة: {info.get('university','')}\n"
        f"🏫 الكلية: {info.get('college','')}\n"
        f"📚 القسم: {info.get('department','')}\n"
        f"👤 الطالب: {info.get('student_name','')}\n"
        f"🔢 المرحلة: {info.get('stage','')}\n"
        f"☀️ الدراسة: {info.get('study_type','')}\n"
        f"📖 المادة: {info.get('subject','')}\n"
        f"👨‍🏫 الأستاذ: {info.get('professor','')}\n\n"
        f"✏️ اختر ما تريد تعديله من الأزرار أدناه:"
    )

    # لوحة أزرار التعديل
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("👤 الاسم", callback_data="edit_name"),
        telebot.types.InlineKeyboardButton("🏢 الجامعة", callback_data="edit_university"),
        telebot.types.InlineKeyboardButton("🏫 الكلية", callback_data="edit_college"),
        telebot.types.InlineKeyboardButton("📚 القسم", callback_data="edit_department"),
        telebot.types.InlineKeyboardButton("🖼️ الشعار", callback_data="edit_logo"),
        telebot.types.InlineKeyboardButton("🔢 المرحلة", callback_data="edit_stage"),
        telebot.types.InlineKeyboardButton("☀️ الدراسة", callback_data="edit_study"),
        telebot.types.InlineKeyboardButton("📖 المادة", callback_data="edit_subject"),
        telebot.types.InlineKeyboardButton("👨‍🏫 الأستاذ", callback_data="edit_professor"),
        telebot.types.InlineKeyboardButton("♻️ ترسيت (مسح البيانات)", callback_data="menu_reset"),
        telebot.types.InlineKeyboardButton("⬅️ العودة للرئيسية", callback_data="back_main")
    )

    bot.answer_callback_query(call.id)

    # عرض الصورة إذا موجودة
    logo_path = info.get("logo_path", "")
    if logo_path and os.path.exists(logo_path):
        bot.send_photo(chat_id, open(logo_path, "rb"), caption=caption, parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "menu_reset")
def confirm_reset(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("✅ نعم، امسح البيانات", callback_data="reset_yes"),
        telebot.types.InlineKeyboardButton("❌ إلغاء", callback_data="reset_no")
    )

    bot.send_message(chat_id, "⚠️ هل أنت متأكد أنك تريد مسح كل بياناتك المحفوظة؟", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in ["reset_yes", "reset_no"])
def handle_reset_choice(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)

    if call.data == "reset_yes":
        # مسح البيانات من الذاكرة والملف
        db = load_users_db()
        if str(chat_id) in db:
            # إذا عنده شعار محفوظ نحذفه من النظام
            logo_path = db[str(chat_id)]["saved_report_info"].get("logo_path") if db[str(chat_id)]["saved_report_info"] else None
            if logo_path and os.path.exists(logo_path):
                try:
                    os.remove(logo_path)
                except Exception as e:
                    print("Logo delete failed:", e)

            db[str(chat_id)]["saved_report_info"] = None
            db[str(chat_id)]["report_info"] = {}
            db[str(chat_id)]["text_list"] = []
            save_users_db(db)
            user_data[chat_id] = db[str(chat_id)]

        # حذف الرسالة الحالية
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except Exception as e:
            print("Delete failed:", e)

        # إرسال رسالة ستارت جديدة مع تنبيه
        reset_text = (
            "✅ <b>تمت إعادة ضبط حسابك بالكامل!</b>\n\n"
            "👑 <b>مرحباً بك في منصة توليد الـ PDF الاحترافية الشاملة!</b>\n\n"
            "⚙️ <b>لوحة التحكم والأزرار:</b>\n"
            "يمكنك تخصيص كل ميزات المستند الخاص بك مباشرة من الأزرار أدناه.\n\n"
            "📥 <b>بدء العمل:</b>\n"
            "اضغط على زر البدء لتجهيز تقريرك الجامعي:\n"
            "ملاحظة مهمة: من تدز اسم الجامعة او اسم الكلية او اسم القسم العلمي دز فقط الاسم بدون كلمة 'كلية العلوم' خطأ | بس خلي العلوم"
        )
        bot.send_message(chat_id, reset_text, parse_mode="HTML", reply_markup=get_main_settings_keyboard(chat_id))

    else:
        bot.send_message(chat_id, "❌ تم إلغاء عملية المسح.", reply_markup=get_main_settings_keyboard(chat_id))

@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def handle_back_main(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)

    # حذف الرسالة الحالية
    try:
        bot.delete_message(chat_id, call.message.message_id)
    except Exception as e:
        print("Delete failed:", e)

    # إرسال رسالة ستارت جديدة
    welcome_text = (
        "👑 <b>مرحباً بك في منصة توليد الـ PDF الاحترافية الشاملة!</b>\n\n"
        "⚙️ <b>لوحة التحكم والأزرار:</b>\n"
        "يمكنك تخصيص كل ميزات المستند الخاص بك مباشرة من الأزرار أدناه.\n\n"
        "📥 <b>بدء العمل:</b>\n"
        "اضغط على زر البدء لتجهيز تقريرك الجامعي:\n"
        "ملاحظة مهمة: من تدز اسم الجامعة او اسم الكلية او اسم القسم العلمي دز فقط الاسم بدون كلمة 'كلية العلوم' خطأ | بس خلي العلوم"
    )
    bot.send_message(chat_id, welcome_text, parse_mode="HTML", reply_markup=get_main_settings_keyboard(chat_id))

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_"))
def edit_profile_field(call):
    chat_id = call.message.chat.id
    field = call.data.split("_")[1]

    field_map = {
        "name": "👤 الاسم الثلاثي الجديد:",
        "university": "🏢 اسم الجامعة الجديد:",
        "college": "🏫 اسم الكلية الجديد:",
        "department": "📚 اسم القسم الجديد:",
        "logo": "🖼️ أرسل صورة الشعار الجديدة:",
        "stage": "🔢 المرحلة الدراسية الجديدة:",
        "study": "☀️ نوع الدراسة الجديد:",
        "subject": "📖 اسم المادة الجديد:",
        "professor": "👨‍🏫 اسم الأستاذ الجديد:"
    }

    bot.answer_callback_query(call.id)
    msg = bot.send_message(chat_id, f"{field_map[field]}")
    bot.register_next_step_handler(msg, lambda m: save_profile_edit(m, field))

def save_profile_edit(message, field):
    chat_id = message.chat.id
    db = load_users_db()
    user_info = db.get(str(chat_id), {})
    if not user_info or not user_info.get("saved_report_info"):
        bot.reply_to(message, "⚠️ لا توجد معلومات محفوظة لتعديلها.")
        return

    if field == "logo":
        # تعديل الشعار كصورة
        if message.content_type in ["photo", "document"]:
            file_id = message.photo[-1].file_id if message.content_type == "photo" else message.document.file_id
            file_info = bot.get_file(file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            logo_path = f"saved_logo_{chat_id}.jpg"
            with open(logo_path, "wb") as new_file:
                new_file.write(downloaded_file)
            user_info["saved_report_info"]["logo_path"] = logo_path
        else:
            bot.reply_to(message, "⚠️ يرجى إرسال صورة شعار جديدة.")
            return
    else:
        user_info["saved_report_info"][field] = message.text.strip()

    save_users_db(db)
    bot.reply_to(message, "✅ تم تحديث معلوماتك بنجاح!")

@bot.callback_query_handler(func=lambda call: call.data == "menu_start_report")
def start_report_flow(call):
    chat_id = call.message.chat.id
    init_user_settings(chat_id, call.from_user.first_name)
    bot.answer_callback_query(call.id)
    
    if user_data[chat_id].get('saved_report_info'):
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            telebot.types.InlineKeyboardButton("📁 استخدام معلوماتي المحفوظة تلقائياً", callback_data="report_use_saved"),
            telebot.types.InlineKeyboardButton("✨ إدخال بيانات جديدة للواجهة", callback_data="report_use_new")
        )
        bot.edit_message_text("🔍 وجدنا معلومات واجهة جامعية محفوظة في ملفك الشخصي، كيف ترغب في المتابعة？", chat_id, call.message.message_id, reply_markup=markup)
    else:
        goTo_new_report_flow(call.message)

@bot.callback_query_handler(func=lambda call: call.data in ["report_use_saved", "report_use_new"])
def handle_report_source_choice(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    
    if call.data == "report_use_saved":
        # 1. نسخ البيانات الثابتة المحفوظة (الجامعة، الكلية، القسم، الاسم، المرحلة، الدراسة، الشعار)
        user_data[chat_id]['report_info'] = user_data[chat_id]['saved_report_info'].copy()
        user_data[chat_id]['mode'] = 'report'
        user_data[chat_id]['text_list'] = []
        
        # 2. نطلب منه الآن إدخال البيانات المتغيرة للتقرير الجديد فوراً
        msg = bot.send_message(chat_id, "📁 تم استدعاء معلوماتك الثابتة بنجاح!\n\n✏️ الآن أرسل عنوان أو اسم التقرير الجديد (مثال: معمارية الحاسوب):")
        # نوديه مباشرة لدالة ask_report_student_name بعد التعديل بالخطوة القادمة
        bot.register_next_step_handler(msg, ask_report_student_name_conditional)
    else:
        goTo_new_report_flow(call.message)
def ask_report_student_name_conditional(message):
    chat_id = message.chat.id
    # حفظ عنوان التقرير
    user_data[chat_id]['report_info']['title'] = message.text.strip()
    
    # إذا كان المستخدم يستعمل معلوماته المحفوظة، نتخطى (الاسم، المرحلة، الدراسة) ونروح للمادة فوراً
    if user_data[chat_id].get('saved_report_info') and user_data[chat_id]['report_info'].get('university') == user_data[chat_id]['saved_report_info'].get('university'):
        msg = bot.reply_to(message, "📖 أرسل الآن اسم المادة الدراسية (مثال: هياكل بيانات):")
        bot.register_next_step_handler(msg, ask_report_professor)
    else:
        # إذا كان تقرير جديد كلياً، يكمل بشكل طبيعي ويسأله عن اسم الطالب الثلاثي
        msg = bot.reply_to(message, "👤 أرسل الآن اسم الطالب الثلاثي:")
        bot.register_next_step_handler(msg, ask_report_stage)
def goTo_new_report_flow(message):
    chat_id = message.chat.id
    user_data[chat_id]['mode'] = 'report'
    user_data[chat_id]['text_list'] = []
    user_data[chat_id]['report_info'] = {}

    # لوحة أزرار فيها خيار إلغاء العملية
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(telebot.types.InlineKeyboardButton("❌ إلغاء العملية", callback_data="cancel_report"))

    msg = bot.send_message(
        chat_id,
        "🏢 لنبدأ بتجهيز واجهة التقرير الجديدة.\n\n"
        ":أرسل الآن اسم الجامعة \n اسم الجامعة فقط بدون كلمة الجامعة \n (مثال: القادسية):",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, ask_report_college)

@bot.callback_query_handler(func=lambda call: call.data == "menu_font")
def choose_font(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)

    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(telebot.types.InlineKeyboardButton("📄 معاينة الخطوط", callback_data="preview_fonts"))
    for key, font in FONTS.items():
        markup.add(telebot.types.InlineKeyboardButton(font["name"], callback_data=f"setfont_{key}"))
    markup.add(telebot.types.InlineKeyboardButton("⬅️ العودة للرئيسية", callback_data="back_main"))
    bot.edit_message_text("✒️ اختر نوع الخط الذي تريده للتقرير:", chat_id, call.message.message_id, reply_markup=markup)

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER

@bot.callback_query_handler(func=lambda call: call.data == "preview_fonts")
def preview_fonts(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)

    file_path = f"fonts_preview_{chat_id}.pdf"
    doc = SimpleDocTemplate(file_path, pagesize=A4)
    story = []

    for key, font in FONTS.items():
        # التأكد من أن الخط مسجل في ReportLab قبل استخدامه، وإلا نستخدم الخط الافتراضي كبديل
        current_font = key if key in pdfmetrics.getRegisteredFontNames() else "Helvetica"
        
        style = ParagraphStyle(
            name=f"PreviewStyle_{key}",
            fontName=current_font,
            fontSize=20,
            alignment=TA_CENTER
        )
        
        info_style = ParagraphStyle(
            name=f"InfoStyle_{key}",
            fontName="Helvetica",
            fontSize=12,
            alignment=TA_CENTER
        )
        
        story.append(Paragraph(process_arabic_text("بسم الله الرحمن الرحيم"), style))
        story.append(Paragraph(f"({font['name']})", info_style))
        story.append(Spacer(1, 20))

    doc.build(story)

    with open(file_path, "rb") as f:
        bot.send_document(chat_id, f, caption="📄 معاينة الخطوط المتاحة:\nكل خط مع جملة 'بسم الله الرحمن الرحيم'")

    try:
        os.remove(file_path)
    except Exception as e:
        print("Delete failed:", e)

@bot.callback_query_handler(func=lambda call: call.data.startswith("setfont_"))
def handle_set_font(call):
    chat_id = call.message.chat.id
    font_key = call.data.split("_")[1]

    user_data[chat_id]['font_name'] = font_key
    update_user_db(chat_id)

    bot.answer_callback_query(call.id, f"تم اختيار الخط {FONTS[font_key]['name']}")

    bot.edit_message_text(
        f"✅ تم حفظ الإعدادات! الخط الحالي هو: <b>{FONTS[font_key]['name']}</b>",
        chat_id,
        call.message.message_id,
        reply_markup=get_main_settings_keyboard(chat_id),
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data == "cancel_report")
def cancel_report_flow(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)

    # حذف الرسالة الحالية
    try:
        bot.delete_message(chat_id, call.message.message_id)
    except Exception as e:
        print("Delete failed:", e)

    # إعادة المستخدم للوحة التحكم الرئيسية
    bot.send_message(
        chat_id,
        "❌ تم إلغاء عملية إنشاء التقرير.\n⚙️ يمكنك التحكم وتخصيص كل ميزات المستند من هنا:",
        reply_markup=get_main_settings_keyboard(chat_id)
    )

def ask_report_college(message):
    chat_id = message.chat.id
    user_data[chat_id]['report_info']['university'] = message.text.strip()
    
    # حفظ التغييرات
    update_user_db(chat_id)
    
    msg = bot.reply_to(message, "ارسل اسم الكلية فقط: \n فقط اسم الكلية بدون كلمة - الكلية - \n مثال : علوم الحاسوب وتكنولوجيا المعلومات ")
    bot.register_next_step_handler(msg, ask_report_department)


def ask_report_department(message):
    chat_id = message.chat.id
    user_data[chat_id]['report_info']['college'] = message.text.strip()
    
    # حفظ التغييرات
    update_user_db(chat_id)
    
    msg = bot.reply_to(message, "🖼️ الآن، يرجى إرسال شعار الكلية أو الجامعة* كصورة أو ملف:")
    bot.register_next_step_handler(msg, catch_report_logo)

def catch_report_logo(message):
    chat_id = message.chat.id
    file_id = None
    file_name = ""

    if message.content_type == 'document':
        file_name = message.document.file_name.lower()
        if file_name.endswith(('.png', '.jpg', '.jpeg', '.webp')):
            file_id = message.document.file_id
        else:
            msg = bot.reply_to(message, "⚠️ الملف المرسل ليس صورة! يرجى إرسال شعار الكلية كصورة أو كملف بترميز (PNG, JPG, JPEG):")
            bot.register_next_step_handler(msg, catch_report_logo)
            return
    elif message.content_type == 'photo':
        file_id = message.photo[-1].file_id
        file_name = "logo.jpg"
    else:
        msg = bot.reply_to(message, "⚠️ يرجى إرسال شعار الكلية كصورة أو كملف مستند (Document):")
        bot.register_next_step_handler(msg, catch_report_logo)
        return

    if file_id:
        try:
            status = bot.reply_to(message, "⏳ جاري تحميل الشعار بالدقة الكاملة ومعالجته...")
            file_info = bot.get_file(file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            ext = ".jpg"
            if '.' in file_name:
                ext = f".{file_name.split('.')[-1]}"
                
            if user_data[chat_id].get('mode') == 'save_profile':
                logo_path = f"saved_logo_{chat_id}{ext}"
            else:
                logo_path = f"logo_{chat_id}{ext}"
            
            with open(logo_path, 'wb') as new_file:
                new_file.write(downloaded_file)
                
            user_data[chat_id]['report_info']['logo_path'] = logo_path
            
            # ✅ حفظ التغييرات في ملف JSON
            update_user_db(chat_id)
            
            bot.delete_message(chat_id, status.message_id)
            
            msg = bot.send_message(chat_id, "🔬 أرسل الآن اسم القسم العلمي فقط: \n بدون كلمة القسم. \n (مثال: علوم الحاسوب):")
            bot.register_next_step_handler(msg, ask_report_title)
        except Exception as e:
            bot.send_message(chat_id, f"❌ حدث خطأ أثناء حفظ الصورة: {str(e)}")
            msg = bot.send_message(chat_id, "🖼️ أرسل الشعار مرة أخرى:")
            bot.register_next_step_handler(msg, catch_report_logo)


def ask_report_title(message):
    chat_id = message.chat.id
    user_data[chat_id]['report_info']['department'] = message.text.strip()
    
    # حفظ التغييرات
    update_user_db(chat_id)
    
    msg = bot.reply_to(message, "📚 أرسل الآن  عنوان أو اسم التقرير (مثال: معمارية الحاسوب):")
    bot.register_next_step_handler(msg, ask_report_student_name_conditional)


def ask_report_student_name(message):
    chat_id = message.chat.id
    user_data[chat_id]['report_info']['title'] = message.text.strip()
    msg = bot.reply_to(message, "👤 أرسل الآن **اسم الطالب الثلاثي**:")
    bot.register_next_step_handler(msg, ask_report_stage)

def ask_report_stage(message):
    chat_id = message.chat.id
    user_data[chat_id]['report_info']['student_name'] = message.text.strip()
    
    # حفظ التغييرات
    update_user_db(chat_id)
    
    msg = bot.reply_to(message, "🔢 أرسل المرحلة الدراسية والشعبة (مثال: المرحلة الأولى - شعبة A):")
    bot.register_next_step_handler(msg, ask_report_study_type)


def ask_report_study_type(message):
    chat_id = message.chat.id
    user_data[chat_id]['report_info']['stage'] = message.text.strip()
    
    # حفظ التغييرات
    update_user_db(chat_id)
    
    msg = bot.reply_to(message, "☀️ أرسل نوع الدراسة (صباحي أم مسائي):")
    bot.register_next_step_handler(msg, ask_report_subject)


def ask_report_subject(message):
    chat_id = message.chat.id
    user_data[chat_id]['report_info']['study_type'] = message.text.strip()
    
    # حفظ التغييرات
    update_user_db(chat_id)
    
    msg = bot.reply_to(message, "📖 أرسل اسم المادة الدراسية (مثال: هياكل بيانات):")
    bot.register_next_step_handler(msg, ask_report_professor)

def ask_report_professor(message):
    chat_id = message.chat.id
    user_data[chat_id]['report_info']['subject'] = message.text.strip()
    
    # حفظ التغييرات
    update_user_db(chat_id)
    
    msg = bot.reply_to(message, "👨‍🏫 أرسل اسم الدكتور المشرف:")
    bot.register_next_step_handler(msg, save_final_report_info)

def save_final_report_info(message):
    chat_id = message.chat.id
    user_data[chat_id]['report_info']['professor'] = message.text.strip()
    
    if user_data[chat_id].get('mode') == 'save_profile':
        user_data[chat_id]['saved_report_info'] = user_data[chat_id]['report_info'].copy()
        update_user_db(chat_id)
        bot.reply_to(message, "🌟 ممتاز! تم حفظ معلومات واجهتك الدراسية وشعارك بنجاح في ملفك الشخصي.")
        bot.send_message(chat_id, "⚙️ لوحة التحكم الرئيسية:", reply_markup=get_main_settings_keyboard(chat_id))
        user_data[chat_id]['mode'] = 'normal'
        user_data[chat_id]['report_info'] = {}
    else:
        user_data[chat_id]['saved_report_info'] = user_data[chat_id]['report_info'].copy()
        user_data[chat_id]['intro_list'] = [] # تصفير القائمة
        user_data[chat_id]['mode'] = 'collecting_intro' # تفعيل وضع جمع المقدمة
        update_user_db(chat_id)
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("✅ انتهيت من المقدمة", callback_data="finish_intro_step"))
        
        bot.send_message(
            chat_id, 
            "📝 **الان يرجى إرسال نصوص المقدمة.**\nيمكنك إرسال أكثر من رسالة وسأقوم بتجميعها لك.\nعند الانتهاء تماماً اضغط على الزر أدناه 👇", 
            parse_mode="Markdown", 
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data == "finish_intro_step")
def handle_finish_intro(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    user_data[chat_id]['mode'] = 'report' # العودة للوضع الطبيعي لاستلام التقرير
    update_user_db(chat_id)
    
    welcome_content_msg = (
        "✅ **تم حفظ المقدمة بنجاح!**\n\n"
        "📥 الآن، تفضل بإرسال **محتوى التقرير الداخلي** (نصوص أو ملفات)، وعند الانتهاء اضغط على زر **(هاهية)**.\n\n"
        "⚠️ **ملاحظة مهمة:** يمنع استخدام الملصقات (الإيموجي) والصور داخل النصوص لأنها ستظهر كمربعات وتسيء لتنسيق التقرير."
        )
    bot.send_message(chat_id, welcome_content_msg, parse_mode="Markdown")
@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def handle_menu_navigation(call):
    chat_id = call.message.chat.id
    init_user_settings(chat_id, call.from_user.first_name)
    action = call.data.split("_")[1]
    bot.answer_callback_query(call.id)
    
    if action == "theme":
        markup = telebot.types.InlineKeyboardMarkup()
        for key, value in THEMES.items():
            markup.add(telebot.types.InlineKeyboardButton(value['name'], callback_data=f"settheme_{key}"))
        markup.add(telebot.types.InlineKeyboardButton("⬅️ العودة للرئيسية", callback_data="back_main"))
        bot.edit_message_text("🎨 اختر ثيم الألوان المفضل لصفحات مستندك:", chat_id, call.message.message_id, reply_markup=markup)
    elif action == "size":
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton("صغير (12)", callback_data="setsize_12"),
            telebot.types.InlineKeyboardButton("متوسط (14)", callback_data="setsize_14"),
            telebot.types.InlineKeyboardButton("كبير (18)", callback_data="setsize_18")
        )
        markup.add(telebot.types.InlineKeyboardButton("⬅️ العودة للرئيسية", callback_data="back_main"))
        bot.edit_message_text("📏 اختر حجم خط المتن المناسب للتقرير:", chat_id, call.message.message_id, reply_markup=markup)
    elif action == "watermark":
        msg = bot.send_message(chat_id, "📝 أرسل العبارة التي تريدها كعلامة مائية مخصصة (أو أرسل 'تلقائي' لنجعلها باسم حسابك):")
        bot.register_next_step_handler(msg, save_watermark)
    elif action == "password":
        msg = bot.send_message(chat_id, "🔑 أرسل كلمة السر التي تود قفل وحماية المستند بها (أو أرسل 'الغاء' لإزالة القفل):")
        bot.register_next_step_handler(msg, save_password)

@bot.callback_query_handler(func=lambda call: call.data == "back_main")
def handle_back_main(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    bot.edit_message_text("⚙️ يمكنك التحكم وتخصيص كل ميزات المستند من هنا عبر الأزرار لراحة تامة:", chat_id, call.message.message_id, reply_markup=get_main_settings_keyboard(chat_id))

@bot.callback_query_handler(func=lambda call: call.data.startswith("settheme_"))
def handle_set_theme(call):
    chat_id = call.message.chat.id
    theme_key = call.data.split("_")[1]

    # حفظ الثيم الجديد في بيانات المستخدم
    user_data[chat_id]['theme'] = theme_key
    update_user_db(chat_id)

    bot.answer_callback_query(call.id, f"تم تفعيل ثيم {THEMES[theme_key]['name']}")

    # رسالة تأكيد مع لوحة التحكم الرئيسية
    bot.edit_message_text(
        f"✅ تم حفظ الإعدادات! الثيم الفعّال حالياً هو: <b>{THEMES[theme_key]['name']}</b>",
        chat_id,
        call.message.message_id,
        reply_markup=get_main_settings_keyboard(chat_id),
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("setsize_"))
def handle_set_size(call):
    chat_id = call.message.chat.id
    size = int(call.data.split("_")[1])

    # حفظ حجم الخط الجديد في بيانات المستخدم
    user_data[chat_id]['font_size'] = size
    update_user_db(chat_id)

    bot.answer_callback_query(call.id, f"تم تغيير حجم الخط إلى {size}")

    # رسالة تأكيد مع لوحة التحكم الرئيسية
    bot.edit_message_text(
        f"✅ تم حفظ الإعدادات! حجم خط المتن الحالي هو: <b>{size}</b>",
        chat_id,
        call.message.message_id,
        reply_markup=get_main_settings_keyboard(chat_id),
        parse_mode="HTML"
    )

def save_password(message):
    chat_id = message.chat.id
    init_user_settings(chat_id, message.from_user.first_name)
    text = message.text.strip()

    if text in ["الغاء", "إلغاء"]:
        # إلغاء كلمة السر
        user_data[chat_id]['password'] = ""
        update_user_db(chat_id)
        bot.reply_to(message, "🔓 تم إلغاء قفل الملفات.")
    else:
        # حفظ كلمة السر الجديدة
        user_data[chat_id]['password'] = text
        update_user_db(chat_id)
        bot.reply_to(message, "🔒 تم تفعيل حماية وتشفير المستندات بكلمة السر الخاصة بك!")

    # عرض لوحة التحكم الرئيسية بعد التحديث
    bot.send_message(
        chat_id,
        "⚙️ يمكنك التحكم وتخصيص كل ميزات المستند من هنا:",
        reply_markup=get_main_settings_keyboard(chat_id)
    )

@bot.message_handler(content_types=['document'])
def handle_incoming_document(message):
    chat_id = message.chat.id
    init_user_settings(chat_id, message.from_user.first_name)
    file_name = message.document.file_name
    
    if file_name.endswith(('.txt', '.py', '.java', '.cpp', '.html', '.css', '.json', '.js')):
        status = bot.reply_to(message, "⏳ جاري قراءة محتويات الملف النصي المرفوع...")
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        try:
            file_content = downloaded_file.decode('utf-8')
        except UnicodeDecodeError:
            try:
                file_content = downloaded_file.decode('windows-1256')
            except Exception:
                bot.edit_message_text("❌ عذراً، لم نتمكن من قراءة ترميز الملف النصي.", chat_id, status.message_id)
                return
        bot.delete_message(chat_id, status.message_id)
        message.text = file_content
        handle_incoming_text(message)
    else:
        bot.reply_to(message, "⚠️ يرجى إرسال ملفات نصية كودية أو عادية فقط (مثل .txt, .py).")

@bot.callback_query_handler(func=lambda call: call.data == "menu_save_profile")
def save_profile_flow(call):
    chat_id = call.message.chat.id
    init_user_settings(chat_id, call.from_user.first_name)
    bot.answer_callback_query(call.id)
    
    user_data[chat_id]['mode'] = 'save_profile'
    user_data[chat_id]['report_info'] = {} 
    
    msg = bot.edit_message_text("💾 أهلاً بك في إعداد ملفك الشخصي الدائم.\n\nأرسل الآن اسم الجامعة ليتم حفظه:", chat_id, call.message.message_id)
    bot.register_next_step_handler(msg, ask_report_college)

import threading

# قفل برمي لضمان حفظ الرسائل المتتالية بالتسلسل الصحيح ومنع التداخل
db_lock = threading.Lock()

@bot.message_handler(content_types=['text'])
def handle_incoming_text(message):
    chat_id = message.chat.id
    init_user_settings(chat_id, message.from_user.first_name)
    
    formatted_text = convert_markdown_to_html(message.text)
    
    # في حال كان المستخدم في مرحلة إرسال المقدمة
    if user_data[chat_id].get('mode') == 'collecting_intro':
        with db_lock:
            user_data[chat_id]['intro_list'].append(formatted_text)
            total_intros = len(user_data[chat_id]['intro_list'])
            update_user_db(chat_id)

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("✅ انتهيت من المقدمة", callback_data="finish_intro_step"))
        
        bot.send_message(
            chat_id, 
            f"📥 **تم استلام النص رقم ({total_intros}) الخاص بالمقدمة!**\nيمكنك إرسال المزيد أو الضغط على زر الانتهاء.", 
            reply_markup=markup, 
            parse_mode="Markdown"
        )
        return

    # الاستلام الطبيعي لمحتوى التقرير
    with db_lock:
        user_data[chat_id]['text_list'].append(formatted_text)
        total_texts = len(user_data[chat_id]['text_list'])
        update_user_db(chat_id)

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("✅ هاهية (توليد المستند)", callback_data="action_finish"))
    
    status_text = (
        f"📥 **تم استلام النص رقم ({total_texts}) ودمجه بنجاح مع النصوص السابقة!**\n\n"
        "يمكنك الاستمرار في إرسال أي نصوص أو ملفات أخرى في أي وقت، "
        "وعندما تكتفي تماماً وتُريد تحميل ملف الـ PDF اضغط على الزر أدناه 👇"
    )
    bot.send_message(chat_id, status_text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("action_"))
def handle_pdf_actions(call):
    chat_id = call.message.chat.id
    if call.data == "action_finish":
        # التحقق من أن قائمة النصوص تحتوي على بيانات فعلياً
        if chat_id not in user_data or not user_data[chat_id]['text_list']:
            bot.answer_callback_query(call.id, "⚠️ قائمة النصوص فارغة! يرجى إرسال نصوص أولاً ليتم دمجها.")
            return
            
        bot.answer_callback_query(call.id)
        
        # الانتقال لخطوة طلب اسم الملف لتوليد الـ PDF
        msg = bot.send_message(chat_id, "📝 ممتاز! أرسل الآن الاسم المخصص الذي تريده لملف الـ PDF:")
        bot.register_next_step_handler(msg, handle_file_name_v5)
def handle_file_name_v5(message):
    chat_id = message.chat.id
    if not message.text:
        msg = bot.reply_to(message, "❌ يرجى إرسال اسم نصي صالح:")
        bot.register_next_step_handler(msg, handle_file_name_v5)
        return

    file_name = message.text.strip().replace("/", "_").replace("\\", "_")
    if chat_id not in user_data:
        bot.send_message(chat_id, "⚠️ حدث خطأ فني، يرجى إعادة المحاولة.")
        return
        
    user_data[chat_id]['file_name'] = file_name
    generate_pdf_v5(chat_id)

def generate_pdf_v5(chat_id):
    data = user_data[chat_id]
    text_list = data['text_list']
    intro_list = data.get('intro_list', [])  # جلب قائمة نصوص المقدمة
    file_name = data['file_name']
    font_size = data['font_size']
    theme_key = data.get('theme', 'classic')
    password = data.get('password', '')
    theme_colors = THEMES.get(theme_key, THEMES['classic'])
    status_msg = bot.send_message(chat_id, "⏳ جاري تنسيق السطور وبناء الإطارات وحساب حجم الملف الفعلي...")
    pdf_filename = f"{file_name}_{chat_id}.pdf"
    
    try:
        # حساب الإحصائيات (المقدمة + المتن)
        combined_raw_text = "\n".join(intro_list + text_list)
        clean_for_stats = re.sub(r'<[^>]*>', '', combined_raw_text)
        word_count = len(clean_for_stats.split())
        line_count = len(clean_for_stats.split('\n'))
        baghdad_tz = ZoneInfo("Asia/Baghdad")
        current_date = datetime.now(baghdad_tz).strftime("%Y-%m-%d %I:%M %p")
        
        doc = SimpleDocTemplate(pdf_filename, pagesize=A4)
        doc.chat_id = chat_id
        doc.theme_colors = theme_colors
        
        styles = getSampleStyleSheet()
        story = []

        # جلب اسم الخط المختار وتأكيده
        chosen_font = data.get("font_name", "cairo")
        if chosen_font not in pdfmetrics.getRegisteredFontNames():
            chosen_font = "Helvetica"

        # 1️⃣ بناء واجهة التقرير
        if 'report_info' in data and data['report_info']:
            info = data['report_info']
            from reportlab.platypus import Table, TableStyle, PageBreak, Image
            
            story.append(Spacer(1, 10))
            
            right_text_style = ParagraphStyle(
                'RepHeaderRight', parent=styles['Normal'], fontName='arial', fontSize=15, leading=18, alignment=TA_RIGHT
            )
            
            header_paragraphs = [
                Paragraph(process_arabic_text("جمهوريــــــة الـــعراق"), right_text_style),
                Paragraph(process_arabic_text("وزارة التعليم العالي والبحث العلمي"), right_text_style),
                Paragraph(process_arabic_text(f"جامعة {info.get('university', '')}"), right_text_style),
                Paragraph(process_arabic_text(f"كلية {info.get('college', '')}"), right_text_style),
                Paragraph(process_arabic_text(f"قسم {info.get('department', '')}"), right_text_style),
            ]

            logo_img = ""
            user_logo_path = info.get('logo_path', '')
            if user_logo_path and os.path.exists(user_logo_path):
                logo_img = Image(user_logo_path, width=110, height=110)
                logo_img.hAlign = 'LEFT'
            else:
                logo_img = Paragraph("", right_text_style)
                
            top_table_data = [[logo_img, header_paragraphs]]
            top_table = Table(top_table_data, colWidths=[130, 380])
            top_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('ALIGN', (0,0), (0,0), 'LEFT'),
                ('ALIGN', (1,0), (1,0), 'RIGHT'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(top_table)
            
            story.append(Spacer(1, 50))
            
            title_text_style = ParagraphStyle(
                'TitleText', parent=styles['Normal'], fontName='arial', fontSize=20, textColor=HexColor('#FFFFFF'), alignment=TA_CENTER
            )
            title_p = Paragraph(process_arabic_text(f"{info.get('title', '')}"), title_text_style)
            
            title_box = Table([[title_p]], colWidths=[320], rowHeights=[45])
            title_box.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), HexColor("#22679B")),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ]))
            story.append(title_box)
            
            story.append(Spacer(1, 80))
            
            info_text_style = ParagraphStyle(
                'InfoText', parent=styles['Normal'], fontName='arial', fontSize=14, leading=font_size + 6, alignment=TA_RIGHT
            )

            student_data_p = [
                Paragraph(process_arabic_text(f"الاسم: {info.get('student_name', '')}"), info_text_style),
                Paragraph(process_arabic_text(f"المرحلة: {info.get('stage', '')}"), info_text_style),
                Paragraph(process_arabic_text(f"الدراسة: {info.get('study_type', '')}"), info_text_style),
                Paragraph(process_arabic_text(f"المادة: {info.get('subject', '')}"), info_text_style),
                Paragraph(process_arabic_text(f"الاشراف: {info.get('professor', '')}"), info_text_style),
            ]
            
            info_box = Table([[student_data_p]], colWidths=[280])
            info_box.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), HexColor('#8BC38A')),
                ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('TOPPADDING', (0,0), (-1,-1), 15),
                ('BOTTOMPADDING', (0,0), (-1,-1), 15),
                ('RIGHTPADDING', (0,0), (-1,-1), 20),
                ('LEFTPADDING', (0,0), (-1,-1), 20),
            ]))
            story.append(info_box)
            
            # فاصل بين الواجهة والمقدمة
            story.append(PageBreak())

        # 2️⃣ بناء قسم المقدمة المعزولة
        if intro_list:
            # عنوان المقدمة بحجم 16
            intro_title_style = ParagraphStyle(
                'IntroHeaderStyle',
                parent=styles['Heading1'],
                fontName=chosen_font,
                fontSize=18,
                textColor=HexColor(theme_colors['primary']),
                alignment=TA_CENTER,
                spaceAfter=15
            )
            story.append(Paragraph(process_arabic_text("المقدمة"), intro_title_style))
            story.append(Spacer(1, 10))
            
            combined_intro_text = "\n".join(intro_list)
            intro_lines = combined_intro_text.split('\n')
            for line in intro_lines:
                if line.strip():
                    align = TA_RIGHT if is_line_arabic(line) else TA_LEFT
                    proc_line = process_arabic_text(line) if is_line_arabic(line) else line
                    
                    intro_body_style = ParagraphStyle(
                        'IntroBodyStyle',
                        parent=styles['Normal'],
                        fontName=chosen_font,
                        fontSize=16,
                        leading=20,
                        alignment=align
                    )
                    story.append(Paragraph(proc_line, intro_body_style))
                else:
                    story.append(Spacer(1, 10))
            
            # فاصل بين المقدمة وبقية نص التقرير
            story.append(PageBreak())

        # 3️⃣ بناء باقي نص التقرير
        main_raw_text = "\n".join(text_list)
        lines = main_raw_text.split('\n')
        for idx, line in enumerate(lines):
            if line.strip():
                if line.strip().startswith("&lt;") and line.strip().endswith("&gt;"):
                    title_content = line.strip().replace("&lt;", "").replace("&gt;", "")
                    if is_line_arabic(title_content):
                        processed_line = process_arabic_text(title_content)
                    else:
                        processed_line = title_content
                    
                    line_style = ParagraphStyle(
                        f'TitleStyle_{idx}',
                        parent=styles['Heading1'],
                        fontName=chosen_font,
                        fontSize=font_size + 5,
                        textColor=HexColor(theme_colors['primary']),
                        leading=font_size + 12,
                        alignment=TA_CENTER,
                        spaceAfter=12,
                        spaceBefore=12
                    )

                    story.append(Paragraph(f"<b>{processed_line}</b>", line_style))
                else:
                    if is_line_arabic(line):
                        alignment = TA_RIGHT
                        processed_line = process_arabic_text(line)
                    else:
                        alignment = TA_LEFT
                        processed_line = line
                    
                    line_style = ParagraphStyle(
                        f'LineStyle_{idx}',
                        parent=styles['Normal'],
                        fontName=chosen_font,
                        fontSize=font_size,
                        leading=font_size + 6,
                        alignment=alignment
                    )
                    story.append(Paragraph(processed_line, line_style))
            else:
                story.append(Spacer(1, 10))
                
        def draw_page_decorations(canvas, doc):
            chat_id = getattr(doc, "chat_id", None)
            theme_colors = getattr(doc, "theme_colors", THEMES["classic"])
        
            canvas.saveState()
            width, height = A4
        
            # خلفية الصفحة
            canvas.setFillColor(HexColor(theme_colors['bg']))
            canvas.rect(0, 0, width, height, fill=True, stroke=False)
        
            # الإطار الخارجي
            canvas.setStrokeColor(HexColor(theme_colors['primary']))
            canvas.setLineWidth(1.5)
            padding = 30
            canvas.rect(padding, padding, width - (padding * 2), height - (padding * 2))
        
            # الإطار الداخلي
            canvas.setStrokeColor(HexColor(theme_colors['secondary']))
            canvas.setLineWidth(0.5)
            canvas.rect(padding + 4, padding + 4, width - ((padding + 4) * 2), height - ((padding + 4) * 2))
        
            # تحديد خط الـ canvas وضمان تسجيله
            font_key = user_data[chat_id].get("font_name", "cairo") if chat_id else "cairo"
            if font_key not in pdfmetrics.getRegisteredFontNames():
                font_key = "Helvetica"
                
            canvas.setFont(font_key, 10)
            canvas.setFillColor(HexColor(theme_colors['primary']))
        
            # إضافة رقم الصفحة
            footer_processed = process_arabic_text(f"صفحة {doc.page}")
            canvas.drawRightString(width - 56, 42, footer_processed)
        
            canvas.restoreState()
    
        if password:
            from reportlab.lib.pdfencrypt import StandardEncryption
            doc.encrypt = StandardEncryption(password, canPrint=1, canModify=0, canCopy=1)
            
        doc.build(story, onFirstPage=draw_page_decorations, onLaterPages=draw_page_decorations)
        
        file_size_mb = round(os.path.getsize(pdf_filename) / (1024 * 1024), 2)
        
        caption_summary = (
            f"✅ <b>تم توليد المستند بنجاح!</b>\n\n"
            f"📊 <b>ملخص المستند الفني:</b>\n"
            f"<blockquote>📄 اسم الملف: {file_name}.pdf</blockquote>\n"
            f"<blockquote>📦 حجم الملف: <code>{file_size_mb} MB</code></blockquote>\n"
            f"<blockquote>📝 عدد الكلمات: {word_count} كلمة || عدد الأسطر: {line_count}</blockquote>\n"
            f"🔒 الحماية بكلمة سر: {'🔒 مفعلة ومقفل' if password else '🔓 غير مقفل (عام)'}\n"
            f"📆 تاريخ الإنشاء: <code>{current_date}</code>\n\n"
            f'<a href="https://t.me/g_z_o_bot">لا تنسى مشاركة البوت مع أصدقائك 🤍</a>'
            )
        
        with open(pdf_filename, 'rb') as pdf_file:
            bot.send_document(
                chat_id, pdf_file, 
                visible_file_name=f"{file_name}.pdf", 
                caption=caption_summary, parse_mode="HTML"
            )
            
        bot.delete_message(chat_id, status_msg.message_id)
        
        if os.path.exists(pdf_filename):
            os.remove(pdf_filename)
            
        # 4️⃣ تنظيف وتفريغ القوائم بعد توليد PDF
        user_data[chat_id]['text_list'] = []
        user_data[chat_id]['intro_list'] = []  # تفريغ قائمة المقدمة
        user_data[chat_id]['mode'] = 'normal'
        
        if not user_data[chat_id].get('saved_report_info'):
            user_data[chat_id]['report_info'] = {}
        else:
            user_data[chat_id]['report_info'] = user_data[chat_id]['saved_report_info'].copy()
        
    except Exception as e:
        bot.edit_message_text(f"❌ حدث خطأ فني أثناء معالجة المستند: {str(e)}", chat_id, status_msg.message_id)
        if os.path.exists(pdf_filename):
            os.remove(pdf_filename)

if __name__ == '__main__':
    print("🤖 البوت النهائي المتكامل يعمل الآن بنجاح وبكافة الأزرار التفاعلية...")
    bot.infinity_polling()
