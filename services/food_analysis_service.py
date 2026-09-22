import io
import os
import uuid
from PIL import Image
from werkzeug.utils import secure_filename
from config.config import Config
from models.food import Food
from models.ai_analysis import AiAnalysis
from services.gemini_service import GeminiService
from services.calculation_service import CalculationService

class FoodAnalysisService:
    """Orchestrates image compression, Gemini AI food scanning, and database caching."""

    @staticmethod
    def compress_image(image_file, max_dimension=1024, quality=85):
        """
        Compresses and resizes the image to fit within max_dimension.
        Returns: (compressed_bytes: bytes, mime_type: str, saved_filename: str)
        """
        image_file.seek(0)
        img = Image.open(image_file.stream)

        # Convert RGBA to RGB for JPEG compatibility
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Resize preserving aspect ratio
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

        # Save to memory bytes
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        compressed_bytes = buffer.getvalue()

        # Generate unique safe filename and save to uploads
        unique_name = f"{uuid.uuid4().hex[:12]}_{secure_filename(image_file.filename or 'scan.jpg')}"
        if not unique_name.lower().endswith((".jpg", ".jpeg")):
            unique_name += ".jpg"

        upload_path = os.path.join(Config.UPLOAD_FOLDER, unique_name)
        with open(upload_path, "wb") as f:
            f.write(compressed_bytes)

        return compressed_bytes, "image/jpeg", unique_name

    @classmethod
    def process_and_analyze(cls, image_file, user_id=None):
        """
        Full analysis pipeline:
        1. Compresses and stores image
        2. Dispatches to Gemini Vision
        3. If non-food, logs and returns clear rejection
        4. If food, checks local cache, caches unknown foods, and calculates portion macros
        """
        compressed_bytes, mime_type, filename = cls.compress_image(image_file)
        relative_image_path = f"/uploads/{filename}"

        # Call Gemini AI
        ai_res = GeminiService.analyze_food_image(compressed_bytes, mime_type=mime_type)

        if not ai_res.get("success"):
            return {
                "success": False,
                "error_code": ai_res.get("error_code", "SCAN_FAILED"),
                "message": ai_res.get("message", "Unable to analyze food image."),
                "image_url": relative_image_path
            }

        is_food = ai_res.get("is_food", False)
        confidence = ai_res.get("confidence", 0.0)

        # Log AI analysis to database if user is authenticated
        if user_id:
            AiAnalysis.log_analysis(
                user_id=user_id,
                image_path=relative_image_path,
                is_food=is_food,
                confidence=confidence,
                raw_response=ai_res.get("raw_response"),
                rejection_reason=ai_res.get("reason") if not is_food else None
            )

        if not is_food:
            return {
                "success": True,
                "is_food": False,
                "confidence": confidence,
                "rejection_reason": ai_res.get("reason", "No food was detected in this image. Please capture an edible food item."),
                "image_url": relative_image_path,
                "foods": []
            }

        # Food items processing & caching
        processed_foods = []
        raw_foods = ai_res.get("foods", [])

        for f_item in raw_foods:
            name = f_item.get("name", "").strip()
            est_weight = float(f_item.get("estimated_weight_g", 100.0))
            serving_desc = f_item.get("serving_description", f"{int(est_weight)}g")
            nutr_100g = f_item.get("nutrition_per_100g", {})

            # 1. Check local database cache
            cached_food = Food.find_by_name(name)
            source = "local_db" if cached_food else "ai_estimated"

            if cached_food:
                food_id = cached_food["id"]
                # Use stored nutrition info
                standard_nutr = {
                    "calories": float(cached_food["calories_per_100g"]),
                    "protein_g": float(cached_food["protein_g_per_100g"]),
                    "carbohydrates_g": float(cached_food["carbs_g_per_100g"]),
                    "fat_g": float(cached_food["fat_g_per_100g"]),
                    "fiber_g": float(cached_food["fiber_g_per_100g"]),
                    "sugar_g": float(cached_food["sugar_g_per_100g"]),
                    "sodium_mg": float(cached_food.get("sodium_mg_per_100g", 0.0))
                }
            else:
                # Cache newly recognized food into local DB
                standard_nutr = nutr_100g
                food_id = Food.create_or_update_with_nutrition(
                    name=name,
                    category="AI Discovered",
                    serving_description=serving_desc,
                    standard_weight_g=est_weight,
                    nutrition_per_100g=standard_nutr,
                    source="gemini_ai"
                )

            # 2. Scale nutrition according to estimated serving weight
            scaled = CalculationService.scale_nutrition(standard_nutr, est_weight)

            processed_foods.append({
                "food_id": food_id,
                "name": name,
                "estimated_weight_g": est_weight,
                "serving_description": serving_desc,
                "source": source,
                "nutrition_per_100g": standard_nutr,
                "scaled_nutrition": scaled
            })

        # Calculate combined total nutrition for all items in the scan
        total_cal = round(sum(f["scaled_nutrition"]["calories"] for f in processed_foods), 1)
        total_pro = round(sum(f["scaled_nutrition"]["protein_g"] for f in processed_foods), 1)
        total_carb = round(sum(f["scaled_nutrition"]["carbs_g"] for f in processed_foods), 1)
        total_fat = round(sum(f["scaled_nutrition"]["fat_g"] for f in processed_foods), 1)
        total_fib = round(sum(f["scaled_nutrition"]["fiber_g"] for f in processed_foods), 1)
        total_sug = round(sum(f["scaled_nutrition"]["sugar_g"] for f in processed_foods), 1)

        return {
            "success": True,
            "is_food": True,
            "confidence": confidence,
            "image_url": relative_image_path,
            "foods": processed_foods,
            "totals": {
                "calories": total_cal,
                "protein_g": total_pro,
                "carbs_g": total_carb,
                "fat_g": total_fat,
                "fiber_g": total_fib,
                "sugar_g": total_sug
            }
        }
