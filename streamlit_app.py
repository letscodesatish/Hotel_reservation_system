import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import re  # <-- 1. Import 're' for validation

# Import your model classes from models.py
try:
    from models import db, user, hotel, room_type, bookings, bookingitem
except ImportError as e:
    st.error(f"Error importing models: {e}")
    st.stop()


# --- Database Connection ---
# Connects to your local MySQL database
@st.cache_resource
def get_engine():
    try:
        # Use 127.0.0.1 instead of 'localhost'
        db_url = "mysql+pymysql://root:satish@127.0.0.1/hotel_reservation"
        return create_engine(db_url)
    except Exception as e:
        st.error(f"Failed to create database engine. Is your local MySQL server running?: {e}")
        st.stop()

engine = get_engine()
SessionLocal = sessionmaker(bind=engine)

def get_session():
    """Creates a new SQLAlchemy session."""
    return SessionLocal()

# This is a safe way to create tables if they don't exist
try:
    with engine.begin() as conn:
        db.metadata.create_all(conn)
except Exception as e:
    st.warning(f"Could not create tables (this is fine if they exist): {e}")


# --- Page: View Hotels ---
def page_view_hotels():
    st.header("🏨 All Available Hotels")
    session = get_session()
    try:
        all_hotels = session.query(hotel).all()
        if not all_hotels:
            st.warning("No hotels found in the database.")
        else:
            hotel_data = [
                {
                    "ID": h.id, 
                    "Name": h.name, 
                    "Location": h.location, 
                    "Rating": h.rating
                } 
                for h in all_hotels
            ]
            st.dataframe(hotel_data, use_container_width=True)
    except Exception as e:
        st.error(f"An error occurred: {e}")
    finally:
        session.close()


# --- Page: Create User (NOW WITH VALIDATION) ---
def page_create_user():
    st.header("🧑 Create a New User")
    
    with st.form("user_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        full_name = st.text_input("Full Name")
        
        submitted = st.form_submit_button("Create User")
        
        if submitted:
            # --- Start Validation ---
            is_valid = True
            
            # 1. Email Validation
            if not email.strip().endswith("@gmail.com"):
                st.error("Invalid email. Please enter a '@gmail.com' address.")
                is_valid = False

            # 2. Password Validation
            if len(password) < 8:
                st.error("Password must be at least 8 characters long.")
                is_valid = False
            elif not re.search(r'[a-z]', password):
                st.error("Password must contain at least one lowercase letter.")
                is_valid = False
            elif not re.search(r'[A-Z]', password):
                st.error("Password must contain at least one uppercase letter.")
                is_valid = False
            elif not re.search(r'\d', password):
                st.error("Password must contain at least one number.")
                is_valid = False
            elif not re.search(r'[^a-zA-Z0-9]', password):
                st.error("Password must contain at least one special character.")
                is_valid = False
            
            # 3. Full Name Validation
            if not full_name:
                st.error("Please enter your full name.")
                is_valid = False
            
            # --- End Validation ---

            # 4. If all checks pass, try to create the user
            if is_valid:
                session = get_session()
                try:
                    new_user = user(
                        email=email,
                        password_hash=password, # WARNING: Storing plain text password
                        full_name=full_name,
                        role='customer'
                    )
                    session.add(new_user)
                    session.commit()
                    st.success(f"User '{full_name}' created with ID: {new_user.id}")
                except Exception as e:
                    session.rollback()
                    st.error(f"Error: {e} (Email might already be taken)")
                finally:
                    session.close()

# --- Page: Book a Room ---
def page_book_room():
    st.header("📝 Book a Room")
    session = get_session()
    
    with st.form("booking_form"):
        # Get User ID
        user_id = st.number_input("Your User ID", min_value=1, step=1)
        
        # Select Hotel
        all_hotels = session.query(hotel).all()
        if not all_hotels:
            st.warning("No hotels loaded. Please add hotels to the database.")
            st.stop()
        
        hotel_names = {h.name: h.id for h in all_hotels}
        selected_hotel_name = st.selectbox("Select Hotel", hotel_names.keys())
        hotel_id = hotel_names[selected_hotel_name]
        
        # Select Room Type (based on hotel)
        rooms = session.query(room_type).filter(room_type.hotel_id == hotel_id).all()
        if not rooms:
            st.warning("This hotel has no rooms available.")
        else:
            room_names = {f"{r.name} (${r.base_price})": r.id for r in rooms}
            selected_room_label = st.selectbox("Select Room", room_names.keys())
            room_type_id = room_names[selected_room_label]
            
            quantity = st.number_input("Quantity", min_value=1, max_value=5, step=1, value=1)
            checkin_date = st.date_input("Check-in Date", value=datetime.today())
            checkout_date = st.date_input("Check-out Date", value=datetime.today() + timedelta(days=1))

            submitted = st.form_submit_button("Book Now")

            if submitted:
                if checkout_date <= checkin_date:
                    st.error("Check-out date must be after check-in date.")
                else:
                    try:
                        # Get room price
                        room = session.get(room_type, room_type_id)
                        total_price = room.base_price * quantity
                        
                        # Create booking
                        new_booking = bookings(
                            user_id=user_id,
                            hotel_id=hotel_id,
                            status="confirmed",
                            total_price=total_price,
                            checkin_date=checkin_date,
                            checkout_date=checkout_date
                        )
                        session.add(new_booking)
                        session.commit() # Commit to get new_booking.id
                        
                        # Create booking item
                        new_item = bookingitem(
                            booking_id=new_booking.id,
                            room_type_id=room_type_id,
                            quantity=quantity,
                            price_per_room=room.base_price
                        )
                        session.add(new_item)
                        session.commit()
                        
                        st.success(f"Booking created! Your Booking ID is: {new_booking.id}")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Error: {e} (Please ensure User ID is correct)")
    session.close()

# --- Page: View Bookings ---
def page_view_bookings():
    st.header("🧾 View Your Bookings")
    user_id_filter = st.number_input("Enter your User ID to find bookings", min_value=1, step=1)
    
    if st.button("Find Bookings"):
        session = get_session()
        try:
            all_bookings = session.query(bookings).filter(bookings.user_id == user_id_filter).all()
            if not all_bookings:
                st.warning("No bookings found for this user.")
            else:
                booking_data = [
                    {
                        "Booking ID": b.id,
                        "Hotel ID": b.hotel_id,
                        "Status": b.status,
                        "Total Price": b.total_price,
                        "Check-in": b.checkin_date,
                        "Check-out": b.checkout_date,
                    }
                    for b in all_bookings
                ]
                st.dataframe(booking_data, use_container_width=True)
        except Exception as e:
            st.error(f"An error occurred: {e}")
        finally:
            session.close()

# --- Main App Navigation ---
st.title("🏨 Hotel Reservation System")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to", 
    ["View Hotels", "Book a Room", "View Bookings", "Create User"]
)

if page == "View Hotels":
    page_view_hotels()
elif page == "Book a Room":
    page_book_room()
elif page == "View Bookings":
    page_view_bookings()
elif page == "Create User":
    page_create_user()

