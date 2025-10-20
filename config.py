import os
class config:
    secret_key=os.environ.get("secret_key","change_me")
    sqlalchemy_database_uri=os.environ.get("database_url","mysql+pymysql://root:passward@localhost/hotel_reservation")
    sqlalchemy_track_modifications=False
    jwt_secret_key=os.environ.get("jwt_secret_key","jwt-secret")