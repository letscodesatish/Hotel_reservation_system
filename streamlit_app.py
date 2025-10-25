import streamlit as st
from sqlalchemy import create_engine, func, not_, or_ # <-- Added func, not_, or_
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import re

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
            st.warning("No hotels found in the database. Try adding one!")
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


# --- Page: Create User (WITH VALIDATION) ---
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

# --- Page: Book a Room (UPDATED WITH AVAILABILITY CHECK) ---
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
            st.warning("This hotel has no rooms available. Please add a room type first.")
        else:
            room_names = {f"{r.name} (${r.base_price})": r.id for r in rooms}
            selected_room_label = st.selectbox("Select Room", room_names.keys())
            room_type_id = room_names[selected_room_label]

            quantity = st.number_input("Quantity", min_value=1, max_value=10, step=1, value=1)
            checkin_date = st.date_input("Check-in Date", value=datetime.today().date()) # Use .date()
            checkout_date = st.date_input("Check-out Date", value=(datetime.today() + timedelta(days=1)).date()) # Use .date()

            submitted = st.form_submit_button("Book Now")

            if submitted:
                if checkout_date <= checkin_date:
                    st.error("Check-out date must be after check-in date.")
                else:
                    try:
                        # --- START AVAILABILITY CHECK ---
                        # 1. Get total rooms available for this type
                        room = session.get(room_type, room_type_id)
                        if not room:
                            st.error("Selected room type not found.")
                            st.stop()
                        total_available = room.total_count

                        # 2. Calculate rooms already booked during the overlap period
                        overlapping_bookings = session.query(func.sum(bookingitem.quantity)).join(
                            bookings, bookingitem.booking_id == bookings.id
                        ).filter(
                            bookingitem.room_type_id == room_type_id,
                            bookings.status.in_(('pending', 'confirmed')),
                            # Check for overlap: NOT (ends_before_new_starts OR starts_after_new_ends)
                            not_(or_(
                                bookings.checkout_date <= checkin_date,
                                bookings.checkin_date >= checkout_date
                            ))
                        ).scalar() # scalar() gets a single value (the sum)

                        booked_count = overlapping_bookings or 0 # Use 0 if the query returns None

                        # 3. Check if enough rooms are available
                        if (total_available - booked_count) < quantity:
                            st.error(f"Sorry, only {total_available - booked_count} room(s) of this type are available for the selected dates.")
                        else:
                            # --- END AVAILABILITY CHECK ---

                            # Availability check passed, proceed with booking
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
    # Ensure session is closed even if form wasn't submitted or an error occurred before closing
    if session.is_active:
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

# --- NEW PAGE: ADD A NEW HOTEL ---
def page_add_hotel():
    st.header("🏨 Add a New Hotel")
    with st.form("add_hotel_form", clear_on_submit=True):
        name = st.text_input("Hotel Name")
        location = st.text_input("Location")
        rating = st.number_input("Initial Rating (0.0 to 5.0)", min_value=0.0, max_value=5.0, step=0.1, value=4.0)

        submitted = st.form_submit_button("Add Hotel")

        if submitted:
            if not name or not location:
                st.error("Please fill in all fields.")
            else:
                session = get_session()
                try:
                    new_hotel = hotel(
                        name=name,
                        location=location,
                        rating=rating
                    )
                    session.add(new_hotel)
                    session.commit()
                    st.success(f"Hotel '{name}' added with ID: {new_hotel.id}")
                except Exception as e:
                    session.rollback()
                    st.error(f"Error: {e}")
                finally:
                    session.close()

# --- NEW PAGE: ADD A NEW ROOM TYPE ---
def page_add_room_type():
    st.header("🛏️ Add a New Room Type")
    session = get_session()

    # We need to select a hotel to add the room to
    all_hotels = session.query(hotel).all()
    if not all_hotels:
        st.warning("You must add a hotel before you can add a room type.")
        session.close()
        return

    hotel_names = {h.name: h.id for h in all_hotels}
    selected_hotel_name = st.selectbox("Select Hotel", hotel_names.keys())
    hotel_id = hotel_names[selected_hotel_name]

    with st.form("add_room_form", clear_on_submit=True):
        name = st.text_input("Room Type Name (e.g., 'Deluxe King')")
        base_price = st.number_input("Base Price per Night", min_value=0.0, step=10.0)
        capacity = st.number_input("Capacity (persons)", min_value=1, step=1)
        total_count = st.number_input("Total Number of these Rooms", min_value=1, step=1)

        submitted = st.form_submit_button("Add Room Type")

        if submitted:
            if not name or not base_price or not capacity or not total_count:
                st.error("Please fill in all fields.")
            else:
                try:
                    new_room_type = room_type(
                        hotel_id=hotel_id,
                        name=name,
                        base_price=base_price,
                        capacity=capacity,
                        total_count=total_count
                    )
                    session.add(new_room_type)
                    session.commit()
                    st.success(f"Room type '{name}' added to {selected_hotel_name}!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Error: {e}")
                finally:
                    session.close() # Make sure to close the session

    # Close the session if it's still open (e.g., if form wasn't submitted)
    if session.is_active:
        session.close()

# --- Main App Navigation ---
st.title("🏨 Hotel Reservation System")

# Sidebar navigation
st.sidebar.title("Navigation")
page_options = [
    "View Hotels",
    "Book a Room",
    "View Bookings",
    "Create User",
    "Add New Hotel",
    "Add New Room Type"
]
page = st.sidebar.radio(
    "Go to",
    page_options
)

if page == "View Hotels":
    page_view_hotels()
elif page == "Book a Room":
    page_book_room()
elif page == "View Bookings":
    page_view_bookings()
elif page == "Create User":
    page_create_user()
elif page == "Add New Hotel":
    page_add_hotel()
elif page == "Add New Room Type":
    page_add_room_type()

