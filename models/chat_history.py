from database.db import execute_query

class ChatHistory:
    """Model for saving and retrieving conversational exchanges with the AI Assistant."""

    @classmethod
    def save_message(cls, user_id, role, message):
        """Saves a single message (role='user' or 'assistant')."""
        sql = "INSERT INTO chat_history (user_id, role, message) VALUES (%s, %s, %s);"
        return execute_query(sql, (user_id, role, message.strip()), insert_id=True)

    @classmethod
    def get_recent_history(cls, user_id, limit=20):
        """Fetches the latest messages in chronological order."""
        sql = """
            SELECT * FROM (
                SELECT * FROM chat_history
                WHERE user_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT %s
            ) sub
            ORDER BY created_at ASC, id ASC;
        """
        return execute_query(sql, (user_id, limit), fetchall=True) or []

    @classmethod
    def clear_history(cls, user_id):
        """Clears all chat history for a given user."""
        sql = "DELETE FROM chat_history WHERE user_id = %s;"
        return execute_query(sql, (user_id,))
