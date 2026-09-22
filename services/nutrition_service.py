from models.food import Food
from services.calculation_service import CalculationService

class NutritionService:
    """Service for calculating and recalculating food nutritional values."""

    @classmethod
    def recalculate_items(cls, items):
        """
        Takes a list of items with food_id (or 100g nutrition) and weight_g,
        recalculates scaled nutrition for each item, and returns item list + aggregate totals.
        """
        updated_items = []
        for item in items:
            weight_g = float(item.get("weight_g", 100.0))
            food_id = item.get("food_id")
            
            # If food_id is available, check cache first
            if food_id:
                food_record = Food.get_by_id(food_id)
                if food_record:
                    nutr_100g = {
                        "calories": float(food_record["calories_per_100g"]),
                        "protein_g": float(food_record["protein_g_per_100g"]),
                        "carbohydrates_g": float(food_record["carbs_g_per_100g"]),
                        "fat_g": float(food_record["fat_g_per_100g"]),
                        "fiber_g": float(food_record["fiber_g_per_100g"]),
                        "sugar_g": float(food_record["sugar_g_per_100g"]),
                        "sodium_mg": float(food_record["sodium_mg_per_100g"])
                    }
                else:
                    nutr_100g = item.get("nutrition_per_100g", {})
            else:
                nutr_100g = item.get("nutrition_per_100g", {})

            scaled = CalculationService.scale_nutrition(nutr_100g, weight_g)

            updated_items.append({
                "food_id": food_id,
                "name": item.get("name", "Food item"),
                "weight_g": weight_g,
                "source": item.get("source", "ai_estimated"),
                "nutrition_per_100g": nutr_100g,
                "scaled_nutrition": scaled,
                # Flattened properties for convenience
                "calories": scaled["calories"],
                "protein_g": scaled["protein_g"],
                "carbs_g": scaled["carbs_g"],
                "fat_g": scaled["fat_g"],
                "fiber_g": scaled["fiber_g"],
                "sugar_g": scaled["sugar_g"]
            })

        total_cal = round(sum(i["calories"] for i in updated_items), 1)
        total_pro = round(sum(i["protein_g"] for i in updated_items), 1)
        total_carb = round(sum(i["carbs_g"] for i in updated_items), 1)
        total_fat = round(sum(i["fat_g"] for i in updated_items), 1)
        total_fib = round(sum(i["fiber_g"] for i in updated_items), 1)
        total_sug = round(sum(i["sugar_g"] for i in updated_items), 1)

        return {
            "items": updated_items,
            "totals": {
                "calories": total_cal,
                "protein_g": total_pro,
                "carbs_g": total_carb,
                "fat_g": total_fat,
                "fiber_g": total_fib,
                "sugar_g": total_sug
            }
        }
