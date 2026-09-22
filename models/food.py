from database.db import execute_query, get_db_connection

class Food:
    """Model for caching and querying food catalog items and standard 100g nutrition."""

    @staticmethod
    def normalize_name(name):
        return name.strip().lower()

    @classmethod
    def find_by_name(cls, name):
        """
        Attempts exact match first, then normalized case-insensitive match,
        then partial match against cached foods with their nutrition per 100g.
        """
        if not name:
            return None
        normalized = cls.normalize_name(name)

        # 1. Exact normalized match
        sql_exact = """
            SELECT f.*, 
                   fn.calories_per_100g, fn.protein_g_per_100g, fn.carbs_g_per_100g,
                   fn.fat_g_per_100g, fn.fiber_g_per_100g, fn.sugar_g_per_100g, fn.sodium_mg_per_100g
            FROM foods f
            JOIN food_nutrition fn ON f.id = fn.food_id
            WHERE f.normalized_name = %s
            LIMIT 1;
        """
        result = execute_query(sql_exact, (normalized,), fetchone=True)
        if result:
            return result

        # 2. Substring like match
        sql_like = """
            SELECT f.*, 
                   fn.calories_per_100g, fn.protein_g_per_100g, fn.carbs_g_per_100g,
                   fn.fat_g_per_100g, fn.fiber_g_per_100g, fn.sugar_g_per_100g, fn.sodium_mg_per_100g
            FROM foods f
            JOIN food_nutrition fn ON f.id = fn.food_id
            WHERE f.normalized_name LIKE %s OR %s LIKE CONCAT('%%', f.normalized_name, '%%')
            ORDER BY LENGTH(f.normalized_name) DESC
            LIMIT 1;
        """
        search_pattern = f"%{normalized}%"
        return execute_query(sql_like, (search_pattern, normalized), fetchone=True)

    @classmethod
    def get_by_id(cls, food_id):
        """Fetches food and nutrition by ID."""
        sql = """
            SELECT f.*, 
                   fn.calories_per_100g, fn.protein_g_per_100g, fn.carbs_g_per_100g,
                   fn.fat_g_per_100g, fn.fiber_g_per_100g, fn.sugar_g_per_100g, fn.sodium_mg_per_100g
            FROM foods f
            JOIN food_nutrition fn ON f.id = fn.food_id
            WHERE f.id = %s
            LIMIT 1;
        """
        return execute_query(sql, (food_id,), fetchone=True)

    @classmethod
    def create_or_update_with_nutrition(cls, name, category, serving_description, standard_weight_g, nutrition_per_100g, source='gemini_ai'):
        """
        Caches a newly recognized food item and its standard 100g nutrition profile
        so future queries do not need to hit the AI again.
        """
        normalized = cls.normalize_name(name)
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Check if food already exists
                cursor.execute("SELECT id FROM foods WHERE normalized_name = %s LIMIT 1;", (normalized,))
                existing = cursor.fetchone()
                
                if existing:
                    food_id = existing["id"]
                else:
                    cursor.execute("""
                        INSERT INTO foods (name, normalized_name, category, serving_description, standard_weight_g, source)
                        VALUES (%s, %s, %s, %s, %s, %s);
                    """, (name.strip(), normalized, category or "General", serving_description or "100g",
                          float(standard_weight_g) if standard_weight_g else 100.0, source))
                    food_id = cursor.lastrowid

                # Upsert food_nutrition
                cursor.execute("""
                    INSERT INTO food_nutrition (
                        food_id, calories_per_100g, protein_g_per_100g, carbs_g_per_100g,
                        fat_g_per_100g, fiber_g_per_100g, sugar_g_per_100g, sodium_mg_per_100g
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        calories_per_100g = VALUES(calories_per_100g),
                        protein_g_per_100g = VALUES(protein_g_per_100g),
                        carbs_g_per_100g = VALUES(carbs_g_per_100g),
                        fat_g_per_100g = VALUES(fat_g_per_100g),
                        fiber_g_per_100g = VALUES(fiber_g_per_100g),
                        sugar_g_per_100g = VALUES(sugar_g_per_100g),
                        sodium_mg_per_100g = VALUES(sodium_mg_per_100g);
                """, (
                    food_id,
                    float(nutrition_per_100g.get("calories", 0.0)),
                    float(nutrition_per_100g.get("protein_g", 0.0)),
                    float(nutrition_per_100g.get("carbohydrates_g", nutrition_per_100g.get("carbs_g", 0.0))),
                    float(nutrition_per_100g.get("fat_g", 0.0)),
                    float(nutrition_per_100g.get("fiber_g", 0.0)),
                    float(nutrition_per_100g.get("sugar_g", 0.0)),
                    float(nutrition_per_100g.get("sodium_mg", 0.0))
                ))
                return food_id
