class CalculationService:
    """
    Scientific and transparent nutrition calculator:
    - Mifflin-St Jeor formula for BMR
    - Activity multipliers for TDEE
    - Goal-oriented macro partitioning
    - Scaled nutrition calculation per gram
    - Transparent 0-100 Daily Wellness Score
    """

    ACTIVITY_MULTIPLIERS = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }

    @classmethod
    def calculate_bmr(cls, weight_kg, height_cm, age, gender="other"):
        """
        Calculates Basal Metabolic Rate using the Mifflin-St Jeor Equation.
        """
        if not weight_kg or not height_cm or not age:
            return 1600.0  # safe standard baseline

        w = float(weight_kg)
        h = float(height_cm)
        a = float(age)

        # Baseline equation: (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
        base = (10.0 * w) + (6.25 * h) - (5.0 * a)

        if gender == "male":
            return round(base + 5.0, 1)
        elif gender == "female":
            return round(base - 161.0, 1)
        else:
            # Average offset (-78)
            return round(base - 78.0, 1)

    @classmethod
    def calculate_tdee(cls, bmr, activity_level="sedentary"):
        """Calculates Total Daily Energy Expenditure."""
        multiplier = cls.ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)
        return round(bmr * multiplier, 1)

    @classmethod
    def calculate_nutrition_targets(cls, age, gender, height_cm, weight_kg, activity_level="sedentary", fitness_goal="maintain"):
        """
        Calculates personalized estimated daily targets for calories, protein, carbs, and fat.
        """
        bmr = cls.calculate_bmr(weight_kg, height_cm, age, gender)
        tdee = cls.calculate_tdee(bmr, activity_level)

        # Goal adjustments
        if fitness_goal == "lose_weight":
            calorie_target = max(1200, int(tdee - 500))
            protein_ratio = 0.30
            fat_ratio = 0.25
            carbs_ratio = 0.45
        elif fitness_goal == "gain_weight":
            calorie_target = int(tdee + 500)
            protein_ratio = 0.20
            fat_ratio = 0.25
            carbs_ratio = 0.55
        elif fitness_goal == "build_muscle":
            calorie_target = int(tdee + 300)
            protein_ratio = 0.30
            fat_ratio = 0.25
            carbs_ratio = 0.45
        else:  # maintain
            calorie_target = int(tdee)
            protein_ratio = 0.22
            fat_ratio = 0.28
            carbs_ratio = 0.50

        # Gram conversions: 4 kcal per gram of protein & carbs, 9 kcal per gram of fat
        protein_g = round((calorie_target * protein_ratio) / 4.0, 1)
        fat_g = round((calorie_target * fat_ratio) / 9.0, 1)
        carbs_g = round((calorie_target * carbs_ratio) / 4.0, 1)

        # Baseline fiber and water recommendations
        fiber_g = 30.0
        water_ml = 2500 if (not weight_kg or float(weight_kg) < 70) else 3000

        return {
            "bmr_kcal": bmr,
            "tdee_kcal": tdee,
            "calorie_target": calorie_target,
            "protein_target_g": protein_g,
            "carbs_target_g": carbs_g,
            "fat_target_g": fat_g,
            "fiber_target_g": fiber_g,
            "water_target_ml": water_ml,
            "fitness_goal": fitness_goal,
            "activity_level": activity_level
        }

    @staticmethod
    def scale_nutrition(nutrition_per_100g, weight_g):
        """
        Scales standard 100g nutrition numbers to an arbitrary serving weight in grams.
        """
        ratio = float(weight_g) / 100.0
        return {
            "weight_g": round(float(weight_g), 1),
            "calories": round(float(nutrition_per_100g.get("calories", 0.0)) * ratio, 1),
            "protein_g": round(float(nutrition_per_100g.get("protein_g", 0.0)) * ratio, 1),
            "carbs_g": round(float(nutrition_per_100g.get("carbohydrates_g", nutrition_per_100g.get("carbs_g", 0.0))) * ratio, 1),
            "fat_g": round(float(nutrition_per_100g.get("fat_g", 0.0)) * ratio, 1),
            "fiber_g": round(float(nutrition_per_100g.get("fiber_g", 0.0)) * ratio, 1),
            "sugar_g": round(float(nutrition_per_100g.get("sugar_g", 0.0)) * ratio, 1),
            "sodium_mg": round(float(nutrition_per_100g.get("sodium_mg", 0.0)) * ratio, 1)
        }

    @staticmethod
    def calculate_wellness_score(consumed, goals):
        """
        Calculates an objective, transparent wellness score (0 to 100) based on:
        - Calorie target adherence (up to 35 pts)
        - Protein target achievement (up to 30 pts)
        - Healthy macro balance (up to 20 pts)
        - Meal consistency / logging activity (up to 15 pts)
        """
        if not goals or not goals.get("calorie_target"):
            return 70  # Default initial baseline

        score = 0.0
        cal_target = float(goals["calorie_target"])
        cal_consumed = float(consumed.get("total_calories", 0.0))

        # 1. Calorie adherence (35 pts)
        if cal_target > 0:
            diff_ratio = abs(cal_consumed - cal_target) / cal_target
            if diff_ratio <= 0.10:
                score += 35.0
            elif diff_ratio <= 0.25:
                score += 25.0
            elif diff_ratio <= 0.40:
                score += 15.0
            else:
                score += 5.0

        # 2. Protein goal (30 pts)
        pro_target = float(goals.get("protein_target_g", 75.0))
        pro_consumed = float(consumed.get("total_protein_g", 0.0))
        if pro_target > 0:
            pro_ratio = min(1.0, pro_consumed / pro_target)
            score += pro_ratio * 30.0

        # 3. Macro presence (20 pts)
        has_pro = pro_consumed > 5.0
        has_carbs = float(consumed.get("total_carbs_g", 0.0)) > 15.0
        has_fat = float(consumed.get("total_fat_g", 0.0)) > 5.0
        macros_present = sum([has_pro, has_carbs, has_fat])
        score += (macros_present / 3.0) * 20.0

        # 4. Meal logging consistency (15 pts)
        meal_count = int(consumed.get("meal_count", 0))
        if meal_count >= 3:
            score += 15.0
        elif meal_count == 2:
            score += 10.0
        elif meal_count == 1:
            score += 5.0

        return int(min(100, max(0, round(score))))
