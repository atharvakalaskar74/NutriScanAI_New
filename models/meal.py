from datetime import date, datetime, timedelta
from decimal import Decimal
from database.db import execute_query, get_db_connection

def serialize_row(row):
    """Converts Decimal, date, datetime, and timedelta fields to JSON-serializable primitives."""
    if not row:
        return row
    clean = dict(row)
    for k, v in clean.items():
        if isinstance(v, (datetime, date)):
            clean[k] = v.isoformat()
        elif isinstance(v, timedelta):
            total_sec = int(v.total_seconds())
            hours = total_sec // 3600
            minutes = (total_sec % 3600) // 60
            seconds = total_sec % 60
            clean[k] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        elif isinstance(v, Decimal):
            clean[k] = float(v)
    return clean

class Meal:
    """Data access model for meals and individual meal items."""

    @classmethod
    def create_meal_with_items(cls, user_id, meal_type, meal_date, meal_time, items, notes=None, image_url=None):
        """
        Creates a parent meal and child meal_items transactionally.
        Calculates totals across all items.
        """
        if not items:
            raise ValueError("A meal must contain at least one item.")

        total_cal = sum(float(i.get("calories", 0.0)) for i in items)
        total_pro = sum(float(i.get("protein_g", 0.0)) for i in items)
        total_carb = sum(float(i.get("carbs_g", i.get("carbohydrates_g", 0.0))) for i in items)
        total_fat = sum(float(i.get("fat_g", 0.0)) for i in items)
        total_fib = sum(float(i.get("fiber_g", 0.0)) for i in items)
        total_sug = sum(float(i.get("sugar_g", 0.0)) for i in items)

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 1. Insert meal
                cursor.execute("""
                    INSERT INTO meals (
                        user_id, meal_type, meal_date, meal_time,
                        total_calories, total_protein_g, total_carbs_g,
                        total_fat_g, total_fiber_g, total_sugar_g,
                        notes, image_url
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (
                    user_id, meal_type, meal_date, meal_time,
                    total_cal, total_pro, total_carb,
                    total_fat, total_fib, total_sug,
                    notes, image_url
                ))
                meal_id = cursor.lastrowid

                # 2. Insert items
                for item in items:
                    cursor.execute("""
                        INSERT INTO meal_items (
                            meal_id, food_name, food_id, weight_g,
                            calories, protein_g, carbs_g, fat_g, fiber_g, sugar_g, source
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """, (
                        meal_id,
                        item.get("name", item.get("food_name", "Unknown item")),
                        item.get("food_id"),
                        float(item.get("weight_g", item.get("estimated_weight_g", 100.0))),
                        float(item.get("calories", 0.0)),
                        float(item.get("protein_g", 0.0)),
                        float(item.get("carbs_g", item.get("carbohydrates_g", 0.0))),
                        float(item.get("fat_g", 0.0)),
                        float(item.get("fiber_g", 0.0)),
                        float(item.get("sugar_g", 0.0)),
                        item.get("source", "ai_estimated")
                    ))
                return meal_id

    @classmethod
    def get_user_meals_by_date(cls, user_id, meal_date):
        """Fetches all meals logged on a given date for a user, including child items."""
        sql_meals = """
            SELECT * FROM meals
            WHERE user_id = %s AND meal_date = %s
            ORDER BY meal_time ASC;
        """
        raw_meals = execute_query(sql_meals, (user_id, meal_date), fetchall=True) or []
        meals = [serialize_row(m) for m in raw_meals]
        for meal in meals:
            sql_items = "SELECT * FROM meal_items WHERE meal_id = %s ORDER BY id ASC;"
            raw_items = execute_query(sql_items, (meal["id"],), fetchall=True) or []
            meal["items"] = [serialize_row(i) for i in raw_items]
        return meals

    @classmethod
    def get_user_meal_history(cls, user_id, start_date=None, end_date=None, limit=50):
        """Fetches recent meal history optionally filtered by date range."""
        params = [user_id]
        where_clauses = ["user_id = %s"]

        if start_date:
            where_clauses.append("meal_date >= %s")
            params.append(start_date)
        if end_date:
            where_clauses.append("meal_date <= %s")
            params.append(end_date)

        params.append(limit)
        sql = f"""
            SELECT * FROM meals
            WHERE {' AND '.join(where_clauses)}
            ORDER BY meal_date DESC, meal_time DESC
            LIMIT %s;
        """
        raw_meals = execute_query(sql, tuple(params), fetchall=True) or []
        meals = [serialize_row(m) for m in raw_meals]
        for meal in meals:
            sql_items = "SELECT * FROM meal_items WHERE meal_id = %s ORDER BY id ASC;"
            raw_items = execute_query(sql_items, (meal["id"],), fetchall=True) or []
            meal["items"] = [serialize_row(i) for i in raw_items]
        return meals

    @classmethod
    def get_meal_details(cls, meal_id, user_id):
        """Fetches a single meal by ID ensuring it belongs to the logged-in user."""
        sql = "SELECT * FROM meals WHERE id = %s AND user_id = %s LIMIT 1;"
        raw_meal = execute_query(sql, (meal_id, user_id), fetchone=True)
        if not raw_meal:
            return None
        meal = serialize_row(raw_meal)
        items_sql = "SELECT * FROM meal_items WHERE meal_id = %s;"
        raw_items = execute_query(items_sql, (meal_id,), fetchall=True) or []
        meal["items"] = [serialize_row(i) for i in raw_items]
        return meal

    @classmethod
    def delete_meal(cls, meal_id, user_id):
        """Deletes a meal if owned by user."""
        sql = "DELETE FROM meals WHERE id = %s AND user_id = %s;"
        return execute_query(sql, (meal_id, user_id))

    @classmethod
    def get_today_summary(cls, user_id, target_date=None):
        """
        Aggregates calories and macros consumed on target_date (defaults to today).
        """
        if not target_date:
            target_date = date.today()

        sql = """
            SELECT 
                COUNT(*) as meal_count,
                COALESCE(SUM(total_calories), 0.0) as total_calories,
                COALESCE(SUM(total_protein_g), 0.0) as total_protein_g,
                COALESCE(SUM(total_carbs_g), 0.0) as total_carbs_g,
                COALESCE(SUM(total_fat_g), 0.0) as total_fat_g,
                COALESCE(SUM(total_fiber_g), 0.0) as total_fiber_g,
                COALESCE(SUM(total_sugar_g), 0.0) as total_sugar_g
            FROM meals
            WHERE user_id = %s AND meal_date = %s;
        """
        res = execute_query(sql, (user_id, target_date), fetchone=True)
        if res:
            return serialize_row(res)
        return {
            "meal_count": 0,
            "total_calories": 0.0,
            "total_protein_g": 0.0,
            "total_carbs_g": 0.0,
            "total_fat_g": 0.0,
            "total_fiber_g": 0.0,
            "total_sugar_g": 0.0,
        }
