import logging
import os 
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, \
                         filters, ConversationHandler, MessageHandler
from dotenv import load_dotenv

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
CATEGORY_KEYBOARD = ReplyKeyboardMarkup([
    ["🏠Housing"], ["🏬Pantry"], ["🚋Transportation"], ["🍎Healthcare"],  # Essentials
    ["🍔Takeout/eating out"], ["🍿Entertainment"], ["🛍️Shopping"], ["✈️Lifestyle"], # Leisure
    ["💰Savings & Investments"] # Financial Growth
])

# STATES
AMOUNT, CATEGORY = range(2) # states for the /expense flow

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
async def ask_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Enter the amount: "
    )

    return AMOUNT

@restricted
async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    context.user_data['amount'] = update.message.text

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="Enter category: ",
        reply_markup=CATEGORY_KEYBOARD
    )
    

    return CATEGORY

@restricted
async def receive_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Expense recorded!"
    )
    amount = context.user_data['amount']
    category = update.message.text
    print(f"Amount: {amount}, Category: {category}")
   

    return ConversationHandler.END

@restricted
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Operation cancelled."
    )
    return ConversationHandler.END

if __name__ == '__main__':

    app = ApplicationBuilder().token(TOKEN).build()

    # Define handlers
    start_handler = CommandHandler('start', start)

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text(["💸 Expense"]), ask_amount)],
        states={
            AMOUNT: [MessageHandler(filters.Regex(r"^\d+(\.\d+)?$"), receive_amount)],
            CATEGORY: [MessageHandler(filters.Text(
                    ["🏠Housing", "🏬Pantry", "🚋Transportation", "🍎Healthcare", "🍔Takeout/eating out", 
                     "🍿Entertainment", "🛍️Shopping", "✈️Lifestyle","💰Savings & Investments"]
            ), receive_category)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    # Add handlers
    app.add_handler(start_handler)
    app.add_handler(conv_handler)



    app.run_polling()