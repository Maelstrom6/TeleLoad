from .config import DefaultConfig as Config
from .models import UserSetting, ChatHistory
import telegram
import logging
import textwrap


class Command:
    def __init__(self, name: str, func):
        self.name = name
        self.func = func


class Queryer:
    command_delimiter = "\n"

    def __init__(self):
        self.commands = [
            Command("start", self.start),
            Command("help", self.help),
            Command("settings", self.settings),
            Command("cancel", self.cancel),
            Command("update", self.update),
            Command("toggleloadshedding", self.toggle_load),
            Command("togglecsgo", self.toggle_csgo),
            Command("toggledota", self.toggle_dota),
            Command("setcode", self.set_code),
            Command("setyoutube", self.set_youtube),
        ]
        self.command_names = [command.name for command in self.commands]

    def start(self, message: telegram.Message) -> (str, bool):
        user = UserSetting(
            chat_id=message.chat_id,
            chat_type=message.chat.type,
        )
        Config.session.add(user)
        response = """
            Hello there, I am a bot that gives you updates about stuff.
            Type /help for a list of commands.
        """
        response = textwrap.dedent(response[1:])[:-1]
        return response, True

    def help(self, message: telegram.Message) -> (str, bool):
        response = """
            Here are a list of commands:
            /start sends a welcome message.
            /help or help gives a list of commands.
            /settings tells you what you are subscribed to.
            /cancel cancels any string of commands so that you can restart.
            /update searches for updates to send you.
            /toggleloadshedding toggles Loadshedding updates.
            /setcode sets your suburb code for loadshedding updates.
            /togglecsgo toggles CS:GO updates.
            /toggledota toggles DOTA 2 updates.
            /setyoutube sets your YouTube playlist so I can send you new songs for that list.
            Use newlines to write a command if you know that you need to elaborate further.
        """
        response = textwrap.dedent(response[1:])[:-1]
        return response, True

    def settings(self, message: telegram.Message) -> (str, bool):
        query = Config.session.query(UserSetting)
        user: UserSetting = query.filter(UserSetting.chat_id == message.chat_id).first()
        response = []
        if user.load:
            response.append(f"Loadshedding updates with code {user.load_code}")
        if user.csgo:
            response.append("CS:GO updates")
        if user.dota:
            response.append("DOTA 2 updates")
        if user.youtube_url != "":
            response.append(f"Youtube playlist updates from {user.youtube_url}")

        if len(response) == 0:
            response = "You are subscribed to nothing."
        else:
            response = "You are subscribed to " + ", ".join(response) + "."
        return response, True

    def cancel(self, message: telegram.Message) -> (str, bool):
        response = "The last interaction has been canceled. You can begin with a new command."
        return response, True

    def update(self, message: telegram.Message) -> (str, bool):
        from .updater import OverallUpdater
        OverallUpdater().get_and_send_updates()
        response = "If nothing appeared, then are no new updates."
        return response, True

    def set_code(self, message: telegram.Message) -> (str, bool):
        commands = message.text.split(self.command_delimiter)
        if len(commands) == 1:
            response = "What is the area code that I should set for you?"
            return response, False
        else:
            code = commands[-1]
            codes = [f"{num}{char}" for num in range(1, 9) for char in ["A", "B"]]
            if code not in codes:
                response = "That is an invalid area code. " \
                           "A valid code is something like 2B. " \
                           "What is the area code that I should set for you?"
                return response, False
            (
                Config.session.query(UserSetting)
                    .filter(UserSetting.chat_id == message.chat_id)
                    .update({UserSetting.load_code: code}, synchronize_session=False)
            )
            response = f"Your loadshedding code has been set to {code}."
            return response, True

    def set_youtube(self, message: telegram.Message) -> (str, bool):
        commands = message.text.split(self.command_delimiter)
        if len(commands) == 1:
            response = "What is the Youtube playlist URL that I should set for you?"
            return response, False
        else:
            url = commands[-1]
            required_url_base = "https://www.youtube.com/playlist?list="
            if required_url_base != url[:len(required_url_base)]:
                response = "That is an invalid Youtube playlist URL. " \
                           "A valid URL is something like " \
                           "https://www.youtube.com/playlist?list=XYZ. " \
                           "What is the Youtube playlist URL that I should set for you?"
                return response, False
            (
                Config
                .session.query(UserSetting)
                .filter(UserSetting.chat_id == message.chat_id)
                .update({UserSetting.youtube_url: url}, synchronize_session=False)
            )
            response = f"Your Youtube URL has been set to {url}."
            return response, True

    def toggle_load(self, message: telegram.Message) -> (str, bool):
        (
            Config.session.query(UserSetting)
            .filter(UserSetting.chat_id == message.chat_id)
            .update({UserSetting.load: not UserSetting.load}, synchronize_session=False)
        )
        return "Loadshedding notifications have been toggled.", True

    def toggle_csgo(self, message: telegram.Message) -> (str, bool):
        (
            Config.session.query(UserSetting)
            .filter(UserSetting.chat_id == message.chat_id)
            .update({UserSetting.csgo: not UserSetting.csgo}, synchronize_session=False)
        )
        return "CS:GO notifications have been toggled.", True

    def toggle_dota(self, message: telegram.Message) -> (str, bool):
        (
            Config.session.query(UserSetting)
            .filter(UserSetting.chat_id == message.chat_id)
            .update({UserSetting.dota: not UserSetting.dota}, synchronize_session=False)
        )
        return "DOTA 2 notifications have been toggled.", True

    def get_response(self, message: telegram.Message) -> (str, bool):
        text = message.text

        response, complete = self.get_basic_response(message)

        if complete is None:
            query = Config.session.query(ChatHistory)
            last_message: ChatHistory = (
                query
                .filter(ChatHistory.chat_id == message.chat_id)
                .order_by(ChatHistory.message_id.desc())
                .first()
            )
            if last_message is None:
                response, complete = self.help(message)
            elif not last_message.complete:
                message.text = last_message.message_text + self.command_delimiter + message.text
                response, complete = self.get_basic_response(message)
            else:
                response, complete = self.help(message)

        if complete is None:
            logging.error(f"Could not find a suitable response for {text}.")
            response, complete = self.help(message)

        history = ChatHistory(
            chat_id=message.chat_id,
            message_id=message.message_id,
            message_date=message.date,
            message_text=message.text,
            message_response=response,
            complete=complete,
        )
        Config.session.add(history)
        Config.session.commit()
        return response

    def get_basic_response(self, message: telegram.Message) -> (str, bool):
        response, complete = None, None

        for command in self.commands:
            sub = message.text.partition(self.command_delimiter)[0]
            if sub == "/" + command.name:
                response, complete = command.func(message)
        return response, complete

    def save_response(self, message: telegram.Message, response: str, complete: bool):
        history = ChatHistory(
            chat_id=message.chat_id,
            message_id=message.message_id,
            message_date=message.date,
            message_text=message.text,
            message_response=response,
            complete=complete,
        )
        Config.session.add(history)
        Config.session.commit()
