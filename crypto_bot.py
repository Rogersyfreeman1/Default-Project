import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import requests

class CryptoPaperTradingBot:
    def __init__(self, config_path: str = "crypto_config.json"):
        self.config = self.load_config(config_path)
        self.position = None
        self.trade_history = []
        self.setup_logging()
        
    def load_config(self, config_path: str) -> Dict:
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def setup_logging(self):
        log_config = self.config.get('logging', {})
        if log_config.get('enabled', True):
            logging.basicConfig(
                filename=log_config.get('file', 'trading_log.txt'),
                level=getattr(logging, log_config.get('level', 'INFO')),
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
        self.logger = logging.getLogger(__name__)
    
    def calculate_position_size(self) -> float:
        pos_config = self.config['trading']['position_size']
        return pos_config['multiplier'] * pos_config['factor']
    
    def calculate_profit_target(self) -> float:
        target_config = self.config['trading']['profit_target']
        return target_config['average']
    
    def open_position(self, direction: str, price: float) -> Dict:
        position_size = self.calculate_position_size()
        units = position_size / price
        
        position = {
            'id': f"POS_{int(time.time())}",
            'symbol': self.config['trading']['symbol'],
            'direction': direction,
            'entry_price': price,
            'units': units,
            'entry_time': datetime.now(),
            'status': 'open',
            'current_price': price,
            'unrealized_pnl': 0
        }
        
        self.position = position
        self.trade_history.append(position)
        self.logger.info(f"Opened {direction} position: {position['id']} at {price}")
        
        return position
    
    def close_position(self, price: float) -> Optional[Dict]:
        if not self.position or self.position['status'] != 'open':
            return None
        
        self.position['exit_price'] = price
        self.position['exit_time'] = datetime.now()
        self.position['status'] = 'closed'
        
        if self.position['direction'] == 'long':
            pnl = (price - self.position['entry_price']) * self.position['units']
        else:
            pnl = (self.position['entry_price'] - price) * self.position['units']
        
        self.position['realized_pnl'] = pnl
        self.position['hold_time'] = self.position['exit_time'] - self.position['entry_time']
        
        self.logger.info(f"Closed position: {self.position['id']} at {price}, PnL: {pnl}")
        
        closed_position = self.position.copy()
        self.position = None
        
        return closed_position
    
    def check_profit_target(self, current_price: float) -> bool:
        if not self.position or self.position['status'] != 'open':
            return False
        
        target = self.calculate_profit_target()
        
        if self.position['direction'] == 'long':
            pnl = (current_price - self.position['entry_price']) * self.position['units']
        else:
            pnl = (self.position['entry_price'] - current_price) * self.position['units']
        
        self.position['current_price'] = current_price
        self.position['unrealized_pnl'] = pnl
        
        return pnl >= target
    
    def process_signal(self, sentiment: str, price: float):
        if self.position and self.position['status'] == 'open':
            if self.check_profit_target(price):
                self.close_position(price)
                self.open_position(sentiment, price)
            else:
                self.position['current_price'] = price
                if self.position['direction'] == 'long':
                    self.position['unrealized_pnl'] = (price - self.position['entry_price']) * self.position['units']
                else:
                    self.position['unrealized_pnl'] = (self.position['entry_price'] - price) * self.position['units']
        else:
            self.open_position(sentiment, price)
    
    def get_status(self) -> Dict:
        status = {
            'capital': self.config['trading']['capital'],
            'symbol': self.config['trading']['symbol'],
            'position': self.position,
            'total_trades': len(self.trade_history),
            'open_trades': len([t for t in self.trade_history if t['status'] == 'open'])
        }
        
        if self.trade_history:
            closed_trades = [t for t in self.trade_history if t['status'] == 'closed']
            if closed_trades:
                total_pnl = sum(t.get('realized_pnl', 0) for t in closed_trades)
                winning_trades = len([t for t in closed_trades if t.get('realized_pnl', 0) > 0])
                status['total_pnl'] = total_pnl
                status['win_rate'] = winning_trades / len(closed_trades) * 100 if closed_trades else 0
        
        return status
    
    def generate_report(self) -> str:
        status = self.get_status()
        report = f"""
=== Crypto Paper Trading Bot Report ===
Time: {datetime.now()}
Capital: ${status['capital']:,.2f}
Symbol: {status['symbol']}

Current Position:
{json.dumps(status['position'], indent=2, default=str) if status['position'] else 'No open position'}

Performance:
Total Trades: {status['total_trades']}
Open Trades: {status['open_trades']}
Total PnL: ${status.get('total_pnl', 0):,.2f}
Win Rate: {status.get('win_rate', 0):.1f}%
"""
        return report

if __name__ == "__main__":
    bot = CryptoPaperTradingBot()
    print("Crypto Paper Trading Bot initialized")
    print(bot.generate_report())
