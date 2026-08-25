import telebot
from telebot import types

TOKEN = "8700020388:AAFADf8SabZu7tkIbg1bv6n5w4su-FhD3go"
bot = telebot.TeleBot(TOKEN)

# 🔐 YOUR MASTER ADMIN TELEGRAM ID (Hidden from other users)
ADMIN_ID = 8818031245  

# 📦 Stock Databases & Analytics
togo_stock = ["2287383833", "2287383639"]
tiktok_stock = ["1928374859", "1928374860"]
all_users = set()

# State Management Dictionaries
user_data = {}   
user_state = {}  
cc_toggle = {}   

# --- KEYBOARD FUNCTIONS ---
def get_main_menu_keyboard(chat_id):
    """Generates the persistent bottom keyboard menu."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("📱 Get Number"), types.KeyboardButton("💰 Withdraw"))
    markup.add(types.KeyboardButton("🎧 Support"))
    
    # Only show the Admin Panel button if the user is the Admin
    if chat_id == ADMIN_ID:
        markup.add(types.KeyboardButton("⚙️ Admin Panel"))
    return markup

# 1. Start command / Bottom Menu
@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    chat_id = message.chat.id
    all_users.add(chat_id)  # Track unique users for admin stats
    user_state[chat_id] = None  
    
    bot.send_message(
        chat_id, 
        f"👋 **Welcome, {message.from_user.first_name}!**\n🆔 ID: `{message.from_user.id}`\n\nChoose an option from the menu below:", 
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(chat_id)
    )

# 2. Bottom Menu Text Handlers
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text
    chat_id = message.chat.id
    
    if text == "❌ Cancel":
        user_state[chat_id] = None
        bot.send_message(chat_id, "🚫 Operation cancelled.", reply_markup=get_main_menu_keyboard(chat_id))
        return

    current_step = user_state.get(chat_id)
    
    # --- WITHDRAWAL & ADMIN STEPS ---
    if current_step == "waiting_bank_acc":
        user_data[chat_id] = {"method": "Bank", "account": text}
        user_state[chat_id] = "waiting_bank_amount"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("❌ Cancel"))
        bot.send_message(chat_id, f"🏦 Account saved: `{text}`\n\n💰 Enter your **withdrawal amount**:", parse_mode="Markdown", reply_markup=markup)
        return

    elif current_step == "waiting_bank_amount":
        data = user_data.get(chat_id, {})
        data["amount"] = text
        user_state[chat_id] = None
        
        bot.send_message(chat_id, "✅ **Withdrawal Request Submitted to Admin for Review!**", parse_mode="Markdown", reply_markup=get_main_menu_keyboard(chat_id))
        
        admin_markup = types.InlineKeyboardMarkup()
        admin_markup.add(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_wd_{chat_id}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_wd_{chat_id}")
        )
        bot.send_message(ADMIN_ID, f"🚨 **New Withdrawal Request!**\n\n👤 User ID: `{chat_id}`\n🏦 Method: Bank Transfer\n📋 Account: `{data.get('account')}`\n💰 Amount: `{text}`", parse_mode="Markdown", reply_markup=admin_markup)
        return

    elif current_step == "waiting_bep20":
        address = text.strip()
        if address.startswith("0x") or address.startswith("Ox"):
            data = user_data.get(chat_id, {})
            data["address"] = address
            user_state[chat_id] = "waiting_usdt_amount"
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("❌ Cancel"))
            bot.send_message(chat_id, f"✅ BEP20 Address saved: `{address}`\n\n💰 Enter your **withdrawal amount**:", parse_mode="Markdown", reply_markup=markup)
        else:
            bot.send_message(chat_id, "❌ **Invalid Address!** Must start with `0x`. Try again or tap Cancel.", parse_mode="Markdown")
        return

    elif current_step == "waiting_usdt_amount":
        data = user_data.get(chat_id, {})
        data["amount"] = text
        user_state[chat_id] = None
        
        bot.send_message(chat_id, "✅ **USDT Withdrawal Submitted to Admin!**", parse_mode="Markdown", reply_markup=get_main_menu_keyboard(chat_id))
        
        admin_markup = types.InlineKeyboardMarkup()
        admin_markup.add(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_wd_{chat_id}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_wd_{chat_id}")
        )
        bot.send_message(ADMIN_ID, f"🚨 **New USDT Withdrawal!**\n\n👤 User ID: `{chat_id}`\n🪙 Provider: {data.get('wallet_type')}\n📍 Address: `{data.get('address')}`\n💰 Amount: `{text}`", parse_mode="Markdown", reply_markup=admin_markup)
        return

    # --- ADMIN STOCK ADDING STEP ---
    elif current_step == "adding_togo_stock" and chat_id == ADMIN_ID:
        togo_stock.append(text.strip())
        user_state[chat_id] = None
        bot.send_message(chat_id, f"✅ Successfully added `{text}` to Togo stock!", parse_mode="Markdown", reply_markup=get_main_menu_keyboard(chat_id))
        return

    # --- MAIN MENU BUTTONS ---
    if text == "📱 Get Number":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🎵 TikTok", callback_data="platform_tiktok"),
            types.InlineKeyboardButton("🇹🇬 Togo", callback_data="platform_togo")
        )
        bot.send_message(chat_id, "Select a platform to get a number:", reply_markup=markup)
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
        
    elif text == "🏦 Bank Transfer":
        user_state[chat_id] = "waiting_bank_acc"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("❌ Cancel"))
        bot.send_message(chat_id, "Please enter your Bank Account details:", reply_markup=markup)
        return
        
    elif text == "🪙 USDT (BEP20)":
        user_data[chat_id] = {"wallet_type": "USDT BEP20"}
        user_state[chat_id] = "waiting_bep20"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("❌ Cancel"))
        bot.send_message(chat_id, "Please enter your USDT BEP20 Address:", reply_markup=markup)
        return

# 3. Keep the bot running
if __name__ == "__main__":
    print("Bot is booting up...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
  
