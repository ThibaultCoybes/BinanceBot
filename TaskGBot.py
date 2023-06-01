
# Remplacez "YOUR_TELEGRAM_BOT_TOKEN" par votre propre jeton d'accès
import time
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram import Update
from binance import Client
import requests

telegram_bot_token = "6080747951:AAHx0ltFzDrLJ3-77oQ6Au8KwRtLF9C6brs"

# Remplacez "YOUR_BINANCE_API_KEY" et "YOUR_BINANCE_API_SECRET" par vos propres clés API Binance
binance_api_key = "UYeVLKKYff1jI8J5aLYjATsQykVXgfoCgLSELpPSOcIQQYJFDWeCidfavfEixAsg"
binance_api_secret = "NfQjl9ct2pHtzyeYudE2reFmJk6m0Eny4KRHeFkhxnWgcpcf56sMumUak2yhrS6C"

# Créez un client Binance
client = Client(binance_api_key, binance_api_secret)

# Symbole de la crypto-monnaie que vous souhaitez récupérer les données
cryptoList = [
    "BTCUSDT",
    "ADAUSDT",
    "MATICUSDT",
    "RNDRUSDT",
    "SOLUSDT"
]


def get_open_orders() -> str:
    orders = client.get_open_orders()
    if orders:
        formatted_orders = []
        for order in orders:
            symbol = order['symbol']
            side = order['side']
            quantity = order['origQty']
            price = order['price']
            formatted_order = f"Symbol: {symbol}\nSide: {side}\nQuantity: {quantity}\nPrice: {price}\n"
            formatted_orders.append(formatted_order)
        return "\n".join(formatted_orders)
    else:
        return "Aucun ordre en cours."


def get_portfolio() -> str:
    try:
        account_info = client.get_account()
    except Exception as e:
        if 'Timestamp for this request was' in str(e):
            # Obtenir l'heure du serveur Binance
            server_time = client.get_server_time()
            timestamp = server_time['serverTime']
            client.timestamp = timestamp  # Mettre à jour le timestamp du client Binance
            return get_portfolio()
        else:
            return "Erreur lors de la récupération des informations sur le portefeuille."

    balances = account_info['balances']
    portfolio = [f"{balance['asset']}: {float(balance['free']) + float(balance['locked'])}" for balance in balances if (
        float(balance['free']) + float(balance['locked'])) > 0]
    if portfolio:
        return "\n".join(portfolio)
    else:
        return "Le portefeuille est vide."


def start_bot(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Bot démarré. Utilisez /order pour obtenir les ordres en cours et /wallet pour obtenir les informations sur le portefeuille. Vous pouvez aussi utilisé /currentPrice pour étudié les derniers prix des cryptos renseignées")


def handle_order_command(update: Update, context: CallbackContext):
    orders = get_open_orders()
    if orders:
        message = "Ordres en cours :\n\n" + orders
    else:
        message = "Aucun ordre en cours."

    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def handle_wallet_command(update: Update, context: CallbackContext):
    portfolio = get_portfolio()
    if portfolio:
        message = "Portefeuille :\n\n" + portfolio
    else:
        message = "Le portefeuille est vide."
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def handle_current_price(update: Update, context: CallbackContext):

    # Intervalle de temps des données (par exemple, 1m pour des bougies de 1 minute)
    interval = Client.KLINE_INTERVAL_1MINUTE

    for symbol in cryptoList:
        # Récupérer les dernières données (la dernière bougie)
        klines = client.get_klines(symbol=symbol, interval=interval, limit=1)
        # Afficher les données
        if len(klines) > 0:
            latest_kline = klines[0]
            open_price = latest_kline[1]
            high_price = latest_kline[2]
            low_price = latest_kline[3]
            close_price = latest_kline[4]
            volume = latest_kline[5]
            message = f"Dernière bougie {symbol} - \n Ouverture: {open_price}, \n Haut: {high_price}, \n Bas: {low_price}, \n Fermeture: {close_price}, \n Volume: {volume}"
        else:
            message = "Aucune donnée disponible pour le symbole spécifié."
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=message)


def handle_crypto_add(update: Update, context: CallbackContext):
    # Récupérer le mot suivant après la commande

    args = context.args
    if len(args) > 0:
        mot = args[0]
        # Appel à l'API Binance pour récupérer les informations d'échange
        response = requests.get('https://api.binance.com/api/v3/exchangeInfo')

        if response.status_code == 200:
            # Extraction des noms de crypto-monnaies à partir de la réponse JSON
            exchange_info = response.json()
            symbols = [symbol['symbol'] for symbol in exchange_info['symbols']]

            # Affichage des noms de crypto-monnaies
            for symbol in symbols:
                if symbol == mot:
                    message = f"La crypto {mot} a était ajoutée a la liste."
                    cryptoList.append(mot)
        else:
            message = f'Une erreur s\'est produite lors de l\'appel à l\'API Binance, le nom de votre Crypto est surrement mal écrit'
    else:
        message = f"Veuillez spécifier une crypto après la commande."

    context.bot.send_message(
        chat_id=update.effective_chat.id, text=message)


def main():
    # Créez une instance du bot Telegram
    updater = Updater(token=telegram_bot_token, use_context=True)

    # Obtenez le gestionnaire de dispatcher pour enregistrer les gestionnaires de commandes
    dispatcher = updater.dispatcher

    # Définissez les gestionnaires de commandes
    dispatcher.add_handler(CommandHandler("start", start_bot))
    dispatcher.add_handler(CommandHandler("order", handle_order_command))
    dispatcher.add_handler(CommandHandler("wallet", handle_wallet_command))
    dispatcher.add_handler(CommandHandler(
        "currentPrice", handle_current_price))
    dispatcher.add_handler(CommandHandler(
        "cryptoAdd", handle_crypto_add))

    # Démarrez le bot
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
