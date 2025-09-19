nano 8.6                    bot.py
import os
import logging
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# ======================
# CONFIG (ENV VARIABLES)
# ======================
BOT_TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.twelvedata.com/price"

ACCOUNT_BALANCE = 1000  # default balance

# ======================
# LOGGING
# ======================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ======================
# STATE
# ======================
user_state = {}

# ======================
# SYMBOL MAP (fix None issue)
# ======================
SYMBOL_MAP = { # Forex majors
    "EURUSD": "EUR/USD", "GBPUSD": "GBP/USD", "USDJPY": "USD/JPY",
    "USDCHF": "USD/CHF", "AUDUSD": "AUD/USD", "USDCAD": "USD/CAD",
    "NZDUSD": "NZD/USD",
    # Forex crosses
    "EURJPY": "EUR/JPY", "EURGBP": "EUR/GBP", "EURCHF": "EUR/CHF",
    "GBPJPY": "GBP/JPY", "GBPCHF": "GBP/CHF", "AUDJPY": "AUD/JPY",
    "AUDNZD": "AUD/NZD", "NZDJPY": "NZD/JPY", "CADJPY": "CAD/JPY",
    "CHFJPY": "CHF/JPY", "EURAUD": "EUR/AUD", "EURNZD": "EUR/NZD",
    "GBPAUD": "GBP/AUD", "GBPNZD": "GBP/NZD", "AUDCAD": "AUD/CAD",
    "NZDCAD": "NZD/CAD", "AUDCHF": "AUD/CHF", "NZDCHF": "NZD/CHF",
    # Commodities
    "XAUUSD": "XAU/USD", "XAGUSD": "XAG/USD", "OILUSD": "WTI",
    # Crypto
    "BTCUSD": "BTC/USD", "ETHUSD": "ETH/USD", "SOLUSD": "SOL/USD",
    # Indices
    "US30": "DJI", "NAS100": "NDX", "SPX500": "SPX"
}

# ======================
# ASSET LISTS
# ======================
FOREX_PAIRS = list({k for k in SYMBOL_MAP.keys() if "/" in SYMBOL_MAP[>
COMMODITIES = ["XAUUSD", "XAGUSD", "OILUSD"]
CRYPTO = ["BTCUSD", "ETHUSD", "SOLUSD"]
INDICES = ["US30", "NAS100", "SPX500"]# ======================
# ASSET LISTS
# ======================
FOREX_PAIRS = list({k for k in SYMBOL_MAP.keys() if "/" in SYMBOL_MAP[>
COMMODITIES = ["XAUUSD", "XAGUSD", "OILUSD"]
CRYPTO = ["BTCUSD", "ETHUSD", "SOLUSD"]
INDICES = ["US30", "NAS100", "SPX500"]

# ======================
# FUNCTIONS
# ======================
def get_price(symbol):
    api_symbol = SYMBOL_MAP.get(symbol, symbol)
    try:
        r = requests.get(f"{BASE_URL}?symbol={api_symbol}&apikey={API_>
        data = r.json()
        return float(data.get("price"))
    except Exception as e:
        logger.error(f"Price fetch failed: {e}")
        return None

def calc_lot(balance, risk_pct, sl_pips, pip_value=10):
    risk_amount = balance * (risk_pct / 100)
    lot_size = risk_amount / (sl_pips * pip_value)
    return round(lot_size, 2) # ======================
# BOT HANDLERS
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state[update.effective_chat.id] = {}
    keyboard = [
        [InlineKeyboardButton("💱 Forex", callback_data="cat_forex")],
        [InlineKeyboardButton("🪙 Commodities", callback_data="cat_com>
        [InlineKeyboardButton("₿ Crypto", callback_data="cat_crypto")],
        [InlineKeyboardButton("📊 Indices", callback_data="cat_indices>
    ]
    await update.message.reply_text(
        "📊 *Lot Size Calculator*\nChoose Asset Category:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def menu(update: Update, pairs, back_to="main"):
    keyboard = [[InlineKeyboardButton(p, callback_data=f"pair_{p}")] f>
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"ba>
    await update.callback_query.edit_message_text(
        "🔎 Select Symbol:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    if query.data == "cat_forex": await menu(update, FOREX_PAIRS, "main")
    elif query.data == "cat_commodities":
        await menu(update, COMMODITIES, "main")
    elif query.data == "cat_crypto":
        await menu(update, CRYPTO, "main")
    elif query.data == "cat_indices":
        await menu(update, INDICES, "main")

    elif query.data.startswith("pair_"):
        symbol = query.data.split("_")[1]
        user_state[chat_id]["symbol"] = symbol
        keyboard = [
            [InlineKeyboardButton("1%", callback_data="risk_1"),
             InlineKeyboardButton("2%", callback_data="risk_2")],
            [InlineKeyboardButton("5%", callback_data="risk_5"),
             InlineKeyboardButton("10%", callback_data="risk_10")],
            [InlineKeyboardButton("⬅️ Back", callback_data="cat_forex")]
        ]
        await query.edit_message_text(
            f"⚖️ Select Risk % for {symbol}:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data.startswith("risk_"):
        risk = int(query.data.split("_")[1])
        user_state[chat_id]["risk"] = risk
        await query.edit_message_text("📏 Enter Stop Loss (pips):")

    elif query.data.startswith("back_"):
        target = query.data.split("_")[1]
        if target == "main":
            await start(query, context) async def stoploss_input(update: Update, context: ContextTypes.DEFAULT>
    chat_id = update.message.chat_id
    if "risk" in user_state.get(chat_id, {}):
        try:
            sl = int(update.message.text)
            user_state[chat_id]["sl"] = sl

            symbol = user_state[chat_id]["symbol"]
            risk = user_state[chat_id]["risk"]

            price = get_price(symbol)
            lot = calc_lot(ACCOUNT_BALANCE, risk, sl)

            text = f"""
✅ *Lot Size Calculation*

📊 Symbol: {symbol}
💵 Price: {price if price else "⚠️ Not Available"}
⚖️ Lot Size: {lot}

📌 Account: ${ACCOUNT_BALANCE}
📉 Risk: {risk}%
🛑 Stop Loss: {sl} pips
"""
            keyboard = [[InlineKeyboardButton("⬅️ Back to Main Menu", c>
            await update.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        except:
            await update.message.reply_text("❌ Please enter a valid n>

# ======================
# MAIN
# ====================== def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, st>
    app.run_polling()

if __name__ == "__main__":
    main() 
