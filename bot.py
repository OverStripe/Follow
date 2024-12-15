import requests
import random
import time
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Constants
TELEGRAM_BOT_TOKEN = "8082481347:AAH45hUl4NzxT6f9xqD5X3OV9rcF1FZCWrs"  # Replace with your Telegram Bot token
MAIL_TM_BASE_URL = "https://api.mail.tm"
PUMP_FUN_SIGNUP_URL = "https://pump.fun/signup"
PUMP_FUN_LOGIN_URL = "https://pump.fun/api/login"
PUMP_FUN_COMMENT_URL = "https://pump.fun/api/comments/{}"  # Format with coin address
DEFAULT_PASSWORD = "SecurePassword123!"
HEADERS = {"Content-Type": "application/json"}

# Predefined Comment Templates
TEMPLATES = [
    "This project, {}, has amazing potential! 🚀",
    "I'm really excited about {}. The future looks bright!",
    "Don't miss out on {} – this could be huge!",
    "Check out {} – it's trending for all the right reasons!",
    "I've been following {}, and it's showing great promise!"
]

# Step 1: Create Temporary Email
def create_temp_email():
    response = requests.post(f"{MAIL_TM_BASE_URL}/accounts", json={
        "address": None,
        "password": DEFAULT_PASSWORD
    })
    if response.status_code == 201:
        email_data = response.json()
        return email_data["address"], email_data["id"]
    else:
        return None, None

# Step 2: Fetch Email Verification Link
def get_verification_email(email_address):
    token_response = requests.post(f"{MAIL_TM_BASE_URL}/token", json={
        "address": email_address,
        "password": DEFAULT_PASSWORD
    })
    if token_response.status_code != 200:
        return None

    token = token_response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    for _ in range(10):  # Retry for 50 seconds
        inbox_response = requests.get(f"{MAIL_TM_BASE_URL}/messages", headers=headers)
        if inbox_response.status_code == 200 and inbox_response.json():
            messages = inbox_response.json()
            for message in messages:
                if "verification" in message["subject"].lower():
                    message_id = message["id"]
                    verification_response = requests.get(
                        f"{MAIL_TM_BASE_URL}/messages/{message_id}",
                        headers=headers
                    )
                    if verification_response.status_code == 200:
                        content = verification_response.json()
                        return extract_verification_link(content["html"])
        time.sleep(5)
    return None

# Helper: Extract Verification Link from Email Content
def extract_verification_link(html_content):
    import re
    match = re.search(r'href=[\'"]?([^\'" >]+)', html_content)
    return match.group(1) if match else None

# Step 3: Verify Account
def verify_account(verification_link):
    response = requests.get(verification_link)
    return response.status_code == 200

# Step 4: Login
def login(email, password):
    response = requests.post(PUMP_FUN_LOGIN_URL, json={"email": email, "password": password}, headers=HEADERS)
    if response.status_code == 200:
        return response.json()["token"]
    else:
        return None

# Step 5: Post Comment
def post_comment(token, coin_address, comment_text):
    url = PUMP_FUN_COMMENT_URL.format(coin_address)
    headers = {**HEADERS, "Authorization": f"Bearer {token}"}
    response = requests.post(url, json={"comment": comment_text}, headers=headers)
    return response.status_code == 200

# Generate Comment
def generate_comment(coin_name, use_ai=False):
    if use_ai:
        return generate_ai_comment(coin_name)
    else:
        template = random.choice(TEMPLATES)
        return template.format(coin_name)

# Optional: AI-Based Comment Generator
def generate_ai_comment(coin_name):
    from transformers import pipeline
    generator = pipeline("text-generation", model="gpt2")
    prompt = f"Write an engaging comment about the cryptocurrency {coin_name}:"
    generated = generator(prompt, max_length=50, num_return_sequences=1)
    return generated[0]["generated_text"]

# Full Automation Workflow
def automate_commenting(coin_address, coin_name, use_ai=False):
    email_address, email_id = create_temp_email()
    if not email_address:
        return "Failed to create temporary email."

    verification_link = get_verification_email(email_address)
    if not verification_link:
        return "Verification email not received."

    if not verify_account(verification_link):
        return "Failed to verify account."

    token = login(email_address, DEFAULT_PASSWORD)
    if not token:
        return "Login failed."

    comment_text = generate_comment(coin_name, use_ai=use_ai)
    if post_comment(token, coin_address, comment_text):
        return f"Comment posted successfully on {coin_address} with text: {comment_text}"
    else:
        return "Failed to post comment."

# Telegram Bot Commands
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Welcome! Use the command /help to understand how to use this bot."
    )

def help_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Send the coin address and name in this format: \n"
        "/comment <coin_address> <coin_name>\n"
        "Example: /comment example_coin_address AmazingCoin"
    )

def comment(update: Update, context: CallbackContext):
    try:
        args = context.args
        if len(args) < 2:
            update.message.reply_text("Usage: /comment <coin_address> <coin_name>")
            return

        coin_address = args[0]
        coin_name = " ".join(args[1:])
        update.message.reply_text(f"Starting commenting process on {coin_address}...")

        # Automate Commenting
        result = automate_commenting(coin_address, coin_name, use_ai=False)
        update.message.reply_text(result)
    except Exception as e:
        update.message.reply_text(f"An error occurred: {str(e)}")

# Main Function
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dispatcher = updater.dispatcher

    # Register Handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("comment", comment))

    # Start the Bot
    updater.start_polling()
    updater.idle()

# Execute Script
if __name__ == "__main__":
    main()
