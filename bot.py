import requests
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

# Solana RPC endpoint
RPC_URL = "https://mainnet.helius-rpc.com/?api-key=3306ede2-b0da-4ea3-a571-50369811ddb4"

# Wallets to monitor
EXCHANGE_WALLETS = [
    "A77HErqtfN1hLLpvZ9pCtu66FEtM8BveoaKbbMoZ4RiR",  # Example Wallet
    "5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9",  # Example Wallet
]

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = "7709293848:AAFfLflnEyOiwRxsR6hDoKL910pSVZn09Hs"  # Replace with your bot token
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Subscribed users and processed transactions
subscribed_users = set()
processed_signatures = set()


# Function to fetch signatures for a specific wallet address
def get_signatures_for_address(pubkey, limit=5):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [pubkey, {"limit": limit}],
    }
    response = requests.post(RPC_URL, json=payload)
    return response.json()


# Function to fetch transaction details for a given signature
def get_transaction(signature):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [signature, {"maxSupportedTransactionVersion": 0}],
    }
    response = requests.post(RPC_URL, json=payload)
    return response.json()


# Monitor wallets and notify subscribed users
async def monitor_wallets():
    while True:
        for wallet in EXCHANGE_WALLETS:
            try:
                # Fetch recent signatures
                signatures_response = get_signatures_for_address(wallet)
                if "result" not in signatures_response or not signatures_response["result"]:
                    continue

                # Process each signature
                for signature_info in signatures_response["result"]:
                    signature = signature_info["signature"]
                    if signature in processed_signatures:
                        continue  # Skip already processed transactions
                    processed_signatures.add(signature)

                    # Fetch transaction details
                    transaction_response = get_transaction(signature)
                    if "result" not in transaction_response or not transaction_response["result"]:
                        continue

                    transaction = transaction_response["result"]
                    message = transaction["transaction"]["message"]
                    account_keys = message["accountKeys"]
                    instructions = message["instructions"]

                    # Check for coin purchases
                    for instruction in instructions:
                        program_id_index = instruction.get("programIdIndex")
                        if account_keys[program_id_index] == "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA":
                            buyer = account_keys[instruction["accounts"][0]]
                            token_address = account_keys[instruction["accounts"][-1]]
                            amount = instruction.get("data", "Unknown Amount")

                            # Create the notification message
                            notification_message = (
                                f"🚨 Coin Purchase Detected 🚨\n"
                                f"- Buyer Address: {buyer}\n"
                                f"- Token Address: {token_address}\n"
                                f"- Amount Purchased: {amount}\n"
                                f"- Transaction Hash: {signature}\n"
                            )

                            # Send notification to all subscribed users
                            for chat_id in subscribed_users:
                                await bot.send_message(chat_id=chat_id, text=notification_message)

            except Exception as e:
                print(f"Error monitoring wallet {wallet}: {e}")

        await asyncio.sleep(10)  # Monitor every 10 seconds


# Telegram command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id not in subscribed_users:
        subscribed_users.add(chat_id)
        print(f"Subscribed users: {subscribed_users}")  # Debugging
        await update.message.reply_text("You are now subscribed to coin purchase notifications!")
    else:
        await update.message.reply_text("You are already subscribed!")


# Telegram command: /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id in subscribed_users:
        subscribed_users.remove(chat_id)
        print(f"Unsubscribed users: {subscribed_users}")  # Debugging
        await update.message.reply_text("You have unsubscribed from notifications.")
    else:
        await update.message.reply_text("You are not subscribed.")


# Main function
async def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))

    # Start monitoring wallets
    asyncio.create_task(monitor_wallets())

    print("Bot is running...")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
    
