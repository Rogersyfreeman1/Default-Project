from flask import Flask, request, jsonify
import json
import logging
import requests
import random
import time
from crypto_bot import CryptoPaperTradingBot
from notifier import Notifier

app = Flask(__name__, static_folder='static')
bot = CryptoPaperTradingBot()
notifier = Notifier()

last_btc_price = 64795.11

def generate_klines(interval, limit):
    global last_btc_price
    candles = []
    now = int(time.time())
    
    intervals = {'1m': 60, '5m': 300, '15m': 900, '1h': 3600, '4h': 14400, '1d': 86400}
    step = intervals.get(interval, 60)
    
    price = last_btc_price
    for i in range(int(limit)):
        ts = now - (int(limit) - i) * step
        change = price * random.uniform(-0.002, 0.002)
        o = price
        c = price + change
        h = max(o, c) + abs(change) * random.uniform(0, 0.5)
        l = min(o, c) - abs(change) * random.uniform(0, 0.5)
        vol = random.uniform(500, 5000)
        candles.append({
            'time': ts,
            'open': round(o, 2),
            'high': round(h, 2),
            'low': round(l, 2),
            'close': round(c, 2),
            'volume': round(vol, 2)
        })
        price = c
    
    last_btc_price = price
    return candles

logging.basicConfig(
    filename='webhook_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        secret = bot.config.get('webhook', {}).get('secret')
        if secret and data.get('secret') != secret:
            logger.warning("Invalid webhook secret")
            return jsonify({'error': 'Invalid secret'}), 401
        
        sentiment = data.get('sentiment', '').lower()
        price = float(data.get('price', 0))
        symbol = data.get('symbol', 'BTCUSD')
        
        if sentiment not in ['bullish', 'bearish']:
            return jsonify({'error': 'Invalid sentiment'}), 400
        
        if price <= 0:
            return jsonify({'error': 'Invalid price'}), 400
        
        old_position = bot.position.copy() if bot.position else None
        
        bot.process_signal(sentiment, price)
        
        if bot.position and (not old_position or old_position['status'] != 'open'):
            notifier.notify_position_opened(bot.position)
        elif old_position and old_position['status'] == 'open' and (not bot.position or bot.position is None):
            notifier.notify_position_closed(old_position, old_position.get('realized_pnl', 0))
        
        logger.info(f"Webhook processed: {sentiment} at {price} for {symbol}")
        
        return jsonify({
            'status': 'success',
            'sentiment': sentiment,
            'price': price,
            'position': bot.position
        })
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def dashboard():
    with open('templates/dashboard.html', 'r') as f:
        return f.read()

@app.route('/education')
def education():
    with open('templates/education.html', 'r') as f:
        return f.read()

@app.route('/journal')
def journal():
    with open('templates/journal.html', 'r') as f:
        return f.read()

@app.route('/scheduler')
def scheduler():
    with open('templates/scheduler.html', 'r') as f:
        return f.read()

@app.route('/status', methods=['GET'])
def status():
    return jsonify(bot.get_status())

@app.route('/api/klines', methods=['GET'])
def get_klines():
    symbol = request.args.get('symbol', 'BTCUSDT')
    interval = request.args.get('interval', '1m')
    limit = request.args.get('limit', '200')
    
    candles = generate_klines(interval, limit)
    return jsonify(candles)

@app.route('/report', methods=['GET'])
def report():
    return bot.generate_report()

if __name__ == '__main__':
    port = bot.config.get('webhook', {}).get('port', 8080)
    logger.info(f"Starting webhook server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)
