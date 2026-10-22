
from datetime import date as Date
from decimal import Decimal, InvalidOperation

from database.connection import get_connection
from mysql.connector import Error


def _validate_amount(amount):
    """Validate a positive monetary amount with at most 2 decimal places."""
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Saving amount must be a valid number.")

    if not value.is_finite() or value <= 0:
        raise ValueError("Saving amount must be greater than zero.")

    if value.as_tuple().exponent < -2:
        raise ValueError("Saving amount can have at most 2 decimal places.")

    return value


def _close_resources(cursor, conn):
    """Close cursor and connection safely."""
    if cursor is not None:
        try:
            cursor.close()
        except Error:
            pass

    if conn is not None:
        try:
            conn.close()
        except Error:
            pass


def add_daily_saving(user_id, goal_id, amount, saving_date):
    """
    Record a saving and update its goal atomically.
    Reject savings that would exceed the goal target.
    """
    amount = _validate_amount(amount)

    if not isinstance(saving_date, Date):
        raise ValueError("saving_date must be a datetime.date value.")

    conn = None
    cursor = None

    try:
        conn = get_connection()
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)

        # Lock the goal row so concurrent savings cannot exceed its target.
        cursor.execute(
            """
            SELECT target_amount, current_amount
            FROM goals
            WHERE goal_id = %s AND user_id = %s
            FOR UPDATE
            """,
            (goal_id, user_id),
        )
        goal = cursor.fetchone()

        if goal is None:
            raise ValueError("Goal not found for this user.")

        current = Decimal(str(goal["current_amount"]))
        target = Decimal(str(goal["target_amount"]))

        if current + amount > target:
            raise ValueError(
                f"Saving exceeds the remaining goal amount of "
                f"{target - current}."
            )

        cursor.execute(
            """
            INSERT INTO daily_savings (user_id, goal_id, amount, date)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, goal_id, amount, saving_date),
        )
        saving_id = cursor.lastrowid

        cursor.execute(
            """
            UPDATE goals
            SET current_amount = current_amount + %s
            WHERE goal_id = %s AND user_id = %s
            """,
            (amount, goal_id, user_id),
        )

        if cursor.rowcount != 1:
            raise RuntimeError("Goal update failed.")

        conn.commit()
        return saving_id

    except Exception:
        if conn is not None:
            try:
                conn.rollback()
            except Error:
                pass
        raise

    finally:
        _close_resources(cursor, conn)


def get_savings_history(user_id, goal_id=None):
    """Return a user's saving history, optionally filtered by goal."""
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        if goal_id is not None:
            cursor.execute(
                """
                SELECT *
                FROM daily_savings
                WHERE user_id = %s AND goal_id = %s
                ORDER BY date, saving_id
                """,
                (user_id, goal_id),
            )
        else:
            cursor.execute(
                """
                SELECT *
                FROM daily_savings
                WHERE user_id = %s
                ORDER BY date, saving_id
                """,
                (user_id,),
            )

        return cursor.fetchall()

    finally:
        _close_resources(cursor, conn)


def get_total_savings(user_id, goal_id=None):
    """Return the total amount recorded in daily savings."""
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        if goal_id is not None:
            cursor.execute(
                """
                SELECT COALESCE(SUM(amount), 0)
                FROM daily_savings
                WHERE user_id = %s AND goal_id = %s
                """,
                (user_id, goal_id),
            )
        else:
            cursor.execute(
                """
                SELECT COALESCE(SUM(amount), 0)
                FROM daily_savings
                WHERE user_id = %s
                """,
                (user_id,),
            )

        return Decimal(str(cursor.fetchone()[0]))

    finally:
        _close_resources(cursor, conn)


def delete_saving(user_id, saving_id):
    """
    Delete a user's saving and reverse its goal balance atomically.
    The amount and goal ID are read from the database, not supplied
    by the caller.
    """
    conn = None
    cursor = None

    try:
        conn = get_connection()
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)

        # Lock the saving record and verify ownership.
        cursor.execute(
            """
            SELECT saving_id, goal_id, amount
            FROM daily_savings
            WHERE saving_id = %s AND user_id = %s
            FOR UPDATE
            """,
            (saving_id, user_id),
        )
        saving = cursor.fetchone()

        if saving is None:
            raise ValueError("Saving record not found for this user.")

        goal_id = saving["goal_id"]
        amount = Decimal(str(saving["amount"]))

        # Lock the goal row and verify ownership.
        cursor.execute(
            """
            SELECT current_amount
            FROM goals
            WHERE goal_id = %s AND user_id = %s
            FOR UPDATE
            """,
            (goal_id, user_id),
        )
        goal = cursor.fetchone()

        if goal is None:
            raise ValueError("Associated goal not found for this user.")

        current = Decimal(str(goal["current_amount"]))

        if current < amount:
            raise RuntimeError(
                "Goal balance is inconsistent with the saving record."
            )

        cursor.execute(
            """
            DELETE FROM daily_savings
            WHERE saving_id = %s AND user_id = %s
            """,
            (saving_id, user_id),
        )

        if cursor.rowcount != 1:
            raise RuntimeError("Saving deletion failed.")

        cursor.execute(
            """
            UPDATE goals
            SET current_amount = current_amount - %s
            WHERE goal_id = %s AND user_id = %s
            """,
            (amount, goal_id, user_id),
        )

        if cursor.rowcount != 1:
            raise RuntimeError("Goal balance update failed.")

        conn.commit()

    except Exception:
        if conn is not None:
            try:
                conn.rollback()
            except Error:
                pass
        raise

    finally:
        _close_resources(cursor, conn)
