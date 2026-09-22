from datetime import date
from flask import Blueprint, render_template, session, jsonify
from models.user import User
from models.nutrition_goal import NutritionGoal
from models.meal import Meal
from services.calculation_service import CalculationService
from routes.auth_routes import login_required

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
@login_required
def dashboard_page():
    user_id = session["user_id"]
    user = User.find_by_id(user_id)
    goals = NutritionGoal.get_by_user_id(user_id)
    
    # If user doesn't have goals yet, initialize them
    if not goals and user:
        targets = CalculationService.calculate_nutrition_targets(
            age=user.get("age"),
            gender=user.get("gender", "other"),
            height_cm=user.get("height_cm"),
            weight_kg=user.get("weight_kg"),
            activity_level=user.get("activity_level", "sedentary"),
            fitness_goal=user.get("fitness_goal", "maintain")
        )
        goals = NutritionGoal.save_or_update(
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

    today = date.today()
    summary = Meal.get_today_summary(user_id, today)
    today_meals = Meal.get_user_meals_by_date(user_id, today)

    # Calculate remaining targets
    cal_target = float(goals.get("calorie_target", 2000)) if goals else 2000
    pro_target = float(goals.get("protein_target_g", 75)) if goals else 75
    carb_target = float(goals.get("carbs_target_g", 250)) if goals else 250
    fat_target = float(goals.get("fat_target_g", 65)) if goals else 65

    cal_consumed = float(summary.get("total_calories", 0.0))
    pro_consumed = float(summary.get("total_protein_g", 0.0))
    carb_consumed = float(summary.get("total_carbs_g", 0.0))
    fat_consumed = float(summary.get("total_fat_g", 0.0))

    cal_remaining = max(0.0, round(cal_target - cal_consumed, 1))
    pro_remaining = max(0.0, round(pro_target - pro_consumed, 1))
    carb_remaining = max(0.0, round(carb_target - carb_consumed, 1))
    fat_remaining = max(0.0, round(fat_target - fat_consumed, 1))

    # Calculate percentage progress for radial / progress bars
    cal_pct = min(100, round((cal_consumed / cal_target * 100), 1)) if cal_target > 0 else 0
    pro_pct = min(100, round((pro_consumed / pro_target * 100), 1)) if pro_target > 0 else 0
    carb_pct = min(100, round((carb_consumed / carb_target * 100), 1)) if carb_target > 0 else 0
    fat_pct = min(100, round((fat_consumed / fat_target * 100), 1)) if fat_target > 0 else 0

    wellness_score = CalculationService.calculate_wellness_score(summary, goals)

    return render_template(
        "dashboard.html",
        user=user,
        goals=goals,
        summary=summary,
        today_meals=today_meals,
        cal_remaining=cal_remaining,
        pro_remaining=pro_remaining,
        carb_remaining=carb_remaining,
        fat_remaining=fat_remaining,
        cal_pct=cal_pct,
        pro_pct=pro_pct,
        carb_pct=carb_pct,
        fat_pct=fat_pct,
        wellness_score=wellness_score,
        today_str=today.strftime("%A, %B %d, %Y")
    )

@dashboard_bp.route("/api/dashboard", methods=["GET"])
@login_required
def api_dashboard():
    user_id = session["user_id"]
    user = User.find_by_id(user_id)
    goals = NutritionGoal.get_by_user_id(user_id)
    today = date.today()
    summary = Meal.get_today_summary(user_id, today)
    today_meals = Meal.get_user_meals_by_date(user_id, today)

    cal_target = float(goals.get("calorie_target", 2000)) if goals else 2000
    cal_consumed = float(summary.get("total_calories", 0.0))
    wellness_score = CalculationService.calculate_wellness_score(summary, goals)

    return jsonify({
        "success": True,
        "date": today.isoformat(),
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "fitness_goal": user.get("fitness_goal", "maintain")
        },
        "goals": goals,
        "summary": summary,
        "remaining": {
            "calories": max(0.0, round(cal_target - cal_consumed, 1)),
            "protein_g": max(0.0, round(float(goals.get("protein_target_g", 75)) - float(summary.get("total_protein_g", 0)), 1)) if goals else 0,
            "carbs_g": max(0.0, round(float(goals.get("carbs_target_g", 250)) - float(summary.get("total_carbs_g", 0)), 1)) if goals else 0,
            "fat_g": max(0.0, round(float(goals.get("fat_target_g", 65)) - float(summary.get("total_fat_g", 0)), 1)) if goals else 0
        },
        "wellness_score": wellness_score,
        "recent_meals": today_meals
    })
