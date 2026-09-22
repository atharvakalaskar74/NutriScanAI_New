from database.db import execute_query

class NutritionGoal:
    """Data access model for user nutrition goals."""

    @classmethod
    def get_by_user_id(cls, user_id):
        """Fetches nutrition goals for a given user."""
        sql = "SELECT * FROM nutrition_goals WHERE user_id = %s LIMIT 1;"
        return execute_query(sql, (user_id,), fetchone=True)

    @classmethod
    def save_or_update(cls, user_id, calorie_target, protein_target_g, carbs_target_g,
                       fat_target_g, fiber_target_g=30.0, water_target_ml=2500,
                       bmr_kcal=None, tdee_kcal=None):
        """
        Inserts or updates user nutrition goals using ON DUPLICATE KEY UPDATE.
        """
        sql = """
            INSERT INTO nutrition_goals (
                user_id, calorie_target, protein_target_g, carbs_target_g,
                fat_target_g, fiber_target_g, water_target_ml, bmr_kcal, tdee_kcal
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                calorie_target = VALUES(calorie_target),
                protein_target_g = VALUES(protein_target_g),
                carbs_target_g = VALUES(carbs_target_g),
                fat_target_g = VALUES(fat_target_g),
                fiber_target_g = VALUES(fiber_target_g),
                water_target_ml = VALUES(water_target_ml),
                bmr_kcal = VALUES(bmr_kcal),
                tdee_kcal = VALUES(tdee_kcal);
        """
        execute_query(
            sql,
            (user_id, int(calorie_target), float(protein_target_g),
             float(carbs_target_g), float(fat_target_g), float(fiber_target_g),
             int(water_target_ml),
             float(bmr_kcal) if bmr_kcal else None,
             float(tdee_kcal) if tdee_kcal else None)
        )
        return cls.get_by_user_id(user_id)
