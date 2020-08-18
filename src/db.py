from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from os import environ


# Create sqlalchemy engine
engine = None
if environ.get('ENV') == 'dev':
    engine = create_engine('sqlite:///db.sqlite3')
else:
    dbdb   = environ.get('DB_DB')
    name = environ.get('DB_NAME')
    pswd = environ.get('DB_PASS')
    engine = create_engine(f'postgresql://{name}:{pswd}@localhost/{dbdb}')


# Create a session
session = sessionmaker(bind=engine)()


# Create base model
Base = declarative_base()