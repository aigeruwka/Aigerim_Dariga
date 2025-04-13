import telebot
import json
import os

data_file = 'data.json'
if not os.path.exists(data_file):
    with open(data_file, 'w') as f:
        json.dump({}, f)

def load_data():
    with open(data_file, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=4)

API_TOKEN = "7736850221:AAFlrTyvkz3uc0K8DZIPmCXCQ7mAAZ_H53M"
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Welcome! I'm your finance assistant bot. Use /help to see what I can do.")

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, "Available commands:\n"
                                     "/start - Welcome message\n"
                                     "/help - List of commands\n"
                                     "/log - Log income or budget in format: income|budget category amount\n"
                                     "/summary - View your balance and budgets\n"
                                     "/config - Show your current categories\n"
                                     "/notifyon - Enable notifications\n"
                                     "/notifyoff - Disable notifications")

@bot.message_handler(commands=['log'])
def log(message):
    bot.send_message(message.chat.id, "Please enter your entry in the format: income|budget category amount\nExample: income salary 150000 or budget groceries 50000")

@bot.message_handler(commands=['summary'])
def summary(message):
    data = load_data()
    user_id = str(message.from_user.id)
    if user_id not in data:
        bot.send_message(message.chat.id, "You have no data logged yet.")
        return

    user_data = data[user_id]
    incomes = user_data.get("income", {})
    budgets = user_data.get("budget", {})
    income_total = sum(incomes.values())
    budget_total = sum(budgets.values())

    summary_msg = f"\n💰 Income: {income_total}\n🗂 Budgets: {budget_total}\n"
    summary_msg += "\nIncome by category:\n"
    for category, amount in incomes.items():
        summary_msg += f"- {category}: {amount}\n"

    summary_msg += "\nBudgets by category:\n"
    for category, amount in budgets.items():
        summary_msg += f"- {category}: {amount}\n"

    bot.send_message(message.chat.id, summary_msg)

@bot.message_handler(commands=['config'])
def config(message):
    data = load_data()
    user_id = str(message.from_user.id)
    if user_id not in data:
        bot.send_message(message.chat.id, "You have no configuration yet.")
        return

    user_data = data[user_id]
    income_categories = list(user_data.get("income", {}).keys())
    budget_categories = list(user_data.get("budget", {}).keys())

    response = "Your current configuration:\n"
    response += f"Income categories: {', '.join(income_categories) if income_categories else 'None'}\n"
    response += f"Budget categories: {', '.join(budget_categories) if budget_categories else 'None'}"

    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['notifyon'])
def notify_on(message):
    data = load_data()
    user_id = str(message.from_user.id)
    if user_id not in data:
        data[user_id] = {}
    data[user_id]['notifications'] = True
    save_data(data)
    bot.send_message(message.chat.id, "Notifications enabled ✅")

@bot.message_handler(commands=['notifyoff'])
def notify_off(message):
    data = load_data()
    user_id = str(message.from_user.id)
    if user_id not in data:
        data[user_id] = {}
    data[user_id]['notifications'] = False
    save_data(data)
    bot.send_message(message.chat.id, "Notifications disabled ❌")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    parts = message.text.split()
    if len(parts) != 3 or parts[0] not in ['income', 'budget']:
        bot.send_message(message.chat.id, "Invalid format. Use: income|budget category amount\nExample: income salary 150000")
        return

    entry_type, category, amount = parts
    user_id = str(message.from_user.id)
    try:
        amount = float(amount)
    except ValueError:
        bot.send_message(message.chat.id, "Amount must be a number.")
        return

    data = load_data()
    if user_id not in data:
        data[user_id] = {}

    if entry_type not in data[user_id]:
        data[user_id][entry_type] = {}

    if category in data[user_id][entry_type]:
        data[user_id][entry_type][category] += amount
    else:
        data[user_id][entry_type][category] = amount

    save_data(data)
    bot.send_message(message.chat.id, f"{entry_type.capitalize()} in category '{category}' of {amount} recorded successfully ✅")

bot.polling(none_stop=True)
