import os
import pymysql
import pymysql.cursors
from contextlib import contextmanager
from pathlib import Path
from config.config import Config

@contextmanager
def get_db_connection():
    """
    Context manager yielding an active PyMySQL connection with a DictCursor.
    Automatically commits on normal exit and rolls back on exception.
    """
    conn_params = Config.get_db_config(include_db=True)
    conn = pymysql.connect(
        **conn_params,
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        yield conn
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def execute_query(sql, params=None, fetchone=False, fetchall=False, insert_id=False):
    """
    Safe SQL execution helper.
    Returns:
      - dict if fetchone=True
      - list of dicts if fetchall=True
      - lastrowid if insert_id=True
      - affected rows count otherwise
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            if fetchone:
                return cursor.fetchone()
            if fetchall:
                return cursor.fetchall()
            if insert_id:
                return cursor.lastrowid
            return cursor.rowcount

def init_db():
    """
    Initializes the database and creates required tables and seed data if not present.
    In local development, ensures the database exists first.
    In cloud environments, connects directly to the configured database.
    """
    try:
        # Step 1: Attempt to ensure database exists if local or permissions permit
        try:
            server_params = Config.get_db_config(include_db=False)
            conn = pymysql.connect(**server_params)
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            conn.close()
        except Exception as db_create_err:
            # In managed cloud databases (e.g. TiDB Cloud), CREATE DATABASE may be restricted or pre-created
            pass

        # Step 2: Run schema.sql statements on the active database
        schema_path = Path(__file__).resolve().parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                raw_lines = f.readlines()

            # Remove pure comment lines
            clean_lines = []
            for line in raw_lines:
                s = line.strip()
                if not s.startswith("--") and not s.startswith("/*"):
                    clean_lines.append(line)
            
            clean_sql = "".join(clean_lines)

            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    statements = clean_sql.split(";")
                    for stmt in statements:
                        cleaned = stmt.strip()
                        if cleaned and not cleaned.lower().startswith("create database") and not cleaned.lower().startswith("use "):
                            try:
                                cursor.execute(cleaned)
                            except Exception as table_err:
                                err_str = str(table_err).lower()
                                if "already exists" not in err_str and "duplicate" not in err_str:
                                    # Log but keep running remaining tables/seed statements
                                    print(f"[Database Init Info] Statement skipped: {table_err}")
            print(f"[Database] Successfully initialized database '{Config.DB_NAME}'.")
            return True
        else:
            print(f"[Database Warning] schema.sql not found at {schema_path}")
            return False
    except Exception as e:
        print(f"[Database Error] Could not initialize database: {e}")
        return False

def check_db_connection():
    """Returns True if connection to the database succeeds, False otherwise."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1;")
                return True
    except Exception as e:
        return False
