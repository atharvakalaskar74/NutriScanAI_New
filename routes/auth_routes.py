from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models.user import User
from models.nutrition_goal import NutritionGoal
from services.validation_service import ValidationService
from services.calculation_service import CalculationService

auth_bp = Blueprint("auth", __name__)

def login_required(f):
    """Decorator ensuring a user is logged in before accessing a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"success": False, "message": "Authentication required. Please log in."}), 401
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route("/register", methods=["GET", "POST"])
def register_page():
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard_page"))

    if request.method == "POST":
        data = request.form.to_dict()
        is_valid, errors = ValidationService.validate_registration(data)
        if not is_valid:
            for err in errors:
                flash(err, "danger")
            return render_template("register.html", form_data=data)

        # Check existing user
        if User.find_by_email(data["email"]):
            flash("An account with this email already exists. Please log in.", "warning")
            return render_template("register.html", form_data=data)

        try:
            # Create user
            user_id = User.create(
                full_name=data["full_name"],
                email=data["email"],
                password=data["password"],
                age=data.get("age"),
                gender=data.get("gender", "other"),
                height_cm=data.get("height_cm"),
                weight_kg=data.get("weight_kg"),
                activity_level=data.get("activity_level", "sedentary"),
                fitness_goal=data.get("fitness_goal", "maintain")
            )

            # Automatically compute and initialize default nutrition goals
            targets = CalculationService.calculate_nutrition_targets(
                age=data.get("age"),
                gender=data.get("gender", "other"),
                height_cm=data.get("height_cm"),
                weight_kg=data.get("weight_kg"),
                activity_level=data.get("activity_level", "sedentary"),
                fitness_goal=data.get("fitness_goal", "maintain")
            )
            NutritionGoal.save_or_update(
                user_id=user_id,
                calorie_target=targets["calorie_target"],
                protein_target_g=targets["protein_target_g"],
                carbs_target_g=targets["carbs_target_g"],
                fat_target_g=targets["fat_target_g"],
                fiber_target_g=targets["fiber_target_g"],
                water_target_ml=targets["water_target_ml"],
                bmr_kcal=targets["bmr_kcal"],
                tdee_kcal=targets["tdee_kcal"]
            )

            # Auto-login upon registration
            session["user_id"] = user_id
            session["user_name"] = data["full_name"]
            session["user_email"] = data["email"].strip().lower()

            flash("Welcome to NutriScan AI! Your personal nutrition targets have been initialized.", "success")
            return redirect(url_for("dashboard.dashboard_page"))

        except Exception as e:
            flash(f"Registration failed: {str(e)}", "danger")
            return render_template("register.html", form_data=data)

    return render_template("register.html", form_data={})

@auth_bp.route("/login", methods=["GET", "POST"])
def login_page():
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard_page"))

    if request.method == "POST":
        data = request.form.to_dict()
        is_valid, errors = ValidationService.validate_login(data)
        if not is_valid:
            for err in errors:
                flash(err, "danger")
            return render_template("login.html", email=data.get("email", ""))

        user = User.find_by_email(data["email"])
        if not user or not User.verify_password(user["password_hash"], data["password"]):
            flash("Invalid email or password. Please try again.", "danger")
            return render_template("login.html", email=data.get("email", ""))

        # Establish session
        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["full_name"]
        session["user_email"] = user["email"]

        flash(f"Welcome back, {user['full_name']}!", "success")
        return redirect(url_for("dashboard.dashboard_page"))

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("auth.login_page"))

# ================= REST API Endpoints =================

@auth_bp.route("/api/auth/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or request.form.to_dict()
    is_valid, errors = ValidationService.validate_registration(data)
    if not is_valid:
        return jsonify({"success": False, "errors": errors}), 400

    if User.find_by_email(data["email"]):
        return jsonify({"success": False, "message": "Email already registered."}), 409

    try:
        user_id = User.create(
            full_name=data["full_name"],
            email=data["email"],
            password=data["password"],
            age=data.get("age"),
            gender=data.get("gender", "other"),
            height_cm=data.get("height_cm"),
            weight_kg=data.get("weight_kg"),
            activity_level=data.get("activity_level", "sedentary"),
            fitness_goal=data.get("fitness_goal", "maintain")
        )

        targets = CalculationService.calculate_nutrition_targets(
            age=data.get("age"),
            gender=data.get("gender", "other"),
            height_cm=data.get("height_cm"),
            weight_kg=data.get("weight_kg"),
            activity_level=data.get("activity_level", "sedentary"),
            fitness_goal=data.get("fitness_goal", "maintain")
        )
        NutritionGoal.save_or_update(
            user_id=user_id,
            calorie_target=targets["calorie_target"],
            protein_target_g=targets["protein_target_g"],
            carbs_target_g=targets["carbs_target_g"],
            fat_target_g=targets["fat_target_g"],
            fiber_target_g=targets["fiber_target_g"],
            water_target_ml=targets["water_target_ml"],
            bmr_kcal=targets["bmr_kcal"],
            tdee_kcal=targets["tdee_kcal"]
        )

        session["user_id"] = user_id
        session["user_name"] = data["full_name"]
        session["user_email"] = data["email"].strip().lower()

        return jsonify({
            "success": True,
            "message": "User registered successfully.",
            "user": {
                "id": user_id,
                "full_name": data["full_name"],
                "email": data["email"]
            }
        }), 201

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@auth_bp.route("/api/auth/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or request.form.to_dict()
    is_valid, errors = ValidationService.validate_login(data)
    if not is_valid:
        return jsonify({"success": False, "errors": errors}), 400

    user = User.find_by_email(data["email"])
    if not user or not User.verify_password(user["password_hash"], data["password"]):
        return jsonify({"success": False, "message": "Invalid email or password."}), 401

    session.clear()
    session["user_id"] = user["id"]
    session["user_name"] = user["full_name"]
    session["user_email"] = user["email"]

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"]
        }
    })

@auth_bp.route("/api/auth/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully."})
