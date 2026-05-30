from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2

# Initialize the Flask application
app = Flask(__name__)

# Secret key for session management
app.secret_key = 'k29photo_cookies_key'

# Getting a new database connection under my username
def get_db_connection():
    conn = psycopg2.connect(database="k29photo_db")
    return conn

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        # Pull the form data from register
        firstName = request.form['first_name']
        lastName = request.form['last_name']
        email = request.form['email']
        passwordPlaintext = request.form['password']
        
        # Hash password for security
        hashedPassword = generate_password_hash(passwordPlaintext)
        
        # Date of Birth is optional
        dob = request.form.get('dob')
        if not dob:
            dob = None 

        # Get a database connection and cursor
        conn = get_db_connection()
        cur = conn.cursor()

        # Insert user into the database
        try:
            cur.execute(
                """
                INSERT INTO Users (first_name, last_name, email, dob, password_hash)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING user_id, first_name
                """,
                (firstName, lastName, email, dob, hashedPassword)
            )
            
            # Fetch the new user's ID and first name for the session
            newUser = cur.fetchone()
            conn.commit()
            
            # Assign new user to the session
            session['user_id'] = newUser[0]
            session['first_name'] = newUser[1]
            session['is_new'] = True
            
            # Redirect back to index
            return redirect(url_for('index'))

        # Handle already existing email error
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            errorMessage = "A user with that email already exists!"
            return render_template('register.html', error=errorMessage)

        # Close connections
        finally:
            cur.close()
            conn.close()

    # Show the registration form for GET requests
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        # Pull the form data from login
        email = request.form['email']
        passwordPlaintext = request.form['password']

        # Get the user's info from the database based on the email they entered
        conn = get_db_connection()
        cur = conn.cursor()

        # Fetch the user's ID, name, and hashed password from the database
        cur.execute("SELECT user_id, first_name, password_hash FROM Users WHERE email = %s", (email,))
        user = cur.fetchone() 

        cur.close()
        conn.close()

        # Check if the user exists and if the password given is valid (user[2] has the hashed password from the database)
        if user and check_password_hash(user[2], passwordPlaintext):
            # Assign the VIP wristband (session)
            session['user_id'] = user[0]
            session['first_name'] = user[1]
            
            # Redirect them to the home page once logged in
            return redirect(url_for('index'))
        else:

            # Failed login (wrong email or password)
            errorMessage = "Invalid email or password."
            return render_template('login.html', error=errorMessage)

    # For the GET request, just show the login form
    return render_template('login.html')

@app.route('/')
def index():
    if 'user_id' in session:
        firstName = session['first_name']
        
        # Check if the user is registered
        if session.pop('is_new', None):
            return f"Welcome to k29photo, {firstName}! You can now start creating albums. <br><a href='/logout'>Logout</a>"
        
        # Otherwise, Welcome them back
        return f"Welcome back to k29photo, {firstName}! <br><a href='/logout'>Logout</a>"
    
    # Show the home page
    return "k29photo is running. You can <br><a href='/login'>Login</a> or <a href='/register'>Register</a>."

@app.route('/logout')
def logout():
    # Clear session and redirect to index
    session.clear()
    return redirect(url_for('index'))