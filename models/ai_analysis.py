from database.db import execute_query

class AiAnalysis:
    """Model for logging AI image scan results and rejection diagnostics."""

    @classmethod
    def log_analysis(cls, user_id, image_path, is_food, confidence=None, raw_response=None, rejection_reason=None):
        """Logs an AI image scan interaction."""
        sql = """
            INSERT INTO ai_analyses (
                user_id, image_path, is_food, confidence, raw_response, rejection_reason
            ) VALUES (%s, %s, %s, %s, %s, %s);
        """
        return execute_query(
            sql,
            (user_id, image_path, is_food,
             float(confidence) if confidence is not None else None,
             raw_response, rejection_reason),
            insert_id=True
        )
