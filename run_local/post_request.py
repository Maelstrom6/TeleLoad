from telegram_bot.config import DefaultConfig as Config
from telegram_bot.queryer import Queryer
import telegram

message = "/start"
length = len(message)

request = {
    'update_id': 7000000,
    'message': {
        'message_id': 101,
        'from': {
            'id': 123456789,
            'is_bot': False,
            'first_name': 'Bob',
            'last_name': 'The Builder',
            'language_code': 'en'
        },
        'chat': {
            'id': 123456789,
            'first_name': 'Bob',
            'last_name': 'The Builder',
            'type': 'private'
        },
        'date': 1610291691,
        'text': message, 'entities': [{
            'offset': 0, 'length': length, 'type': 'bot_command'
        }]
    }
}

update: telegram.Update = telegram.Update.de_json(request, Config.bot)
response = Queryer().get_response(update.message)
print(response)
# will get an OutOfContext error but that is nothing to worry about
