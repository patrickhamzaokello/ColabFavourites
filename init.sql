-- Initialize MW Recommender Database
-- This script creates the basic schema if it doesn't exist

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS mwonya CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE mwonya;

-- Create genres table
CREATE TABLE IF NOT EXISTS genres (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create songs table
CREATE TABLE IF NOT EXISTS songs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    artist VARCHAR(255),
    genre INT,
    duration INT, -- in seconds
    path VARCHAR(500) NOT NULL,
    available TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (genre) REFERENCES genres(id) ON DELETE SET NULL,
    INDEX idx_song_available (available),
    INDEX idx_song_genre (genre),
    INDEX idx_song_title (title)
);

-- Create frequency table (user-song interactions)
CREATE TABLE IF NOT EXISTS frequency (
    id INT AUTO_INCREMENT PRIMARY KEY,
    userid VARCHAR(255) NOT NULL,
    songid INT NOT NULL,
    plays INT DEFAULT 1,
    last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (songid) REFERENCES songs(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_song (userid, songid),
    INDEX idx_frequency_user (userid),
    INDEX idx_frequency_song (songid),
    INDEX idx_frequency_plays (plays)
);

-- Insert sample genres if empty
INSERT IGNORE INTO genres (name, description) VALUES
('Afro pop', 'African popular music'),
('Hiphop or Rap', 'Hip hop and rap music'),
('Afro-Beat', 'Afrobeat genre'),
('Dance Hall', 'Dancehall music'),
('Christian and Gospel', 'Christian and gospel music'),
('Reggae', 'Reggae music'),
('RnB', 'Rhythm and Blues'),
('Audio Dramas', 'Audio drama content'),
('Education', 'Educational content'),
('Society and Culture', 'Society and culture content');

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_songs_path_available ON songs(path, available);
CREATE INDEX IF NOT EXISTS idx_frequency_composite ON frequency(userid, songid, plays);

-- Create a view for active songs (songs with path and available)
CREATE OR REPLACE VIEW active_songs AS
SELECT s.*, g.name as genre_name
FROM songs s
LEFT JOIN genres g ON s.genre = g.id
WHERE s.path != '' AND s.available = 1;

-- Create a view for user statistics
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    userid,
    COUNT(*) as total_songs_played,
    SUM(plays) as total_plays,
    AVG(plays) as avg_plays_per_song,
    MAX(plays) as max_plays,
    MIN(plays) as min_plays,
    MAX(last_played) as last_activity
FROM frequency
GROUP BY userid;

-- Create a view for song statistics
CREATE OR REPLACE VIEW song_stats AS
SELECT 
    s.id,
    s.title,
    s.artist,
    g.name as genre,
    COUNT(f.userid) as unique_users,
    COALESCE(SUM(f.plays), 0) as total_plays,
    COALESCE(AVG(f.plays), 0) as avg_plays_per_user,
    COALESCE(MAX(f.plays), 0) as max_plays
FROM songs s
LEFT JOIN frequency f ON s.id = f.songid
LEFT JOIN genres g ON s.genre = g.id
WHERE s.path != '' AND s.available = 1
GROUP BY s.id, s.title, s.artist, g.name;

-- Create stored procedure for getting similar songs data
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS GetFrequencyData()
BEGIN
    SELECT f.userid, f.songid, f.plays 
    FROM frequency f 
    JOIN songs s ON s.id = f.songid  
    WHERE s.path <> '' AND s.available = 1;
END //
DELIMITER ;

-- Create stored procedure for getting song details
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS GetSongDetails()
BEGIN
    SELECT s.id as songid, s.title, g.name as genre, s.artist, s.duration, s.path, s.created_at
    FROM songs s 
    JOIN genres g ON g.id = s.genre 
    WHERE s.path <> '' AND s.available = 1;
END //
DELIMITER ;

-- Show table information
SELECT 'Database initialized successfully' as status;
SHOW TABLES;