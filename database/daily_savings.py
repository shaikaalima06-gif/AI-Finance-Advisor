from connection import get_connection
from goals import add_money_to_goal


def add_daily_saving(user_id, goal_id, amount, date):
    """Records a daily saving entry and updates the linked goal's current_amount."""
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO daily_savings (user_id, goal_id, amount, date)
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (user_id, goal_id, amount, date))
    conn.commit()
    new_saving_id = cursor.lastrowid
    cursor.close()
    conn.close()

    # Keep the goal's current_amount in sync automatically
    add_money_to_goal(goal_id, amount)

    return new_saving_id


def get_savings_history(user_id, goal_id=None):
    """Returns all savings entries for a user, optionally filtered to one goal."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if goal_id:
        query = "SELECT * FROM daily_savings WHERE user_id = %s AND goal_id = %s ORDER BY date"
        cursor.execute(query, (user_id, goal_id))
    else:
        query = "SELECT * FROM daily_savings WHERE user_id = %s ORDER BY date"
        cursor.execute(query, (user_id,))

    history = cursor.fetchall()
    cursor.close()
    conn.close()
    return history


def get_total_savings(user_id, goal_id=None):
    """Returns the sum of all savings for a user, optionally for one goal."""
    conn = get_connection()
    cursor = conn.cursor()

    if goal_id:
        query = "SELECT SUM(amount) FROM daily_savings WHERE user_id = %s AND goal_id = %s"
        cursor.execute(query, (user_id, goal_id))
    else:
        query = "SELECT SUM(amount) FROM daily_savings WHERE user_id = %s"
        cursor.execute(query, (user_id,))

    total = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return float(total) if total else 0.0


def delete_saving(saving_id, goal_id, amount):
    """Deletes a saving entry and subtracts the amount back from the goal's current_amount."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM daily_savings WHERE saving_id = %s", (saving_id,))
    conn.commit()
    cursor.close()
    conn.close()

    # Reverse the goal update
    conn = get_connection()
    cursor = conn.cursor()
    query = "UPDATE goals SET current_amount = GREATEST(current_amount - %s, 0) WHERE goal_id = %s"
    cursor.execute(query, (amount, goal_id))
    conn.commit()
    cursor.close()
    conn.close()