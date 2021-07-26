import flask
from . import config
from sqlalchemy import create_engine
app = flask.Flask(__name__)

db_file = "./config/database.ini"

db_config = config.config_db(db_file)

db_url = f'postgresql+psycopg2://{db_config["user"]}:{db_config["password"]}@{db_config["host"]}:{db_config["port"]}/{db_config["database"]}'
    
print(db_url)

# Create a SQLAlchemy engine instance

alchemyEngine   = create_engine(db_url)
# Connect to PostgreSQL server

conn    = alchemyEngine.connect()