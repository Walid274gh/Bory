import requests
import time
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Token du bot Telegram
TELEGRAM_BOT_TOKEN = '7405265138:AAGkpBBd1tO_QSuIsX15uJNtXoBNQCLS9Ec'

# Fonction pour obtenir l'OTP
def get_otp(mobile_number):
    headers = {
        'User-Agent': 'okhttp/4.9.3',
        'Connection': 'Keep-Alive',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    data = {
        'client_id': 'ibiza-app',
        'grant_type': 'password',
        'mobile-number': mobile_number,
        'language': 'FR',
    }

    response = requests.post('https://ibiza.ooredoo.dz/auth/realms/ibiza/protocol/openid-connect/token', headers=headers, data=data)
    return response

# Fonction pour obtenir le token
def get_token(mobile_number, otp):
    headers = {
        'User-Agent': 'okhttp/4.9.3',
        'Connection': 'Keep-Alive',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    data = {
        'client_id': 'ibiza-app',
        'otp': otp,
        'grant_type': 'password',
        'mobile-number': mobile_number,
        'language': 'FR',
    }

    response = requests.post('https://ibiza.ooredoo.dz/auth/realms/ibiza/protocol/openid-connect/token', headers=headers, data=data)
    
    if response.status_code == 200:
        response_json = response.json()
        if 'access_token' in response_json:
            return response_json.get('access_token')
        else:
            print("Erreur de réponse:", response_json)
    else:
        print("Erreur HTTP:", response.status_code, response.text)
    return None

# Fonction pour vérifier le bonus
def check_bonus(token):
    headers = {
        'User-Agent': 'okhttp/4.9.3',
        'Connection': 'Keep-Alive',
        'Authorization': f'Bearer {token}',
        'language': 'FR',
        'request-id': '8e4cfe43-9d00-4027-a1e6-9f9097cf3447',
        'flavour-type': 'gms',
    }

    response = requests.get('https://ibiza.ooredoo.dz/api/v1/mobile-bff/users/balance', headers=headers)
    return response.json()

# Fonction pour démarrer le bot
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Bonjour ! Entrez votre numéro de téléphone.')

# Fonction pour gérer les messages
def handle_message(update: Update, context: CallbackContext) -> None:
    user_data = context.user_data

    if 'step' not in user_data:
        user_data['step'] = 'phone_number'
        update.message.reply_text('Entrez votre numéro de téléphone.')
        return

    if user_data['step'] == 'phone_number':
        user_data['phone_number'] = update.message.text
        otp_response = get_otp(user_data['phone_number'])
        if otp_response.status_code == 200:
            user_data['step'] = 'otp'
            update.message.reply_text('Entrez OTP :')
        else:
            update.message.reply_text('Erreur lors de la demande OTP. Réessayez.')
        return

    if user_data['step'] == 'otp':
        user_data['otp'] = update.message.text
        token = get_token(user_data['phone_number'], user_data['otp'])
        if token:
            user_data['token'] = token
            user_data['step'] = 'done'
            update.message.reply_text('OTP vérifié avec succès ! Vérification du bonus...')
            bonus_info = check_bonus(token)
            if 'accounts' in bonus_info:
                for account in bonus_info['accounts']:
                    if account['accountName'] == 'BonusDataMGMAccountID':
                        update.message.reply_text(f'Bonus : {account["value"]}')
                        break
                else:
                    update.message.reply_text('Aucun bonus trouvé.')
            else:
                update.message.reply_text('Informations non disponibles.')
        else:
            update.message.reply_text('OTP incorrect. Réessayez.')
        return

# Configuration du bot
def main() -> None:
    updater = Updater(TELEGRAM_BOT_TOKEN)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
