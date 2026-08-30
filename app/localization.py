from typing import Dict

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "fa": {
        "welcome": "سلام! به Hushly خوش آمدید.\nشما می‌توانید لینک ناشناس خود را بسازید و پیام دریافت کنید.",
        "choose_language": "زبان خود را انتخاب کنید / Choose your language:",
        "main_menu": "منوی اصلی",
        "messages": "💌 پیام‌ها",
        "my_links": "🔗 لینک‌های من",
        "statistics": "📊 آمار",
        "quick_replies": "⚡ پاسخ‌های سریع",
        "settings": "⚙️ تنظیمات",
        "help": "❓ راهنما",
        "admin": "پنل مدیریت",
        "create_link": "ساخت لینک جدید",
        "no_links": "شما هنوز هیچ لینکی ندارید.",
        "link_created": "لینک شما با موفقیت ساخته شد!\n\nلینک تلگرام:\n{telegram_url}\n\nلینک وب:\n{web_url}",
        "send_message_prompt": "لطفاً پیام ناشناس خود را برای {name} بنویسید:",
        "message_sent": "پیام شما با موفقیت ارسال شد! ✉️",
        "message_received": "شما یک پیام ناشناس جدید دارید! 💌\n\n{content}",
        "reply_button": "💬 پاسخ",
        "block_button": "🚫 مسدود کردن",
        "report_button": "⚠️ گزارش",
        "react_button": "واکنش",
        "rate_limited": "شما بیش از حد درخواست ارسال کرده‌اید. لطفاً کمی صبر کنید.",
        "user_blocked": "کاربر مسدود شد.",
        "message_reported": "پیام گزارش شد. ممنون از همکاری شما.",
        "reply_prompt": "لطفاً پاسخ خود را بنویسید:",
        "reply_sent": "پاسخ شما ارسال شد.",
        "error_occurred": "خطایی رخ داد. لطفاً دوباره تلاش کنید.",
        "web_entry_title": "ارسال پیام ناشناس به {name}",
        "web_entry_button": "باز کردن در تلگرام",
        "invalid_token": "لینک نامعتبر است یا منقضی شده است."
    },
    "en": {
        "welcome": "Hello! Welcome to Hushly.\nYou can create your anonymous link and receive messages.",
        "choose_language": "زبان خود را انتخاب کنید / Choose your language:",
        "main_menu": "Main Menu",
        "messages": "💌 Messages",
        "my_links": "🔗 My Links",
        "statistics": "📊 Statistics",
        "quick_replies": "⚡ Quick Replies",
        "settings": "⚙️ Settings",
        "help": "❓ Help",
        "admin": "Admin Panel",
        "create_link": "Create New Link",
        "no_links": "You don't have any links yet.",
        "link_created": "Your link has been created successfully!\n\nTelegram link:\n{telegram_url}\n\nWeb link:\n{web_url}",
        "send_message_prompt": "Please write your anonymous message for {name}:",
        "message_sent": "Your message has been sent successfully! ✉️",
        "message_received": "You have a new anonymous message! 💌\n\n{content}",
        "reply_button": "💬 Reply",
        "block_button": "🚫 Block",
        "report_button": "⚠️ Report",
        "react_button": "React",
        "rate_limited": "You have sent too many requests. Please wait a moment.",
        "user_blocked": "User has been blocked.",
        "message_reported": "Message reported. Thank you.",
        "reply_prompt": "Please write your reply:",
        "reply_sent": "Your reply has been sent.",
        "error_occurred": "An error occurred. Please try again.",
        "web_entry_title": "Send an anonymous message to {name}",
        "web_entry_button": "Open in Telegram",
        "invalid_token": "The link is invalid or has expired."
    }
}

def get_text(lang: str, key: str, **kwargs) -> str:
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    text = lang_dict.get(key, TRANSLATIONS["en"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text
