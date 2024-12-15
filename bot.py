import requests
import json
import asyncio
import logging
from telegram import Bot
from typing import List, Dict

# Setup logging
logging.basicConfig(filename="wallet_monitor.log", level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Load configuration
with open("config.json", "r") as config_file:
    config = json.load(config_file)

rpc_url = config["rpc_url"]
telegram_bot_token = config["telegram_bot_token"]
telegram_user_id = config["telegram_user_id"]
exchange_wallets = config["exchange_wallets"]

bot = Bot(token=telegram_bot_token)

# Function to get signatures for the address
def get_signatures_for_address(pubkey: str, limit: int = 5) -> Dict:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [pubkey, {"limit": limit}],
    }
    try:
        response = requests.post(rpc_url, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Error fetching signatures for {pubkey}: {e}")
        return {}

# Function to get transaction details for a given signature
def get_transaction(signature: str) -> Dict:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransaction",
        "params": [signature, {"maxSupportedTransactionVersion": 0}],
    }
    try:
        response = requests.post(rpc_url, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Error fetching transaction details for {signature}: {e}")
        return {}

# Function to get token metadata from CoinGecko
def get_token_metadata(token_address: str) -> Dict:
    try:
        # Replace with actual CoinGecko API endpoint or a relevant Solana API
        coingecko_url = f"https://api.coingecko.com/api/v3/simple/token_price/solana?contract_addresses={token_address}&vs_currencies=usd"
        response = requests.get(coingecko_url)
        response.raise_for_status()
        data = response.json()
        return data.get(token_address, {})
    except Exception as e:
        logging.error(f"Error fetching metadata for token {token_address}: {e}")
        return {"market_cap": "Unknown"}

# Monitor wallets for new transactions and notify on coin purchases
async def monitor_wallets():
    processed_signatures = set()
    processed_wallets = set()

    while True:
        for wallet in exchange_wallets:
            signatures_response = get_signatures_for_address(wallet)
            if "result" not in signatures_response or len(signatures_response["result"]) == 0:
                continue

            for signature_info in signatures_response["result"]:
                signature = signature_info["signature"]

                # Skip if already processed
                if signature in processed_signatures:
                    continue
                processed_signatures.add(signature)

                # Get transaction details
                transaction_response = get_transaction(signature)
                if "result" not in transaction_response or not transaction_response["result"]:
                    continue

                transaction = transaction_response["result"]
                message = transaction["transaction"]["message"]
                account_keys = message["accountKeys"]
                instructions = message["instructions"]

                # Detect new wallets receiving funds
                for account in account_keys[1:]:
                    if account not in processed_wallets:
                        processed_wallets.add(account)

                        logging.info(f"New wallet detected: {account}")

                        # Check if any instruction indicates a token transfer (coin purchase)
                        for instruction in instructions:
                            program_id = instruction.get("programId")
                            if program_id == "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA":  # Token program
                                token_address = account_keys[instruction["accounts"][-1]]
                                token_data = get_token_metadata(token_address)
                                market_cap = token_data.get("usd", "Unknown")

                                # Send notification
                                notification_message = (
                                    f"New wallet detected: {account}\n"
                                    f"Coin purchased: {token_address}\n"
                                    f"Market Cap: {market_cap} USD\n"
                                )
                                await bot.send_message(chat_id=telegram_user_id, text=notification_message)

        await asyncio.sleep(60)

# Entry point
if __name__ == "__main__":
    try:
        asyncio.run(monitor_wallets())
    except Exception as e:
        logging.error(f"Error in monitor_wallets: {e}")
        
