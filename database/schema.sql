-- ==========================================================
-- NutriScan AI Database Schema
-- Compatible with MySQL 8.x and MariaDB (XAMPP / Free Cloud MySQL)
-- ==========================================================

CREATE DATABASE IF NOT EXISTS nutriscan_ai_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE nutriscan_ai_db;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    age INT NULL,
    gender ENUM('male', 'female', 'other') DEFAULT 'other',
    height_cm DECIMAL(5,2) NULL,
    weight_kg DECIMAL(5,2) NULL,
    activity_level ENUM('sedentary', 'light', 'moderate', 'active', 'very_active') DEFAULT 'sedentary',
    fitness_goal ENUM('maintain', 'lose_weight', 'gain_weight', 'build_muscle') DEFAULT 'maintain',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Nutrition Goals Table
CREATE TABLE IF NOT EXISTS nutrition_goals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    calorie_target INT NOT NULL,
    protein_target_g DECIMAL(6,2) NOT NULL,
    carbs_target_g DECIMAL(6,2) NOT NULL,
    fat_target_g DECIMAL(6,2) NOT NULL,
    fiber_target_g DECIMAL(6,2) DEFAULT 30.00,
    water_target_ml INT DEFAULT 2500,
    bmr_kcal DECIMAL(7,2) NULL,
    tdee_kcal DECIMAL(7,2) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 3. Foods Cache Table
CREATE TABLE IF NOT EXISTS foods (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    normalized_name VARCHAR(150) NOT NULL,
    category VARCHAR(100) DEFAULT 'General',
    serving_description VARCHAR(100) DEFAULT '100g',
    standard_weight_g DECIMAL(6,2) DEFAULT 100.00,
    source ENUM('local_db', 'gemini_ai', 'verified_nutrition') DEFAULT 'local_db',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_normalized_name (normalized_name)
) ENGINE=InnoDB;

-- 4. Food Nutrition Table (Per 100g basis)
CREATE TABLE IF NOT EXISTS food_nutrition (
    id INT AUTO_INCREMENT PRIMARY KEY,
    food_id INT NOT NULL UNIQUE,
    calories_per_100g DECIMAL(7,2) NOT NULL,
    protein_g_per_100g DECIMAL(6,2) NOT NULL,
    carbs_g_per_100g DECIMAL(6,2) NOT NULL,
    fat_g_per_100g DECIMAL(6,2) NOT NULL,
    fiber_g_per_100g DECIMAL(6,2) DEFAULT 0.00,
    sugar_g_per_100g DECIMAL(6,2) DEFAULT 0.00,
    sodium_mg_per_100g DECIMAL(7,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 5. Meals Table
CREATE TABLE IF NOT EXISTS meals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    meal_type ENUM('breakfast', 'lunch', 'dinner', 'snack', 'other') NOT NULL,
    meal_date DATE NOT NULL,
    meal_time TIME NOT NULL,
    total_calories DECIMAL(7,2) NOT NULL DEFAULT 0.00,
    total_protein_g DECIMAL(6,2) NOT NULL DEFAULT 0.00,
    total_carbs_g DECIMAL(6,2) NOT NULL DEFAULT 0.00,
    total_fat_g DECIMAL(6,2) NOT NULL DEFAULT 0.00,
    total_fiber_g DECIMAL(6,2) DEFAULT 0.00,
    total_sugar_g DECIMAL(6,2) DEFAULT 0.00,
    notes TEXT NULL,
    image_url VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_date (user_id, meal_date),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 6. Meal Items Table
CREATE TABLE IF NOT EXISTS meal_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    meal_id INT NOT NULL,
    food_name VARCHAR(150) NOT NULL,
    food_id INT NULL,
    weight_g DECIMAL(6,2) NOT NULL,
    calories DECIMAL(7,2) NOT NULL,
    protein_g DECIMAL(6,2) NOT NULL,
    carbs_g DECIMAL(6,2) NOT NULL,
    fat_g DECIMAL(6,2) NOT NULL,
    fiber_g DECIMAL(6,2) DEFAULT 0.00,
    sugar_g DECIMAL(6,2) DEFAULT 0.00,
    source VARCHAR(50) DEFAULT 'ai_estimated',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meal_id) REFERENCES meals(id) ON DELETE CASCADE,
    FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 7. AI Analyses Log Table
CREATE TABLE IF NOT EXISTS ai_analyses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    is_food BOOLEAN NOT NULL,
    confidence DECIMAL(4,3) NULL,
    raw_response TEXT NULL,
    rejection_reason VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 8. Chat History Table
CREATE TABLE IF NOT EXISTS chat_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    role ENUM('user', 'assistant') NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_chat (user_id, created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ==========================================================
-- SEED DATA: 30 Common Dishes & Staples (Per 100g standard)
-- ==========================================================

INSERT IGNORE INTO foods (id, name, normalized_name, category, serving_description, standard_weight_g, source) VALUES
(1, 'Steamed White Rice', 'steamed white rice', 'Grains', '1 bowl', 150.00, 'local_db'),
(2, 'Yellow Dal Tadka', 'yellow dal tadka', 'Legumes & Curries', '1 small bowl', 150.00, 'local_db'),
(3, 'Whole Wheat Roti / Chapati', 'whole wheat roti / chapati', 'Breads', '1 medium roti', 40.00, 'local_db'),
(4, 'Paneer Tikka', 'paneer tikka', 'Appetizers', '6 pieces', 180.00, 'local_db'),
(5, 'Chicken Biryani', 'chicken biryani', 'Rice Dishes', '1 regular plate', 300.00, 'local_db'),
(6, 'Masala Dosa', 'masala dosa', 'Breakfast', '1 standard dosa', 200.00, 'local_db'),
(7, 'Steamed Idli', 'steamed idli', 'Breakfast', '2 idlis', 100.00, 'local_db'),
(8, 'Vegetable Samosa', 'vegetable samosa', 'Snacks', '1 samosa', 75.00, 'local_db'),
(9, 'Poha', 'poha', 'Breakfast', '1 medium plate', 180.00, 'local_db'),
(10, 'Upma', 'upma', 'Breakfast', '1 bowl', 160.00, 'local_db'),
(11, 'Pav Bhaji', 'pav bhaji', 'Street Food', '1 serving with 2 pavs', 280.00, 'local_db'),
(12, 'Apple (Fresh)', 'apple (fresh)', 'Fruits', '1 medium apple', 182.00, 'local_db'),
(13, 'Banana (Fresh)', 'banana (fresh)', 'Fruits', '1 medium banana', 118.00, 'local_db'),
(14, 'Hard Boiled Egg', 'hard boiled egg', 'Eggs & Poultry', '1 large egg', 50.00, 'local_db'),
(15, 'Grilled Chicken Breast', 'grilled chicken breast', 'Poultry & Meat', '1 fillet', 150.00, 'local_db'),
(16, 'Greek Yogurt (Plain)', 'greek yogurt (plain)', 'Dairy', '1 cup', 170.00, 'local_db'),
(17, 'Mixed Green Salad', 'mixed green salad', 'Salads & Veggies', '1 large bowl', 120.00, 'local_db'),
(18, 'Cheese Pizza Slice', 'cheese pizza slice', 'Fast Food', '1 standard slice', 107.00, 'local_db'),
(19, 'Oatmeal Porridge (Water)', 'oatmeal porridge (water)', 'Breakfast', '1 bowl', 200.00, 'local_db'),
(20, 'Peanut Butter', 'peanut butter', 'Spreads & Nuts', '2 tbsp', 32.00, 'local_db'),
(21, 'White Bread', 'white bread', 'Bakery', '1 slice', 30.00, 'local_db'),
(22, 'Whole Milk', 'whole milk', 'Dairy', '1 glass', 244.00, 'local_db'),
(23, 'Raw Almonds', 'raw almonds', 'Nuts & Seeds', '1 handful', 28.00, 'local_db'),
(24, 'Pan Seared Salmon', 'pan seared salmon', 'Seafood', '1 fillet', 150.00, 'local_db'),
(25, 'Palak Paneer', 'palak paneer', 'Curries', '1 bowl', 200.00, 'local_db'),
(26, 'Rajma Masala', 'rajma masala', 'Legumes & Curries', '1 bowl', 200.00, 'local_db'),
(27, 'Chana Masala', 'chana masala', 'Legumes & Curries', '1 bowl', 200.00, 'local_db'),
(28, 'Masala Omelette', 'masala omelette', 'Eggs & Breakfast', '2-egg omelette', 120.00, 'local_db'),
(29, 'Veg Burger', 'veg burger', 'Fast Food', '1 burger', 210.00, 'local_db'),
(30, 'Vegetable Sabzi (Dry)', 'vegetable sabzi (dry)', 'Curries & Veggies', '1 katori', 150.00, 'local_db');

INSERT IGNORE INTO food_nutrition (food_id, calories_per_100g, protein_g_per_100g, carbs_g_per_100g, fat_g_per_100g, fiber_g_per_100g, sugar_g_per_100g, sodium_mg_per_100g) VALUES
(1, 130.00, 2.70, 28.20, 0.30, 0.40, 0.10, 1.00),     -- Steamed White Rice
(2, 95.00, 5.20, 12.00, 2.80, 2.50, 0.80, 280.00),    -- Yellow Dal Tadka
(3, 264.00, 9.00, 55.00, 3.20, 7.50, 1.50, 120.00),   -- Whole Wheat Roti
(4, 215.00, 12.50, 6.80, 15.50, 1.20, 2.00, 420.00),  -- Paneer Tikka
(5, 173.00, 8.20, 20.40, 6.50, 1.20, 0.80, 380.00),   -- Chicken Biryani
(6, 168.00, 3.80, 26.50, 5.20, 2.10, 1.20, 320.00),   -- Masala Dosa
(7, 132.00, 4.00, 27.50, 0.40, 1.50, 0.30, 210.00),   -- Steamed Idli
(8, 262.00, 4.50, 31.00, 13.50, 2.80, 1.80, 350.00),  -- Samosa
(9, 145.00, 2.90, 25.80, 3.50, 1.90, 1.10, 260.00),   -- Poha
(10, 128.00, 3.20, 22.00, 3.10, 1.80, 0.90, 290.00),  -- Upma
(11, 142.00, 3.50, 21.00, 5.00, 3.20, 2.40, 410.00),  -- Pav Bhaji
(12, 52.00, 0.30, 13.80, 0.20, 2.40, 10.40, 1.00),    -- Apple
(13, 89.00, 1.10, 22.80, 0.30, 2.60, 12.20, 1.00),    -- Banana
(14, 155.00, 12.60, 1.10, 10.60, 0.00, 1.10, 124.00), -- Hard Boiled Egg
(15, 165.00, 31.00, 0.00, 3.60, 0.00, 0.00, 74.00),   -- Grilled Chicken Breast
(16, 59.00, 10.00, 3.60, 0.40, 0.00, 3.20, 36.00),    -- Greek Yogurt
(17, 24.00, 1.40, 4.20, 0.30, 2.10, 1.80, 25.00),     -- Mixed Green Salad
(18, 266.00, 11.40, 33.30, 9.80, 2.30, 3.60, 598.00), -- Cheese Pizza
(19, 71.00, 2.50, 12.00, 1.50, 1.70, 0.30, 2.00),     -- Oatmeal Porridge
(20, 588.00, 25.00, 20.00, 50.00, 6.00, 9.00, 420.00), -- Peanut Butter
(21, 265.00, 9.00, 49.00, 3.20, 2.70, 5.00, 491.00),  -- White Bread
(22, 61.00, 3.20, 4.80, 3.30, 0.00, 5.10, 43.00),     -- Whole Milk
(23, 579.00, 21.20, 21.60, 49.90, 12.50, 4.40, 1.00),  -- Almonds
(24, 208.00, 20.40, 0.00, 13.40, 0.00, 0.00, 59.00),  -- Pan Seared Salmon
(25, 160.00, 7.50, 5.20, 12.50, 2.80, 1.50, 340.00),  -- Palak Paneer
(26, 125.00, 6.10, 17.80, 3.20, 4.50, 1.20, 320.00),  -- Rajma Masala
(27, 138.00, 6.50, 19.40, 3.80, 5.10, 1.60, 340.00),  -- Chana Masala
(28, 154.00, 10.80, 2.40, 11.20, 0.60, 1.20, 290.00), -- Masala Omelette
(29, 218.00, 6.20, 31.50, 7.80, 3.40, 4.20, 460.00),  -- Veg Burger
(30, 88.00, 2.40, 10.50, 4.20, 3.80, 2.50, 260.00);   -- Vegetable Sabzi
