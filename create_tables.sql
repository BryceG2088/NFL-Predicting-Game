-- NFL Predictions Database Tables
-- Run this script after creating the nfl_predictions database

USE nfl_predictions;

-- Users table
CREATE TABLE brycegayan_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Leagues table
CREATE TABLE brycegayan_leagues (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    join_code VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users-Leagues relationship table
CREATE TABLE brycegayan_users_leagues (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    league_id INT NOT NULL,
    score INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES brycegayan_users(id) ON DELETE CASCADE,
    FOREIGN KEY (league_id) REFERENCES brycegayan_leagues(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_league (user_id, league_id)
);

-- Submitted predictions table
CREATE TABLE brycegayan_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    team1 VARCHAR(10) NOT NULL,
    score1 INT NOT NULL,
    team2 VARCHAR(10) NOT NULL,
    score2 INT NOT NULL,
    week INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES brycegayan_users(id) ON DELETE CASCADE,
    INDEX idx_user_week (user_id, week),
    INDEX idx_week (week)
);

-- Saved predictions table
CREATE TABLE brycegayan_savedpredictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    team1 VARCHAR(10) NOT NULL,
    score1 INT NOT NULL,
    team2 VARCHAR(10) NOT NULL,
    score2 INT NOT NULL,
    week INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES brycegayan_users(id) ON DELETE CASCADE,
    INDEX idx_user_week (user_id, week),
    INDEX idx_week (week)
);

-- Application info table
CREATE TABLE brycegayan_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recentWeek INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert initial data
INSERT INTO brycegayan_info (recentWeek) VALUES (0);

-- Verify tables were created
SHOW TABLES; 