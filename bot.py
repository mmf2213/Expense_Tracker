import os
import datetime
import telebot
import database as db

# Retrieve token from environment variable or fallback to hardcoded
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8784526850:AAE1lE2496Y06mcqQV2LBOeKnAJOhYNRDt0")
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    help_text = (
        "🤖 *Expense Tracker Bot*\n\n"
        "Commands:\n"
        "• `/balance` - Check live wallet balances\n"
        "• `/exp <amount> <category> <note>` - Log an expense\n"
        "  _Example: `/exp 150 Food Lunch`_\n"
        "• `/inc <amount> <source> <note>` - Log income\n"
        "  _Example: `/inc 2000 Allowance Mom`_\n"
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['balance'])
def check_balance(message):
    wallets = db.get_wallets()
    online_bal = float(wallets.get('online_balance', 0.0))
    offline_bal = float(wallets.get('offline_balance', 0.0))
    total_net = online_bal + offline_bal
    
    response = (
        f"💳 *Online Balance:* ₹{online_bal:,.2f}\n"
        f"💵 *Cash Balance:* ₹{offline_bal:,.2f}\n"
        f"🏦 *Total Liquidity:* ₹{total_net:,.2f}"
    )
    bot.reply_to(message, response, parse_mode="Markdown")

@bot.message_handler(commands=['exp'])
def log_expense(message):
    try:
        args = message.text.split(maxsplit=3)
        if len(args) < 3:
            bot.reply_to(message, "⚠️ Usage: `/exp <amount> <category> [note]`", parse_mode="Markdown")
            return

        amount = float(args[1])
        category = args[2].capitalize()
        note = args[3] if len(args) > 3 else "Logged via Telegram"

        db.add_transaction(
            date=datetime.date.today(),
            category=category,
            amount=amount,
            payment_mode="UPI",
            note=note,
            trans_type="EXPENSE"
        )
        bot.reply_to(message, f"✅ Logged Expense: *₹{amount}* under *{category}*", parse_mode="Markdown")
    except ValueError:
        bot.reply_to(message, "❌ Invalid amount. Please enter a valid number.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['inc'])
def log_income(message):
    try:
        args = message.text.split(maxsplit=3)
        if len(args) < 3:
            bot.reply_to(message, "⚠️ Usage: `/inc <amount> <source> [note]`", parse_mode="Markdown")
            return

        amount = float(args[1])
        category = args[2].capitalize()
        note = args[3] if len(args) > 3 else "Logged via Telegram"

        db.add_transaction(
            date=datetime.date.today(),
            category=category,
            amount=amount,
            payment_mode="UPI",
            note=note,
            trans_type="INCOME"
        )
        bot.reply_to(message, f"✅ Logged Income: *₹{amount}* under *{category}*", parse_mode="Markdown")
    except ValueError:
        bot.reply_to(message, "❌ Invalid amount. Please enter a valid number.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("Bot is starting polling...")
    bot.infinity_polling()
