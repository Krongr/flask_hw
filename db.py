import configparser
import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()

class Users(Base):
    __tablename__ = 'users'
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    name = sq.Column(sq.String, unique=True, nullable=False)
    password = sq.Column(sq.String, nullable=False)
    ads = relationship('Ads', backref='ad_owner')

class Ads(Base):
    __tablename__ = 'ads'
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    title = sq.Column(sq.String, nullable=False)    
    text = sq.Column(sq.Text, nullable=False)
    owner = sq.Column(sq.Integer, sq.ForeignKey('users.id'), nullable=False)
    created_at = sq.Column(sq.DateTime, server_default=sq.func.now())


config = configparser.ConfigParser()
config.read("db_config.ini")

# DB config:
type=config['DB']['TYPE']
name=config['DB']['NAME']
host=config['DB']['HOST']
port=config['DB']['PORT']
user=config['DB']['USER']
password=config['DB']['PASSWORD']

db = f'{type}://{user}:{password}@{host}:{port}/{name}'
engine = sq.create_engine(db)

if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)
