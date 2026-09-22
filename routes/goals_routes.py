from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from models.user import User
from models.nutrition_goal import NutritionGoal
from services.calculation_service import CalculationService
from routes.auth_routes import login_required

goals_bp = Blueprint("goals", __name__)

@goals_bp.route("/goals", methods=["GET", "POST"])
@login_required
def goals_page():
    user_id = session["user_id"]
    user = User.find_by_id(user_id)
    goals = NutritionGoal.get_by_user_id(user_id)

    if request.method == "POST":
        cal_target = request.form.get("calorie_target")
        pro_target = request.form.get("protein_target_g")
        carb_target = request.form.get("carbs_target_g")
        fat_target = request.form.get("fat_target_g")
        fiber_target = request.form.get("fiber_target_g", 30.0)
        water_target = request.form.get("water_target_ml", 2500)

        # Recalculate BMR and TDEE if physical parameters available
        bmr = CalculationService.calculate_bmr(
            user.get("weight_kg"), user.get("height_cm"), user.get("age"), user.get("gender", "other")
        )
        tdee = CalculationService.calculate_tdee(bmr, user.get("activity_level", "sedentary"))

        NutritionGoal.save_or_update(
            user_id=user_id,
            calorie_target=cal_target,
            protein_target_g=pro_target,
            carbs_target_g=carb_target,
            fat_target_g=fat_target,
            fiber_target_g=fiber_target,
            water_target_ml=water_target,
            bmr_kcal=bmr,
            tdee_kcal=tdee
        )
        flash("Your nutrition goals have been updated successfully!", "success")
        return redirect(url_for("goals.goals_page"))

    # Initial recommendation calculation
    recommended = CalculationService.calculate_nutrition_targets(
        age=user.get("age"),
        gender=user.get("gender", "other"),
        height_cm=user.get("height_cm"),
        weight_kg=user.get("weight_kg"),
        activity_level=user.get("activity_level", "sedentary"),
        fitness_goal=user.get("fitness_goal", "maintain")
    )

    return render_template(
        "goals.html",
        user=user,
        goals=goals or recommended,
        recommended=recommended
    )

@goals_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile_page():
    user_id = session["user_id"]
    user = User.find_by_id(user_id)

    if request.method == "POST":
        full_name = request.form.get("full_name", user["full_name"]).strip()
        age = request.form.get("age")
        gender = request.form.get("gender", "other")
        height_cm = request.form.get("height_cm")
        weight_kg = request.form.get("weight_kg")
        activity_level = request.form.get("activity_level", "sedentary")
        fitness_goal = request.form.get("fitness_goal", "maintain")

        # Update profile
        User.update_profile(
            user_id=user_id,
            full_name=full_name,
            age=age,
            gender=gender,
            height_cm=height_cm,
            weight_kg=weight_kg,
            activity_level=activity_level,
            fitness_goal=fitness_goal
        )
        session["user_name"] = full_name

        # Optionally auto-recalculate goals if user checked the box
        if request.form.get("recalculate_goals") == "1":
            recomputed = CalculationService.calculate_nutrition_targets(
                age=age, gender=gender, height_cm=height_cm, weight_kg=weight_kg,
                activity_level=activity_level, fitness_goal=fitness_goal
            )
            NutritionGoal.save_or_update(
                user_id=user_id,
                calorie_target=recomputed["calorie_target"],
                protein_target_g=recomputed["protein_target_g"],
                carbs_target_g=recomputed["carbs_target_g"],
                fat_target_g=recomputed["fat_target_g"],
                fiber_target_g=recomputed["fiber_target_g"],
                water_target_ml=recomputed["water_target_ml"],
                bmr_kcal=recomputed["bmr_kcal"],
                tdee_kcal=recomputed["tdee_kcal"]
            )
            flash("Profile updated and nutrition goals recalculated!", "success")
        else:
            flash("Profile updated successfully!", "success")

        # Password change handling
        new_pwd = request.form.get("new_password")
        if new_pwd and len(new_pwd) >= 6:
            User.update_password(user_id, new_pwd)
            flash("Password updated successfully.", "info")

        return redirect(url_for("goals.profile_page"))

    goals = NutritionGoal.get_by_user_id(user_id)
    return render_template("profile.html", user=user, goals=goals)

# ================= REST API Endpoints =================

@goals_bp.route("/api/goals/calculate", methods=["POST"])
@login_required
def api_calculate_goals():
    data = request.get_json(silent=True) or request.form.to_dict()
    targets = CalculationService.calculate_nutrition_targets(
        age=data.get("age"),
        gender=data.get("gender", "other"),
        height_cm=data.get("height_cm"),
        weight_kg=data.get("weight_kg"),
        activity_level=data.get("activity_level", "sedentary"),
        fitness_goal=data.get("fitness_goal", "maintain")
    )
    return jsonify({"success": True, "calculated_targets": targets})

@goals_bp.route("/api/goals", methods=["GET", "PUT"])
@login_required
def api_goals():
    user_id = session["user_id"]
    if request.method == "GET":
        goals = NutritionGoal.get_by_user_id(user_id)
        return jsonify({"success": True, "goals": goals})

    data = request.get_json(silent=True) or {}
    updated = NutritionGoal.save_or_update(
        user_id=user_id,
        calorie_target=data.get("calorie_target", 2000),
        protein_target_g=data.get("protein_target_g", 75),
        carbs_target_g=data.get("carbs_target_g", 250),
        fat_target_g=data.get("fat_target_g", 65),
        fiber_target_g=data.get("fiber_target_g", 30),
        water_target_ml=data.get("water_target_ml", 2500)
    )
    return jsonify({"success": True, "message": "Goals updated.", "goals": updated})
