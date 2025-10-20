from flask import Flask,jsonify
from models import db
from config import config
from flask_migrate import migrate
def create_app():
    app=Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)
    migrate=migrate(app,db)
    from routes.auth import auth_bp
    from routes.hotels import hotels_bp
    from routes.bookings import bookings_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(hotels_bp, url_prefix='/api/hotels')
    app.register_blueprint(bookings_bp, url_prefix='/api/bookings')

    def index():
        return jsonify({"status":"ok","message":"Hotel Reservation API"})

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)