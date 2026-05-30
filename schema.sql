-- Users Table
-- Stores all user attributes
CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    date_of_birth DATE,
    password_hash VARCHAR(255) NOT NULL
);

-- Friends Table (Many-to-Many Relationship)
-- Links users to other users
CREATE TABLE Friends (
    user_id_1 INT REFERENCES Users(user_id) ON DELETE CASCADE,
    user_id_2 INT REFERENCES Users(user_id) ON DELETE CASCADE,
    PRIMARY KEY (user_id_1, user_id_2),
    CHECK (user_id_1 != user_id_2) -- A user cannot be friends with themselves
);

-- Albums Table (One-to-Many Relationship).
CREATE TABLE Albums (
    album_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    user_id INT NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Photos Table (One-to-Many Relationship)
CREATE TABLE Photos (
    photo_id SERIAL PRIMARY KEY,
    caption TEXT,
    data BYTEA NOT NULL, -- Binary representation of the image 
    album_id INT NOT NULL REFERENCES Albums(album_id) ON DELETE CASCADE
);

-- Tags Table (One-to-Many Relationship)
CREATE TABLE Tags (
    tag_word VARCHAR(100) PRIMARY KEY,
    CHECK (tag_word ~ '^[a-z]+$')  -- Tags must be single words (no spaces) and strictly lowercase
);

-- Photo_Tags Table (Many-to-Many Relationship)
-- Links photos to tags, allowing multiple photos per tag and multiple tags per photo
CREATE TABLE Photo_Tags (
    photo_id INT REFERENCES Photos(photo_id) ON DELETE CASCADE,
    tag_word VARCHAR(100) REFERENCES Tags(tag_word) ON DELETE CASCADE,
    PRIMARY KEY (photo_id, tag_word)
);

-- Comments Table (One-to-Many Relationship)
-- Stores text comments left on photos.
CREATE TABLE Comments (
    comment_id SERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    user_id INT NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE, -- The comment owner 
    photo_id INT NOT NULL REFERENCES Photos(photo_id) ON DELETE CASCADE,
    post_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Likes Table (Many-to-Many Relationship)
-- Tracks which users liked which photos
CREATE TABLE Likes (
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    photo_id INT REFERENCES Photos(photo_id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, photo_id)
);