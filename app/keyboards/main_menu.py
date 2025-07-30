# app/keyboards/main_menu.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.i18n import t

# Адаптивные эмодзи для тем
EMOJI = {
    "light": {
        "teacher_notes": "📝",
        "teacher_add": "➕",
        "teacher_ticket": "🛠",
        "teacher_media": "📹",
        "admin_broadcast": "📢",
        "admin_tickets": "🗂",
        "admin_media": "🎬",
        "par_tasks": "📋",
        "par_cert": "📝",
        "stu_tasks": "📋",
        "stu_help": "🆘",
        "psy_inbox": "📋",
        "theme": "🌗",
        "back": "◀️",
        "stub": "📊",
    },
    "dark": {
        "teacher_notes": "📜",
        "teacher_add": "➕",
        "teacher_ticket": "🔧",
        "teacher_media": "🎥",
        "admin_broadcast": "📢",
        "admin_tickets": "📁",
        "admin_media": "🎬",
        "par_tasks": "📋",
        "par_cert": "📄",
        "stu_tasks": "📋",
        "stu_help": "🆘",
        "psy_inbox": "📋",
        "theme": "☀️",
        "back": "◀️",
        "stub": "📊",
    },
}

# Кнопка возврата в главное меню
def get_back_btn(nonce: str = "") -> InlineKeyboardButton:
    return InlineKeyboardButton(text="◀️ Главное меню", callback_data=f"{nonce}:back_to_main")

def menu(role: str, lang: str = "ru", theme: str = "light", nonce: str = "") -> InlineKeyboardMarkup:
    e = EMOJI[theme]  # Получаем эмодзи для текущей темы
    
    if role == "super":      # Демо-учётка → меню переключения ролей
        kb = [
            [InlineKeyboardButton(text="👩‍🏫 Учитель", callback_data=f"{nonce}:switch_teacher"),
             InlineKeyboardButton(text="🏛 Админ", callback_data=f"{nonce}:switch_admin")],
            [InlineKeyboardButton(text="📈 Директор", callback_data=f"{nonce}:switch_director"),
             InlineKeyboardButton(text="👪 Родитель", callback_data=f"{nonce}:switch_parent")],
            [InlineKeyboardButton(text="👨‍🎓 Ученик", callback_data=f"{nonce}:switch_student"),
             InlineKeyboardButton(text="🧑‍⚕️ Психолог", callback_data=f"{nonce}:switch_psych")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=kb)

    # «обычные» меню-заглушки
    if role == "teacher":
        kb = [
            [InlineKeyboardButton(text=f"{e['teacher_notes']} {t('teacher.menu_notes', lang)}", callback_data=f"{nonce}:teacher_notes")],
            [InlineKeyboardButton(text=f"{e['teacher_add']} {t('teacher.menu_add', lang)}", callback_data=f"{nonce}:teacher_add")],
            [InlineKeyboardButton(text=f"{e['teacher_ticket']} {t('teacher.ticket_prompt', lang)}", callback_data=f"{nonce}:teacher_ticket")],
            [InlineKeyboardButton(text=f"{e['teacher_media']} Заявка в медиацентр", callback_data=f"{nonce}:teacher_media")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=kb)
    
    if role == "admin":
        kb = [
            [InlineKeyboardButton(text=f"{e['admin_broadcast']} Рассылка", callback_data=f"{nonce}:admin_broadcast")],
            [InlineKeyboardButton(text=f"{e['admin_tickets']} Заявки IT", callback_data=f"{nonce}:admin_tickets")],
            [InlineKeyboardButton(text=f"{e['admin_media']} Медиацентр", callback_data=f"{nonce}:admin_media")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=kb)
    
    if role == "parent":
        kb = [
            [InlineKeyboardButton(text=f"{e['par_tasks']} Задания ребёнка", callback_data=f"{nonce}:par_tasks")],
            [InlineKeyboardButton(text=f"{e['par_cert']} Заказать справку", callback_data=f"{nonce}:par_cert")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=kb)
    
    if role == "director":
        kb = [
            [InlineKeyboardButton(text=f"{e['stub']} KPI", callback_data=f"{nonce}:stub")],
            [InlineKeyboardButton(text="⏱ Поручения", callback_data=f"{nonce}:director_tasks")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=kb)
    
    if role == "student":
        kb = [
            [InlineKeyboardButton(text=f"{e['stu_tasks']} Задания", callback_data=f"{nonce}:stu_tasks")],
            [InlineKeyboardButton(text=f"{e['stu_help']} Психолог", callback_data=f"{nonce}:stu_help")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=kb)
    
    if role == "psych":
        kb = [
            [InlineKeyboardButton(text=f"{e['psy_inbox']} {t('psych.menu_requests', lang)}", callback_data=f"{nonce}:psy_inbox")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=kb)
    
    mapping = {}
    kb = [[InlineKeyboardButton(text=text, callback_data=f"{nonce}:stub")]
          for text in sum(mapping.get(role, []), [])]
    
    # Добавляем кнопку переключения темы во все меню
    kb.append([InlineKeyboardButton(text=f"{e['theme']} Тема", callback_data="switch_theme")])
    
    return InlineKeyboardMarkup(inline_keyboard=kb) 