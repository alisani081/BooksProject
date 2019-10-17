from dotenv import load_dotenv
load_dotenv()
import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# setup database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    # Open csv file
    f = open('books.csv', 'r')
    reader = csv.reader(f)
    next(reader, None)

    # insert rows into db
    for isbn, title, name, year in reader:
        db.execute("INSERT INTO authors (name) VALUES (:name)", {"name": name})
    print("Inserted!")
    db.commit()
    

if __name__ == "__main__":
    main()
