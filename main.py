from flask import jsonify, make_response, Request
import telegram
import logging
from telegram_bot import DefaultConfig as Config, OverallUpdater, Queryer, Observer

ok_response = "ok"


def try_catch(function):
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as error:
            logging.exception(str(error))
            Config.session.rollback()
            return make_response("Error occurred")
    return wrapper


@try_catch
def receiver(request: Request):
    method = request.method
    if method == "POST":
        request_json = request.get_json(force=True)
        logging.error(f"Received a POST request: {request_json}")
        update: telegram.Update = telegram.Update.de_json(request_json, Config.bot)
        chat_id = update.message.chat.id

        # if update.effective_message.effective_type == 'photo':
        if len(update.message.photo) != 0:
            response = Observer().get_response(update.message)
        else:
            response = Queryer().get_response(update.message)

        if response is None:
            return ok_response
        return send_message_in_https_response(chat_id, response)

    elif method == "GET":
        logging.error(f"Received a GET request")
        updater = OverallUpdater()
        updater.get_and_send_updates()

    else:
        logging.error(f"Received {method} request. I don't know what to do.")
    return make_response("Completed the request")


def send_message_in_https_response(chat_id, response: str):
    data = {"method": "sendMessage", "chat_id": chat_id, "text": response}
    return jsonify(data)
