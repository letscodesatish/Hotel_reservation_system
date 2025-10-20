from models import db, roominventory,roomtype,bookings,bookingitem
from sqlalchemy import and_, func
from datetime import timedelta
def book_roomds(user_id,hotel_id,room_type_id,checkin_date,checkout_date,quantity,payment_info=None,coupon_code=None):
    from flask import current_app
    session=db.session
    days=(checkout_date - checkin_date).days 
    if days <=0:
        raise ValueError("Invalid date range")
    try:
        inventories=session.query(roominventory)\
        .filter(
            roominventory.room_type_id==room_type_id,
            roominventory.date>=checkin_date,
            roominventory.date<checkout_date
        )\
       .with_for_update(nowait=False).all()
        if not inventories:
            rt=session.query(roomtype).filter(roomtype.id==room_type_id).with_for_update().one()
            booked_qty=session.query(func.ifnull(func.sum(bookingitem.quantity),0))\
            .join(bookings,bookings.id==bookingitem.booking_id)\
            .filter(
                bookingitem.room_type_id==room_type_id,
                bookings.status.in_(("pending","confirmed")),
                not_(
                    (bookings.checkout_date<=checkin_date)| (bookings.checkin_date>=checkout_date)
                )
            ).scalar()
            available=rt.total_count -(booked_qty or 0)
            if available < quantity:
                raise Exception("Insufficient rooms available")
            else:
                for inv in inventories:
                   if  inv.available_count < quantity:
                       raise Exception("Not enough availability on date: %s" % inv.date.isoformat())
            
            total_price=0
            if inventories:
                for inv in inventories:
                    price=inv.price_override if inv.price_override is not None else inv.room_type.base_price
                    total_price += float(price)* quantity
            else:
                rt=session.query(roomtype).get(room_type_id)
                total_price= float(rt.base_price)* days * quantity
            booking=bookings(
                user_id=user_id,
                hotel_id=hotel_id,
                total_amount=total_price,
                checkin_date=checkin_date,
                checkout_date=checkout_date,
                status="pending",
            )
            session.add(booking)
            session.flush()
            bi=bookingitem(
                booking_id=booking.id,
                room_type_id=room_type_id,
                quantity=quantity,
                price_per_room=total_price/(quantity* days)
            )
            session.add(bi)
            for inv in inventories:
                inv.available_count -= quantity
                session.add(inv)
            session.commit()
            return booking
    except Exception as e:
        session.rollback()
        raise
