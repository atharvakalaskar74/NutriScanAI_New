from datetime import date
from flask import Blueprint, render_template, request, jsonify, session
from models.user import User
from models.nutrition_goal import NutritionGoal
from models.meal import Meal
from models.chat_history import ChatHistory
from services.gemini_service import GeminiService
from routes.auth_routes import login_required

chatbot_bp = Blueprint("chatbot", __name__)

@chatbot_bp.route("/assistant")
@login_required
def assistant_page():
    user_id = session["user_id"]
    history = ChatHistory.get_recent_history(user_id, limit=30)
    user = User.find_by_id(user_id)
    goals = NutritionGoal.get_by_user_id(user_id)
    summary = Meal.get_today_summary(user_id, date.today())

    cal_target = float(goals.get("calorie_target", 2000)) if goals else 2000
    cal_consumed = float(summary.get("total_calories", 0.0))
    cal_remaining = max(0.0, round(cal_target - cal_consumed, 1))

    return render_template(
        "chatbot.html",
        history=history,
        user=user,
        goals=goals,
        summary=summary,
        cal_remaining=cal_remaining
    )

@chatbot_bp.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    """
    Handles user chat message with Gemini AI Nutrition Assistant.
    Injects user profile and today's tracked intake context.
    """
    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"success": False, "message": "Message cannot be empty."}), 400

    user_id = session["user_id"]
    user = User.find_by_id(user_id)
    goals = NutritionGoal.get_by_user_id(user_id)
    summary = Meal.get_today_summary(user_id, date.today())

    # Build context payload
    cal_target = float(goals.get("calorie_target", 2000)) if goals else 2000
    cal_consumed = float(summary.get("total_calories", 0.0))

    user_context = {
        "full_name": user.get("full_name", "User"),
        "age": user.get("age"),
        "gender": user.get("gender"),
        "weight_kg": user.get("weight_kg"),
        "height_cm": user.get("height_cm"),
        "fitness_goal": user.get("fitness_goal"),
        "activity_level": user.get("activity_level"),
        "calorie_target": cal_target,
        "calories_consumed": cal_consumed,
        "calories_remaining": max(0.0, round(cal_target - cal_consumed, 1)),
        "protein_target": float(goals.get("protein_target_g", 75)) if goals else 75,
        "protein_consumed": float(summary.get("total_protein_g", 0.0)),
        "carbs_target": float(goals.get("carbs_target_g", 250)) if goals else 250,
        "carbs_consumed": float(summary.get("total_carbs_g", 0.0)),
        "fat_target": float(goals.get("fat_target_g", 65)) if goals else 65,
        "fat_consumed": float(summary.get("total_fat_g", 0.0)),
        "meal_count": int(summary.get("meal_count", 0))
    }

    # Fetch recent conversation history
    history = ChatHistory.get_recent_history(user_id, limit=6)

    # Save user message to database
    ChatHistory.save_message(user_id=user_id, role="user", message=user_message)

    # Call Gemini Assistant
    ai_res = GeminiService.chat_assistant(
        user_message=user_message,
        user_context=user_context,
        conversation_history=history
    )

    if not ai_res.get("success"):
        return jsonify({
            "success": False,
            "error_code": ai_res.get("error_code", "CHAT_ERROR"),
            "message": ai_res.get("message", "AI Assistant is currently unavailable.")
        }), 500

    reply = ai_res.get("reply", "")

    # Save assistant reply to database
    ChatHistory.save_message(user_id=user_id, role="assistant", message=reply)

    return jsonify({
        "success": True,
        "reply": reply
    })

@chatbot_bp.route("/api/chat/history", methods=["GET"])
@login_required
def api_chat_history():
    user_id = session["user_id"]
    history = ChatHistory.get_recent_history(user_id, limit=50)
    return jsonify({"success": True, "history": history})

@chatbot_bp.route("/api/chat/history", methods=["DELETE"])
@login_required
def api_clear_chat():
    user_id = session["user_id"]
    ChatHistory.clear_history(user_id)
    return jsonify({"success": True, "message": "Chat history cleared."})
