import json
import logging
import re
from google import genai
from google.genai import types
from google.genai.errors import APIError
from config.config import Config

logger = logging.getLogger(__name__)

FOOD_SCAN_SYSTEM_PROMPT = """
You are an expert AI food recognition and nutritional analysis engine.
Carefully inspect the provided image.

STEP 1: Determine whether the image contains genuine edible FOOD or BEVERAGE.
- If the image contains a person, selfie, face, body part, clothing, electronics (laptop, phone), vehicle, animal/pet, landscape, document, or non-edible object:
  Set "is_food": false
  Set "confidence": a float between 0.0 and 1.0
  Set "reason": A polite, explicit explanation specifying what is seen (e.g. "Non-food image detected. This appears to contain a person/face rather than food. Please scan an edible food item.")
  Leave "foods": []

STEP 2: If the image DOES contain food:
- Set "is_food": true
- Set "confidence": a float between 0.0 and 1.0
- Identify all distinct food items present (e.g., if a plate contains Rice, Dal, and Roti, identify each separate item).
- For each food item, provide:
  - "name": Clean, common food name (e.g., "Chicken Biryani", "Steamed White Rice", "Yellow Dal Tadka", "Paneer Tikka")
  - "estimated_weight_g": Realistic estimated weight in grams for this portion (e.g. 150 for a bowl of rice, 40 for a roti, 300 for a biryani plate).
  - "serving_description": A friendly descriptor (e.g. "1 medium bowl", "2 pieces", "1 regular plate")
  - "nutrition_per_100g": Standard nutritional breakdown for 100 grams of this food:
    - "calories": float kcal
    - "protein_g": float grams
    - "carbohydrates_g": float grams
    - "fat_g": float grams
    - "fiber_g": float grams
    - "sugar_g": float grams

CRITICAL OUTPUT FORMAT:
You MUST respond ONLY with valid JSON. Do not output conversational filler or preamble.
Example JSON for food:
{
  "is_food": true,
  "confidence": 0.95,
  "foods": [
    {
      "name": "Chicken Biryani",
      "estimated_weight_g": 300,
      "serving_description": "1 regular plate",
      "nutrition_per_100g": {
        "calories": 173.0,
        "protein_g": 8.2,
        "carbohydrates_g": 20.4,
        "fat_g": 6.5,
        "fiber_g": 1.2,
        "sugar_g": 0.8
      }
    }
  ]
}

Example JSON for non-food:
{
  "is_food": false,
  "confidence": 0.98,
  "reason": "Non-food image detected. This appears to contain a person rather than food. Please scan a food item.",
  "foods": []
}
"""

class GeminiService:
    """Service wrapper for Google Gemini multimodal analysis and AI nutrition assistant."""

    @classmethod
    def get_client(cls):
        """Initializes and returns the Google GenAI Client if API key is configured."""
        api_key = Config.GEMINI_API_KEY
        if not api_key:
            return None
        return genai.Client(api_key=api_key)

    @classmethod
    def analyze_food_image(cls, image_bytes, mime_type="image/jpeg"):
        """
        Sends food image to Gemini Vision model for classification & nutritional estimation.
        Returns: dict with is_food, confidence, foods list, and optional reason or error.
        """
        client = cls.get_client()
        if not client:
            return {
                "success": False,
                "error_code": "NO_API_KEY",
                "message": "Gemini API key is not configured. Please add your GEMINI_API_KEY to the .env file."
            }

        try:
            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type
            )

            model_name = Config.GEMINI_MODEL or "gemini-3.6-flash"
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    image_part,
                    FOOD_SCAN_SYSTEM_PROMPT
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )

            raw_text = response.text.strip() if response.text else ""
            data = cls._parse_json_response(raw_text)

            # Backend response validation
            if not isinstance(data, dict):
                return {
                    "success": False,
                    "error_code": "INVALID_AI_RESPONSE",
                    "message": "The AI service returned an unrecognized format. Please try again."
                }

            is_food = bool(data.get("is_food", False))
            confidence = float(data.get("confidence", 0.85))
            reason = data.get("reason", "")
            foods = data.get("foods", [])

            if not is_food:
                return {
                    "success": True,
                    "is_food": False,
                    "confidence": confidence,
                    "reason": reason or "This image does not appear to contain food. Please point your camera at an edible food item.",
                    "foods": [],
                    "raw_response": raw_text
                }

            # Normalize food items
            sanitized_foods = []
            for item in foods:
                if not isinstance(item, dict) or not item.get("name"):
                    continue
                nutr = item.get("nutrition_per_100g", {})
                sanitized_foods.append({
                    "name": str(item.get("name", "Unknown Food")).strip(),
                    "estimated_weight_g": float(item.get("estimated_weight_g", 100.0)),
                    "serving_description": str(item.get("serving_description", "1 serving")),
                    "nutrition_per_100g": {
                        "calories": float(nutr.get("calories", 100.0)),
                        "protein_g": float(nutr.get("protein_g", 5.0)),
                        "carbohydrates_g": float(nutr.get("carbohydrates_g", nutr.get("carbs_g", 15.0))),
                        "fat_g": float(nutr.get("fat_g", 2.0)),
                        "fiber_g": float(nutr.get("fiber_g", 1.0)),
                        "sugar_g": float(nutr.get("sugar_g", 1.0)),
                        "sodium_mg": float(nutr.get("sodium_mg", 0.0))
                    }
                })

            if not sanitized_foods:
                return {
                    "success": True,
                    "is_food": False,
                    "confidence": confidence,
                    "reason": "No identifiable food items could be distinguished in this image. Please try a clearer food photo.",
                    "foods": [],
                    "raw_response": raw_text
                }

            return {
                "success": True,
                "is_food": True,
                "confidence": confidence,
                "foods": sanitized_foods,
                "raw_response": raw_text
            }

        except APIError as e:
            logger.error(f"Gemini API Error: {e}")
            err_msg = str(e).lower()
            if "quota" in err_msg or "429" in err_msg or "resource_exhausted" in err_msg:
                return {
                    "success": False,
                    "error_code": "QUOTA_EXCEEDED",
                    "message": "Gemini API free-tier quota exceeded or rate limit reached. Please wait a minute and retry."
                }
            elif "api_key" in err_msg or "unauthenticated" in err_msg:
                return {
                    "success": False,
                    "error_code": "INVALID_API_KEY",
                    "message": "Invalid Gemini API key. Please check your credentials in .env."
                }
            return {
                "success": False,
                "error_code": "AI_API_ERROR",
                "message": f"Gemini AI service error: {str(e)}"
            }
        except Exception as ex:
            logger.error(f"Unexpected error in analyze_food_image: {ex}")
            return {
                "success": False,
                "error_code": "UNEXPECTED_ERROR",
                "message": f"Failed to analyze image: {str(ex)}"
            }

    @classmethod
    def chat_assistant(cls, user_message, user_context=None, conversation_history=None):
        """
        AI Nutrition Assistant chatbot utilizing Gemini with injected user profile & daily macros context.
        """
        client = cls.get_client()
        if not client:
            return {
                "success": False,
                "error_code": "NO_API_KEY",
                "message": "Gemini API key is not configured in .env. Please configure your free Gemini API key to activate the AI Assistant."
            }

        # Build context system prompt
        ctx = user_context or {}
        context_str = f"""
You are the NutriScan AI Personal Nutrition Assistant.
Current User Profile:
- Name: {ctx.get('full_name', 'User')}
- Age: {ctx.get('age', 'Not specified')}
- Gender: {ctx.get('gender', 'Not specified')}
- Weight: {ctx.get('weight_kg', 'Not specified')} kg
- Height: {ctx.get('height_cm', 'Not specified')} cm
- Fitness Goal: {ctx.get('fitness_goal', 'maintain')}
- Activity Level: {ctx.get('activity_level', 'sedentary')}

Today's Nutrition Tracker Status:
- Calories Consumed: {ctx.get('calories_consumed', 0)} kcal / Daily Target: {ctx.get('calorie_target', 2000)} kcal (Remaining: {ctx.get('calories_remaining', 2000)} kcal)
- Protein Consumed: {ctx.get('protein_consumed', 0)}g / Target: {ctx.get('protein_target', 75)}g
- Carbs Consumed: {ctx.get('carbs_consumed', 0)}g / Target: {ctx.get('carbs_target', 250)}g
- Fat Consumed: {ctx.get('fat_consumed', 0)}g / Target: {ctx.get('fat_target', 65)}g
- Meals Logged Today: {ctx.get('meal_count', 0)}

INSTRUCTIONS:
1. Provide practical, accurate, supportive nutrition advice tailored directly to their current intake numbers and goals.
2. If their protein is low, suggest healthy protein-rich food items (e.g. dal, paneer, eggs, chicken, yogurt, tofu).
3. If they ask what to eat for their next meal, take into account their remaining calorie and macro budget.
4. Keep replies clear, well-formatted, and concise with bullet points where helpful.
5. Always maintain scientific integrity. Include a brief, friendly closing note that this is general nutrition guidance, not medical advice.
"""

        try:
            # Prepare conversation
            contents = [context_str]
            if conversation_history:
                for msg in conversation_history[-6:]:  # Keep last 3 turns
                    role = "user" if msg.get("role") == "user" else "model"
                    contents.append(f"{role.upper()}: {msg.get('message', '')}")
            contents.append(f"USER: {user_message}")

            model_name = Config.GEMINI_MODEL or "gemini-3.6-flash"
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=1500
                )
            )

            reply = response.text.strip() if response.text else "I am here to help you reach your nutrition goals. How can I assist you today?"
            return {
                "success": True,
                "reply": reply
            }

        except APIError as e:
            logger.error(f"Gemini Chat API Error: {e}")
            err_msg = str(e).lower()
            if "quota" in err_msg or "429" in err_msg:
                return {
                    "success": False,
                    "error_code": "QUOTA_EXCEEDED",
                    "message": "Gemini API quota exceeded. Please wait a minute and ask again."
                }
            return {
                "success": False,
                "error_code": "AI_API_ERROR",
                "message": f"AI Assistant is currently unavailable: {str(e)}"
            }
        except Exception as ex:
            logger.error(f"Unexpected chat error: {ex}")
            return {
                "success": False,
                "error_code": "UNEXPECTED_ERROR",
                "message": f"Chatbot error: {str(ex)}"
            }

    @staticmethod
    def _parse_json_response(raw_text):
        """Extracts JSON object from text even if enclosed in markdown code blocks."""
        if not raw_text:
            return None
        text = raw_text.strip()
        # Remove ```json and ``` fences
        if text.startswith("```"):
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback regex extraction of first {...} block
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
            return None
