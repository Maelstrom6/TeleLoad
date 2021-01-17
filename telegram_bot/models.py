from .config import DefaultConfig as Config
from sqlalchemy import Column, String, Integer, Boolean, TIMESTAMP


class UpdateLog(Config.Base):
    __tablename__ = "UpdateLog"
    topic = Column(String, primary_key=True)
    last_update = Column(String, primary_key=True)


class UserSetting(Config.Base):
    __tablename__ = "UserSetting"
    chat_id = Column(Integer, primary_key=True)
    chat_type = Column(String, default="private")
    load = Column(Boolean, default=False)
    load_code = Column(String, default="")
    csgo = Column(Boolean, default=False)
    dota = Column(Boolean, default=False)
    youtube_url = Column(String, default="")


class LoadTime(Config.Base):
    __tablename__ = "LoadTime"
    day = Column(Integer, primary_key=True)
    stage = Column(Integer, primary_key=True)
    time = Column(Integer, primary_key=True)
    code = Column(String)


class SentSong(Config.Base):
    __tablename__ = "SentSong"
    chat_id = Column(Integer, primary_key=True)
    youtube_url = Column(String, primary_key=True)


class ChatHistory(Config.Base):
    __tablename__ = "ChatHistory"
    chat_id = Column(Integer, primary_key=True)
    message_id = Column(Integer, primary_key=True)
    message_date = Column(TIMESTAMP)
    message_text = Column(String)
    message_response = Column(String)
    complete = Column(Boolean, default=True)


Config.Base.metadata.create_all(Config.engine)
Config.factory.configure(bind=Config.engine)
Config.session = Config.factory()
