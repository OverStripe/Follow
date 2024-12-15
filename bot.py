import requests
from bs4 import BeautifulSoup
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Telegram Bot Token
TELEGRAM_TOKEN = "8082481347:AAGl1LqSwQgWoaX-GBIKtdcTncebS6HQl3o"

# Solscan URL for scraping
SOLSCAN_URL = "https://solscan.io/"

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


# Scrape transactions from Solscan
def scrape_transactions():
    response = requests.get(SOLSCAN_URL)
    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, "lxml")

    # Find the latest transactions table
    transactions_table = soup.find("table", {"class": "table"})
    if not transactions_table:
        print("Error: Transactions table not found")
        return []

    # Extract rows from the table
    rows = transactions_table.find("tbody").find_all("tr")

    transactions = []
    for row in rows:
        cols = row.find_all("td")
        tx_hash = cols[0].text.strip()
        token = cols[1].text.strip()
        amount = cols[2].text.strip()
        buyer = cols[3].text.strip()  # Adjust index based on actual HTML
        seller = cols[4].text.strip()  # Adjust index based on actual HTML
        timestamp = cols[5].text.strip()  # Adjust index based on actual HTML

        transactions.append({
            "txHash": tx_hash,
            "token": token,
            "amount": amount,
            "buyer": buyer,
            "seller": seller,
            "timestamp": timestamp,
        })

    return transactions


# Fetch transactions and notify users
async def fetch_and_notify(application: Application) -> None:
    global processed_transactions

    # Scrape transactions
    transactions = scrape_transactions()
    if not transactions:
        print("No transactions found.")
        return

    for transaction in transactions:
        tx_hash = transaction["txHash"]
        token = transaction["token"]
        amount = transaction["amount"]
        buyer = transaction["buyer"]
        seller = transaction["seller"]
        timestamp = transaction["timestamp"]

        # Skip already processed transactions
        if tx_hash in processed_transactions:
            continue

        processed_transactions.add(tx_hash)

        # Notify all subscribed users
        for chat_id in subscribed_users:
            message = (
                f"🚨 New Coin Purchase Detected 🚨\n"
                f"- Token: {token}\n"
                f"- Amount Bought: {amount}\n"
                f"- Buyer: {buyer}\n"
                f"- Seller: {seller}\n"
                f"- Tx Hash: {tx_hash}\n"
                f"- Timestamp: {timestamp}"
            )
            bot: Bot = application.bot
            await bot.send_message(chat_id=chat_id, text=message)


# Main function
def main():
    # Telegram application setup
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Schedule task to fetch transactions every 8 seconds
    scheduler = AsyncIOScheduler()
    scheduler.add_job(fetch_and_notify, "interval", seconds=8, args=[application])  # 8-second interval
    scheduler.start()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))

    # Start the bot and let Application manage the event loop
    print("Bot is running...")
    application.run_polling()


if __name__ == "__main__":
    main()
