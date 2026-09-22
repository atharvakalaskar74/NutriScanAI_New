import re
import os
from PIL import Image
from config.config import Config

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

class ValidationService:
    """Input validation and sanitization service."""

    @staticmethod
    def validate_registration(data):
        """
        Validates user registration payload.
        Returns: (is_valid: bool, errors: list[str])
        """
        errors = []
        full_name = data.get("full_name", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not full_name or len(full_name) < 2 or len(full_name) > 100:
            errors.append("Full name must be between 2 and 100 characters.")

        if not email or not EMAIL_REGEX.match(email) or len(email) > 150:
            errors.append("A valid email address is required (e.g. user@example.com).")

        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters long.")

        # Optional demographic & physical fields
        age = data.get("age")
        if age is not None and str(age).strip() != "":
            try:
                age_val = int(age)
                if age_val < 10 or age_val > 120:
                    errors.append("Age must be between 10 and 120.")
            except (ValueError, TypeError):
                errors.append("Age must be a valid integer.")

        gender = data.get("gender", "other")
        if gender not in ("male", "female", "other"):
            errors.append("Gender must be 'male', 'female', or 'other'.")

        height = data.get("height_cm")
        if height is not None and str(height).strip() != "":
            try:
                h_val = float(height)
                if h_val < 50 or h_val > 270:
                    errors.append("Height must be between 50 cm and 270 cm.")
            except (ValueError, TypeError):
                errors.append("Height must be a valid number.")

        weight = data.get("weight_kg")
        if weight is not None and str(weight).strip() != "":
            try:
                w_val = float(weight)
                if w_val < 20 or w_val > 450:
                    errors.append("Weight must be between 20 kg and 450 kg.")
            except (ValueError, TypeError):
                errors.append("Weight must be a valid number.")

        activity = data.get("activity_level", "sedentary")
        if activity not in ("sedentary", "light", "moderate", "active", "very_active"):
            errors.append("Invalid activity level selected.")

        fitness_goal = data.get("fitness_goal", "maintain")
        if fitness_goal not in ("maintain", "lose_weight", "gain_weight", "build_muscle"):
            errors.append("Invalid fitness goal selected.")

        return len(errors) == 0, errors

    @staticmethod
    def validate_login(data):
        """Validates login credentials format."""
        errors = []
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not email or not EMAIL_REGEX.match(email):
            errors.append("Valid email is required.")
        if not password:
            errors.append("Password is required.")

        return len(errors) == 0, errors

    @staticmethod
    def validate_image_file(file_storage):
        """
        Validates uploaded image file:
        - Presence of filename
        - Extension in allowed list
        - Can be opened and identified as a valid image format by Pillow
        Returns: (is_valid: bool, error_msg: str or None)
        """
        if not file_storage or not file_storage.filename:
            return False, "No file selected for upload."

        filename = file_storage.filename.lower()
        ext = filename.rsplit(".", 1)[-1] if "." in filename else ""

        if ext not in Config.ALLOWED_EXTENSIONS:
            return False, f"File format not supported. Allowed formats: {', '.join(Config.ALLOWED_EXTENSIONS).upper()}"

        try:
            # Check image validity using Pillow without saving to disk yet
            file_storage.seek(0)
            img = Image.open(file_storage.stream)
            img.verify()  # Verifies image structure
            file_storage.seek(0)  # Reset stream position for later reading
            return True, None
        except Exception:
            file_storage.seek(0)
            return False, "The uploaded file is not a valid image."
