from flask import Flask, render_template, request, redirect, url_for, session, Response
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

@app.route('/')
def index():
    # Get a database connection and cursor
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Fetch all photos along with their album name and uploader details
    cur.execute("""
        SELECT p.photo_id, p.caption, a.name AS album_name, u.first_name, u.last_name
        FROM Photos p
        JOIN Albums a ON p.album_id = a.album_id
        JOIN Users u ON a.user_id = u.user_id
        ORDER BY p.photo_id DESC
    """)
    photos = cur.fetchall()
    
    # Close connections
    cur.close()
    conn.close()

    # Pass the photos and session data to the index template
    return render_template('index.html', photos=photos, session=session)

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

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    # Security check to ensure the user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Pull the form data from upload
        albumName = request.form['album_name']
        caption = request.form.get('caption') or ''
        
        # Get the uploaded file from the request
        photoFile = request.files['photo_file']

        # Read the raw binary data of the image
        photoData = photoFile.read()

        # Get a database connection and cursor
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # Insert the new album and get its ID
            cur.execute(
                """
                INSERT INTO Albums (name, user_id)
                VALUES (%s, %s)
                RETURNING album_id
                """,
                (albumName, session['user_id'])
            )
            newAlbumId = cur.fetchone()[0]

            # Insert the photo using the binary data and the new album ID
            cur.execute(
                """
                INSERT INTO Photos (caption, data, album_id)
                VALUES (%s, %s, %s)
                """,
                (caption, psycopg2.Binary(photoData), newAlbumId)
            )
            
            # Commit the changes to the database
            conn.commit()
            
            # Redirect to the home page feed on success
            return redirect(url_for('index'))

        # Handle any insertion errors
        except Exception as e:
            conn.rollback()
            return f"An error occurred: {e}"

        # Close connections
        finally:
            cur.close()
            conn.close()

    # Show the upload form for GET requests
    return render_template('upload.html')

@app.route('/photo/<int:photo_id>')
def serve_photo(photo_id):
    # Get a database connection and cursor
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Fetch the binary data for the requested photo
    cur.execute("SELECT data FROM Photos WHERE photo_id = %s", (photo_id,))
    photo = cur.fetchone()
    
    # Close connections
    cur.close()
    conn.close()

    # Check if the photo exists and serve it explicitly as an image
    if photo:
        return Response(photo[0], mimetype='image/jpeg')
    else:
        return "Photo not found", 404

@app.route('/view/<int:photo_id>')
def view_photo(photo_id):
    # Get a database connection and cursor
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch the specific photo and its uploader's details
    # FIX: Changed p.user_id to u.user_id
    cur.execute("""
        SELECT p.photo_id, p.caption, u.first_name, u.last_name, a.name, u.user_id
        FROM Photos p
        JOIN Albums a ON p.album_id = a.album_id
        JOIN Users u ON a.user_id = u.user_id
        WHERE p.photo_id = %s
    """, (photo_id,))
    photoDetails = cur.fetchone()

    # Count the total number of likes for this photo
    cur.execute("SELECT COUNT(*) FROM Likes WHERE photo_id = %s", (photo_id,))
    likeCount = cur.fetchone()[0]

    # Check if the currently logged-in user has already liked this photo
    hasLiked = False
    if 'user_id' in session:
        cur.execute("SELECT 1 FROM Likes WHERE user_id = %s AND photo_id = %s", (session['user_id'], photo_id))
        if cur.fetchone():
            hasLiked = True

    # Close connections
    cur.close()
    conn.close()

    # Pass everything to the specific photo template
    return render_template('view_photo.html', photo=photoDetails, likes=likeCount, has_liked=hasLiked, session=session)

@app.route('/like/<int:photo_id>', methods=['POST'])
def like_photo(photo_id):
    # Security check to ensure the user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Get a database connection and cursor
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Insert the like into the database
        cur.execute(
            "INSERT INTO Likes (user_id, photo_id) VALUES (%s, %s)",
            (session['user_id'], photo_id)
        )
        # Commit the changes to the database
        conn.commit()

    # If the user already liked it (UniqueViolation), we just ignore the error
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
    
    # Handle any other database errors
    except Exception as e:
        conn.rollback()
        print(f"Error liking photo: {e}")

    # Close connections
    finally:
        cur.close()
        conn.close()

    # Redirect the user right back to the same photo they just liked
    return redirect(url_for('view_photo', photo_id=photo_id))

@app.route('/logout')
def logout():
    # Clear session and redirect to index
    session.clear()
    return redirect(url_for('index'))