from .auth_routes import auth_bp
from .dashboard_routes import dashboard_bp
from .scanner_routes import scanner_bp
from .nutrition_routes import nutrition_bp
from .meal_routes import meal_bp
from .goals_routes import goals_bp
from .chatbot_routes import chatbot_bp

__all__ = [
    "auth_bp",
    "dashboard_bp",
    "scanner_bp",
    "nutrition_bp",
    "meal_bp",
    "goals_bp",
    "chatbot_bp"
]
