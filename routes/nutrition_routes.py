from flask import Blueprint, request, jsonify
from services.nutrition_service import NutritionService
from models.food import Food
from routes.auth_routes import login_required

nutrition_bp = Blueprint("nutrition", __name__)

@nutrition_bp.route("/api/nutrition/recalculate", methods=["POST"])
@login_required
def api_recalculate():
    """
    Recalculates nutrition values when user adjusts portion weight.
    Accepts: { "items": [ { "food_id": 1, "weight_g": 250, "nutrition_per_100g": {...} } ] }
    Returns: Recalculated items and updated combined totals.
    """
    data = request.get_json(silent=True) or {}
    items = data.get("items", [])
    if not items:
        return jsonify({"success": False, "message": "No items provided for recalculation."}), 400

    try:
        result = NutritionService.recalculate_items(items)
        return jsonify({
            "success": True,
            "items": result["items"],
            "totals": result["totals"]
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Recalculation error: {str(e)}"}), 500

@nutrition_bp.route("/api/nutrition/search", methods=["GET"])
@login_required
def api_search():
    """Search cached food database by name."""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"success": True, "results": []})

    food = Food.find_by_name(query)
    results = [food] if food else []
    return jsonify({"success": True, "results": results})
