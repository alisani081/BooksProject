from dotenv import load_dotenv
import os
import requests
from datetime import datetime as dt

from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
api_key = os.getenv("GOODREADS_KEY")

#Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=["POST", "GET"])
def index():
    
    #Check if user is logged in
    
    user_id = session.get('user_id')

    if user_id is None:
        flash("Login is required", 'danger')
        return redirect(url_for('login'))
    else:
        user = db.execute(
           "SELECT * FROM users WHERE id = :user_id", {
               "user_id": user_id
           }
        ).fetchone()

    return render_template("index.html", user=user)
    

@app.route("/signup", methods=["POST","GET"])
def signup():

    # Get form inputs
    if request.method == "POST":
        name = request.form.get('name')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        error = None

        # Check password length
        if len(password) <= 5:
            error = "Password: Minimum of 6 characters required!"
        
        # Check if user already exist
        if db.execute(
            "SELECT username FROM users WHERE username = :username", 
                {"username": username}
        ).fetchone() is not None:
            error = f"{username} already exist!"            

        # Create user account if no errors found
        if error is None:
            password = generate_password_hash(password)
            db.execute(
                "INSERT INTO users (name, email, username, password) VALUES (:name, :email, :username, :password)",{
                    "name": name, "email": email, "username": username, "password": password
                }
            ) 
            
            db.commit()
            
            flash(f"Account created successfully! Use your details to login now.", 'success')

            return redirect(url_for('login'))
        
        flash(error, 'danger')

    if session.get('user_id') is not None:
       return redirect(url_for('index'))

    return render_template("signup.html")


@app.route("/login", methods=["POST","GET"])
def login():
    # Get form inputs
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

    # Check username and passowrd if exist or empty
        error = None

        if username == '':
            error = "Username is required"
        elif password == '':
            error = "Password is required"
        
        if error is not None:
            flash(error, 'danger')
            return render_template('login.html')
        
        user = db.execute(
            "SELECT * FROM users WHERE username = :username", {
                "username": username
                }
            ).fetchone()
        
        if user is None:
            error = "Incorrect login details"
        elif not check_password_hash(user['password'], password):
            error = "Incorrect Password"

        # Log user in and start a session
        if error is None:
            session.clear()
            session['user_id'] = user['id']

            flash(f"Logged in successfully!", 'success')
            return redirect(url_for('index'))

        flash(error, 'danger')

    if 'user_id' in session:
       return redirect(url_for('index'))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", 'success')
    return redirect(url_for("login"))


@app.route("/search", methods=["POST", "GET"])
def search():

    # Verify login
    user_id = session.get('user_id')

    if user_id is None:
        flash("Login is required", 'danger')
        return redirect(url_for('login'))

    if request.method == "GET":
        # Get search term
        #searchword = request.form.get('searchword')
        searchword = request.args.get('searchword')

        if searchword == " ":
            flash("No result found, please try again!", 'danger')
            return redirect(url_for('index'))
        else:
            results = db.execute(
                "SELECT * FROM books WHERE (title||isbn||author) ILIKE :searchword LIMIT 5",{
                    "searchword": f'%{searchword}%'
                }
            ).fetchall()

            if len(results) < 1:
                flash(f"No result found for {searchword}, please try again!", 'danger')
                return redirect(url_for("index"))

        return render_template('index.html', results=results)


@app.route("/book/<int:book_id>", methods=["POST", "GET"])
def book(book_id):

    # Verify login
    user_id = session.get('user_id')

    if user_id is None:
        flash("Login is required", 'danger')
        return redirect(url_for('login'))

    # Check if book exist
    book = db.execute(
        "SELECT * FROM books WHERE id = :book_id", {
            "book_id": book_id
        }
    ).fetchone() 

    if book is None:
        flash("Book does not exist", 'danger')
        return redirect(url_for("index"))
    
    if request.method == "POST":
        rating = request.form.get('rate')
        comment = request.form.get('comment')     

    # Check if user submitted a review for the book before
        if db.execute(
            "SELECT * FROM reviews WHERE book_id = :book_id AND user_id = :user_id", {
                "book_id": book_id, "user_id": user_id
            }
        ).fetchone() is not None:
            flash(f"You've already submitted a review for this book", 'danger')
            return redirect(url_for('book', book_id=book_id))
        else:    
            db.execute(
                "INSERT INTO reviews (user_id, book_id, comment, rating, date) VALUES (:user_id, :book_id, :comment, :rating, :date)", {
                    "user_id": user_id, "book_id": book_id, "comment": comment, "rating": rating, "date": dt.date(dt.now())
                }
            )
            db.commit()   

    # Get logged in user review    
    user_review = db.execute(
        "SELECT * FROM reviews WHERE book_id = :book_id AND user_id = :user_id", {
            "book_id": book_id, "user_id": user_id
        }
    ).fetchone()

    # Get all reviews for a particular book
    reviews = db.execute(
        "SELECT username, book_id, comment, rating, date FROM reviews r, users u, books b WHERE book_id = :book_id AND r.book_id = b.id AND u.id = r.user_id", {
            "book_id": book_id
        }
    ).fetchall()      

    # Get number of reviews for a particular book
    review_count = len(reviews)
    
    # Get book average rating
    avg_rating = db.execute(
        "SELECT avg(rating) as average FROM reviews WHERE book_id = :book_id", {
            "book_id": book_id
        }
    ).fetchone()

    # Format average rating to 2 decimal places
    try:
        avg_rating = format(avg_rating.average, '.2f')
    except TypeError:
        avg_rating = "Not available"

   # API Request to Goodreads
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": api_key, "isbns": book.isbn})
    data = res.json()
   
    return render_template("book.html", book=book, reviews=reviews, user_review=user_review, review_count=review_count, avg_rating=avg_rating, data=data)


@app.route("/api/<isbn>")
def api(isbn):
    if db.execute(
        "SELECT * FROM books WHERE isbn = :isbn", {
            "isbn": isbn
        }
    ).fetchone() is None:
        return jsonify({"error": "No book found"}), 404

    book = db.execute(
        "SELECT title, author, year, isbn, count(rating) as review_count, avg(rating) as average_score FROM books, reviews WHERE isbn = :isbn AND books.id = reviews.book_id GROUP BY title,author,year,isbn", {
            "isbn": isbn
        }
    ).fetchone()

    if book is None:
        return jsonify({"data":"No reviews found for this book"})
    
    return jsonify({
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "isbn": book.isbn,
        "review_count": book.review_count,
        "average_score": format(book.average_score, '.2f')
    })
