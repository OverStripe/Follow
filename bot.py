import requests
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Telegram Bot Token
TELEGRAM_TOKEN = "8082481347:AAEBpazl2x-vMI4J-VN7YE2Vst9kXD_Eigw"

# Solscan API Key
SOLSCAN_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjcmVhdGVkQXQiOjE3MzQyNjQ1Mjk1MTcsImVtYWlsIjoic29uZ2luZGlhbjE2QGdtYWlsLmNvbSIsImFjdGlvbiI6InRva2VuLWFwaSIsImFwaVZlcnNpb24iOiJ2MiIsImlhdCI6MTczNDI2NDUyOX0.gTWa20HeXjgBhbqH2t0XyjU0W030Hd1Ck5HLBmSeXgU"

# Solscan API Base URL
SOLSCAN_API_BASE = "https://api.solscan.io/v1.0"

# List of active chat IDs
subscribed_users = set()  # Stores user chat IDs

# Track processed transactions
processed_transactions = set()


# Command: Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id not in subscribed_users:
        subscribed_users.add(chat_id)
        await update.message.reply_text(
            "You are now subscribed to receive coin purchase notifications."
        )
    else:
        await update.message.reply_text("You are already subscribed.")


# Command: Stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id in subscribed_users:
        subscribed_users.remove(chat_id)
        await update.message.reply_text("You have unsubscribed from purchase notifications.")
    else:
        await update.message.reply_text("You are not subscribed.")


# Fetch transactions and notify users
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
        buyer = transaction.get("source", "N/A")  # Buyer address
        seller = transaction.get("destination", "N/A")  # Seller address

        # Skip already processed transactions
        if tx_hash in processed_transactions:
            continue

        processed_transactions.add(tx_hash)

        # Identify "buy" transactions
        if amount > 0 and buyer != "N/A" and seller != "N/A":
            # Notify all subscribed users
            for chat_id in subscribed_users:
                message = (
                    f"🚨 New Coin Purchase Detected 🚨\n"
                    f"- Token: {token_symbol}\n"
                    f"- Amount Bought: {amount}\n"
                    f"- Buyer: {buyer}\n"
                    f"- Seller: {seller}\n"
                    f"- Tx Hash: {tx_hash}\n"
                    f"- Timestamp: {transaction.get('blockTime', 'N/A')}"
                )
                bot: Bot = application.bot
                await bot.send_message(chat_id=chat_id, text=message)


# Main function
def main():
    # Telegram application setup
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Schedule task to fetch transactions every 10 seconds
    scheduler = AsyncIOScheduler()
    scheduler.add_job(fetch_and_notify, "interval", seconds=10, args=[application])  # 10-second interval
    scheduler.start()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))

    # Start the bot and let Application manage the event loop
    print("Bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()
    
