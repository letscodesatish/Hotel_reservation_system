from flask_sqlalchemy import SQLAlchemy
from datetime import datetime,timezone
db=SQLAlchemy()
class user(db.Model):
    __tablename__= "users"
    id = db.Column(db.Integer, primary_key=True)
    email= db.column(db.String(50),unique=True,nullable=False)
    password_hash=db.column(db.string(50),nullable=False)
    full_name=db.column(db.string(50))
    role=db.column(db.enum("customer","admin"),default="customer")
    created_at=db.column(db.DateTime,default=datetime.now(timezone.utc))

class hotel(db.Model):
    __tablename__="hotels"
    id=db.column(db.Integer,primary_key=True)
    name=db.column(db.string(30),nullable=False)
class roomtype(db.Model):
    __tablename__="roomtypes"
    id=db.column(db.integer,primary_key=True)
    room_type_id=db.column(db.integer,db.foreignkey("room_types.id"),nullable=False)
    date=db.column(db.date,nullable=False)
    available_count=db.column(db.integer,nullable=False)
    price_override=db.column(db.numeric(10,2))
class roominventory(db.Model):
    __tablename__="room_inventory"
    id=db.column(db.integer,primary_key=True)
    room_type_id=db.column(db.integer,db.foreignkey("room_type.id"), nullable=False)
    date=db.column(db.Date,nullable=False)
    available_count=db.column(db.integer,nullable=False)
    price_override=db.column(db.numeric(10,2))
class bookings(db.Model):
    __tablename__="bookings"
    id=db.column(db.integer,primary_key=True)
    user_id=db.column(db.integer,db.foreignkey("users.id"),nullable=False)
    hotel_id=db.column(db.integer,db.foreignkey("hotels.id"),nullable=False)
    status=db.column(db.enum("pending","confirmed","cancelled","checked_in","checked_out"),default="pending")
    total_price=db.column(db.numeric(10,2),nullable=False)
    checkin_dat= db.column(db.date,nullable=False)
    checkout_date=db.column(db.date,nullable=False)
class bookingitem(db.Model):
    __tablename__="booking_items"
    id=db.column(db.biginteger,primary_key=True)
    booking_id=db.column(db.biginteger,db.foreignkey("bookings.id"),nullable=False)
    room_type_id=db.column(db.integer,db.foreignkey("room_types.id"),nullable=False)
    quantity=db.column(db.integer,nullable=False)
    price_per_room=db.column(db.numeric(10,2),nullable=False)
