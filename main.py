import telebot
from telebot import types

TOKEN = "8700020388:AAFADf8SabZu7tkIbg1bv6n5w4su-FhD3go"
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 8818031245  

# Live Stock Database (Tracks exact counts automatically)
stock_db = {
    "tiktok_global": ["1928374859", "1928374860", "1928374861", "1928374862"],
    "whatsapp_togo": ["2287383833", "2287383639", "2287383844", "2287383855"],
    "facebook_usa": ["15552345678", "15552345679", "15552345680"],
    "telegram_global": ["9995551234", "9995551235", "9995551236"]
}

all_users = set()
referrals = {} # Tracks who referred who
user_state = {}  

def get_main_menu_keyboard(chat_id):
    """Permanent menu keyboard at the bottom like the reference bot"""
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
    
    # Check for referral link usage (e.g. /start ref_8818031245)
    text_parts = message.text.split()
    if len(text_parts) > 1 and text_parts[1].startswith("ref_"):
        referrer_id = text_parts[1].replace("ref_", "")
        if referrer_id.isdigit():
            ref_id = int(referrer_id)
            if ref_id != chat_id:
                referrals[chat_id] = ref_id

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

    # --- ADMIN: ADDING STOCK DYNAMICALLY ---
    if current_step and current_step.startswith("adding_stock_") and chat_id == ADMIN_ID:
        key = current_step.replace("adding_stock_", "")
        if key not in stock_db:
            stock_db[key] = []
        
        # Allows admin to paste multiple numbers separated by lines/commas
        new_items = [item.strip() for item in text.split("\n") if item.strip()]
        stock_db[key].extend(new_items)
        user_state[chat_id] = None
        
        total_left = len(stock_db[key])
        bot.send_message(
            chat_id, 
            f"✅ Added {len(new_items)} numbers!\n📦 Total stock left in `{key}`: `{total_left}`", 
            parse_mode="Markdown", 
            reply_markup=get_main_menu_keyboard(chat_id)
        )
        return

    # --- MAIN MENU BUTTON HANDLERS ---
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
        # Generate unique referral link for the user
        bot_info = bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start=ref_{chat_id}"
        my_refs_count = sum(1 for uid, ref in referrals.items() if ref == chat_id)
        
        bot.send_message(
            chat_id,
            f"👥 **Referral Program**\n\nShare your link with friends and earn rewards!\n\n🔗 Your Link:\n`{ref_link}`\n\n📊 Total Users Referred: `{my_refs_count}`",
            parse_mode="Markdown",
            reply_markup=get_main_menu_keyboard(chat_id)
        )
        return

    elif text == "🎧 Support":
        bot.send_message(chat_id, "For assistance, please contact our support admin: @sheyivibescartel")
        return
        
    elif text == "💰 Withdraw":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("🏦 Bank Transfer"), types.KeyboardButton("🪙 USDT (BEP20)"))
        markup.add(types.KeyboardButton("❌ Cancel"))
        bot.send_message(chat_id, "Select your preferred withdrawal method:", reply_markup=markup)
        return

    elif text == "⚙️ Admin Panel" and chat_id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup(row_width=2)
        for key in stock_db.keys():
            markup.add(types.InlineKeyboardButton(f"➕ Add {key.replace('_', ' ').title()}", callback_data=f"adm_add_{key}"))
        
        total_stock = sum(len(v) for v in stock_db.values())
        bot.send_message(
            chat_id, 
            f"👑 **Admin Panel Dashboard**\n\n👥 Total Users: `{len(all_users)}`\n📦 Total Stock Items Across All Categories: `{total_stock}`\n\nChoose a category to add stock:", 
            parse_mode="Markdown",
            reply_markup=markup
        )
        return

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    data = call.data

    if data.startswith("plat_"):
        platform = data.replace("plat_", "")
        markup = types.InlineKeyboardMarkup(row_width=1)
        matching_keys = [k for k in stock_db.keys() if k.startswith(platform)]
        
        if not matching_keys:
            bot.answer_callback_query(call.id, "No stock available for this platform.")
            return

        for key in matching_keys:
            country_name = key.split("_")[1].upper()
            count = len(stock_db[key]) # Exact live count check
            markup.add(types.InlineKeyboardButton(f"🇳🇬/🌍 {country_name} — TOTAL : {count} Numbers", callback_data=f"get_{key}"))
        
        bot.edit_message_text(f"🌍 Choose a region for **{platform.upper()}**:", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif data.startswith("get_"):
        stock_key = data.replace("get_", "")
        if stock_key in stock_db and len(stock_db[stock_key]) > 0:
            
            # --- DISPENSE UP TO 3 NUMBERS AT A TIME ---
            take_count = min(3, len(stock_db[stock_key]))
            assigned_numbers = stock_db[stock_key][:take_count] # Grab 3
            del stock_db[stock_key][:take_count] # Remove them from stock permanently
            
            remaining_count = len(stock_db[stock_key]) # Exact remaining count calculation
            
            nums_text = "\n".join([f"`{num}`" for num in assigned_numbers])
            bot.answer_callback_query(call.id, f"Successfully dispensed {take_count} numbers!")
            bot.send_message(
                chat_id, 
                f"🎉 **Here are your numbers ({stock_key}):**\n{nums_text}\n\n📦 **Remaining Stock:** `{remaining_count}` numbers left.", 
                parse_mode="Markdown"
            )
        else:
            bot.answer_callback_query(call.id, "Sorry, this stock is completely empty!")
            bot.send_message(chat_id, "❌ Sorry, this stock category is currently out of stock.")

    elif data.startswith("adm_add_") and chat_id == ADMIN_ID:
        target_key = data.replace("adm_add_", "")
        user_state[chat_id] = f"adding_stock_{target_key}"
        bot.send_message(chat_id, f"📥 Send the new numbers to add to `{target_key}`\n*(You can send multiple numbers separated by lines)*:", parse_mode="Markdown")

if __name__ == "__main__":
    print("Bot is booting up...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
    
