import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import db, hotel, room_type  # Import your models

DB_USER = "root"
DB_PASS = "satish" 
DB_HOST = "localhost"
DB_NAME = "hotel_reservation"

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

print("Creating tables...")
db.metadata.create_all(bind=engine)


try:
    
    df = pd.read_excel("HotelFinalDataset.xlsx")
except FileNotFoundError:
    print("Error: 'HotelFinalDataset.xlsx' not found. Make sure it's in the same folder.")
    exit()

print(f"Found {len(df)} hotels in Excel file. Seeding to database...")
for _, row in df.iterrows():
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

try:
    session.commit()
    print("✅ Success! Database has been seeded with hotel data.")
except Exception as e:
    session.rollback()
    print(f"Error committing to database: {e}")
finally:
    session.close()

