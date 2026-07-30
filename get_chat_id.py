import requests
import json

BOT_TOKEN = "8941809435:AAEFplfhpMAvIXpnEavSWXiD0lGmr3SM7Q4"

def get_chat_id():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    response = requests.get(url)
    data = response.json()
    
    if data.get('result'):
        for update in data['result']:
            if 'message' in update:
                chat_id = update['message']['chat']['id']
                username = update['message']['chat'].get('username', 'Unknown')
                first_name = update['message']['chat'].get('first_name', 'Unknown')
                print(f"Found chat_id: {chat_id}")
                print(f"Username: @{username}")
                print(f"Name: {first_name}")
                return str(chat_id)
    
    print("No messages found. Please send a message to your bot first.")
    print("1. Open Telegram")
    print("2. Search for @Troyjudahbot")
    print("3. Send 'hi' to it")
    print("4. Run this script again")
    return None

def save_chat_id(chat_id):
    with open('crypto_config.json', 'r') as f:
        config = json.load(f)
    
    config['notifications']['telegram']['chat_id'] = chat_id
    
    with open('crypto_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Saved chat_id: {chat_id}")

if __name__ == "__main__":
    chat_id = get_chat_id()
    if chat_id:
        save_chat_id(chat_id)
        print("\nDone! Your bot will now send notifications to Telegram.")
