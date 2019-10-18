from dotenv import load_dotenv
import os

from flask import Flask, session, render_template, request, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

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


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["POST","GET"])
def signup():
    if request.method == "POST":
        name = request.form.get('name')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        error = None

        if not name:
            error = "All fields are required!"

        if db.execute("SELECT username FROM users WHERE username = :username", {"username": username}
        ).fetchone() is not None:
            error = f"{username} already exist!"            

        if error is None:
            password = generate_password_hash(password)
            user = db.execute("INSERT INTO users (name, email, username, password) VALUES (:name, :email, :username, :password) RETURNING id",
                {"name": name, "email": email, "username": username, "password": password}) 
            
            db.commit()
            
            flash('Account created successfully! Use your details to login now.', 'success')

            return redirect(url_for('login'))
        
        flash(error, 'danger')

    return render_template("signup.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/book")
def book():
    return render_template("book.html")
