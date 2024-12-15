import requests
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram import Update
from modules.temp_email import get_temp_email
from bot.utils import save_account, fetch_accounts, generate_username, generate_password

def create_account():
    email = get_temp_email()
    if not email:
        return {"status": "error", "message": "Failed to fetch temporary email"}
    
    api_url = "http://127.0.0.1:5000/create_account"
    payload = {
        "email": email,
        "username": generate_username(),
        "password": generate_password()
    }

    try:
        response = requests.post(api_url, json=payload)
        data = response.json()

        if data.get("status") == "success":
            save_account(data["email"], data["username"], payload["password"])

        return data
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}

def create_command(update: Update, context: CallbackContext):
    try:
        num_accounts = int(context.args[0])
        update.message.reply_text(f"Creating {num_accounts} accounts. Please wait...")
        
        for i in range(num_accounts):
            result = create_account()
            if result.get("status") == "success":
                print(f"Created account {i+1}/{num_accounts}: {result['username']}")
            else:
                print(f"Failed to create account {i+1}/{num_accounts}: {result['message']}")

        update.message.reply_text(f"Successfully created {num_accounts} accounts!")
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /create <number_of_accounts>")
    except Exception as e:
        update.message.reply_text(f"An error occurred: {str(e)}")

def send_command(update: Update, context: CallbackContext):
    try:
        target_username = context.args[0]
        accounts = fetch_accounts()

        if not accounts:
            update.message.reply_text("No accounts available to follow.")
            return

        update.message.reply_text(f"Accounts are now following {target_username}. Please wait...")

        for account in accounts:
            username = account[0]
            api_url = "http://127.0.0.1:5000/follow"
            payload = {
                "follower": username,
                "target": target_username
            }

            try:
                response = requests.post(api_url, json=payload)
                result = response.json()
                if result.get("status") == "success":
                    print(f"{username} followed {target_username}")
                else:
                    print(f"{username} failed to follow {target_username}: {result['message']}")
            except requests.exceptions.RequestException as e:
                print(f"{username} encountered an error: {str(e)}")

        update.message.reply_text(f"All accounts have attempted to follow {target_username}!")
    except IndexError:
        update.message.reply_text("Usage: /send <target_username>")
    except Exception as e:
        update.message.reply_text(f"An error occurred: {str(e)}")

def main():
    TOKEN = "7709293848:AAHLGPqxGixXzUMJI7ubA7qj_wO4mytFDIc"
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("create", create_command))
    dispatcher.add_handler(CommandHandler("send", send_command))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
  
