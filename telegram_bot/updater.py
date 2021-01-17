from bs4 import BeautifulSoup
import requests
import logging
from .models import UpdateLog, UserSetting, LoadTime, SentSong
from .config import DefaultConfig as Config
from datetime import datetime, date, timedelta
import re

from mutagen.mp4 import MP4Cover
from mutagen import File
from io import BytesIO
from PIL import Image
import time
import pytube


class Updater:
    update_logs_row_name: str = None

    def get_and_send_updates(self):
        raise NotImplementedError

    def should_run(self) -> bool:
        return True

    def get_entry(self) -> UpdateLog:
        query = Config.session.query(UpdateLog)
        entry = query.filter(UpdateLog.topic == self.update_logs_row_name).first()
        return entry

    def get_local_last_update(self) -> str:
        entry = self.get_entry()
        str_result = entry.last_update
        return str_result

    def set_local_last_update(self, value: str) -> None:
        entry = self.get_entry()
        entry.last_update = value


class OverallUpdater(Updater):
    update_logs_row_name = "overall"

    def get_and_send_updates(self) -> None:
        if self.should_run():
            CSGOUpdater().get_and_send_updates()
            LoadUpdater().get_and_send_updates()
            YoutubeUpdater().get_and_send_updates()

            now = datetime.utcnow()
            now_str = now.strftime(Config.date_format)
            self.set_local_last_update(now_str)

    def should_run(self) -> bool:
        last_update_str = self.get_local_last_update()
        last_update = datetime.strptime(last_update_str, Config.date_format)
        now = datetime.utcnow()
        return (now - last_update).seconds > 60  # 1 minute


class CSGOUpdater(Updater):
    update_logs_row_name = "csgo"

    def get_subscribed_chats(self) -> list[UserSetting]:
        query = Config.session.query(UserSetting)
        # column = self.chat_settings_name
        chats: list[UserSetting] = query.filter(UserSetting.csgo == True).all()
        return chats

    def get_and_send_updates(self):
        if self.should_run():
            local_time = self.get_local_last_update()
            remote_time, update_text = self.get_remote_last_update()

            if local_time != remote_time:
                update_str = "Hi, a new CS:GO update is here!\n" + update_text.replace("TWEET", "")
                chats = self.get_subscribed_chats()
                for chat in chats:
                    chat_id = chat.chat_id
                    logging.debug(f"Sending CS:GO update message to {chat_id}")
                    Config.bot.send_message(chat_id, update_str)

            self.set_local_last_update(remote_time)

    def get_remote_last_update(self) -> (str, str):
        url = "https://blog.counter-strike.net/index.php/category/updates/"
        source = requests.get(url)
        text = source.text
        soup = BeautifulSoup(text, features="html.parser")
        update_time = str(soup.find("p", {"class", "post_date"}).text).replace("   - ", "")
        update_text = soup.find("div", {"class", "inner_post"}).text
        return update_time, update_text


class LoadUpdater(Updater):
    update_logs_row_name = "load"

    def get_subscribed_chats(self) -> list[UserSetting]:
        query = Config.session.query(UserSetting)
        # column = self.chat_settings_name
        chats = query.filter(UserSetting.load == True).all()
        return chats

    def get_and_send_updates(self):
        if self.should_run():
            stage = self.get_remote_stage()
            today = date.today().day
            suburb_codes = self.get_suburb_codes()
            for code in suburb_codes:
                chats = self.get_subscribed_chats_for(code)
                for chat in chats:
                    chat_id = chat.chat_id
                    if stage == 0:
                        pass
                    else:
                        times_today = self.get_times_for_today(today, stage, code)
                        date_tomorrow = (date.today() + timedelta(days=1)).day
                        times_tomorrow = self.get_times_for_today(date_tomorrow, stage, code)
                        email_text = f"Hi there, {code}, \nWe are currently at stage {stage} loadshedding. " \
                                     f"\nWe will be loadshedding today {times_today}. " \
                                     f"\nWe will be loadshedding tomorrow {times_tomorrow}."

                        logging.debug(f"Sending loadshedding update to {chat_id}")
                        Config.bot.send_message(chat_id, email_text)

            now = datetime.utcnow()
            now_str = now.strftime(Config.date_format)
            self.set_local_last_update(now_str)

    def get_subscribed_chats_for(self, code) -> list[UserSetting]:
        query = Config.session.query(UserSetting)
        chats = query.filter(
            UserSetting.load == True,
            UserSetting.load_code == code
        ).all()
        return chats

    def get_suburb_codes(self):
        query = Config.session.query(UserSetting.load_code)
        chats: list[UserSetting] = query.distinct()
        return [chat.load_code for chat in chats]

    def should_run(self) -> bool:
        last_update_str = self.get_local_last_update()
        last_update = datetime.strptime(last_update_str, Config.date_format)
        now = datetime.utcnow()
        return (now - last_update).seconds > Config.load_update_frequency

    def get_remote_stage(self):
        url = "https://www.citypower.co.za/customers/Pages/Load_Shedding_Downloads.aspx"
        source = requests.get(url)
        text = source.text
        soup = BeautifulSoup(text, features="html.parser")
        if soup.find(string=re.compile("NOT.LOAD.SHEDDING", re.I)) is not None:
            return 0
        else:
            s = str(soup.find(string=re.compile("Stage [0-9]")))
            s = s[s.index("Stage "):s.index("Stage ") + 7]
            return int(s.replace("Stage ", ""))

    def get_times_for_today(self, today, stage, code):
        # Consults the database to provide the times for a given date, stage and area
        query = Config.session.query(LoadTime.time)
        data: list[LoadTime] = query.filter(
            LoadTime.day == today,
            LoadTime.stage <= stage,
            LoadTime.code == code
        ).all()
        times = [row.time for row in data]

        result = ""
        if len(times) == 0:
            result = "never"
        else:
            times.sort()
            first_time = times[0]
            previous_time = times[0]
            times.append(100)
            times.append(
                100 + 2)  # these 2 are added since result will not append the last pair of times
            for t in times:
                if t - previous_time <= 2:
                    previous_time = t
                else:
                    result = result + f" and from {first_time}:00 to {previous_time + 2}:30"
                    first_time = t
                    previous_time = t
            result = result[5:]  # remove the " and "
        return result


class YoutubeUpdater(Updater):
    update_logs_row_name = "youtube"
    max_song_len = Config.youtube_max_song_length

    def get_and_send_updates(self):
        if self.should_run():
            sent_songs = self.get_local_songs()
            songs_to_send = self.get_remote_songs()
            for song_to_send in songs_to_send:
                if song_to_send not in sent_songs:
                    chat_id = song_to_send[0]
                    url = song_to_send[1]
                    self.send_song(chat_id, url)
                    self.insert_song_to_db(chat_id, url)

    def get_local_songs(self):
        query = Config.session.query(SentSong)
        data: list[SentSong] = query.all()
        result = []
        for row in data:
            result.append((row.chat_id, row.youtube_url))
        return result

    def get_remote_songs(self):
        query = Config.session.query(UserSetting)
        users: list[UserSetting] = query.all()
        result = []

        for row in users:
            if (row.youtube_url is not None) or (row.youtube_url != ""):
                playlist = pytube.Playlist(row.youtube_url)
                # playlist._video_regex = re.compile(r"\"url\":\"(/watch\?v=[\w-]*)")
                for url in playlist.video_urls:
                    result.append((row.chat_id, str(url)))

        return result

    def send_song(self, chat_id, link) -> None:
        # Load video
        time.sleep(10)
        print(link)
        video = pytube.YouTube(link)

        # Check if video length is greater than 10 minutes
        if video.length > self.max_song_len:
            return None

        # Stream the video and set the title. It saves as mp4 even though it's only audio
        stream = video.streams.filter(only_audio=True).first()
        bio = BytesIO()
        stream.stream_to_buffer(bio)
        bio.name = video.title
        bio.seek(0)
        if " - " in bio.name:
            artist_name = bio.name[:bio.name.index(" - ")]
            song_name = bio.name[bio.name.index(" - ") + len(" - "):]
            album_name = video.author
        else:
            artist_name = video.author
            song_name = bio.name
            album_name = video.author

        # Get thumbnail as a BytesIO object
        thumb = self.get_thumb(video.thumbnail_url)

        # When I save the song to music on my phone, the meta tags don't save
        # So here I do it manually by setting it into the audio itself
        audio = File(bio)
        audio["\xa9alb"] = album_name  # Album name
        audio["\xa9nam"] = song_name  # Song name
        audio["\xa9ART"] = artist_name  # Artist name
        audio["covr"] = [MP4Cover(thumb.read(), imageformat=MP4Cover.FORMAT_JPEG)]  # Thumbnail
        audio.save(bio)

        # Reset to 0
        bio.seek(0)
        thumb.seek(0)

        # Send it
        logging.debug(f"Sending audio {artist_name} - {song_name} (album {album_name})")
        Config.bot.send_audio(chat_id, bio, duration=video.length, title=song_name + ".mp3",
                              performer=artist_name, thumb=thumb, timeout=1000)
        # self.bot.send_document(chat_id, bio, bio.name, timeout=1000)
        return None

    def get_thumb(self, image_url: str) -> BytesIO:
        response = requests.get(image_url)
        img: Image = Image.open(BytesIO(response.content))
        size = (90, 90)
        img.thumbnail(size)
        thumb_bio = BytesIO()
        img.save(thumb_bio, "JPEG")
        thumb_bio.seek(0)
        return thumb_bio

    def insert_song_to_db(self, chat_id, url):
        song = SentSong(chat_id=chat_id, youtube_url=url)
        Config.session.add(song)
        Config.session.commit()
