import requests
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Telegram Bot Token
TELEGRAM_TOKEN = "8082481347:AAGsTOVI-k6Y3qWKDHkTCuhkVk7qr1-R9wY"

# Solscan API Key
SOLSCAN_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjcmVhdGVkQXQiOjE3MzQyNjQ1Mjk1MTcsImVtYWlsIjoic29uZ2luZGlhbjE2QGdtYWlsLmNvbSIsImFjdGlvbiI6InRva2VuLWFwaSIsImFwaVZlcnNpb24iOiJ2MiIsImlhdCI6MTczNDI2NDUyOX0.gTWa20HeXjgBhbqH2t0XyjU0W030Hd1Ck5HLBmSeXgU"

# Solscan API Base URL
SOLSCAN_API_BASE = "https://api.solscan.io/v1.0"

# User-specific thresholds
user_thresholds = {}  # {chat_id: threshold}

# Track processed transactions
processed_transactions = set()


# Command: Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_thresholds[chat_id] = 10  # Default threshold
    await update.message.reply_text(
        "Welcome to the Solscan Alert Bot!\n"
        "Default threshold is set to 10.\n"
        "Use /change <amount> to adjust your threshold."
    )


# Command: Change Threshold
async def change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    try:
        new_threshold = int(context.args[0])
        user_thresholds[chat_id] = new_threshold
        await update.message.reply_text(f"Threshold updated to {new_threshold}.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /change <amount>")


# Fetch transactions for all coins and notify users
async def fetch_and_notify(application: Application) -> None:
    global processed_transactions

    url = f"{SOLSCAN_API_BASE}/transactions/latest"  # Endpoint for recent transactions

    headers = {
        "Authorization": f"Bearer {SOLSCAN_API_KEY}",
        "Content-Type": "application/json",
    }

    # Fetch data from Solscan
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching data: {response.text}")
        return

    # Process transactions
    data = response.json()
    transactions = data.get("data", [])
    for transaction in transactions:
        tx_hash = transaction.get("txHash")
        token_symbol = transaction.get("tokenSymbol", "Unknown Token")
        amount = float(transaction.get("amount", 0))
        source = transaction.get("source", "N/A")
        destination = transaction.get("destination", "N/A")

        # Skip already processed transactions
        if tx_hash in processed_transactions:
            continue

        processed_transactions.add(tx_hash)

        # Notify each user based on their threshold
        for chat_id, threshold in user_thresholds.items():
            if amount >= threshold:
                # Prepare message with transaction details
                message = (
                    f"New Transaction Detected:\n"
                    f"- Token: {token_symbol}\n"
                    f"- Amount: {amount}\n"
                    f"- Sender: {source}\n"
                    f"- Receiver: {destination}\n"
                    f"- Tx Hash: {tx_hash}\n"
                    f"- Timestamp: {transaction.get('blockTime', 'N/A')}"
                )
                bot: Bot = application.bot
                await bot.send_message(chat_id=chat_id, text=message)


# Main function
def main():
    # Telegram application setup
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Schedule task to fetch transactions periodically
    scheduler = AsyncIOScheduler()
    scheduler.add_job(fetch_and_notify, "interval", seconds=60, args=[application])
    scheduler.start()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("change", change))

    # Start the bot and let Application manage the event loop
    print("Bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()
