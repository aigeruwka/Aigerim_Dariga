import telebot
import json
import os
import schedule
import time
import threading

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

API_TOKEN = "7736850221:AAH60dcdHmjLSNDdZhpSd-b9dugAMkfudmI"
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
                                     "/notifyoff - Disable notifications\n"
                                     "/reset - Delete all data")

@bot.message_handler(commands=['log'])
def log(message):
    bot.send_message(message.chat.id, "Please enter your entry in the format: income|budget|expense category amount\nExample: income salary 150000, budget groceries 50000, expense food 1500")

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

@bot.message_handler(commands=['reset'])
def reset_data(message):
    data = load_data()
    user_id = str(message.from_user.id)
    
    if user_id in data:
        # Clear all financial data but keep settings
        data[user_id] = {
            'income': {},
            'budget': {},
            'expense': {},
            'notifications': data[user_id].get('notifications', False)
        }
        save_data(data)
        bot.reply_to(message, "♻️ All your financial data has been reset!\n"
                             "Income, expenses and budgets were cleared.\n"
                             "Notification settings were preserved.")
    else:
        bot.reply_to(message, "ℹ️ No data to reset - you're starting fresh!")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    parts = message.text.split()
    if message.text.startswith('/'):
        return
    if len(parts) != 3 or parts[0] not in ['income', 'budget', 'expense']:
        bot.send_message(message.chat.id, "Invalid format. Use: income|budget|expense category amount\nExample: expense food 1500")
        return

    entry_type, category, amount_str = parts
    user_id = str(message.from_user.id)

    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError("Amount must be positive")
    except ValueError:
        bot.send_message(message.chat.id, "Amount must be a positive number.")
        return

    data = load_data()
    if user_id not in data:
        data[user_id] = {'income': {}, 'budget': {}, 'expense': {}}

    # Для расходов делаем отрицательное значение (опционально)
    processed_amount = -abs(amount) if entry_type == 'expense' else amount

    # Накопление суммы (а не перезапись)
    data[user_id][entry_type][category] = data[user_id][entry_type].get(category, 0) + amount

    save_data(data)
    bot.send_message(message.chat.id, f"{entry_type.capitalize()} in category '{category}' of {amount} recorded successfully ✅")


def send_daily_summary():
    data = load_data()
    for user_id, user_data in data.items():
        if user_data.get("notifications", False):
            # Суммируем все доходы по категориям
            total_income = sum(user_data.get("income", {}).values())
            
            # Суммируем все бюджеты по категориям (если нужно)
            total_budget = sum(user_data.get("budget", {}).values())
            
            # Если у вас есть расходы, их нужно хранить аналогично доходам
            # Например: "expenses": {"food": 500, "transport": 300}
            total_expenses = sum(user_data.get("expenses", {}).values())
            
            balance = total_income - total_expenses

            message = (
                f"📊 Daily Summary\n"
                f"💸 Total Income: {total_income}₸\n"
                f"📝 Total Budget: {total_budget}₸\n"
                f"💰 Total Expenses: {total_expenses}₸\n"
                f"📉 Balance: {balance}₸"
            )

            try:
                bot.send_message(chat_id=user_id, text=message)
            except Exception as e:
                print(f"Failed to send message to {user_id}: {e}")

def run_scheduler():
    schedule.every().day.at("09:00").do(send_daily_summary)
    while True:
        schedule.run_pending()
        time.sleep(60)
threading.Thread(target=run_scheduler, daemon=True).start()

bot.polling(none_stop=True)