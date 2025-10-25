import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from decimal import Decimal
import re  

from models import db, user, hotel, room_type, bookings, bookingitem

DATABASE_URL = "mysql+pymysql://root:satish@localhost/hotel_reservation"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def as_dict(obj):
    """Helper function to convert database objects to dictionaries"""
    return {c.name: str(getattr(obj, c.name)) for c in obj.__table__.columns}

def _save_bookings_to_json(session):
    """This is the automatic save function"""
    print("...saving bookings to JSON...")
    
    all_bookings = session.query(bookings).all()
    bookings_list = [as_dict(b) for b in all_bookings]
    
    filename = "bookings_export.json"
    try:
        with open(filename, 'w') as f:
            json.dump(bookings_list, f, indent=4)
        print(f"✅ Bookings automatically saved to '{filename}'.")
    except Exception as e:
        print(f"❌ ERROR: Could not save JSON file: {e}")

def view_hotels(session):
    print("\n--- 🏨 All Hotels ---")
    
    
    all_hotels = session.query(hotel).all()
    
    if not all_hotels:
        print("No hotels found in the database.")
        return

    for h in all_hotels:
        print(f"  ID: {h.id} | Name: {h.name} | Location: {h.location} | Rating: {h.rating}")
    print("------------------------\n")


def book_room(session):
    print("\n--- 📝 Create a New Booking ---")
    
    try:
        user_id = int(input("Enter your User ID: "))
        hotel_id = int(input("Enter the Hotel ID you want to book: "))
        
        rooms = session.query(room_type).filter(room_type.hotel_id == hotel_id).all()
        if not rooms:
            print("Sorry, that hotel has no room types defined.")
            return
            
        print("\nAvailable Room Types for this Hotel:")
        for rt in rooms:
            print(f"  Room Type ID: {rt.id} | Name: {rt.name} | Price: ${rt.base_price}")
        
        room_type_id = int(input("Enter the Room Type ID: "))
        quantity = int(input("How many rooms: "))
        checkin_date = input("Enter check-in date (YYYY-MM-DD): ")
        checkout_date = input("Enter check-out date (YYYY-MM-DD): ")

        room = session.get(room_type, room_type_id)
        if not room:
            print("Invalid Room Type ID.")
            return
            
        total_price = room.base_price * quantity
        
        new_booking = bookings(
            user_id=user_id,
            hotel_id=hotel_id,
            status="confirmed",
            total_price=total_price,
            checkin_date=datetime.strptime(checkin_date, '%Y-%m-%d').date(),
            checkout_date=datetime.strptime(checkout_date, '%Y-%m-%d').date()
        )
        
        session.add(new_booking)
        session.commit()
        
        new_item = bookingitem(
            booking_id=new_booking.id, 
            room_type_id=room_type_id,
            quantity=quantity,
            price_per_room=room.base_price
        )
        session.add(new_item)
        session.commit()

        print("\n✅ SUCCESS! Booking created.")
        print(f"  Booking ID: {new_booking.id}, Total Price: ${total_price}")
        
        _save_bookings_to_json(session)
        
    except ValueError:
        print("\n❌ ERROR: Invalid input. Please enter numbers for IDs.")
        session.rollback()
    except Exception as e:
        print(f"\n❌ ERROR: An error occurred: {e}")
        session.rollback()


def view_bookings(session):
    print("\n--- 🧾 All Bookings ---")
    
    all_bookings = session.query(bookings).all()
    
    if not all_bookings:
        print("No bookings found.")
        return

    for b in all_bookings:
        print(f"  ID: {b.id} | Hotel ID: {b.hotel_id} | User ID: {b.user_id} | Status: {b.status} | Total: ${b.total_price}")
    print("-----------------------\n")


def create_user(session):
    print("\n--- 🧑 Create New User ---")

    while True:
        email = input("Enter email (must be a @gmail.com address): ")
        if not email.strip().endswith("@gmail.com"):
            print("❌ ERROR: Invalid email. Please enter a '@gmail.com' address.")
        else:
            break  

    print("\nPassword must be at least 8 characters long and contain:")
    print("  - At least one lowercase letter [a-z]")
    print("  - At least one uppercase letter [A-Z]")
    print("  - At least one number [0-9]")
    print("  - At least one special character [!, @, #, $...]")
    
    while True:
        password = input("Enter password: ")
        
        if len(password) < 8:
            print("❌ ERROR: Password must be at least 8 characters long.")
        elif not re.search(r'[a-z]', password):
            print("❌ ERROR: Password must contain at least one lowercase letter.")
        elif not re.search(r'[A-Z]', password):
            print("❌ ERROR: Password must contain at least one uppercase letter.")
        elif not re.search(r'\d', password):
            print("❌ ERROR: Password must contain at least one number.")
        elif not re.search(r'[^a-zA-Z0-9]', password):
            # This checks for any character that is not a letter or number
            print("❌ ERROR: Password must contain at least one special character.")
        else:
            print("✅ Password is strong.")

    full_name = input("Enter full name: ")
    
    try:
        new_user = user(
            email=email,
            password_hash=password,  
            full_name=full_name,
            role='customer'
        )
        session.add(new_user)
        session.commit()
        
        print(f"\n✅ SUCCESS! Created user '{full_name}' with ID: {new_user.id}")
        
    except Exception as e:
        print(f"\n❌ DATABASE ERROR: {e}") # This will catch "email already taken"
        session.rollback()


def main():
    db.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    
    print("Welcome to the Hotel Reservation Terminal!")
    
    while True:
        print("\n--- MAIN MENU ---")
        print("1. View all hotels")
        print("2. Book a room")
        print("3. View all bookings")
        print("4. Create a new user") 
        print("5. Exit") 
        
        choice = input("Please enter your choice (1-5): ")
        
        if choice == '1':
            view_hotels(session)
        elif choice == '2':
            book_room(session)
        elif choice == '3':
            view_bookings(session)
        elif choice == '4':
            create_user(session) 
        elif choice == '5':
            print("Goodbye!") 
            break
        else:
            print("Invalid choice. Please try again.")
            
    session.close()

if __name__ == "__main__":
    main()

