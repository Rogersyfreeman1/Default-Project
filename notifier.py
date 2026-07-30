import json
import requests
from datetime import datetime

class Notifier:
    def __init__(self, config_path: str = "crypto_config.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.telegram_config = self.config.get('notifications', {}).get('telegram', {})
        self.enabled = self.config.get('notifications', {}).get('enabled', False)
        self.bot_token = self.telegram_config.get('bot_token', '')
        self.chat_id = self.telegram_config.get('chat_id', '')
    
    def send_telegram(self, message: str):
        if not self.enabled or not self.telegram_config.get('enabled', False):
            return False
        
        if not self.bot_token:
            print("No Telegram bot token configured")
            return False
        
        if not self.chat_id:
            print("No Telegram chat_id configured")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, json=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"Telegram error: {e}")
            return False
    
    def get_chat_id(self):
        if not self.bot_token:
            return None
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            response = requests.get(url)
            data = response.json()
            
            if data.get('result'):
                for update in data['result']:
                    if 'message' in update:
                        chat_id = update['message']['chat']['id']
                        return str(chat_id)
            return None
        except Exception as e:
            print(f"Error getting chat_id: {e}")
            return None
    
    def set_chat_id(self, chat_id: str):
        self.chat_id = chat_id
        self.config['notifications']['telegram']['chat_id'] = chat_id
        with open('crypto_config.json', 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def notify_position_opened(self, position: dict):
        message = f"""
🟢 <b>Position Opened</b>

Direction: {position['direction'].upper()}
Symbol: {position['symbol']}
Entry Price: ${position['entry_price']:,.2f}
Units: {position['units']:.6f}
Time: {position['entry_time']}

Profit Target: $50,000,000
"""
        self.send_telegram(message)
    
    def notify_position_closed(self, position: dict, pnl: float):
        emoji = "🟢" if pnl > 0 else "🔴"
        message = f"""
{emoji} <b>Position Closed</b>

Direction: {position['direction'].upper()}
Entry Price: ${position['entry_price']:,.2f}
Exit Price: ${position['exit_price']:,.2f}
Hold Time: {position['hold_time']}
P&L: ${pnl:,.2f}

Time: {datetime.now()}
"""
        self.send_telegram(message)
    
    def notify_profit_milestone(self, current_pnl: float, milestone: str):
        message = f"""
💰 <b>Profit Milestone</b>

Current P&L: ${current_pnl:,.2f}
Milestone: {milestone}

Keep riding the trend!
"""
        self.send_telegram(message)
    
    def notify_error(self, error_msg: str):
        message = f"""
⚠️ <b>Bot Error</b>

{error_msg}

Time: {datetime.now()}
"""
        self.send_telegram(message)
