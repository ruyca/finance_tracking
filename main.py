import logging
import os 
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, \
                         filters, ConversationHandler, MessageHandler
from dotenv import load_dotenv
from datetime import datetime

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ENV VARIABLES
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT')
USER_ID = os.getenv('USER_ID') # my own user id

# KEYBOARDS
OPTIONS_KEYBOARD = ReplyKeyboardMarkup([
    ["💸 Expense"], ["💰 Revenue"],
    ["🤝 Lend"], ["⚖️ Balance"]
])
EXPENSES_KEYBOARD = ReplyKeyboardMarkup([
    ["🏠 Housing"], ["🏬 Pantry"], ["🚋 Transportation"], ["🍎 Healthcare"],  # Essentials
    ["🍔 Takeout/eating out"], ["🍿 Entertainment"], ["🛍️ Shopping"], ["✈️ Lifestyle"], # Leisure
    ["💰 Savings & Investments"] # Financial Growth
])
REVENUE_KEYBOARD = ReplyKeyboardMarkup([
    ["💻 Payroll"], ["🔎 Bonus"], ["👾 Other"]
])

# STATES
AMOUNT, CATEGORY = range(2) # states for the /expense flow
AMOUNT2, CATEGORY2 = range(2, 4) # states for /revenue flow


# SAVE EXPENSE FUNCTION #
def save_expense(amount, category):
    purchase_time = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    stripped = category.split(" ", 1)[-1]

    with open("expenses.txt", "a", encoding="utf-8") as file: 
        file.write(f"{purchase_time} - ${amount} - {stripped}\n")

# SAVE REVENUE FUNCTION # 
def save_revenue(amount, category):
    purchase_time = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    stripped = category.split(" ", 1)[-1]

    with open("revenues.txt", "a", encoding="utf-8") as file: 
        file.write(f"{purchase_time} - ${amount} - {stripped}\n")


# Decorator that restricts functions by user_id
def restricted(original_function):
    async def new_function(update, context):
        if update.effective_user.id == int(USER_ID): 
            return await original_function(update, context)
        else: 
            return await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Operation not allowed"
            )
    return new_function

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome Ruy!",
        reply_markup=OPTIONS_KEYBOARD
    )

@restricted
async def ask_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Enter the amount: "
    )

    return AMOUNT

@restricted
async def receive_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amount = update.message.text.replace(',', '')
    context.user_data['expense_amount'] = amount
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="Enter category: ",
        reply_markup=EXPENSES_KEYBOARD
    )
    
    return CATEGORY

@restricted
async def receive_expense_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Expense recorded!"
    )
    amount = context.user_data['expense_amount']
    category = update.message.text
    print(f"Amount: {amount}, Category: {category}")
   
    save_expense(amount, category)

    return ConversationHandler.END

@restricted
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Operation cancelled."
    )
    return ConversationHandler.END


@restricted
async def ask_revenue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Enter the amount: "
    )

    return AMOUNT2

@restricted
async def receive_revenue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amount = update.message.text.replace(',', '')
    context.user_data['revenue_amount'] = amount
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="Enter category: ",
        reply_markup=REVENUE_KEYBOARD
    )
    
    return CATEGORY2


@restricted
async def receive_revenue_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Revenue recorded!"
    )
    amount = context.user_data['revenue_amount']
    category = update.message.text
    print(f"Amount: {amount}, Category: {category}")
   
    save_revenue(amount, category)

    return ConversationHandler.END


if __name__ == '__main__':

    app = ApplicationBuilder().token(TOKEN).build()

    # Define handlers
    start_handler = CommandHandler('start', start)

    # CONVERSATION HANDLERS
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text(["💸 Expense"]), ask_expense)],
        states={
            AMOUNT: [MessageHandler(filters.Regex(r"^[\d,]+(\.\d+)?$"), receive_expense)],
            CATEGORY: [MessageHandler(filters.Text(
                    ["🏠 Housing", "🏬 Pantry", "🚋 Transportation", "🍎 Healthcare", "🍔 Takeout/eating out", 
                     "🍿 Entertainment", "🛍️ Shopping", "✈️ Lifestyle","💰 Savings & Investments"]
            ), receive_expense_category)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    conv_handler2 = ConversationHandler(
        entry_points=[MessageHandler(filters.Text(["💰 Revenue"]), ask_revenue)],
        states = {
            AMOUNT2: [MessageHandler(filters.Regex(r"^[\d,]+(\.\d+)?$"), receive_revenue)],
            CATEGORY2: [MessageHandler(filters.Text(["💻 Payroll", "🔎 Bonus","👾 Other"]), receive_revenue_category)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Add handlers
    app.add_handler(start_handler)
    app.add_handler(conv_handler)
    app.add_handler(conv_handler2)



    app.run_polling()