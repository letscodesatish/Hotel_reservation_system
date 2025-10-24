from flask_sqlalchemy import SQLAlchemy
from datetime import datetime,timezone
db=SQLAlchemy()

class user(db.Model):
    __tablename__= "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password_hash=db.Column(db.String(50),nullable=False)
    full_name=db.Column(db.String(50))
    role=db.Column(db.Enum("customer","admin"),default="customer")
    created_at=db.Column(db.DateTime,default=datetime.now(timezone.utc))

class hotel(db.Model):
    __tablename__="hotels"
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(30),nullable=False)
    location = db.Column(db.String(255))
    rating = db.Column(db.Float, default=0.0)

# --- THIS IS THE CORRECTED ROOM_TYPE CLASS ---
class room_type(db.Model):
    __tablename__="room_types"
    id=db.Column(db.Integer,primary_key=True)
    
    # A room type must belong to a hotel
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotels.id'), nullable=False)
    
    # Properties of the room type itself
    name = db.Column(db.String(100), nullable=False)
    base_price = db.Column(db.Numeric(10, 2), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    total_count = db.Column(db.Integer, default=10) # Example: 10 rooms of this type

class room_inventory(db.Model):
    __tablename__="room_inventory"
    id=db.Column(db.Integer,primary_key=True)
    room_type_id=db.Column(db.Integer,db.ForeignKey("room_types.id"), nullable=False)
    date=db.Column(db.Date,nullable=False)
    available_count=db.Column(db.Integer,nullable=False)
    price_override=db.Column(db.Numeric(10,2))

class bookings(db.Model):
    __tablename__="bookings"
    id=db.Column(db.BigInteger,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False)
    hotel_id=db.Column(db.Integer,db.ForeignKey("hotels.id"),nullable=False)
    status=db.Column(db.Enum("pending","confirmed","cancelled","checked_in","checked_out"),default="pending")
    total_price=db.Column(db.Numeric(10,2),nullable=False)
    
    # --- FIXED TYPO: checkin_date ---
    checkin_date = db.Column(db.Date,nullable=False)
    checkout_date=db.Column(db.Date,nullable=False)

class bookingitem(db.Model):
    __tablename__="booking_items"
    id=db.Column(db.BigInteger,primary_key=True)
    booking_id=db.Column(db.BigInteger,db.ForeignKey("bookings.id"),nullable=False)
    room_type_id=db.Column(db.Integer,db.ForeignKey("room_types.id"),nullable=False)
    quantity=db.Column(db.Integer,nullable=False)
    price_per_room=db.Column(db.Numeric(10,2),nullable=False)