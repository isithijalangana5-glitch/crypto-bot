import telebot
import requests
import datetime
from collections import defaultdict
import os

TOKEN = os.environ.get("TOKEN")
bot = telebot.TeleBot(TOKEN)

PREMIUM_USERS = [8481784949]
user_usage = defaultdict(list)

def is_premium(user_id):
    return user_id in PREMIUM_USERS

def can_use_signal(user_id):
    if is_premium(user_id):
        return True
    today = datetime.date.today()
    user_usage[user_id] = [d for d in user_usage[user_id] if d == today]
    if len(user_usage[user_id]) < 2:
        user_usage[user_id].append(today)
        return True
    return False

COINS = ["BTC","ETH","SOL","XRP","DOGE","ADA","LINK","AVAX","DOT","MATIC","LTC","TRX","NEAR","APT","ATOM"]

def get_price(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}USDT"
        r = requests.get(url, timeout=5).json()
        return float(r['price'])
    except:
        return None

def get_rsi(symbol):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=1h&limit=50"
        data = requests.get(url, timeout=5).json()
        closes = [float(x[4]) for x in data]
        gains = []
        losses = []
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i-1]
            if diff > 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(diff))
        avg_gain = sum(gains[-14:]) / 14
        avg_loss = sum(losses[-14:]) / 14
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 1)
    except:
        return 50

def make_signal_text(symbol):
    price = get_price(symbol)
    if price is None:
        return "Error: Price ගන්න බැරි උනා"
    rsi = get_rsi(symbol)
    if rsi < 30:
        trend = "Oversold - පහලටම වැටිලා"
        signal = "WAIT - තාම Buy කරන්න එපා"
    elif rsi > 70:
        trend = "Overbought - ගොඩක් උඩට ගිහින්"
        signal = "WAIT - තාම Buy කරන්න එපා"
    else:
        trend = "Sideways"
        signal = "WAIT"
    tp1 = round(price * 1.02, 4)
    tp2 = round(price * 1.04, 4)
    sl = round(price * 0.98, 4)
    return f"📊 {symbol} Analysis\n\n💰 Price: ${price}\n📈 RSI: {rsi}\n📉 Trend: {trend}\n\n🎯 Signal: {signal}\n\nTP1: ${tp1}\nTP2: ${tp2}\nSL: ${sl}\n\n⚠️ මේක Analysis Tool එකක් විතරයි."

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 Welcome!\n\n/all - ඔක්කොම Price\n/signal BTC - Analysis (Free දවසට 2යි)\n/signalall - Premium Only")

@bot.message_handler(commands=['all', 'coins'])
def all_coins(message):
    txt = "💰 All Coins\n\n"
    for c in COINS:
        p = get_price(c)
        if p:
            txt += f"{c}: ${p}\n"
    bot.reply_to(message, txt)

@bot.message_handler(commands=['signal'])
def signal(message):
    user_id = message.from_user.id
    if not can_use_signal(user_id):
        bot.reply_to(message, "⚠️ Free Limit ඉවරයි!\n\nදවසට 2යි Free. Premium ගන්න Admin ට කියපන්.")
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Use කරන්න: /signal BTC")
        return
    symbol = parts[1].upper()
    bot.reply_to(message, make_signal_text(symbol))

@bot.message_handler(commands=['signalall'])
def signalall(message):
    if not is_premium(message.from_user.id):
        bot.reply_to(message, "🔒 මේක Premium Feature එකක්.")
        return
    bot.reply_to(message, "Premium SignalAll... Coin 15ම Analysis කරනවා.")
    for c in COINS:
        bot.send_message(message.chat.id, make_signal_text(c))

print("Bot is running...")
bot.polling()
