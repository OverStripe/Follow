import requests
import json
import asyncio
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# Solana RPC endpoint
rpc_url = "https://mainnet.helius-rpc.com/?api-key=3306ede2-b0da-4ea3-a571-50369811ddb4"

# Exchange wallet addresses to monitor
exchange_wallets = [
    "A77HErqtfN1hLLpvZ9pCtu66FEtM8BveoaKbbMoZ4RiR",  # Example Wallet
    "5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9",  # Example Wallet
]

# Telegram bot setup
telegram_bot_token = "7709293848:AAFpmhubng8CYFbzbIpnRNLEf9GJJ4mm6IU"  # Replace with your bot token
bot = Bot(token=telegram_bot_token)

# Track subscribed users
subscribed_users = set()


# Function to get signatures for the address
def get_signatures_for_address(pubkey, limit=5):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [pubkey, {"limit": limit}],
    }
    response = requests.post(rpc_url, json=payload)
    return response.json()


# Function to get transaction details for a given signature
def get_transaction(signature):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [signature, {"maxSupportedTransactionVersion": 0}],
    }
    response = requests.post(rpc_url, json=payload)
    return response.json()


# Monitor wallets for coin purchases and notify
async def monitor_wallets():
    processed_signatures = set()

    while True:
        for wallet in exchange_wallets:
            signatures_response = get_signatures_for_address(wallet)
            if "result" not in signatures_response or len(signatures_response["result"]) == 0:
                continue

            for signature_info in signatures_response["result"]:
                signature = signature_info["signature"]

                if signature in processed_signatures:
                    continue
                processed_signatures.add(signature)

                transaction_response = get_transaction(signature)
                if "result" not in transaction_response or not transaction_response["result"]:
                    continue

                transaction = transaction_response["result"]
                message = transaction["transaction"]["message"]
                account_keys = message["accountKeys"]
                instructions = message["instructions"]

                # Process instructions to detect coin purchases
                for instruction in instructions:
                    program_id = instruction.get("programIdIndex")
                    if account_keys[program_id] == "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA":
                        # Extract details from the transaction
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

        await asyncio.sleep(5)  # Monitor every 5 seconds


# Telegram command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if chat_id not in subscribed_users:
        subscribed_users.add(chat_id)
        await update.message.reply_text("You are now subscribed to coin purchase notifications!")
    else:
        await update.message.reply_text("You are already subscribed!")


# Main function
async def main():
    app = Application.builder().token(telegram_bot_token).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start))

    # Start monitoring wallets
    asyncio.create_task(monitor_wallets())

    print("Bot is running...")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
