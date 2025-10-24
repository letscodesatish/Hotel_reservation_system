import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import db, hotel, room_type  # Import your models

# --- IMPORTANT ---
# 1. Updated with your LOCAL database credentials
DB_USER = "root"
DB_PASS = "satish" # Your password from earlier
DB_HOST = "localhost"
DB_NAME = "hotel_reservation"

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

# --- SCRIPT ---

# 1. Connect to your cloud database
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# 2. Make sure all your tables exist
print("Creating tables...")
db.metadata.create_all(bind=engine)

# 3. Read your downloaded Kaggle Excel file
#    --- This is the line you asked about ---
try:
    # We use pd.read_excel for .xlsx files
    df = pd.read_excel("HotelFinalDataset.xlsx")
except FileNotFoundError:
    print("Error: 'HotelFinalDataset.xlsx' not found. Make sure it's in the same folder.")
    exit()

print(f"Found {len(df)} hotels in Excel file. Seeding to database...")
# 4. Loop through the CSV and add hotels
for _, row in df.iterrows():
    # --- IMPORTANT: Change 'Hotel Name', 'Location', 'Rating'
    #     to match the actual column names in your CSV file ---
    try:
        new_hotel = hotel(
            name=row['Hotel Name'],
            location=row['Location'],
            rating=row['Rating']
        )
        session.add(new_hotel)
    
    except KeyError:
        print("ERROR: Your CSV column names don't match 'Hotel Name', 'Location', 'Rating'.")
        print("Please edit seed.py to match your CSV.")
        session.rollback()
        exit()
    except Exception as e:
        print(f"Error adding row: {e}")

# 5. Commit all the new hotels to the database
try:
    session.commit()
    print("✅ Success! Database has been seeded with hotel data.")
except Exception as e:
    session.rollback()
    print(f"Error committing to database: {e}")
finally:
    session.close()

