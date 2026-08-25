import telebot
from telebot import types

TOKEN = "8700020388:AAFADf8SabZu7tkIbg1bv6n5w4su-FhD3go"
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 8818031245  

# Channels required for users to join before using the bot (leave empty [] if none for now)
REQUIRED_CHANNELS = [] 

# Comprehensive Stock Database (Add your initial numbers here or via Admin Panel)
stock_db = {
    "whatsapp_togo": ["2287383833", "2287383639", "2287383844"],
    "whatsapp_nigeria": ["2348012345678", "2348098765432"],
    "tiktok_global": ["1928374859", "1928374860"],
    "telegram_global": ["447911123456"]
}

all_users = set()
referrals = {}
user_state = {}  
user_data = {}

def check_user_subscription(user_id):
    if not REQUIRED_CHANNELS:
        return True
    for channel in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception:
            pass
    return True

def get_main_menu_keyboard(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("🚀 Get Number"), types.KeyboardButton("👥 Referral"))
    markup.add(types.KeyboardButton("💰 Withdraw"), types.KeyboardButton("🎧 Support"))
    if chat_id == ADMIN_ID:
        markup.add(types.KeyboardButton("⚙️ Admin Panel"))
    return markup

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    chat_id = message.chat.id
    all_users.add(chat_id)
    user_state[chat_id] = None
    
    text_parts = message.text.split()
    if len(text_parts) > 1 and text_parts[1].startswith("ref_"):
        referrer_id = text_parts[1].replace("ref_", "")
        if referrer_id.isdigit():
            ref_id = int(referrer_id)
            if ref_id != chat_id:
                referrals[chat_id] = ref_id

    if not check_user_subscription(chat_id):
        markup = types.InlineKeyboardMarkup()
        for ch in REQUIRED_CHANNELS:
            markup.add(types.InlineKeyboardButton(f"📢 Join {ch}", url=f"https://t.me/{ch.replace('@','')}"))
        markup.add(types.InlineKeyboardButton("🔄 I have joined", callback_data="check_sub"))
        bot.send_message(chat_id, "❌ **You must join our update channels before using this bot!**", parse_mode="Markdown", reply_markup=markup)
        return

    bot.send_message(
        chat_id, 
        f"👋 **Welcome, {message.from_user.first_name}!**\n\nChoose an option from the menu below:", 
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(chat_id)
    )

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text
    chat_id = message.chat.id
    
    if text == "❌ Cancel":
        user_state[chat_id] = None
        bot.send_message(chat_id, "🚫 Operation cancelled.", reply_markup=get_main_menu_keyboard(chat_id))
        return

    current_step = user_state.get(chat_id)

    # Admin: Adding Stock Flow
    if current_step and current_step.startswith("adding_stock_") and chat_id == ADMIN_ID:
        target_key = current_step.replace("adding_stock_", "")
        new_items = [item.strip() for item in text.split("\n") if item.strip()]
        
        if target_key not in stock_db:
            stock_db[target_key] = []
        stock_db[target_key].extend(new_items)
        user_state[chat_id] = None
        
        total_left = len(stock_db[target_key])
        bot.send_message(
            chat_id, 
            f"✅ Successfully added {len(new_items)} numbers!\n📦 Total stock in `{target_key}`: `{total_left}`", 
            parse_mode="Markdown", 
            reply_markup=get_main_menu_keyboard(chat_id)
        )
        return

    # Admin: Creating Custom Category Flow
    if current_step == "creating_custom_category" and chat_id == ADMIN_ID:
        parts = [p.strip().lower() for p in text.split(",")]
        if len(parts) == 2:
            custom_key = f"{parts[0]}_{parts[1]}"
            user_state[chat_id] = f"adding_stock_{custom_key}"
            bot.send_message(chat_id, f"📥 Now send the numbers for `{custom_key}` (you can paste multiple numbers line by line):", parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "❌ Format incorrect. Please use `platform,country` (e.g., `whatsapp,nigeria`)", parse_mode="Markdown")
        return

    # User: Withdrawal Flow
    if current_step == "waiting_for_account":
        user_data[chat_id] = {"account_info": text}
        user_state[chat_id] = "waiting_for_withdrawal_amount"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("❌ Cancel"))
        bot.send_message(chat_id, f"📥 Account saved: `{text}`\n\n💰 Enter the **amount** to withdraw:", parse_mode="Markdown", reply_markup=markup)
        return

    elif current_step == "waiting_for_withdrawal_amount":
        user_state[chat_id] = None
        bot.send_message(chat_id, "✅ **Withdrawal request submitted successfully to admin!**", parse_mode="Markdown", reply_markup=get_main_menu_keyboard(chat_id))
        return

    # Main Menu Navigation
    if text == "🚀 Get Number":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🎵 TikTok", callback_data="plat_tiktok"),
            types.InlineKeyboardButton("📘 Facebook", callback_data="plat_facebook"),
            types.InlineKeyboardButton("✈️ Telegram", callback_data="plat_telegram"),
            types.InlineKeyboardButton("💬 WhatsApp", callback_data="plat_whatsapp")
        )
        bot.send_message(chat_id, "📲 **Select a platform** to get numbers:", parse_mode="Markdown", reply_markup=markup)
        return
        
    elif text == "👥 Referral":
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start=ref_{chat_id}"
        my_refs_count = sum(1 for uid, ref in referrals.items() if ref == chat_id)
        bot.send_message(
            chat_id,
            f"👥 **Referral Program**\n\nShare your link with friends to invite them:\n\n🔗 `{ref_link}`\n\n📊 Total Referred: `{my_refs_count}` users",
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(chat_id)
        )
        return

    elif text == "🎧 Support":
        bot.send_message(chat_id, "For assistance, please contact our support admin: @sheyivibescartel")
        return
        
    elif text == "💰 Withdraw":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(types.KeyboardButton("🏦 Bank Transfer"), types.KeyboardButton("🪙 USDT (BEP20)"))
        markup.add(types.KeyboardButton("❌ Cancel"))
        bot.send_message(chat_id, "Select your preferred withdrawal method:", reply_markup=markup)
        return

    elif text == "🏦 Bank Transfer" or text == "🪙 USDT (BEP20)":
        user_state[chat_id] = "waiting_for_account"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("❌ Cancel"))
        bot.send_message(chat_id, f"📝 You selected **{text}**.\n\nPlease send your account details or wallet address:", parse_mode="Markdown", reply_markup=markup)
        return

    elif text == "⚙️ Admin Panel" and chat_id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("➕ Add New Country/Platform Stock", callback_data="adm_create_new"))
        for key in stock_db.keys():
            markup.add(types.InlineKeyboardButton(f"➕ Add Stock to {key.replace('_', ' ').title()}", callback_data=f"adm_add_{key}"))
        
        total_stock = sum(len(v) for v in stock_db.values())
        bot.send_message(
            chat_id, 
            f"👑 **Admin Panel Dashboard**\n\n👥 Total Users: `{len(all_users)}`\n📦 Total Stock Items: `{total_stock}`\n\nChoose an action:", 
            parse_mode="Markdown",
            reply_markup=markup
        )
        return

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    data = call.data

    if data == "check_sub":
        if check_user_subscription(chat_id):
            bot.answer_callback_query(call.id, "Verification successful!")
            bot.send_message(chat_id, "✅ Verified successfully! Welcome.", reply_markup=get_main_menu_keyboard(chat_id))
        else:
            bot.answer_callback_query(call.id, "You haven't joined all channels yet!", show_alert=True)
        return

    if data.startswith("plat_"):
        platform = data.replace("plat_", "")
        markup = types.InlineKeyboardMarkup(row_width=1)
        matching_keys = [k for k in stock_db.keys() if k.startswith(platform)]
        
        if not matching_keys:
            bot.answer_callback_query(call.id, "No stock available for this platform yet.", show_alert=True)
            return

        for key in matching_keys:
            parts = key.split("_", 1)
            country_name = parts[1].upper() if len(parts) > 1 else "GLOBAL"
            count = len(stock_db[key])
            markup.add(types.InlineKeyboardButton(f"🌍 {country_name} — TOTAL : {count} Numbers", callback_data=f"get_{key}"))
        
        bot.edit_message_text(f"🌍 Choose a region for **{platform.upper()}**:", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif data.startswith("get_"):
        stock_key = data.replace("get_", "")
        if stock_key in stock_db and len(stock_db[stock_key]) > 0:
            take_count = min(3, len(stock_db[stock_key]))
            assigned_numbers = stock_db[stock_key][:take_count]
            del stock_db[stock_key][:take_count]
            
            remaining_count = len(stock_db[stock_key])
            nums_text = "\n".join([f"`{num}`" for num in assigned_numbers])
            
            bot.answer_callback_query(call.id, f"Successfully dispensed {take_count} numbers!")
            bot.send_message(
                chat_id, 
                f"🎉 **Here are your numbers ({stock_key}):**\n{nums_text}\n\n📦 **Remaining Stock:** `{remaining_count}` numbers left.", 
                parse_mode="Markdown"
            )
        else:
            bot.answer_callback_query(call.id, "Sorry, this stock category is empty!", show_alert=True)

    elif data == "adm_create_new" and chat_id == ADMIN_ID:
        user_state[chat_id] = "creating_custom_category"
        bot.send_message(chat_id, "✍️ Send the platform and country separated by a comma.\nExample: `whatsapp,nigeria` or `tiktok,usa`", parse_mode="Markdown")

    elif data.startswith("adm_add_") and chat_id == ADMIN_ID:
        target_key = data.replace("adm_add_", "")
        user_state[chat_id] = f"adding_stock_{target_key}"
        bot.send_message(chat_id, f"📥 Send the new numbers to add to `{target_key}`\n*(You can paste your bulk list here safely)*:", parse_mode="Markdown")

if __name__ == "__main__":
    print("Bot is booting up...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
        
