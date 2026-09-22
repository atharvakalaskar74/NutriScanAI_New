import os
from flask import Flask, render_template, send_from_directory, jsonify, session, redirect, url_for
from config.config import Config
from database.db import init_db, check_db_connection

def create_app():
    """Application factory for NutriScan AI."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure upload directory exists
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    # Initialize database tables and seed data if MySQL is running
    try:
        init_db()
    except Exception as e:
        app.logger.warning(f"Database initialization deferred: {e}")

    # Register Route Blueprints
    from routes.auth_routes import auth_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.scanner_routes import scanner_bp
    from routes.nutrition_routes import nutrition_bp
    from routes.meal_routes import meal_bp
    from routes.goals_routes import goals_bp
    from routes.chatbot_routes import chatbot_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(scanner_bp)
    app.register_blueprint(nutrition_bp)
    app.register_blueprint(meal_bp)
    app.register_blueprint(goals_bp)
    app.register_blueprint(chatbot_bp)

    # Root landing page
    @app.route("/")
    def index():
        if "user_id" in session:
            return redirect(url_for("dashboard.dashboard_page"))
        return render_template("index.html")

    # Secure uploads route with ephemeral resilience
    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        full_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        if os.path.isfile(full_path):
            return send_from_directory(Config.UPLOAD_FOLDER, filename)
        
        # Return clean food placeholder if file was removed after dyno restart
        from flask import Response
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">'
            '<rect width="400" height="300" fill="#f8fafc" stroke="#e2e8f0" stroke-width="2"/>'
            '<text x="50%" y="45%" dominant-baseline="middle" text-anchor="middle" font-size="48">🍽️</text>'
            '<text x="50%" y="65%" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" font-size="14" fill="#64748b">NutriScan AI — Meal Record Preserved</text>'
            '</svg>'
        )
        return Response(svg, mimetype="image/svg+xml")

    # Health check endpoint for deployment monitoring
    @app.route("/health")
    def health_check():
        db_ok = check_db_connection()
        return jsonify({
            "status": "healthy" if db_ok else "degraded",
            "database_connected": db_ok,
            "version": "1.0.0",
            "gemini_model": Config.GEMINI_MODEL
        }), (200 if db_ok else 503)

    # Error Handlers
    @app.errorhandler(404)
    def handle_not_found(e):
        return render_template("base.html", content_override="<div class='container' style='text-align: center; padding: 4rem 1rem;'><h2>404 — Page Not Found</h2><p style='color: var(--text-muted);'>The requested page does not exist.</p><a href='/' class='btn btn-primary' style='margin-top: 1rem;'>Return Home</a></div>"), 404

    @app.errorhandler(413)
    def handle_large_file(e):
        return jsonify({
            "success": False,
            "error_code": "FILE_TOO_LARGE",
            "message": "The uploaded image exceeds the 16 MB maximum size limit. Please choose a smaller photo."
        }), 413

    @app.errorhandler(500)
    def handle_server_error(e):
        app.logger.error(f"Internal Server Error: {e}")
        return jsonify({
            "success": False,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again."
        }), 500

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
