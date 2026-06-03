import psycopg2
from werkzeug.security import generate_password_hash

# A tiny, mathematically valid 1x1 pixel blank image in raw binary
DUMMY_IMAGE = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x03\x02\x02\x02\x02\x02\x03\x02\x02\x02\x03\x03\x03\x03\x04\x06\x04\x04\x04\x04\x04\x08\x06\x06\x05\x06\t\x08\n\n\t\x08\t\t\n\x0c\x0f\x0c\n\x0b\x0e\x0b\t\t\r\x11\r\x0e\x0f\x10\x10\x11\x10\n\x0c\x12\x13\x12\x10\x13\x0f\x10\x10\x10\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\x00'

def fill_database():
    print("Connecting to database...")
    conn = psycopg2.connect(database="k29photo_db")
    cur = conn.cursor()

    try:
        # Wipe old slate clean
        print("Clearing old data...")
        cur.execute("TRUNCATE Users CASCADE;")
        cur.execute("TRUNCATE Tags CASCADE;")

        # Create Mock Users (Easy password '123')
        print("Injecting users...")
        users_data = [
            ('Maria', 'Pappa', 'maria@test.com', generate_password_hash('123')),
            ('Kostas', 'Galanis', 'kostas@test.com', generate_password_hash('123')),
            ('Eleni', 'Rigas', 'eleni@test.com', generate_password_hash('123')),
            ('Nikos', 'Sotiropoulos', 'nikos@test.com', generate_password_hash('123')),
            ('Anna', 'Lappa', 'anna@test.com', generate_password_hash('123'))
        ]
        user_ids = []
        for u in users_data:
            cur.execute("INSERT INTO Users (first_name, last_name, email, password_hash) VALUES (%s, %s, %s, %s) RETURNING user_id", u)
            user_ids.append(cur.fetchone()[0])

        # Create Albums & Photos
        print("Injecting albums and photos...")
        photo_ids = []
        for i, uid in enumerate(user_ids):
            # Create an album for each user
            cur.execute("INSERT INTO Albums (name, user_id) VALUES (%s, %s) RETURNING album_id", (f"Album {i+1}", uid))
            album_id = cur.fetchone()[0]
            
            # Insert 2 photos per album
            for j in range(2):
                cur.execute("INSERT INTO Photos (caption, data, album_id) VALUES (%s, %s, %s) RETURNING photo_id", 
                            (f"Cool photo {j+1} by user {uid}", psycopg2.Binary(DUMMY_IMAGE), album_id))
                photo_ids.append(cur.fetchone()[0])

        # Insert Tags
        print("Injecting tags...")
        tags = ['summer', 'university', 'code', 'friends', 'vacation']
        for tag in tags:
            cur.execute("INSERT INTO Tags (tag_word) VALUES (%s) RETURNING tag_id", (tag,))
            tag_id = cur.fetchone()[0]
            # Attach this tag to the first 3 photos
            for pid in photo_ids[:3]:
                cur.execute("INSERT INTO Photo_Tags (photo_id, tag_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (pid, tag_id))

        # Insert Comments & Likes (Scattered to create different Contribution Scores)
        print("Injecting social interactions...")
        cur.execute("INSERT INTO Comments (text, user_id, photo_id) VALUES ('What a picture!', %s, %s)", (user_ids[1], photo_ids[0]))
        cur.execute("INSERT INTO Comments (text, user_id, photo_id) VALUES ('Looks amazing!', %s, %s)", (user_ids[2], photo_ids[0]))
        cur.execute("INSERT INTO Comments (text, user_id, photo_id) VALUES ('Unbelievable!', %s, %s)", (user_ids[1], photo_ids[1]))
        
        cur.execute("INSERT INTO Likes (user_id, photo_id) VALUES (%s, %s)", (user_ids[1], photo_ids[0]))
        cur.execute("INSERT INTO Likes (user_id, photo_id) VALUES (%s, %s)", (user_ids[2], photo_ids[0]))

        # Insert Friends (Maria is friends with Kostas and Eleni)
        print("Injecting friendships...")
        cur.execute("INSERT INTO Friends (user_id, friend_id) VALUES (%s, %s)", (user_ids[0], user_ids[1]))
        cur.execute("INSERT INTO Friends (user_id, friend_id) VALUES (%s, %s)", (user_ids[0], user_ids[2]))

        # Commit all changes
        conn.commit()
        print("✅ Database successfully filled with test data!")

    except Exception as e:
        conn.rollback()
        print(f"Error filling database: {e}")

    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    fill_database()