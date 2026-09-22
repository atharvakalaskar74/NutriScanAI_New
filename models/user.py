from werkzeug.security import generate_password_hash, check_password_hash
from database.db import execute_query

class User:
    """User data access model."""

    @staticmethod
    def hash_password(password):
        return generate_password_hash(password)

    @staticmethod
    def verify_password(stored_hash, password):
        return check_password_hash(stored_hash, password)

    @classmethod
    def create(cls, full_name, email, password, age=None, gender='other',
               height_cm=None, weight_kg=None, activity_level='sedentary',
               fitness_goal='maintain'):
        """Creates a new user record with hashed password."""
        pwd_hash = cls.hash_password(password)
        sql = """
            INSERT INTO users (
                full_name, email, password_hash, age, gender,
                height_cm, weight_kg, activity_level, fitness_goal
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        user_id = execute_query(
            sql,
            (full_name.strip(), email.strip().lower(), pwd_hash,
             age if age else None, gender,
             height_cm if height_cm else None,
             weight_kg if weight_kg else None,
             activity_level, fitness_goal),
            insert_id=True
        )
        return user_id

    @classmethod
    def find_by_email(cls, email):
        """Finds user by email (case-insensitive)."""
        sql = "SELECT * FROM users WHERE email = %s LIMIT 1;"
        return execute_query(sql, (email.strip().lower(),), fetchone=True)

    @classmethod
    def find_by_id(cls, user_id):
        """Finds user by primary key id."""
        sql = "SELECT * FROM users WHERE id = %s LIMIT 1;"
        return execute_query(sql, (user_id,), fetchone=True)

    @classmethod
    def update_profile(cls, user_id, full_name, age, gender, height_cm, weight_kg, activity_level, fitness_goal):
        """Updates user profile information."""
        sql = """
            UPDATE users SET
                full_name = %s,
                age = %s,
                gender = %s,
                height_cm = %s,
                weight_kg = %s,
                activity_level = %s,
                fitness_goal = %s
            WHERE id = %s;
        """
        return execute_query(
            sql,
            (full_name.strip(),
             age if age else None,
             gender,
             height_cm if height_cm else None,
             weight_kg if weight_kg else None,
             activity_level,
             fitness_goal,
             user_id)
        )

    @classmethod
    def update_password(cls, user_id, new_password):
        """Updates user password hash."""
        pwd_hash = cls.hash_password(new_password)
        sql = "UPDATE users SET password_hash = %s WHERE id = %s;"
        return execute_query(sql, (pwd_hash, user_id))
