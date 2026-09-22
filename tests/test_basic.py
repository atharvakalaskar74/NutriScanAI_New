import unittest
from services.calculation_service import CalculationService
from services.validation_service import ValidationService
from models.user import User
from app import create_app

class TestNutriScanCore(unittest.TestCase):
    """Unit tests for calculation, validation, auth security, and routes."""

    def test_password_hashing(self):
        pwd = "SecretPassword123!"
        hashed = User.hash_password(pwd)
        self.assertNotEqual(pwd, hashed)
        self.assertTrue(User.verify_password(hashed, pwd))
        self.assertFalse(User.verify_password(hashed, "WrongPassword"))

    def test_bmr_calculation_mifflin_st_jeor(self):
        # Male: 70kg, 175cm, 25yr -> (10*70) + (6.25*175) - (5*25) + 5 = 700 + 1093.75 - 125 + 5 = 1673.75 -> 1673.8
        bmr_male = CalculationService.calculate_bmr(weight_kg=70, height_cm=175, age=25, gender="male")
        self.assertAlmostEqual(bmr_male, 1673.8, delta=0.5)

        # Female: 60kg, 165cm, 25yr -> (10*60) + (6.25*165) - (5*25) - 161 = 600 + 1031.25 - 125 - 161 = 1345.25 -> 1345.2
        bmr_female = CalculationService.calculate_bmr(weight_kg=60, height_cm=165, age=25, gender="female")
        self.assertAlmostEqual(bmr_female, 1345.2, delta=0.5)

    def test_tdee_calculation(self):
        bmr = 1600.0
        tdee_sedentary = CalculationService.calculate_tdee(bmr, "sedentary")
        self.assertEqual(tdee_sedentary, 1920.0)  # 1600 * 1.2

        tdee_moderate = CalculationService.calculate_tdee(bmr, "moderate")
        self.assertEqual(tdee_moderate, 2480.0)   # 1600 * 1.55

    def test_nutrition_targets_macro_splits(self):
        targets = CalculationService.calculate_nutrition_targets(
            age=25, gender="male", height_cm=175, weight_kg=70,
            activity_level="moderate", fitness_goal="maintain"
        )
        self.assertIn("calorie_target", targets)
        self.assertIn("protein_target_g", targets)
        self.assertIn("carbs_target_g", targets)
        self.assertIn("fat_target_g", targets)
        self.assertGreater(targets["calorie_target"], 1200)

    def test_scaled_nutrition_calculation(self):
        # 100g base: 200 kcal, 10g protein
        base_100g = {
            "calories": 200.0,
            "protein_g": 10.0,
            "carbohydrates_g": 25.0,
            "fat_g": 6.0,
            "fiber_g": 2.0,
            "sugar_g": 1.0
        }
        # Scaled to 250g: factor 2.5
        scaled = CalculationService.scale_nutrition(base_100g, weight_g=250.0)
        self.assertEqual(scaled["weight_g"], 250.0)
        self.assertEqual(scaled["calories"], 500.0)
        self.assertEqual(scaled["protein_g"], 25.0)
        self.assertEqual(scaled["carbs_g"], 62.5)
        self.assertEqual(scaled["fat_g"], 15.0)

    def test_wellness_score_bounds(self):
        consumed = {"total_calories": 2000, "total_protein_g": 80, "total_carbs_g": 250, "total_fat_g": 65, "meal_count": 3}
        goals = {"calorie_target": 2000, "protein_target_g": 80}
        score = CalculationService.calculate_wellness_score(consumed, goals)
        self.assertTrue(0 <= score <= 100)
        self.assertGreater(score, 70)  # Near perfect adherence

    def test_validation_rules(self):
        # Valid data
        valid, errors = ValidationService.validate_registration({
            "full_name": "Test User",
            "email": "test@nutriscan.ai",
            "password": "validpassword",
            "age": 25,
            "height_cm": 175,
            "weight_kg": 70
        })
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)

        # Invalid email and short password
        invalid, errs = ValidationService.validate_registration({
            "full_name": "T",
            "email": "invalid-email-no-domain",
            "password": "123"
        })
        self.assertFalse(invalid)
        self.assertGreater(len(errs), 0)

    def test_flask_routes_smoke(self):
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        # Public routes
        res_home = client.get("/")
        self.assertEqual(res_home.status_code, 200)

        res_login = client.get("/login")
        self.assertEqual(res_login.status_code, 200)

        res_reg = client.get("/register")
        self.assertEqual(res_reg.status_code, 200)

        # Health check
        res_health = client.get("/health")
        self.assertIn(res_health.status_code, (200, 503))

    def test_gemini_json_parser(self):
        from services.gemini_service import GeminiService
        
        # 1. Plain JSON
        plain = '{"is_food": true, "confidence": 0.95, "foods": []}'
        self.assertEqual(GeminiService._parse_json_response(plain)["is_food"], True)

        # 2. Markdown fenced JSON
        fenced = '```json\n{"is_food": false, "confidence": 0.99, "reason": "Person detected"}\n```'
        parsed = GeminiService._parse_json_response(fenced)
        self.assertEqual(parsed["is_food"], False)
        self.assertEqual(parsed["reason"], "Person detected")

        # 3. Text prefix
        prefixed = 'Here is the analysis:\n{"is_food": true, "confidence": 0.91, "foods": [{"name": "Rice"}]}'
        parsed_p = GeminiService._parse_json_response(prefixed)
        self.assertEqual(parsed_p["is_food"], True)
        self.assertEqual(parsed_p["foods"][0]["name"], "Rice")

if __name__ == "__main__":
    unittest.main()
