from datetime import date, datetime
from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from models.meal import Meal
from routes.auth_routes import login_required

meal_bp = Blueprint("meal", __name__)

@meal_bp.route("/meal-history")
@login_required
def history_page():
    user_id = session["user_id"]
    selected_date_str = request.args.get("date")

    if selected_date_str:
        try:
            target_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
        except ValueError:
            target_date = date.today()
    else:
        target_date = date.today()

    meals = Meal.get_user_meals_by_date(user_id, target_date)
    daily_summary = Meal.get_today_summary(user_id, target_date)

    return render_template(
        "meal_history.html",
        selected_date=target_date,
        selected_date_str=target_date.strftime("%Y-%m-%d"),
        formatted_date=target_date.strftime("%A, %B %d, %Y"),
        meals=meals,
        summary=daily_summary,
        is_today=(target_date == date.today())
    )

# ================= REST API Endpoints =================

@meal_bp.route("/api/meals", methods=["POST"])
@login_required
def api_save_meal():
    """
    Saves an analyzed meal with its constituent food items.
    Accepts: {
        "meal_type": "lunch",
        "meal_date": "2026-09-23",
        "meal_time": "13:30:00",
        "items": [...],
        "notes": "Optional notes",
        "image_url": "/uploads/..."
    }
    """
    data = request.get_json(silent=True) or {}
    items = data.get("items", [])
    if not items:
        return jsonify({"success": False, "message": "Meal must contain at least one item."}), 400

    meal_type = data.get("meal_type", "lunch").lower()
    if meal_type not in ("breakfast", "lunch", "dinner", "snack", "other"):
        meal_type = "lunch"

    meal_date = data.get("meal_date") or date.today().isoformat()
    meal_time = data.get("meal_time") or datetime.now().strftime("%H:%M:%S")

    user_id = session["user_id"]
    try:
        meal_id = Meal.create_meal_with_items(
            user_id=user_id,
            meal_type=meal_type,
            meal_date=meal_date,
            meal_time=meal_time,
            items=items,
            notes=data.get("notes"),
            image_url=data.get("image_url")
        )
        return jsonify({
            "success": True,
            "message": "Meal successfully saved to your nutrition log.",
            "meal_id": meal_id
        }), 201
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to save meal: {str(e)}"}), 500

@meal_bp.route("/api/meals", methods=["GET"])
@login_required
def api_get_meals():
    """Fetches user meals by date or range."""
    user_id = session["user_id"]
    target_date = request.args.get("date")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if target_date:
        meals = Meal.get_user_meals_by_date(user_id, target_date)
    else:
        meals = Meal.get_user_meal_history(user_id, start_date=start_date, end_date=end_date)

    return jsonify({"success": True, "meals": meals})

@meal_bp.route("/api/meals/<int:meal_id>", methods=["GET"])
@login_required
def api_get_meal_details(meal_id):
    user_id = session["user_id"]
    meal = Meal.get_meal_details(meal_id, user_id)
    if not meal:
        return jsonify({"success": False, "message": "Meal not found."}), 404
    return jsonify({"success": True, "meal": meal})

@meal_bp.route("/api/meals/<int:meal_id>", methods=["DELETE"])
@login_required
def api_delete_meal(meal_id):
    user_id = session["user_id"]
    res = Meal.delete_meal(meal_id, user_id)
    if res > 0:
        return jsonify({"success": True, "message": "Meal deleted successfully."})
    return jsonify({"success": False, "message": "Meal not found or unauthorized."}), 404
