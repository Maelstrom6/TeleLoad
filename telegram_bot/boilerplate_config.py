import telegram
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class DefaultConfig:
    # In order to run locally, you need application credentials.
    # Path to credentials should be the environment variable GOOGLE_APPLICATION_CREDENTIALS.

    project_id = "some-google-project-id"  # change this -----------------------
    bigquery_dataset = "telegramdataset"  # change this -----------------------
    bigquery_table = "telegram-table"  # change this -----------------------
    bigquery_uri = f'bigquery://{project_id}/{bigquery_dataset}'
    engine = create_engine(bigquery_uri)

    Base = declarative_base()

    factory = sessionmaker()
    session = factory()

    telegram_token = "4429054:randomstringoflettersandthings"  # change this -----------------------
    bot = telegram.Bot(token=telegram_token)

    date_format = "%Y-%m-%d %H:%M:%S.%f"

    youtube_max_song_length = 20 * 60  # 20 minutes
    load_update_frequency = 8 * 60 * 60  # 8 hours
