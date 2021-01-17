from .config import DefaultConfig as Config
import telegram
from io import BytesIO
from .google_apis import Vision


class Observer:
    def get_response(self, message: telegram.Message):
        file = Config.bot.getFile(message.photo[-1].file_id)
        ba = file.download_as_bytearray()
        bio = BytesIO(ba)
        vision = Vision()
        text = vision.get_text(bio.getvalue())
        return text
