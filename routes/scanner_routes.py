from flask import Blueprint, render_template, request, jsonify, session
from services.validation_service import ValidationService
from services.food_analysis_service import FoodAnalysisService
from routes.auth_routes import login_required

scanner_bp = Blueprint("scanner", __name__)

@scanner_bp.route("/scanner")
@login_required
def scanner_page():
    return render_template("scanner.html")

@scanner_bp.route("/api/scan", methods=["POST"])
@login_required
def api_scan():
    """
    Endpoint for AI Food Recognition.
    Accepts multipart/form-data containing 'image' file.
    Validates file format, compresses image, queries Gemini multimodal AI,
    and returns food or non-food structured payload.
    """
    if "image" not in request.files and "file" not in request.files:
        return jsonify({
            "success": False,
            "error_code": "NO_FILE",
            "message": "No image file provided. Please capture or upload a food picture."
        }), 400

    file_obj = request.files.get("image") or request.files.get("file")
    is_valid, err_msg = ValidationService.validate_image_file(file_obj)
    if not is_valid:
        return jsonify({
            "success": False,
            "error_code": "INVALID_FILE",
            "message": err_msg
        }), 400

    user_id = session.get("user_id")
    result = FoodAnalysisService.process_and_analyze(file_obj, user_id=user_id)

    status_code = 200 if result.get("success") else 500
    if result.get("error_code") == "NO_API_KEY":
        status_code = 503  # Service Unavailable / Unconfigured
    elif result.get("error_code") == "QUOTA_EXCEEDED":
        status_code = 429  # Rate limited

    return jsonify(result), status_code
